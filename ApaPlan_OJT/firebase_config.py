import os
import firebase_admin
from firebase_admin import credentials, firestore, auth
from dotenv import load_dotenv

load_dotenv()

# Initialize Firebase Admin SDK
# Note: The service account key file should be handled securely and not
# exposed in the code. 
try:
    # Construct a path to the service account key file.
    # Assumes 'serviceAccountKey.json' is in the project root directory.
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    cred_path = os.path.join(BASE_DIR, "serviceAccountKey.json")

    if not os.path.exists(cred_path):
        raise FileNotFoundError(
            "Firebase service account key file not found at "
            f"'{cred_path}'. Please make sure 'serviceAccountKey.json' "
            "is in the project root."
        )

    cred = credentials.Certificate(cred_path)
    if not firebase_admin._apps:
        firebase_admin.initialize_app(cred)
    db = firestore.client()
    print("Firestore client initialized successfully.")
except Exception as e:
    print(f"Failed to initialize Firestore client: {e}")
    db = None
