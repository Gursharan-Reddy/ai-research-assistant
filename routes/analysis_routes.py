from fastapi import APIRouter
from pydantic import BaseModel
from typing import List
from src.vector_store.manager import VectorStoreManager
from src.rag.summarizer import DocumentSummarizer
from src.rag.comparator import DocumentComparator

router = APIRouter(prefix="/analysis", tags=["Summarization & Comparison"])
vector_manager = VectorStoreManager()
summarizer = DocumentSummarizer(vector_manager)
comparator = DocumentComparator(vector_manager)

class CompareRequest(BaseModel):
    doc_ids: List[str]

@router.get("/summarize/{doc_id}")
def summarize_document(doc_id: str):
    return summarizer.generate_summary(doc_id)

@router.post("/compare")
def compare_documents(req: CompareRequest):
    return comparator.compare_documents(req.doc_ids)