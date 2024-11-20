from dotenv import load_dotenv
import firebase_admin
from firebase_admin import credentials, firestore
import os

load_dotenv()

def initialize_firebase():
    """
    Initializes Firebase Admin SDK securely.
    """
    if not firebase_admin._apps:  # Ensures Firebase isn't initialized multiple times
        # Load credentials securely from an environment variable
        firebase_key_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
        if not firebase_key_path:
            raise ValueError("GOOGLE_APPLICATION_CREDENTIALS environment variable is not set.")
        
        cred = credentials.Certificate(firebase_key_path)
        firebase_admin.initialize_app(cred)
    return firestore.client()

# Initialize Firestore client globally for reuse
firestore_client = initialize_firebase()
