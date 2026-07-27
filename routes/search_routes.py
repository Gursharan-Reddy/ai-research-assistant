from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from src.database.base import get_db
from src.database.models import ConversationSession
from src.vector_store.manager import VectorStoreManager
from src.rag.qa_chain import RAGEngine
from src.analytics.metrics import AnalyticsEngine

router = APIRouter(prefix="/search", tags=["Search & RAG QA"])
vector_manager = VectorStoreManager()
rag_engine = RAGEngine(vector_manager)

class QueryRequest(BaseModel):
    query: str
    session_id: str = "default_session"
    search_mode: str = "hybrid"

@router.post("/query")
def answer_question(req: QueryRequest, db: Session = Depends(get_db)):
    history_records = db.query(ConversationSession).filter(
        ConversationSession.session_id == req.session_id
    ).order_by(ConversationSession.timestamp.desc()).limit(3).all()

    history_str = "\n".join([f"User: {h.user_query}\nAssistant: {h.assistant_response}" for h in reversed(history_records)])

    response_data = rag_engine.answer_question(req.query, conversation_history=history_str, mode=req.search_mode)

    db.add(ConversationSession(
        session_id=req.session_id,
        user_query=req.query,
        assistant_response=response_data["answer"]
    ))
    db.commit()

    AnalyticsEngine.log_event(db, "question_asked", req.query)

    return response_data