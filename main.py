import os
import shutil
import traceback
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

# LangChain Document Loaders & Splitters (Using PyMuPDFLoader to match pymupdf)
from langchain_community.document_loaders import PyMuPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS

# Google Gemini Integration (LLM & Cloud Embeddings)
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings

# Modern Core LCEL Imports
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough

# Load Environment Variables
load_dotenv()

api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
if not api_key:
    raise ValueError("GOOGLE_API_KEY (or GEMINI_API_KEY) is missing from environment variables!")

os.environ["GOOGLE_API_KEY"] = api_key

# Initialize FastAPI App
app = FastAPI(title="AI Research Assistant")

# Configure CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = "uploaded_docs"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Cache for Vector Stores
vector_stores = {}

# Standard Gemini Embeddings
embeddings = GoogleGenerativeAIEmbeddings(model="gemini-embedding-2-preview")

llm = ChatGoogleGenerativeAI(
    model="gemini-3.5-flash",
    temperature=0.2,
    max_retries=2
)


def format_docs(docs):
    return "\n\n".join(doc.page_content for doc in docs)


# Request Models
class SummarizePayload(BaseModel):
    filename: str

class QueryPayload(BaseModel):
    filename: str
    question: str


# --- API ENDPOINTS ---

@app.get("/")
def home():
    return {"status": "online", "message": "AI Research Assistant API is running!"}


@app.post("/api/upload")
async def upload_document(file: UploadFile = File(...)):
    try:
        file_path = os.path.join(UPLOAD_DIR, file.filename)
        
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # PyMuPDFLoader uses the pymupdf library
        loader = PyMuPDFLoader(file_path)
        documents = loader.load()
        
        if not documents:
            raise HTTPException(status_code=400, detail="Could not extract text from PDF.")
        
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=150)
        split_docs = text_splitter.split_documents(documents)
        
        vector_store = FAISS.from_documents(split_docs, embeddings)
        vector_stores[file.filename] = vector_store
        
        print(f"✅ Indexed '{file.filename}': {len(split_docs)} chunks embedded via Google API.")
        
        return {
            "message": "File processed successfully.",
            "filename": file.filename,
            "document": {
                "id": file.filename,
                "filename": file.filename
            }
        }

    except Exception as e:
        print("❌ Upload Error:")
        traceback.print_exc()
        raise HTTPException(
            status_code=500, 
            detail=f"Upload Failed ({type(e).__name__}): {str(e)}"
        )


@app.post("/api/summarize")
async def summarize_document(payload: SummarizePayload):
    filename = payload.filename
    file_path = os.path.join(UPLOAD_DIR, filename)

    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found.")

    try:
        loader = PyMuPDFLoader(file_path)
        docs = loader.load()
        full_text = "\n\n".join([doc.page_content for doc in docs])[:3000]

        # Explicitly instruct Gemini to use clean line breaks and bullet points
        prompt = ChatPromptTemplate.from_template(
            "Summarize the following document in clean, well-formatted Markdown with separate bullet points.\n"
            "Use line breaks between each point.\n\n"
            "Format example:\n"
            "- **Document Objective:** ...\n"
            "- **Structure & Key Sections:** ...\n"
            "- **Conclusion:** ...\n\n"
            "Document Text:\n{text}"
        )
        
        chain = prompt | llm | StrOutputParser()
        summary_text = chain.invoke({"text": full_text})

        return {"summary": summary_text}

    except Exception as e:
        print(f"❌ Summarization Error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to summarize: {str(e)}")

@app.post("/api/query")
async def query_document(payload: QueryPayload):
    filename = payload.filename
    question = payload.question

    if filename not in vector_stores:
        raise HTTPException(
            status_code=400, 
            detail="Document vector index not found. Please upload the file first."
        )

    try:
        vector_store = vector_stores[filename]
        # Fetch top relevant chunks
        retriever = vector_store.as_retriever(search_kwargs={"k": 4})

        prompt = ChatPromptTemplate.from_template(
            "You are an AI assistant. Answer the user's question using ONLY the provided context.\n"
            "If the answer cannot be deduced from the context, say 'The requested information is not in the document.'\n\n"
            "Context:\n{context}\n\n"
            "Question: {question}"
        )

        rag_chain = (
            {"context": retriever | format_docs, "question": RunnablePassthrough()}
            | prompt
            | llm
            | StrOutputParser()
        )

        answer = rag_chain.invoke(question)
        return {"answer": answer}

    except Exception as e:
        print(f"❌ Query Error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to process query: {str(e)}")