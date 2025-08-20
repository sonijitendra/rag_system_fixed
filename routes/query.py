import logging
from flask import Blueprint, request, render_template, jsonify, flash
from services.rag_service import RAGService

logger = logging.getLogger(__name__)

query_bp = Blueprint('query', __name__)

@query_bp.route('/query', methods=['GET', 'POST'])
def query_documents():
    if request.method == 'GET':
        return render_template('query.html')
    
    try:
        # Get question from form or JSON
        if request.is_json:
            data = request.get_json()
            question = data.get('question', '').strip()
            k = data.get('k', 5)
        else:
            question = request.form.get('question', '').strip()
            k = int(request.form.get('k', 5))
        
        # Validate input
        if not question:
            error_msg = 'Please provide a question'
            if request.is_json:
                return jsonify({'error': error_msg}), 400
            flash(error_msg, 'error')
            return render_template('query.html')
        
        # Validate k parameter
        k = max(1, min(k, 20))  # Limit k between 1 and 20
        
        # Process query
        rag_service = RAGService()
        result = rag_service.query(question, k=k)
        
        if request.is_json:
            return jsonify(result)
        
        # For web interface, add the question to the result for display
        result['question'] = question
        result['k_used'] = k
        
        return render_template('query.html', result=result)
        
    except Exception as e:
        logger.error(f"Query error: {e}")
        error_msg = f'Query failed: {str(e)}'
        
        if request.is_json:
            return jsonify({'error': error_msg}), 500
        
        flash(error_msg, 'error')
        return render_template('query.html')

@query_bp.route('/api/query', methods=['POST'])
def api_query():
    """API endpoint for querying documents"""
    try:
        data = request.get_json()
        
        if not data or 'question' not in data:
            return jsonify({'error': 'Question is required'}), 400
        
        question = data['question'].strip()
        k = data.get('k', 5)
        
        if not question:
            return jsonify({'error': 'Question cannot be empty'}), 400
        
        # Validate and limit k
        k = max(1, min(int(k), 20))
        
        rag_service = RAGService()
        result = rag_service.query(question, k=k)
        
        return jsonify(result)
        
    except ValueError as e:
        return jsonify({'error': f'Invalid parameter: {str(e)}'}), 400
    except Exception as e:
        logger.error(f"API query error: {e}")
        return jsonify({'error': f'Query processing failed: {str(e)}'}), 500

@query_bp.route('/system/status')
def system_status():
    """Get system status"""
    try:
        rag_service = RAGService()
        status = rag_service.get_system_status()
        return jsonify(status)
    except Exception as e:
        logger.error(f"Status check error: {e}")
        return jsonify({'error': str(e)}), 500
