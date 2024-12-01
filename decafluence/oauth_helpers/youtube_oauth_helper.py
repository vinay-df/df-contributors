import os
import requests
from dotenv import load_dotenv
from firebase_admin import firestore
from decafluence.oauth_helpers.base_oauth import BaseOAuthHelper

class YouTubeOAuthHelper(BaseOAuthHelper):
    def __init__(self):
        load_dotenv()  # Load environment variables from .env
        self.client_id = os.getenv('YOUTUBE_CLIENT_ID')
        self.client_secret = os.getenv('YOUTUBE_CLIENT_SECRET')
        self.redirect_uri = os.getenv('REDIRECT_URI')
        self.token_url = 'https://oauth2.googleapis.com/token'
        self.auth_url = 'https://accounts.google.com/o/oauth2/auth'
        self.scope = 'https://www.googleapis.com/auth/youtube.upload'
        self.firestore_client = firestore.client()

    def get_authorization_url(self, redirect_uri):
        """Generate the authorization URL for OAuth."""
        auth_url = f"{self.auth_url}?client_id={self.client_id}&redirect_uri={redirect_uri}&scope={self.scope}&response_type=code"
        return auth_url

    def exchange_code_for_token(self, authorization_code, redirect_uri):
        """Exchange authorization code for access token."""
        data = {
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'grant_type': 'authorization_code',
            'redirect_uri': redirect_uri,
            'code': authorization_code
        }
        response = requests.post(self.token_url, data=data)
        if response.status_code == 200:
            return response.json()  # Returns a JSON containing access_token and refresh_token
        else:
            raise Exception(f"Failed to exchange code for token: {response.text}")

    def save_token(self, user_id, token_data):
        """Save token data to Firebase for persistent storage."""
        user_tokens_ref = self.firestore_client.collection('user_tokens')
        user_tokens_ref.document(user_id).set(token_data)

    def get_token(self, user_id):
        """Retrieve saved token from Firebase."""
        user_tokens_ref = self.firestore_client.collection('user_tokens')
        token_doc = user_tokens_ref.document(user_id).get()
        return token_doc.to_dict() if token_doc.exists else None

    def refresh_token(self, user_id):
        """Refresh access token using the refresh token."""
        token_data = self.get_token(user_id)
        if not token_data:
            raise ValueError("No token found for user.")
        
        refresh_token = token_data.get('refresh_token')
        if not refresh_token:
            raise ValueError("No refresh token available.")
        
        data = {
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'grant_type': 'refresh_token',
            'refresh_token': refresh_token
        }
        
        response = requests.post(self.token_url, data=data)
        if response.status_code == 200:
            new_token_data = response.json()
            # Update the stored token data with the new access token
            self.save_token(user_id, new_token_data)
            return new_token_data['access_token']
        else:
            raise Exception(f"Failed to refresh token: {response.text}")
