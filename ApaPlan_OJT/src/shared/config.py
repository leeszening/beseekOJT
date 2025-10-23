import os
from dotenv import load_dotenv

# Load environment variables from .env file only in local development
if 'K_SERVICE' not in os.environ:
    load_dotenv()

API_KEY = os.getenv("FIREBASE_WEB_API_KEY")
