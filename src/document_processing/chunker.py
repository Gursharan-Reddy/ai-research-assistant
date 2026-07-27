from typing import List, Dict, Any

class TextChunker:
    def __init__(self, chunk_size: int = 900, chunk_overlap: int = 150):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def create_chunks(self, pages_data: List[Dict[str, Any]], file_name: str) -> List[Dict[str, Any]]:
        chunks = []
        global_chunk_id = 0

        for page in pages_data:
            text = page["text"]
            start = 0
            text_len = len(text)

            while start < text_len:
                end = min(start + self.chunk_size, text_len)
                chunk_text = text[start:end]

                chunks.append({
                    "chunk_id": f"{page['doc_id']}_c{global_chunk_id}",
                    "doc_id": page["doc_id"],
                    "file_name": file_name,
                    "page_number": page["page_number"],
                    "text": chunk_text
                })

                global_chunk_id += 1
                if end == text_len:
                    break
                start += (self.chunk_size - self.chunk_overlap)

        return chunks