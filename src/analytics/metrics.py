from sqlalchemy.orm import Session
from src.database.models import DocumentMetadata, SystemMetric
from typing import Dict, Any

class AnalyticsEngine:
    @staticmethod
    def log_event(db: Session, event_type: str, detail: str = None):
        metric = SystemMetric(metric_type=event_type, detail=detail)
        db.add(metric)
        db.commit()

    @staticmethod
    def get_system_stats(db: Session) -> Dict[str, Any]:
        total_docs = db.query(DocumentMetadata).count()
        processed_docs = db.query(DocumentMetadata).filter(DocumentMetadata.processing_status == "PROCESSED").all()
        
        total_pages = sum([doc.total_pages for doc in processed_docs])
        total_chunks = sum([doc.total_chunks for doc in processed_docs])
        total_questions = db.query(SystemMetric).filter(SystemMetric.metric_type == "question_asked").count()
        
        category_distribution = {}
        for doc in processed_docs:
            cat = doc.category or "Unclassified"
            category_distribution[cat] = category_distribution.get(cat, 0) + 1

        return {
            "total_documents": total_docs,
            "total_pages_processed": total_pages,
            "total_chunks_indexed": total_chunks,
            "total_questions_answered": total_questions,
            "category_distribution": category_distribution
        }