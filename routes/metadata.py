import logging
from flask import Blueprint, request, render_template, jsonify
# NEW ✅
from extensions import db
from models import Document, DocumentChunk
from sqlalchemy import func

logger = logging.getLogger(__name__)

metadata_bp = Blueprint('metadata', __name__)

@metadata_bp.route('/metadata')
def view_metadata():
    """View document metadata with pagination"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        
        # Limit per_page to reasonable values
        per_page = max(1, min(per_page, 100))
        
        # Query documents with chunk count
        documents_query = db.session.query(
            Document,
            func.count(DocumentChunk.id).label('chunk_count')
        ).outerjoin(DocumentChunk).group_by(Document.id).order_by(Document.upload_date.desc())
        
        # Paginate
        documents_paginated = documents_query.paginate(
            page=page, 
            per_page=per_page, 
            error_out=False
        )
        
        # Prepare data for template
        documents_data = []
        for document, chunk_count in documents_paginated.items:
            documents_data.append({
                'id': document.id,
                'filename': document.filename,
                'original_filename': document.original_filename,
                'file_size': document.file_size,
                'file_type': document.file_type,
                'upload_date': document.upload_date,
                'total_chunks': chunk_count or 0,
                'processing_status': document.processing_status
            })
        
        if request.is_json:
            return jsonify({
                'documents': documents_data,
                'pagination': {
                    'page': page,
                    'per_page': per_page,
                    'total': documents_paginated.total,
                    'pages': documents_paginated.pages,
                    'has_next': documents_paginated.has_next,
                    'has_prev': documents_paginated.has_prev
                }
            })
        
        return render_template('metadata.html', 
                             documents=documents_data,
                             pagination=documents_paginated)
        
    except Exception as e:
        logger.error(f"Metadata view error: {e}")
        if request.is_json:
            return jsonify({'error': str(e)}), 500
        return render_template('metadata.html', documents=[], error=str(e))

@metadata_bp.route('/api/metadata')
def api_metadata():
    """API endpoint for document metadata"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        
        # Limit per_page
        per_page = max(1, min(per_page, 100))
        
        # Query with chunk counts
        documents_query = db.session.query(
            Document.id,
            Document.filename,
            Document.original_filename,
            Document.file_size,
            Document.file_type,
            Document.upload_date,
            Document.processing_status,
            func.count(DocumentChunk.id).label('chunk_count')
        ).outerjoin(DocumentChunk).group_by(Document.id).order_by(Document.upload_date.desc())
        
        documents_paginated = documents_query.paginate(
            page=page, 
            per_page=per_page, 
            error_out=False
        )
        
        documents_data = []
        for row in documents_paginated.items:
            documents_data.append({
                'document_id': row.id,
                'filename': row.filename,
                'original_filename': row.original_filename,
                'file_size_bytes': row.file_size,
                'file_size_mb': round(row.file_size / (1024 * 1024), 2),
                'file_type': row.file_type,
                'upload_date': row.upload_date.isoformat(),
                'chunks_stored': row.chunk_count or 0,
                'processing_status': row.processing_status
            })
        
        return jsonify({
            'documents': documents_data,
            'pagination': {
                'current_page': page,
                'per_page': per_page,
                'total_documents': documents_paginated.total,
                'total_pages': documents_paginated.pages,
                'has_next': documents_paginated.has_next,
                'has_prev': documents_paginated.has_prev
            }
        })
        
    except Exception as e:
        logger.error(f"API metadata error: {e}")
        return jsonify({'error': str(e)}), 500

@metadata_bp.route('/document/<int:document_id>')
def document_details(document_id):
    """Get detailed information about a specific document"""
    try:
        document = Document.query.get_or_404(document_id)
        
        # Get chunk information
        chunks = DocumentChunk.query.filter_by(document_id=document_id).order_by(DocumentChunk.chunk_index).all()
        
        chunks_data = []
        for chunk in chunks:
            chunks_data.append({
                'chunk_index': chunk.chunk_index,
                'content_preview': chunk.content[:200] + '...' if len(chunk.content) > 200 else chunk.content,
                'content_length': len(chunk.content),
                'page_number': chunk.page_number,
                'start_char': chunk.start_char,
                'end_char': chunk.end_char,
                'has_embedding': chunk.embedding_vector_id is not None
            })
        
        document_data = {
            'id': document.id,
            'filename': document.filename,
            'original_filename': document.original_filename,
            'file_path': document.file_path,
            'file_size': document.file_size,
            'file_size_mb': round(document.file_size / (1024 * 1024), 2),
            'file_type': document.file_type,
            'upload_date': document.upload_date.isoformat(),
            'total_chunks': document.total_chunks,
            'processing_status': document.processing_status,
            'chunks': chunks_data
        }
        
        if request.is_json:
            return jsonify(document_data)
        
        return render_template('document_details.html', document=document_data)
        
    except Exception as e:
        logger.error(f"Document details error: {e}")
        if request.is_json:
            return jsonify({'error': str(e)}), 500
        return render_template('error.html', error=str(e))

@metadata_bp.route('/api/stats')
def api_stats():
    """Get system statistics"""
    try:
        # Document stats
        total_documents = Document.query.count()
        completed_documents = Document.query.filter_by(processing_status='completed').count()
        failed_documents = Document.query.filter_by(processing_status='failed').count()
        processing_documents = Document.query.filter_by(processing_status='processing').count()
        
        # Chunk stats
        total_chunks = DocumentChunk.query.count()
        
        # File type distribution
        file_type_stats = db.session.query(
            Document.file_type,
            func.count(Document.id)
        ).group_by(Document.file_type).all()
        
        # Total file size
        total_size = db.session.query(func.sum(Document.file_size)).scalar() or 0
        
        return jsonify({
            'documents': {
                'total': total_documents,
                'completed': completed_documents,
                'failed': failed_documents,
                'processing': processing_documents
            },
            'chunks': {
                'total': total_chunks,
                'average_per_document': round(total_chunks / max(total_documents, 1), 2)
            },
            'file_types': dict(file_type_stats),
            'storage': {
                'total_size_bytes': total_size,
                'total_size_mb': round(total_size / (1024 * 1024), 2)
            }
        })
        
    except Exception as e:
        logger.error(f"Stats error: {e}")
        return jsonify({'error': str(e)}), 500
