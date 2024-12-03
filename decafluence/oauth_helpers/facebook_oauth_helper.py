import logging
import requests
from firebase_config import firestore_client
from decafluence.oauth_helpers.base_oauth import BaseOAuthHelper

# Set up the logger
logger = logging.getLogger("app_logger")


class FacebookOAuthHelper(BaseOAuthHelper):
    def __init__(self):
        self.client_id = 'YOUR_FACEBOOK_CLIENT_ID'
        self.client_secret = 'YOUR_FACEBOOK_CLIENT_SECRET'
        self.redirect_uri = 'YOUR_REDIRECT_URI'
        self.scopes = 'public_profile,email,pages_manage_posts,pages_read_engagement'
        self.auth_url = 'https://www.facebook.com/v11.0/dialog/oauth'
        self.token_url = 'https://graph.facebook.com/v11.0/oauth/access_token'
        self.pages_url = 'https://graph.facebook.com/v11.0/me/accounts'
        self.firestore_client = firestore_client
        logger.info("FacebookOAuthHelper initialized")

    def get_authorization_url(self, redirect_uri=None):
        """Generate the Facebook authorization URL."""
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
        params = {
            'client_id': self.client_id,
            'redirect_uri': redirect_uri,
            'client_secret': self.client_secret,
            'code': authorization_code,
        }
        response = requests.get(self.token_url, params=params)
        response.raise_for_status()
        token_data = response.json()
        logger.info("Token exchange successful")
        return token_data

    def fetch_user_pages(self, access_token):
        """Fetch the list of Pages the user manages."""
        params = {"access_token": access_token}
        response = requests.get(self.pages_url, params=params)
        response.raise_for_status()
        pages_data = response.json()
        return pages_data.get('data', [])

    def save_token_and_pages(self, user_id, token_data, pages):
        """Save user tokens and Page details to Firestore."""
        user_ref = self.firestore_client.collection('user_tokens').document(user_id)
        user_ref.set({"token_data": token_data, "pages": pages})
        logger.info(f"Tokens and pages saved for user {user_id}")

    def refresh_token(self, user_id):
        """
        Refresh the user's token using saved refresh token data.
        """
        user_ref = self.firestore_client.collection('user_tokens').document(user_id)
        user_data = user_ref.get().to_dict()
        if not user_data:
            raise ValueError(f"No token data found for user {user_id}")

        token_data = user_data.get("token_data", {})
        access_token = token_data.get("access_token")
        if not access_token:
            raise ValueError(f"No access token found for user {user_id}")

        logger.info(f"Token refreshed for user {user_id}")
        return access_token

    def save_token(self, user_id, token_data):
        """
        Save the token data for the user.
        """
        user_ref = self.firestore_client.collection('user_tokens').document(user_id)
        user_ref.set({"token_data": token_data}, merge=True)
        logger.info(f"Token saved for user {user_id}")

    def complete_authentication_flow(self, user_id):
        """Complete the authentication flow and save tokens and Pages."""
        try:
            # Step 1: Generate authorization URL
            auth_url = self.get_authorization_url()
            print(f"Please go to this URL and authorize the application:\n{auth_url}")

            # Step 2: Get authorization code
            authorization_code = input("Enter the authorization code from Facebook: ")

            # Step 3: Exchange code for token
            token_data = self.exchange_code_for_token(authorization_code)

            # Step 4: Fetch Pages the user manages
            access_token = token_data['access_token']
            pages = self.fetch_user_pages(access_token)

            # Step 5: Save tokens and Pages
            self.save_token_and_pages(user_id, token_data, pages)

            logger.info(f"Authentication flow completed successfully for user {user_id}")
        except Exception as e:
            logger.error(f"Error during authentication flow: {e}")
            raise
