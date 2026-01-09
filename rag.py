"""
Retrieval-Augmented Generation (RAG) Module for Agentic AI Education Service System
Handles document retrieval, embedding, and context-aware response generation
"""

from typing import List, Dict, Tuple, Optional
import json
from datetime import datetime
import hashlib


class DocumentStore:
    """Stores and manages educational documents"""
    
    def __init__(self):
        self.documents = {}
        self.document_index = {}
        self.metadata_store = {}
        
    def add_document(self, doc_id: str, content: str, metadata: Dict = None) -> str:
        """Add a document to the store"""
        self.documents[doc_id] = content
        self.metadata_store[doc_id] = metadata or {}
        self.metadata_store[doc_id]["added_at"] = datetime.now().isoformat()
        
        # Create index
        words = content.lower().split()
        for word in set(words):
            if word not in self.document_index:
                self.document_index[word] = []
            self.document_index[word].append(doc_id)
        
        return doc_id
    
    def retrieve_document(self, doc_id: str) -> Optional[Dict]:
        """Retrieve a specific document"""
        if doc_id in self.documents:
            return {
                "doc_id": doc_id,
                "content": self.documents[doc_id],
                "metadata": self.metadata_store.get(doc_id, {})
            }
        return None
    
    def search_documents(self, query: str, top_k: int = 5) -> List[Dict]:
        """Search documents based on query"""
        query_words = query.lower().split()
        doc_scores = {}
        
        for word in query_words:
            if word in self.document_index:
                for doc_id in self.document_index[word]:
                    doc_scores[doc_id] = doc_scores.get(doc_id, 0) + 1
        
        ranked_docs = sorted(doc_scores.items(), key=lambda x: x[1], reverse=True)[:top_k]
        
        results = []
        for doc_id, score in ranked_docs:
            results.append({
                "doc_id": doc_id,
                "content": self.documents[doc_id][:200],
                "score": score,
                "metadata": self.metadata_store.get(doc_id, {})
            })
        
        return results


