import os
import pyrebase
from dotenv import load_dotenv

# Load environment variables from .env file only in local development
if 'K_SERVICE' not in os.environ:
    load_dotenv()


def get_firebase_config():
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


firebase_config = get_firebase_config()
firebase = pyrebase.initialize_app(firebase_config)
auth = firebase.auth()


def sign_in_user(email, password):
    try:
        user = auth.sign_in_with_email_and_password(email, password)
        return {"status": "success", "data": user}
    except Exception as e:
        return {"status": "error", "message": str(e)}


def send_password_reset_email_pyrebase(email):
    try:
        auth.send_password_reset_email(email)
        return {"status": "success"}
    except Exception as e:
        return {"status": "error", "message": str(e)}
