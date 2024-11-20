import requests
from firebase_admin import firestore
from requests_oauthlib import OAuth1Session
from decafluence.oauth_helpers.base_oauth import BaseOAuthHelper

class XOAuthHelper(BaseOAuthHelper):
    def __init__(self):
        self.client_key = 'YOUR_X_API_KEY'
        self.client_secret = 'YOUR_X_API_SECRET'
        self.access_token_url = 'https://api.twitter.com/oauth/access_token'
        self.request_token_url = 'https://api.twitter.com/oauth/request_token'
        self.auth_url = 'https://api.twitter.com/oauth/authorize'
        self.firestore_client = firestore.client()

    def get_authorization_url(self):
        oauth = OAuth1Session(self.client_key, client_secret=self.client_secret)
        fetch_response = oauth.fetch_request_token(self.request_token_url)
        resource_owner_key = fetch_response.get('oauth_token')
        resource_owner_secret = fetch_response.get('oauth_token_secret')

        self.firestore_client.collection('request_tokens').document('temp').set({
            'resource_owner_key': resource_owner_key,
            'resource_owner_secret': resource_owner_secret
        })

        return f"{self.auth_url}?oauth_token={resource_owner_key}"

    def exchange_code_for_token(self, oauth_verifier):
        temp_tokens = self.firestore_client.collection('request_tokens').document('temp').get().to_dict()
        oauth_token = temp_tokens.get('resource_owner_key')
        oauth_token_secret = temp_tokens.get('resource_owner_secret')

        oauth = OAuth1Session(self.client_key, client_secret=self.client_secret,
                              resource_owner_key=oauth_token,
                              resource_owner_secret=oauth_token_secret,
                              verifier=oauth_verifier)
        access_token_response = oauth.fetch_access_token(self.access_token_url)
        return access_token_response

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

        access_token = token_data.get('oauth_token')
        access_token_secret = token_data.get('oauth_token_secret')
        if not access_token or not access_token_secret:
            raise ValueError("No access token available.")

        return access_token, access_token_secret
