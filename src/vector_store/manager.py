import os
import chromadb
from sentence_transformers import SentenceTransformer
from rank_bm25 import BM25Okapi
from typing import List, Dict, Any
from config.settings import settings

class VectorStoreManager:
    def __init__(self):
        os.makedirs(settings.VECTOR_DB_DIR, exist_ok=True)
        self.chroma_client = chromadb.PersistentClient(path=settings.VECTOR_DB_DIR)
        self.collection = self.chroma_client.get_or_create_collection(name="research_docs")
        self.embedding_model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

    def add_chunks(self, chunks: List[Dict[str, Any]]):
        if not chunks:
            return

        documents = [c["text"] for c in chunks]
        embeddings = self.embedding_model.encode(documents).tolist()
        ids = [c["chunk_id"] for c in chunks]
        metadatas = [
            {
                "doc_id": c["doc_id"],
                "file_name": c["file_name"],
                "page_number": c["page_number"]
            }
            for c in chunks
        ]

        self.collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas
        )

    def delete_document_chunks(self, doc_id: str):
        self.collection.delete(where={"doc_id": doc_id})

    def semantic_search(self, query: str, limit: int = 4, doc_ids: List[str] = None) -> List[Dict[str, Any]]:
        query_embedding = self.embedding_model.encode([query]).tolist()
        where_clause = {"doc_id": {"$in": doc_ids}} if doc_ids else None

        results = self.collection.query(
            query_embeddings=query_embedding,
            n_results=limit,
            where=where_clause
        )

        formatted_results = []
        if results and results["documents"]:
            for i in range(len(results["documents"][0])):
                formatted_results.append({
                    "text": results["documents"][0][i],
                    "metadata": results["metadatas"][0][i],
                    "score": float(results["distances"][0][i]) if "distances" in results and results["distances"] else 0.0
                })
        return formatted_results

    def keyword_search(self, query: str, limit: int = 4) -> List[Dict[str, Any]]:
        all_docs = self.collection.get()
        if not all_docs or not all_docs["documents"]:
            return []

        corpus = [doc.split() for doc in all_docs["documents"]]
        bm25 = BM25Okapi(corpus)
        tokenized_query = query.split()
        scores = bm25.get_scores(tokenized_query)
        
        top_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:limit]
        
        results = []
        for idx in top_indices:
            if scores[idx] > 0:
                results.append({
                    "text": all_docs["documents"][idx],
                    "metadata": all_docs["metadatas"][idx],
                    "score": float(scores[idx])
                })
        return results

    def hybrid_search(self, query: str, limit: int = 4) -> List[Dict[str, Any]]:
        semantic = self.semantic_search(query, limit=limit)
        keyword = self.keyword_search(query, limit=limit)
        
        seen = set()
        combined = []
        for item in semantic + keyword:
            if item["text"] not in seen:
                seen.add(item["text"])
                combined.append(item)
        return combined[:limit]