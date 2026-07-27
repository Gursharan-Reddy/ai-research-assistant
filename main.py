import os
import shutil
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

# LangChain Document Loaders & Splitters
from langchain_community.document_loaders import PyPDFLoader
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

# Google Cloud API Embeddings (Lightweight, instant server startup)
embeddings = GoogleGenerativeAIEmbeddings(model="models/text-embedding-004")

# Gemini LLM Initialization
llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash", temperature=0.2)


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
        
        loader = PyPDFLoader(file_path)
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
        print(f"❌ Upload Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/summarize")
async def summarize_document(payload: SummarizePayload):
    filename = payload.filename
    file_path = os.path.join(UPLOAD_DIR, filename)

    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found.")

    try:
        loader = PyPDFLoader(file_path)
        docs = loader.load()
        full_text = "\n\n".join([doc.page_content for doc in docs])

        prompt = ChatPromptTemplate.from_template(
            "Summarize the following document concisely, highlighting key objectives, findings, and conclusions:\n\n{text}"
        )
        
        chain = prompt | llm | StrOutputParser()
        summary_text = chain.invoke({"text": full_text[:4000]})

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
        retriever = vector_store.as_retriever(search_kwargs={"k": 8})

        prompt = ChatPromptTemplate.from_template(
            "Answer the question based strictly on the provided context below. "
            "If the answer is not contained in the context, respond with 'The requested information is not in the document.'\n\n"
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