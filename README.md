# AI Research & Knowledge Assistant

An enterprise-grade Retrieval-Augmented Generation (RAG) backend designed to process, summarize, compare, and analyze technical research documents and enterprise knowledge bases with strict citation tracking and deep learning domain classification.

## Tech Stack
- **Framework:** FastAPI, Pydantic, SQLAlchemy
- **Document Ingestion:** PyMuPDF (fitz)
- **Vector DB & Embeddings:** ChromaDB, Sentence-Transformers (`all-MiniLM-L6-v2`)
- **LLM Engine:** OpenAI GPT-3.5-Turbo / GPT-4
- **Machine Learning:** TensorFlow / Keras (Text Classification)
- **Search:** BM25 Keyword Search & Dense Vector Similarity Search (Hybrid)

## Features
1. **Document Management:** Upload multi-page PDFs with background parsing and SQLite metadata persistence.
2. **Intelligent Chunking:** Page-aware sliding window chunking (~900 chars with 150-char overlap).
3. **TensorFlow Classification:** Deep Learning model trained to auto-categorize uploaded technical PDFs into defined domains.
4. **Citation Grounding:** Answers questions with explicit document source names and page number references.
5. **Multi-Document Comparison & Summarization:** Extracts multi-tier executive summaries and comparative breakdowns across multiple documents.
6. **Conversational Memory:** Maintains multi-turn context across user interactions.

## Setup Instructions

1. **Initialize Virtual Environment (PowerShell):**
   ```powershell
   python -m venv venv
   .\venv\Scripts\Activate.ps1
   pip install -r requirements.txt

Set Environment Variables:
Create a .env file from .env.example:

Ini, TOML
OPENAI_API_KEY=your_openai_api_key_here
VECTOR_DB_DIR=./data/vector_db
MODEL_PATH=./models/tf_classifier.h5
TOKENIZER_PATH=./models/tokenizer.pickle
DATABASE_URL=sqlite:///./data/assistant.db

Run Application:

PowerShell
python main.py
Access Interactive Swagger API Docs at: http://localhost:8000/docs
---

## Execution Verification Steps

To launch and verify the full suite in PowerShell:

```powershell
# 1. Start Server
python main.py
Navigate to http://localhost:8000/docs in your browser.

Use POST /documents/upload to upload a PDF research paper.

Check GET /documents/list to inspect auto-extracted page counts, chunk metrics, and TensorFlow predicted categories.

Call POST /search/query with a question about the document to receive grounded answers with document names and page references.