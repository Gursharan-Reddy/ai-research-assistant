from google import genai
from typing import List, Dict, Any
from config.settings import settings
from src.vector_store.manager import VectorStoreManager

class DocumentComparator:
    def __init__(self, vector_store: VectorStoreManager):
        self.vector_store = vector_store
        self.client = genai.Client(api_key=settings.GEMINI_API_KEY) if settings.GEMINI_API_KEY else None

    def compare_documents(self, doc_ids: List[str]) -> Dict[str, Any]:
        collected_texts = {}
        for d_id in doc_ids:
            chunks = self.vector_store.semantic_search(query="methodology results conclusions comparison", limit=4, doc_ids=[d_id])
            collected_texts[d_id] = "\n".join([c["text"] for c in chunks])

        formatted_context = ""
        for d_id, text in collected_texts.items():
            formatted_context += f"\n=== Document ID: {d_id} ===\n{text[:2000]}\n"

        prompt = f"""
        Compare the following documents across these key sections:
        1. Methodologies
        2. Advantages & Disadvantages
        3. Key Similarities
        4. Key Differences
        5. Implementation Approaches

        Documents Data:
        {formatted_context}
        """

        if not self.client:
            return {"comparison": "Mock Comparison - Set GEMINI_API_KEY in .env"}

        response = self.client.models.generate_content(
            model="gemini-3.6-flash",
            contents=prompt,
            config={"temperature": 0.2}
        )

        return {"comparison": response.text}