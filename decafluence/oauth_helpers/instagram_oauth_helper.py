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
        self.scopes = 'instagram_business_basic%2Cinstagram_business_manage_messages%2Cinstagram_business_manage_comments%2Cinstagram_business_content_publish'
        self.auth_url = 'https://api.instagram.com/oauth/authorize'
        self.token_url = 'https://api.instagram.com/oauth/access_token'
        self.media_url = 'https://graph.instagram.com/me/media'
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

    def fetch_user_media(self, access_token):
        """Fetch the list of media objects from the user's Instagram account."""
        params = {
            "fields": "id,caption,media_type,media_url,timestamp",
            "access_token": access_token,
        }
        response = requests.get(self.media_url, params=params)
        response.raise_for_status()
        media_data = response.json()
        return media_data.get('data', [])

    def save_token(self, user_id, token_data):
        """Save the token data to Firestore."""
        user_ref = self.firestore_client.collection('user_tokens').document(user_id)
        user_ref.set({"token_data": token_data})
        logger.info(f"Token data saved for user {user_id}")

    def refresh_token(self, user_id):
        """Refresh and retrieve the current access token for the user."""
        user_ref = self.firestore_client.collection('user_tokens').document(user_id)
        user_data = user_ref.get().to_dict()
        if not user_data:
            raise ValueError(f"No token data found for user {user_id}")

        token_data = user_data.get("token_data", {})
        access_token = token_data.get("access_token")
        if not access_token:
            raise ValueError(f"No access token found for user {user_id}")

        logger.info(f"Access token retrieved for user {user_id}")
        return access_token

    def save_token_and_media(self, user_id, token_data, media):
        """Save user tokens and media details to Firestore."""
        user_ref = self.firestore_client.collection('user_tokens').document(user_id)
        user_ref.set({"token_data": token_data, "media": media})
        logger.info(f"Tokens and media saved for user {user_id}")

    def complete_authentication_flow(self, user_id):
        """Complete the authentication flow and save tokens and user media."""
        try:
            # Step 1: Generate authorization URL
            auth_url = self.get_authorization_url()
            print(f"Please go to this URL and authorize the application:\n{auth_url}")

            # Step 2: Get authorization code
            authorization_code = input("Enter the authorization code from Instagram: ")

            # Step 3: Exchange code for token
            token_data = self.exchange_code_for_token(authorization_code)

            # Step 4: Fetch user media
            access_token = token_data['access_token']
            media = self.fetch_user_media(access_token)

            # Step 5: Save tokens and media
            self.save_token_and_media(user_id, token_data, media)

            logger.info(f"Authentication flow completed successfully for user {user_id}")
        except Exception as e:
            logger.error(f"Error during authentication flow: {e}")
            raise
