"""
Root app.py that imports the application from the backend directory.
This file is used for compatibility with various hosting platforms.
"""

import sys
import os

# Make sure backend directory is in the path
backend_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'backend')
if backend_dir not in sys.path:
    sys.path.append(backend_dir)

# Import app from backend
try:
    from backend.app import app
except ImportError:
    # Direct import if module structure is different
    import os
    import sys
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    from backend.app import app

# Add health endpoint if it doesn't exist in the imported app
from flask import jsonify
import os

@app.route('/health', methods=['GET'])
def health_check():
    """Simple health check endpoint to verify the app is running"""
    api_key = os.environ.get("GEMINI_API_KEY")
    api_key_status = "available" if api_key else "missing"
    return jsonify({
        "status": "healthy",
        "api_key": api_key_status,
        "environment": os.environ.get('RAILWAY_ENVIRONMENT', 'development')
    })

# Run the app if executed directly
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5050))
    app.run(host="0.0.0.0", port=port, debug=(os.environ.get('RAILWAY_ENVIRONMENT') != 'production')) 