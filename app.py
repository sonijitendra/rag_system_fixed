import os
import logging
from extensions import db
from flask import Flask, render_template
from werkzeug.middleware.proxy_fix import ProxyFix

# Configure logging
logging.basicConfig(level=logging.DEBUG)

def create_app():
    app = Flask(__name__)
    app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key-change-in-production")
    app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

    # Configure database
    app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///rag_system.db")
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
        "pool_recycle": 300,
        "pool_pre_ping": True,
    }
    
    # Configure upload settings
    app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB max file size
    app.config['UPLOAD_FOLDER'] = 'uploads'
    
    # Create upload directory if it doesn't exist
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs('vector_db', exist_ok=True)
     os.makedirs("/tmp", exist_ok=True)
  

    # Initialize extensions
    db.init_app(app)

    with app.app_context():
        # Import models to ensure tables are created
        import models
        db.create_all()
        
        # Register blueprints
        from routes.upload import upload_bp
        from routes.query import query_bp
        from routes.metadata import metadata_bp
        
        app.register_blueprint(upload_bp)
        app.register_blueprint(query_bp)
        app.register_blueprint(metadata_bp)

        # Main route
        @app.route('/')
        def index():
            return render_template('index.html')

    return app


if __name__ == "__main__":
    app = create_app()
    port = int(os.environ.get("PORT", 8080))
    print(f"🚀 Starting Flask app on http://0.0.0.0:{port}")
    app.run(host="0.0.0.0", port=port, debug=True)
