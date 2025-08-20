import os
import logging
from typing import List, Dict, Any, Optional
from openai import OpenAI
from services.vector_store import VectorStore

logger = logging.getLogger(__name__)

class RAGService:
    def __init__(self):
        self.openai_client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
        self.vector_store = VectorStore()
    
    def query(self, question: str, k: int = 5) -> Dict[str, Any]:
        """Process a question using RAG approach"""
        try:
            # Step 1: Retrieve relevant chunks
            similar_chunks = self.vector_store.search_similar(question, k=k)
            
            if not similar_chunks:
                return {
                    "answer": "No relevant information found in the uploaded documents.",
                    "sources": [],
                    "context_used": False
                }
            
            # Step 2: Prepare context
            context = self._prepare_context(similar_chunks)
            
            # Step 3: Generate answer using LLM
            answer = self._generate_answer(question, context)
            
            # Step 4: Extract sources
            sources = self._extract_sources(similar_chunks)
            
            return {
                "answer": answer,
                "sources": sources,
                "context_used": True,
                "chunks_retrieved": len(similar_chunks)
            }
            
        except Exception as e:
            logger.error(f"Error in RAG query: {e}")
            return {
                "answer": f"An error occurred while processing your question: {str(e)}",
                "sources": [],
                "context_used": False
            }
    
    def _prepare_context(self, chunks: List[Dict[str, Any]]) -> str:
        """Prepare context from retrieved chunks"""
        context_parts = []
        
        for i, chunk in enumerate(chunks):
            # Add source information
            source_info = f"[Source {i+1}: {chunk['filename']}, Page {chunk['page_number']}]"
            context_parts.append(f"{source_info}\n{chunk['content']}")
        
        return "\n\n".join(context_parts)
    
    def _generate_answer(self, question: str, context: str) -> str:
        """Generate answer using OpenAI GPT"""
        try:
            # the newest OpenAI model is "gpt-4o" which was released May 13, 2024.
            # do not change this unless explicitly requested by the user
            system_prompt = """You are a helpful AI assistant that answers questions based on the provided context. 
            
Guidelines:
- Use only the information provided in the context to answer the question
- If the context doesn't contain enough information to fully answer the question, clearly state this
- Be accurate and specific
- Cite the sources when possible
- If multiple sources provide different information, acknowledge this
- Keep your response concise but comprehensive"""
            
            user_prompt = f"""Context:
{context}

Question: {question}

Please provide a helpful answer based on the context above."""
            
            response = self.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3,
                max_tokens=1000
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"Error generating answer: {e}")
            return f"I apologize, but I encountered an error while generating the answer: {str(e)}"
    
    def _extract_sources(self, chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extract source information from chunks"""
        sources = []
        seen_sources = set()
        
        for chunk in chunks:
            source_key = (chunk['filename'], chunk['page_number'])
            if source_key not in seen_sources:
                sources.append({
                    "filename": chunk['filename'],
                    "page": chunk['page_number'],
                    "similarity_score": round(chunk.get('similarity_score', 0), 3)
                })
                seen_sources.add(source_key)
        
        return sources
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get system status for RAG service"""
        try:
            vector_stats = self.vector_store.get_stats()
            
            # Test OpenAI connection
            openai_status = "connected"
            try:
                self.openai_client.models.list()
            except:
                openai_status = "error"
            
            return {
                "vector_store": vector_stats,
                "openai_status": openai_status,
                "service_status": "operational"
            }
        except Exception as e:
            logger.error(f"Error getting system status: {e}")
            return {
                "service_status": "error",
                "error": str(e)
            }
