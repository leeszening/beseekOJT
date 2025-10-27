import os
from dotenv import load_dotenv
import pyrebase

# Load environment variables from .env file only in local development
if 'K_SERVICE' not in os.environ:
    load_dotenv()

# --- Server-side (firebase-admin) ---
# This module now only serves as a placeholder for the db client.
# The initialization is handled in the main application entry point (src/main.py)
# to ensure correct startup order.
db = None


# --- Client-side (pyrebase) ---
def get_pyrebase_config():
    return {
        "apiKey": os.getenv("FIREBASE_WEB_API_KEY"),
        "authDomain": os.getenv("AUTH_DOMAIN"),
        "projectId": os.getenv("PROJECT_ID"),
        "storageBucket": os.getenv("STORAGE_BUCKET"),
        "messagingSenderId": os.getenv("MESSAGING_SENDER_ID"),
        "appId": os.getenv("APP_ID"),
        "measurementId": os.getenv("MEASUREMENT_ID"),
        "databaseURL": ""
    }

pyrebase_config = get_pyrebase_config()
pyrebase_app = pyrebase.initialize_app(pyrebase_config)
pyrebase_auth = pyrebase_app.auth()
