"""
Production WSGI entrypoint for Railway and Gunicorn deployment.
"""
import os
from app import create_app

# Instantiate production app
app = create_app(os.getenv("APP_ENV", os.getenv("FLASK_ENV", "production")))

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
