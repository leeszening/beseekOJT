import os
import firebase_admin
from firebase_admin import credentials, firestore, auth, storage
from dotenv import load_dotenv

load_dotenv()

# Initialize Firebase Admin SDK
# Note: The service account key file should be handled securely and not
# exposed in the code.
try:
    # Check if running in Google Cloud Run
    if 'K_SERVICE' in os.environ:
        # Initialize without credentials, relying on Application Default Credentials
        if not firebase_admin._apps:
            firebase_admin.initialize_app({
                'storageBucket': os.getenv("STORAGE_BUCKET")
            })
    else:
        # Construct a path to the service account key file for local
        # development. Assumes 'serviceAccountKey.json' is in the
        # project root directory.
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
            firebase_admin.initialize_app(cred, {
                'storageBucket': os.getenv("STORAGE_BUCKET")
            })

    db = firestore.client()
    print("Firestore client initialized successfully.")
except Exception as e:
    print(f"Failed to initialize Firestore client: {e}")
    db = None
