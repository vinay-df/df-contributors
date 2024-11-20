import requests
from firebase_admin import firestore
from decafluence.oauth_helpers.base_oauth import BaseOAuthHelper

class FacebookOAuthHelper(BaseOAuthHelper):
    def __init__(self):
        self.client_id = 'YOUR_FACEBOOK_CLIENT_ID'
        self.client_secret = 'YOUR_FACEBOOK_CLIENT_SECRET'
        self.redirect_uri = 'YOUR_REDIRECT_URI'
        self.token_url = 'https://graph.facebook.com/v11.0/oauth/access_token'
        self.auth_url = 'https://www.facebook.com/v11.0/dialog/oauth'
        self.firestore_client = firestore.client()

    def get_authorization_url(self):
        return f"{self.auth_url}?client_id={self.client_id}&redirect_uri={self.redirect_uri}&scope=public_profile,email,publish_to_groups"

    def exchange_code_for_token(self, authorization_code):
        data = {
            'client_id': self.client_id,
            'redirect_uri': self.redirect_uri,
            'client_secret': self.client_secret,
            'code': authorization_code
        }
        response = requests.get(self.token_url, params=data)
        return response.json()

    def save_token(self, user_id, token_data):
        user_tokens_ref = self.firestore_client.collection('user_tokens')
        user_tokens_ref.document(user_id).set(token_data)

    def get_token(self, user_id):
        user_tokens_ref = self.firestore_client.collection('user_tokens')
        token_doc = user_tokens_ref.document(user_id).get()
        return token_doc.to_dict() if token_doc.exists else None

    def refresh_token(self, user_id):
        token_data = self.get_token(user_id)
        if not token_data:
            raise ValueError("No token found for user.")

        access_token = token_data.get('access_token')
        if not access_token:
            raise ValueError("No access token available.")
        
        return access_token  # Facebook doesn't have refresh tokens; use access token directly.
