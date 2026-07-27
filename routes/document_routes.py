from fastapi import APIRouter, UploadFile, File, BackgroundTasks, Depends, HTTPException
from sqlalchemy.orm import Session
import os, uuid
from src.database.base import get_db
from src.database.models import DocumentMetadata
from src.document_processing.pdf_parser import PDFParser
from src.document_processing.chunker import TextChunker
from src.ml.predictor import DocumentClassifier
from src.vector_store.manager import VectorStoreManager
from config.settings import settings

router = APIRouter(prefix="/documents", tags=["Document Management"])
vector_manager = VectorStoreManager()
classifier = DocumentClassifier()

def process_pdf_background(doc_id: str, file_path: str, file_name: str, db_session_factory):
    db = db_session_factory()
    try:
        parsed_data = PDFParser.parse_pdf(file_path, doc_id)
        full_sample_text = " ".join([p["text"] for p in parsed_data["pages"][:3]])
        predicted_category = classifier.predict(full_sample_text)
        
        chunker = TextChunker()
        chunks = chunker.create_chunks(parsed_data["pages"], file_name)
        
        vector_manager.add_chunks(chunks)
        
        doc_record = db.query(DocumentMetadata).filter(DocumentMetadata.doc_id == doc_id).first()
        if doc_record:
            doc_record.total_pages = parsed_data["total_pages"]
            doc_record.total_chunks = len(chunks)
            doc_record.category = predicted_category
            doc_record.processing_status = "PROCESSED"
            db.commit()
    except Exception:
        doc_record = db.query(DocumentMetadata).filter(DocumentMetadata.doc_id == doc_id).first()
        if doc_record:
            doc_record.processing_status = "FAILED"
            db.commit()
    finally:
        db.close()

@router.post("/upload")
async def upload_document(
    background_tasks: BackgroundTasks, 
    file: UploadFile = File(...), 
    db: Session = Depends(get_db)
):
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")

    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    doc_id = str(uuid.uuid4())
    file_path = os.path.join(settings.UPLOAD_DIR, f"{doc_id}_{file.filename}")

    with open(file_path, "wb") as f:
        f.write(await file.read())

    doc_metadata = DocumentMetadata(
        doc_id=doc_id,
        file_name=file.filename,
        file_path=file_path,
        processing_status="PENDING"
    )
    db.add(doc_metadata)
    db.commit()

    from src.database.base import SessionLocal
    background_tasks.add_task(process_pdf_background, doc_id, file_path, file.filename, SessionLocal)

    return {"message": "Upload successful. Processing initiated.", "doc_id": doc_id}

@router.get("/list")
def list_documents(db: Session = Depends(get_db)):
    return db.query(DocumentMetadata).all()

@router.delete("/{doc_id}")
def delete_document(doc_id: str, db: Session = Depends(get_db)):
    doc = db.query(DocumentMetadata).filter(DocumentMetadata.doc_id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found.")

    vector_manager.delete_document_chunks(doc_id)
    if os.path.exists(doc.file_path):
        os.remove(doc.file_path)

    db.delete(doc)
    db.commit()
    return {"message": f"Document {doc_id} deleted successfully."}