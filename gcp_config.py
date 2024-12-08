# gcp_config.py
import json
from google.cloud import storage
from google.cloud import secretmanager
import os
from google.auth import exceptions

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

def initialize_gcp_storage():
    """
    Initialize Google Cloud Storage client and return the bucket object.
    """
    try:
        # Fetch the path to the service account key from the environment variable
        gcp_credentials_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
        
        if gcp_credentials_path:
            # If credentials path is found, use it to initialize the storage client
            client = _get_credentials_from_secret_manager(
                os.getenv('gcp_project_id'),
                os.getenv('credentials_secret_id')
            )
        else:
            # If the environment variable is not set, the client will automatically look for credentials
            # set via other mechanisms (like gcloud auth application-default login)
            print("Using default credentials for GCP Storage.")
            client = storage.Client()

        # Fetch the GCP bucket name from environment variables
        bucket_name = os.getenv('GCP_BUCKET_NAME')
        
        # If bucket name is not set in environment, raise an error
        if not bucket_name:
            raise ValueError("GCP_BUCKET_NAME environment variable is not set.")
        
        # Get the GCP bucket object
        bucket = client.get_bucket(bucket_name)
        
        # Print confirmation message for successful initialization
        print(f"GCP Storage initialized with bucket: {bucket_name}")
        
        return bucket
    except exceptions.DefaultCredentialsError:
        print("Error: Default credentials not found.")
        raise
    except Exception as e:
        # Catch and log any error during initialization
        print(f"Error initializing GCP Storage: {e}")
        raise
