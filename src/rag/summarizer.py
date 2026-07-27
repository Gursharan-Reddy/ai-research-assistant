from google import genai
from typing import Dict, Any
from config.settings import settings
from src.vector_store.manager import VectorStoreManager

class DocumentSummarizer:
    def __init__(self, vector_store: VectorStoreManager):
        self.vector_store = vector_store
        self.client = genai.Client(api_key=settings.GEMINI_API_KEY) if settings.GEMINI_API_KEY else None

    def generate_summary(self, doc_id: str) -> Dict[str, Any]:
        chunks = self.vector_store.semantic_search(query="overview summary findings conclusions", limit=8, doc_ids=[doc_id])
        full_text = "\n".join([c["text"] for c in chunks])

        if not full_text:
            return {"error": "No content found for the specified document ID."}

        prompt = f"""
        Analyze the following document content and produce a structured multi-tier summary with these exact headings:

        ## Executive Summary
        ## Technical Summary
        ## Bullet Point Summary
        ## Key Takeaways

        Content:
        {full_text[:4000]}
        """

        if not self.client:
            return {"summary": "Mock Summary - Set GEMINI_API_KEY in .env"}

        response = self.client.models.generate_content(
            model="gemini-3.6-flash",
            contents=prompt,
            config={"temperature": 0.2}
        )

        return {"summary": response.text}