from extensions import db
from datetime import datetime
from sqlalchemy import Text, Integer, String, DateTime, Float

class Document(db.Model):
    __tablename__ = 'documents'
    
    id = db.Column(Integer, primary_key=True)
    filename = db.Column(String(255), nullable=False)
    original_filename = db.Column(String(255), nullable=False)
    file_path = db.Column(String(500), nullable=False)
    file_size = db.Column(Integer, nullable=False)
    file_type = db.Column(String(50), nullable=False)
    upload_date = db.Column(DateTime, default=datetime.utcnow)
    total_chunks = db.Column(Integer, default=0)
    processing_status = db.Column(String(50), default='pending')  # pending, processing, completed, failed
    
    # Relationship to chunks
    chunks = db.relationship('DocumentChunk', backref='document', cascade='all, delete-orphan')

class DocumentChunk(db.Model):
    __tablename__ = 'document_chunks'
    
    id = db.Column(Integer, primary_key=True)
    document_id = db.Column(Integer, db.ForeignKey('documents.id'), nullable=False)
    chunk_index = db.Column(Integer, nullable=False)
    content = db.Column(Text, nullable=False)
    page_number = db.Column(Integer, nullable=True)
    start_char = db.Column(Integer, nullable=True)
    end_char = db.Column(Integer, nullable=True)
    embedding_vector_id = db.Column(String(100), nullable=True)  # Reference to vector store
    created_date = db.Column(DateTime, default=datetime.utcnow)
