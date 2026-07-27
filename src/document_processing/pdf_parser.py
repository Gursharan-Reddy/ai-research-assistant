import fitz  # PyMuPDF
from typing import List, Dict, Any

class PDFParser:
    @staticmethod
    def parse_pdf(file_path: str, doc_id: str) -> Dict[str, Any]:
        doc = fitz.open(file_path)
        pages_data = []

        for page_num in range(len(doc)):
            page = doc[page_num]
            text = page.get_text("text").strip()
            if text:
                pages_data.append({
                    "doc_id": doc_id,
                    "page_number": page_num + 1,
                    "text": text
                })
        
        total_pages = len(doc)
        doc.close()
        
        return {
            "total_pages": total_pages,
            "pages": pages_data
        }