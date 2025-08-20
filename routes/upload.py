import os
import logging
from flask import Blueprint, request, render_template, flash, redirect, url_for, current_app, jsonify
from werkzeug.utils import secure_filename
# NEW ✅
from extensions import db
from models import Document, DocumentChunk
from services.document_processor import DocumentProcessor
from services.vector_store import VectorStore

logger = logging.getLogger(__name__)

upload_bp = Blueprint('upload', __name__)

ALLOWED_EXTENSIONS = {'txt', 'pdf', 'docx', 'doc'}
MAX_FILES = 20
MAX_PAGES = 1000

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@upload_bp.route('/upload', methods=['GET', 'POST'])
def upload_documents():
    if request.method == 'GET':
        return render_template('upload.html')
    
    try:
        # Check if files were uploaded
        if 'files' not in request.files:
            flash('No files selected', 'error')
            return redirect(request.url)
        
        files = request.files.getlist('files')
        
        # Validate number of files
        if len(files) > MAX_FILES:
            flash(f'Too many files. Maximum {MAX_FILES} files allowed.', 'error')
            return redirect(request.url)
        
        if not files or all(file.filename == '' for file in files):
            flash('No files selected', 'error')
            return redirect(request.url)
        
        processed_files = []
        errors = []
        
        # Initialize services
        doc_processor = DocumentProcessor()
        vector_store = VectorStore()
        
        for file in files:
            if file and file.filename and allowed_file(file.filename):
                try:
                    result = process_single_file(file, doc_processor, vector_store)
                    processed_files.append(result)
                except Exception as e:
                    error_msg = f"Error processing {file.filename}: {str(e)}"
                    errors.append(error_msg)
                    logger.error(error_msg)
            else:
                errors.append(f"Invalid file type: {file.filename}")
        
        # Show results
        if processed_files:
            flash(f'Successfully processed {len(processed_files)} files', 'success')
        
        if errors:
            for error in errors:
                flash(error, 'error')
        
        if not processed_files and not errors:
            flash('No valid files to process', 'warning')
        
        return render_template('upload.html', 
                             processed_files=processed_files, 
                             errors=errors)
        
    except Exception as e:
        logger.error(f"Upload error: {e}")
        flash(f'Upload failed: {str(e)}', 'error')
        return redirect(url_for('upload.upload_documents'))

def process_single_file(file, doc_processor, vector_store):
    """Process a single uploaded file"""
    # Secure filename
    filename = secure_filename(file.filename)
    file_ext = filename.rsplit('.', 1)[1].lower()
    
    # Save file
    file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
    file.save(file_path)
    
    # Get file size
    file_size = os.path.getsize(file_path)
    
    try:
        # Create document record
        document = Document(
            filename=filename,
            original_filename=file.filename,
            file_path=file_path,
            file_size=file_size,
            file_type=file_ext,
            processing_status='processing'
        )
        db.session.add(document)
        db.session.commit()
        
        # Extract text
        text = doc_processor.extract_text(file_path, file_ext)
        
        # Validate document size (rough page count)
        estimated_pages = len(text) // 2000  # Rough estimate: 2000 chars per page
        if estimated_pages > MAX_PAGES:
            raise ValueError(f"Document too large. Estimated {estimated_pages} pages, maximum {MAX_PAGES} allowed.")
        
        # Chunk text
        chunks = doc_processor.chunk_text(text)
        
        # Add page number estimation
        for chunk in chunks:
            chunk['page_number'] = doc_processor.estimate_page_number(
                chunk['chunk_index'], len(chunks), estimated_pages
            )
        
        # Generate embeddings and store in vector database
        vector_ids = vector_store.add_document_chunks(chunks, document.id, filename)
        
        # Store chunk metadata in database
        for i, chunk in enumerate(chunks):
            chunk_record = DocumentChunk(
                document_id=document.id,
                chunk_index=chunk['chunk_index'],
                content=chunk['content'],
                page_number=chunk['page_number'],
                start_char=chunk.get('start_char'),
                end_char=chunk.get('end_char'),
                embedding_vector_id=vector_ids[i] if i < len(vector_ids) else None
            )
            db.session.add(chunk_record)
        
        # Update document status
        document.total_chunks = len(chunks)
        document.processing_status = 'completed'
        db.session.commit()
        
        logger.info(f"Successfully processed {filename}: {len(chunks)} chunks created")
        
        return {
            'filename': filename,
            'document_id': document.id,
            'chunks_created': len(chunks),
            'file_size': file_size,
            'estimated_pages': estimated_pages
        }
        
    except Exception as e:
        # Update document status to failed
        if 'document' in locals():
            document.processing_status = 'failed'
            db.session.commit()
        
        # Clean up file
        if os.path.exists(file_path):
            os.remove(file_path)
        
        raise e

@upload_bp.route('/api/upload', methods=['POST'])
def api_upload():
    """API endpoint for file upload (JSON response)"""
    try:
        result = upload_documents()
        if isinstance(result, str):  # Redirect response
            return jsonify({'status': 'success', 'message': 'Files uploaded successfully'})
        return jsonify({'status': 'success', 'data': result})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500
