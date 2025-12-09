import requests
import json
import logging
from typing import List, Dict, Any, Optional
import time
from app.config import settings
from app.database import vector_db
from app.ocr import ocr_processor

logger = logging.getLogger(__name__)

class RAGSystem:
    def __init__(self):
        self.ollama_host = settings.OLLAMA_HOST
        self.chat_model = settings.APP_CHAT_MODEL
        self.embedding_model = settings.APP_EMBEDDING_MODEL
        
    def create_embedding(self, text: str) -> Optional[List[float]]:
        """Create embedding vector using Ollama"""
        try:
            url = f"{self.ollama_host}/api/embeddings"
            payload = {
                "model": self.embedding_model,
                "prompt": text
            }
            
            response = requests.post(url, json=payload, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            return result.get("embedding")
            
        except Exception as e:
            logger.error(f"Embedding creation failed: {e}")
            return None
    
    def generate_answer(self, query: str, context: str) -> str:
        """Generate answer using LLM (Ollama)"""
        try:
            # Prepare prompt with context
            prompt = f"""Based on the following context, answer the question.

Context:
{context}

Question: {query}

Answer:"""
            
            url = f"{self.ollama_host}/api/generate"
            payload = {
                "model": self.chat_model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.7,
                    "top_p": 0.9
                }
            }
            
            response = requests.post(url, json=payload, timeout=60)
            response.raise_for_status()
            
            result = response.json()
            return result.get("response", "I couldn't generate an answer.")
            
        except Exception as e:
            logger.error(f"LLM generation failed: {e}")
            return f"Error generating answer: {str(e)}"
    
    def check_ollama_health(self) -> Dict[str, bool]:
        """Check Ollama and model availability"""
        health_status = {
            "ollama": False,
            "embedding_model": False,
            "chat_model": False
        }
        
        try:
            # Check Ollama service
            response = requests.get(f"{self.ollama_host}/api/tags", timeout=10)
            if response.status_code == 200:
                health_status["ollama"] = True
                
                # Check if models are available
                models = response.json().get("models", [])
                model_names = [model.get("name") for model in models]
                
                if self.embedding_model in model_names:
                    health_status["embedding_model"] = True
                
                if self.chat_model in model_names:
                    health_status["chat_model"] = True
                    
        except Exception as e:
            logger.error(f"Ollama health check failed: {e}")
            
        return health_status
    
    def query_rag(self, query_text: str, table_name: str = "documents", 
                  top_k: int = 5) -> Dict[str, Any]:
        """Main RAG query pipeline"""
        start_time = time.time()
        
        # Step 1: Create embedding for query
        logger.info(f"Creating embedding for query: {query_text[:50]}...")
        query_embedding = self.create_embedding(query_text)
        
        if not query_embedding:
            return {
                "answer": "Error creating embedding for query.",
                "sources": [],
                "similarity_scores": [],
                "query_time": time.time() - start_time
            }
        
        # Step 2: Similarity search in vector database
        logger.info(f"Searching in table {table_name} with top_k={top_k}")
        search_results = vector_db.similarity_search(
            query_embedding, table_name, top_k
        )
        
        if not search_results:
            return {
                "answer": "No relevant documents found in the database.",
                "sources": [],
                "similarity_scores": [],
                "query_time": time.time() - start_time
            }
        
        # Step 3: Prepare context from retrieved documents
        context_parts = []
        sources = []
        similarity_scores = []
        
        for result in search_results:
            context_parts.append(result['content_text'])
            sources.append(result['original_data'])
            similarity_scores.append(float(result['similarity']))
        
        context = "\n\n---\n\n".join(context_parts)
        
        # Step 4: Generate answer using LLM
        logger.info("Generating answer with LLM")
        answer = self.generate_answer(query_text, context)
        
        return {
            "answer": answer,
            "sources": sources,
            "similarity_scores": similarity_scores,
            "query_time": time.time() - start_time
        }
    
    def query_with_image(self, image_bytes: bytes, 
                        query_text: Optional[str] = None,
                        table_name: str = "documents",
                        top_k: int = 5) -> Dict[str, Any]:
        """RAG query with image OCR"""
        # Process image with OCR
        combined_query = ocr_processor.process_image_query(
            image_bytes, query_text
        )
        
        if not combined_query:
            return {
                "answer": "No text could be extracted from the image and no text query provided.",
                "sources": [],
                "similarity_scores": [],
                "query_time": 0
            }
        
        # Proceed with regular RAG query
        return self.query_rag(combined_query, table_name, top_k)

# Singleton instance
rag_system = RAGSystem()