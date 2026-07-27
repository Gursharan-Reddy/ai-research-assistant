from google import genai
from typing import Dict, Any
from config.settings import settings
from src.vector_store.manager import VectorStoreManager

class RAGEngine:
    def __init__(self, vector_store: VectorStoreManager):
        self.vector_store = vector_store
        self.client = genai.Client(api_key=settings.GEMINI_API_KEY) if settings.GEMINI_API_KEY else None

    def answer_question(self, query: str, conversation_history: str = "", mode: str = "hybrid") -> Dict[str, Any]:
        if mode == "semantic":
            retrieved_chunks = self.vector_store.semantic_search(query, limit=4)
        elif mode == "keyword":
            retrieved_chunks = self.vector_store.keyword_search(query, limit=4)
        else:
            retrieved_chunks = self.vector_store.hybrid_search(query, limit=4)

        if not retrieved_chunks:
            return {
                "answer": "I cannot determine the answer from the provided documents (No relevant content found).",
                "citations": [],
                "retrieved_context": []
            }

        context_str = ""
        citations = []
        for chunk in retrieved_chunks:
            meta = chunk["metadata"]
            context_str += f"\n--- Source: {meta.get('file_name')} (Page {meta.get('page_number')}) ---\n{chunk['text']}\n"
            citations.append({
                "document": meta.get("file_name"),
                "page": meta.get("page_number")
            })

        system_instruction = (
            "You are an AI Research & Knowledge Assistant. Answer the question using ONLY the provided document context. "
            "If the context does not contain enough information, state clearly: 'I cannot determine the answer from the provided documents.' "
            "Always include precise document names and page references in your reasoning."
        )

        user_prompt = f"Conversation History:\n{conversation_history}\n\nRetrieved Context:\n{context_str}\n\nQuestion: {query}"

        if not self.client:
            return {
                "answer": f"[Mock Response - Set GEMINI_API_KEY in .env]\nContext retrieved:\n{context_str[:250]}...",
                "citations": citations,
                "retrieved_context": [c["text"] for c in retrieved_chunks]
            }

        response = self.client.models.generate_content(
            model="gemini-3.6-flash",
            contents=user_prompt,
            config={"system_instruction": system_instruction, "temperature": 0.1}
        )

        return {
            "answer": response.text,
            "citations": citations,
            "retrieved_context": [c["text"] for c in retrieved_chunks]
        }