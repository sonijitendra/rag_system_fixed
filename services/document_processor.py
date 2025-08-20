import os
import logging
from typing import List, Dict, Any
import PyPDF2
from docx import Document as DocxDocument
import re

logger = logging.getLogger(__name__)

class DocumentProcessor:
    def __init__(self, chunk_size: int = 500, chunk_overlap: int = 50):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
    
    def extract_text(self, file_path: str, file_type: str) -> str:
        """Extract text from different file types"""
        try:
            if file_type.lower() == 'pdf':
                return self._extract_pdf_text(file_path)
            elif file_type.lower() == 'txt':
                return self._extract_txt_text(file_path)
            elif file_type.lower() in ['docx', 'doc']:
                return self._extract_docx_text(file_path)
            else:
                raise ValueError(f"Unsupported file type: {file_type}")
        except Exception as e:
            logger.error(f"Error extracting text from {file_path}: {str(e)}")
            raise
    
    def _extract_pdf_text(self, file_path: str) -> str:
        """Extract text from PDF file"""
        text = ""
        try:
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
        except Exception as e:
            logger.error(f"Error reading PDF {file_path}: {str(e)}")
            raise
        return text
    
    def _extract_txt_text(self, file_path: str) -> str:
        """Extract text from TXT file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                return file.read()
        except UnicodeDecodeError:
            # Try with different encoding
            with open(file_path, 'r', encoding='latin-1') as file:
                return file.read()
    
    def _extract_docx_text(self, file_path: str) -> str:
        """Extract text from DOCX file"""
        try:
            doc = DocxDocument(file_path)
            text = ""
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
            return text
        except Exception as e:
            logger.error(f"Error reading DOCX {file_path}: {str(e)}")
            raise
    
    def chunk_text(self, text: str) -> List[Dict[str, Any]]:
        """Split text into chunks with overlap"""
        # Clean the text
        text = self._clean_text(text)
        
        # Split into words for more accurate chunking
        words = text.split()
        chunks = []
        
        start_idx = 0
        chunk_index = 0
        
        while start_idx < len(words):
            # Calculate end index for this chunk
            end_idx = min(start_idx + self.chunk_size, len(words))
            
            # Extract chunk
            chunk_words = words[start_idx:end_idx]
            chunk_content = ' '.join(chunk_words)
            
            # Calculate character positions in original text
            start_char = len(' '.join(words[:start_idx]))
            end_char = start_char + len(chunk_content)
            
            chunks.append({
                'chunk_index': chunk_index,
                'content': chunk_content,
                'start_char': start_char,
                'end_char': end_char,
                'word_count': len(chunk_words)
            })
            
            chunk_index += 1
            
            # Move start index for next chunk (with overlap)
            start_idx = max(start_idx + self.chunk_size - self.chunk_overlap, start_idx + 1)
            
            # Break if we've reached the end
            if end_idx >= len(words):
                break
        
        logger.info(f"Created {len(chunks)} chunks from text of {len(words)} words")
        return chunks
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize text"""
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        # Remove special characters but keep basic punctuation
        text = re.sub(r'[^\w\s\.\,\!\?\;\:\-\(\)]', ' ', text)
        # Strip and return
        return text.strip()
    
    def estimate_page_number(self, chunk_index: int, total_chunks: int, total_pages: int = None) -> int:
        """Estimate page number for a chunk"""
        if total_pages is None:
            # Rough estimate: assume 500 words per page
            estimated_pages = max(1, total_chunks // 3)
            return max(1, int((chunk_index / total_chunks) * estimated_pages))
        else:
            return max(1, int((chunk_index / total_chunks) * total_pages))
