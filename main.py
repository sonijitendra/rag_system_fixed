import os
from app import create_app

if __name__ == "__main__":
    app = create_app()
    port = int(os.environ.get("PORT", 8080))
    print(f"🚀 Starting Flask app on http://0.0.0.0:{port}")
    app.run(host="0.0.0.0", port=port, debug=False)