class EmbeddingGenerator:
    """Generates embeddings for documents and queries"""
    
    def __init__(self, embedding_dim: int = 384):
        self.embedding_dim = embedding_dim
        self.embeddings = {}
        
    def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for text"""
        # Simplified embedding: hash-based approach for demonstration
        hash_obj = hashlib.md5(text.encode())
        hash_int = int(hash_obj.hexdigest(), 16)
        
        embedding = []
        for i in range(self.embedding_dim):
            embedding.append(float((hash_int >> i) % 100) / 100.0)
        
        return embedding
    
    def similarity_score(self, emb1: List[float], emb2: List[float]) -> float:
        """Calculate cosine similarity between two embeddings"""
        dot_product = sum(a * b for a, b in zip(emb1, emb2))
        magnitude1 = sum(a ** 2 for a in emb1) ** 0.5
        magnitude2 = sum(b ** 2 for b in emb2) ** 0.5
        
        if magnitude1 == 0 or magnitude2 == 0:
            return 0.0
        
        return dot_product / (magnitude1 * magnitude2)
    
    def store_embedding(self, doc_id: str, embedding: List[float]):
        """Store embedding for a document"""
        self.embeddings[doc_id] = embedding


class ContextRetriever:
    """Retrieves relevant context for generating responses"""
    
    def __init__(self, document_store: DocumentStore, embedding_gen: EmbeddingGenerator):
        self.doc_store = document_store
        self.embedding_gen = embedding_gen
        
    def retrieve_context(self, query: str, top_k: int = 3) -> List[Dict]:
        """Retrieve context for a given query"""
        query_embedding = self.embedding_gen.generate_embedding(query)
        
        # Search documents
        search_results = self.doc_store.search_documents(query, top_k)
        
        context_results = []
        for result in search_results:
            doc_embedding = self.embedding_gen.generate_embedding(result["content"])
            similarity = self.embedding_gen.similarity_score(query_embedding, doc_embedding)
            
            context_results.append({
                "doc_id": result["doc_id"],
                "content": result["content"],
                "similarity": similarity,
                "metadata": result["metadata"]
            })
        
        return sorted(context_results, key=lambda x: x["similarity"], reverse=True)


class ResponseGenerator:
    """Generates responses using retrieved context"""
    
    def __init__(self, context_retriever: ContextRetriever):
        self.context_retriever = context_retriever
        
    def generate_response(self, query: str, student_id: str = None) -> Dict:
        """Generate a response with context"""
        # Retrieve relevant context
        context = self.context_retriever.retrieve_context(query, top_k=3)
        
        # Generate response based on context
        response_text = self._build_response(query, context)
        
        return {
            "query": query,
            "response": response_text,
            "context_used": len(context),
            "sources": [
                {
                    "doc_id": c["doc_id"],
                    "relevance": c["similarity"]
                }
                for c in context
            ],
            "student_id": student_id,
            "generated_at": datetime.now().isoformat()
        }
    
    def _build_response(self, query: str, context: List[Dict]) -> str:
        """Build response from context"""
        if not context:
            return f"I couldn't find relevant information about: {query}"
        
        response_parts = [f"Based on available educational materials:\n"]
        
        for i, ctx in enumerate(context, 1):
            response_parts.append(f"\n{i}. {ctx['content'][:150]}...")
        
        response_parts.append("\n\nWould you like me to explain any part of this further?")
        
        return "".join(response_parts)


class RAGSystem:
    """Complete Retrieval-Augmented Generation System"""
    
    def __init__(self):
        self.doc_store = DocumentStore()
        self.embedding_gen = EmbeddingGenerator()
        self.context_retriever = ContextRetriever(self.doc_store, self.embedding_gen)
        self.response_generator = ResponseGenerator(self.context_retriever)
        self.conversation_history = {}
        
    def add_educational_resource(self, resource_id: str, content: str, 
                                metadata: Dict = None) -> str:
        """Add educational resource to the RAG system"""
        doc_id = self.doc_store.add_document(resource_id, content, metadata)
        embedding = self.embedding_gen.generate_embedding(content)
        self.embedding_gen.store_embedding(doc_id, embedding)
        return doc_id
    
    def answer_student_query(self, query: str, student_id: str = None) -> Dict:
        """Answer a student query using RAG"""
        response = self.response_generator.generate_response(query, student_id)
        
        # Store in conversation history
        if student_id:
            if student_id not in self.conversation_history:
                self.conversation_history[student_id] = []
            
            self.conversation_history[student_id].append({
                "query": query,
                "response": response,
                "timestamp": datetime.now().isoformat()
            })
        
        return response
    
    def get_conversation_history(self, student_id: str) -> List[Dict]:
        """Get conversation history for a student"""
        return self.conversation_history.get(student_id, [])


if __name__ == "__main__":
    # Example usage
    rag_system = RAGSystem()
    
    # Add educational resources
    resources = [
        {
            "id": "intro_python",
            "content": "Python is a high-level programming language known for its simplicity and readability.",
            "metadata": {"topic": "Programming", "level": "Beginner"}
        },
        {
            "id": "python_loops",
            "content": "For loops and while loops are fundamental control structures in Python programming.",
            "metadata": {"topic": "Programming", "level": "Beginner"}
        },
        {
            "id": "python_functions",
            "content": "Functions allow you to organize code into reusable blocks with parameters and return values.",
            "metadata": {"topic": "Programming", "level": "Intermediate"}
        }
    ]
    
    for resource in resources:
        rag_system.add_educational_resource(
            resource["id"],
            resource["content"],
            resource["metadata"]
        )
    
    # Answer a student query
    query = "What are loops in Python?"
    response = rag_system.answer_student_query(query, student_id="STU001")
    print("Query:", query)
    print("Response:", response)
    
    # Get another response
    query2 = "Explain functions"
    response2 = rag_system.answer_student_query(query2, student_id="STU001")
    print("\nQuery:", query2)
    print("Response:", response2)
