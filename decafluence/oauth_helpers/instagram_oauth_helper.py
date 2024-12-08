import logging
import requests
from firebase_config import firestore_client
from decafluence.oauth_helpers.base_oauth import BaseOAuthHelper

# Set up the logger
logger = logging.getLogger("app_logger")

class InstagramOAuthHelper(BaseOAuthHelper):
    def __init__(self):
        self.client_id = 'YOUR_INSTAGRAM_CLIENT_ID'
        self.client_secret = 'YOUR_INSTAGRAM_CLIENT_SECRET'
        self.redirect_uri = 'YOUR_REDIRECT_URI'
        self.scopes = "instagram_business_basic%2Cinstagram_business_manage_messages%2Cinstagram_business_manage_comments%2Cinstagram_business_content_publish"
        self.auth_url = 'https://api.instagram.com/oauth/authorize'
        self.token_url = 'https://api.instagram.com/oauth/access_token'
        self.graph_url = 'https://graph.instagram.com'
        self.firestore_client = firestore_client
        logger.info("InstagramOAuthHelper initialized")

    def get_authorization_url(self, redirect_uri=None):
        """Generate the Instagram authorization URL."""
        redirect_uri = redirect_uri or self.redirect_uri
        auth_url = (
            f"{self.auth_url}?client_id={self.client_id}"
            f"&redirect_uri={redirect_uri}"
            f"&scope={self.scopes}&response_type=code"
        )
        logger.info(f"Authorization URL: {auth_url}")
        return auth_url

    def exchange_code_for_token(self, authorization_code, redirect_uri=None):
        """Exchange the authorization code for an access token."""
        redirect_uri = redirect_uri or self.redirect_uri
        data = {
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'grant_type': 'authorization_code',
            'redirect_uri': redirect_uri,
            'code': authorization_code,
        }
        response = requests.post(self.token_url, data=data)
        response.raise_for_status()
        token_data = response.json()
        logger.info("Token exchange successful")
        return token_data

    def fetch_user_info(self, access_token):
        """Fetch the user ID and other details from Instagram."""
        url = f"{self.graph_url}/me"
        params = {
            "fields": "id,username",
            "access_token": access_token,
        }
        response = requests.get(url, params=params)
        response.raise_for_status()
        user_data = response.json()
        return user_data

    def save_token_and_user_info(self, user_id, token_data, user_data):
        """Save token and user information to Firestore."""
        user_ref = self.firestore_client.collection('user_tokens').document(user_id)
        user_ref.set({
            "token_data": token_data,
            "user_info": user_data
        }, merge=True)
        logger.info(f"Token and user info saved for user {user_id}")

    def complete_authentication_flow(self, user_id):
        """Complete the authentication flow and save tokens and user data."""
        try:
            # Step 1: Generate authorization URL
            auth_url = self.get_authorization_url()
            print(f"Please go to this URL and authorize the application:\n{auth_url}")

            # Step 2: Get authorization code
            authorization_code = input("Enter the authorization code from Instagram: ")

            # Step 3: Exchange code for token
            token_data = self.exchange_code_for_token(authorization_code)

            # Step 4: Fetch user info (user_id)
            access_token = token_data['access_token']
            user_data = self.fetch_user_info(access_token)

            # Step 5: Save token data and user info to Firestore
            # Use the user_id passed in the function arguments
            self.save_token_and_user_info(user_id, token_data, user_data)

            logger.info(f"Authentication flow completed successfully for user {user_id}")
        except Exception as e:
            logger.error(f"Error during authentication flow: {e}")
            raise

    def refresh_token(self, refresh_token):
        """Refresh the access token using the refresh token."""
        data = {
            'grant_type': 'refresh_token',
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'refresh_token': refresh_token
        }
        response = requests.post(self.token_url, data=data)
        response.raise_for_status()
        token_data = response.json()
        logger.info("Token refreshed successfully")
        return token_data

    def save_token(self, user_id, token_data):
        """Save the new token data for a user."""
        user_ref = self.firestore_client.collection('user_tokens').document(user_id)
        user_ref.update({
            "token_data": token_data
        })
        logger.info(f"Token updated for user {user_id}")
