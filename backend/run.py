"""
Local development server runner for Transport GPS Tracking System.
"""
import os
from app import create_app

app = create_app(os.getenv("APP_ENV", os.getenv("FLASK_ENV", "development")))

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    debug = os.getenv("FLASK_DEBUG", "1") == "1"
    print(f"[*] Starting Transport GPS Tracking API on http://127.0.0.1:{port} (debug={debug})")
    app.run(host="0.0.0.0", port=port, debug=debug)
