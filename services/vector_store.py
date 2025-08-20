import os
import logging
import pickle
import numpy as np
from typing import List, Dict, Any, Optional
import faiss
from openai import OpenAI

logger = logging.getLogger(__name__)

class VectorStore:
    def __init__(self, vector_db_path: str = "vector_db"):
        self.vector_db_path = vector_db_path
        self.index_file = os.path.join(vector_db_path, "faiss_index.bin")
        self.metadata_file = os.path.join(vector_db_path, "metadata.pkl")
        self.dimension = 1536  # OpenAI embedding dimension
        
        # Initialize OpenAI
        self.openai_client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
        
        # Load or create index
        self.index = self._load_or_create_index()
        self.metadata = self._load_metadata()
        
        os.makedirs(vector_db_path, exist_ok=True)
    
    def _load_or_create_index(self) -> faiss.Index:
        """Load existing FAISS index or create new one"""
        if os.path.exists(self.index_file):
            try:
                index = faiss.read_index(self.index_file)
                logger.info(f"Loaded existing FAISS index with {index.ntotal} vectors")
                return index
            except Exception as e:
                logger.warning(f"Failed to load existing index: {e}. Creating new one.")
        
        # Create new index
        index = faiss.IndexFlatIP(self.dimension)  # Inner product for cosine similarity
        logger.info("Created new FAISS index")
        return index
    
    def _load_metadata(self) -> List[Dict]:
        """Load metadata for stored vectors"""
        if os.path.exists(self.metadata_file):
            try:
                with open(self.metadata_file, 'rb') as f:
                    metadata = pickle.load(f)
                logger.info(f"Loaded metadata for {len(metadata)} vectors")
                return metadata
            except Exception as e:
                logger.warning(f"Failed to load metadata: {e}. Starting with empty metadata.")
        
        return []
    
    def _save_index(self):
        """Save FAISS index to disk"""
        try:
            faiss.write_index(self.index, self.index_file)
            logger.info("Saved FAISS index to disk")
        except Exception as e:
            logger.error(f"Failed to save index: {e}")
    
    def _save_metadata(self):
        """Save metadata to disk"""
        try:
            with open(self.metadata_file, 'wb') as f:
                pickle.dump(self.metadata, f)
            logger.info("Saved metadata to disk")
        except Exception as e:
            logger.error(f"Failed to save metadata: {e}")
    
    def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding using OpenAI API"""
        try:
            response = self.openai_client.embeddings.create(
                model="text-embedding-ada-002",
                input=text
            )
            embedding = response.data[0].embedding
            # Normalize for cosine similarity
            norm = np.linalg.norm(embedding)
            if norm > 0:
                embedding = embedding / norm
            return embedding
        except Exception as e:
            logger.error(f"Failed to generate embedding: {e}")
            raise
    
    def add_document_chunks(self, chunks: List[Dict[str, Any]], document_id: int, filename: str) -> List[str]:
        """Add document chunks to vector store"""
        vector_ids = []
        
        try:
            for chunk in chunks:
                # Generate embedding
                embedding = self.generate_embedding(chunk['content'])
                
                # Convert to numpy array
                vector = np.array([embedding], dtype=np.float32)
                
                # Add to index
                self.index.add(vector)
                
                # Create vector ID
                vector_id = f"doc_{document_id}_chunk_{chunk['chunk_index']}"
                vector_ids.append(vector_id)
                
                # Store metadata
                metadata = {
                    'vector_id': vector_id,
                    'document_id': document_id,
                    'chunk_index': chunk['chunk_index'],
                    'filename': filename,
                    'content': chunk['content'],
                    'page_number': chunk.get('page_number', 1),
                    'start_char': chunk.get('start_char'),
                    'end_char': chunk.get('end_char')
                }
                self.metadata.append(metadata)
            
            # Save to disk
            self._save_index()
            self._save_metadata()
            
            logger.info(f"Added {len(chunks)} chunks to vector store for document {document_id}")
            return vector_ids
            
        except Exception as e:
            logger.error(f"Failed to add chunks to vector store: {e}")
            raise
    
    def search_similar(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        """Search for similar chunks"""
        try:
            if self.index.ntotal == 0:
                logger.warning("Vector store is empty")
                return []
            
            # Generate query embedding
            query_embedding = self.generate_embedding(query)
            query_vector = np.array([query_embedding], dtype=np.float32)
            
            # Search
            scores, indices = self.index.search(query_vector, min(k, self.index.ntotal))
            
            results = []
            for i, (score, idx) in enumerate(zip(scores[0], indices[0])):
                if idx >= 0 and idx < len(self.metadata):
                    result = self.metadata[idx].copy()
                    result['similarity_score'] = float(score)
                    result['rank'] = i + 1
                    results.append(result)
            
            logger.info(f"Found {len(results)} similar chunks for query")
            return results
            
        except Exception as e:
            logger.error(f"Failed to search vector store: {e}")
            raise
    
    def delete_document_vectors(self, document_id: int):
        """Delete all vectors for a document (note: FAISS doesn't support deletion, so we rebuild)"""
        try:
            # Filter out metadata for this document
            self.metadata = [m for m in self.metadata if m['document_id'] != document_id]
            
            # Rebuild index (FAISS doesn't support deletion)
            if self.metadata:
                new_index = faiss.IndexFlatIP(self.dimension)
                for meta in self.metadata:
                    embedding = self.generate_embedding(meta['content'])
                    vector = np.array([embedding], dtype=np.float32)
                    new_index.add(vector)
                self.index = new_index
            else:
                self.index = faiss.IndexFlatIP(self.dimension)
            
            self._save_index()
            self._save_metadata()
            
            logger.info(f"Deleted vectors for document {document_id}")
            
        except Exception as e:
            logger.error(f"Failed to delete document vectors: {e}")
            raise
    
    def get_stats(self) -> Dict[str, Any]:
        """Get vector store statistics"""
        return {
            'total_vectors': self.index.ntotal,
            'dimension': self.dimension,
            'total_documents': len(set(m['document_id'] for m in self.metadata)) if self.metadata else 0,
            'index_file_exists': os.path.exists(self.index_file),
            'metadata_file_exists': os.path.exists(self.metadata_file)
        }
