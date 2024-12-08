import json
from dotenv import load_dotenv
import firebase_admin
from firebase_admin import credentials, firestore
import os
from google.cloud import secretmanager
import os

load_dotenv()

def _get_credentials_from_secret_manager(project_id, secret_id):
    """Fetch credentials from Secret Manager."""
    try:
        # logger.info(f"Accessing Secret Manager in project: {project_id}")
        client = secretmanager.SecretManagerServiceClient()
        name = f"projects/{project_id}/secrets/{secret_id}/versions/latest"
        response = client.access_secret_version(request={"name": name})
        credentials_json = json.loads(response.payload.data.decode("UTF-8"))
        # logger.info("Successfully retrieved credentials from Secret Manager")
        return credentials_json
    except Exception as e:
        # logger.error(f"Error accessing Secret Manager: {str(e)}")
        raise

def initialize_firebase():
    """
    Initializes Firebase Admin SDK securely.
    """
    if not firebase_admin._apps:  # Ensures Firebase isn't initialized multiple times
        # Load credentials securely from an environment variable
        client = _get_credentials_from_secret_manager(
                os.getenv('gcp_project_id'),
                os.getenv('credentials_secret_id')
            )
        
        cred = credentials.Certificate(client)
        firebase_admin.initialize_app(cred)
    return firestore.client()

# Initialize Firestore client globally for reuse
firestore_client = initialize_firebase()
