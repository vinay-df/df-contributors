import logging
import requests
from firebase_config import firestore_client
from decafluence.oauth_helpers.base_oauth import BaseOAuthHelper

# Set up the logger
logger = logging.getLogger("app_logger")

class LinkedInOAuthHelper(BaseOAuthHelper):
    def __init__(self):
        self.client_id = 'YOUR_LINKEDIN_CLIENT_ID'
        self.client_secret = 'YOUR_LINKEDIN_CLIENT_SECRET'
        self.redirect_uri = 'YOUR_REDIRECT_URI'
        self.scopes = 'w_member_social%20profile%20email%20openid'
        self.token_url = 'https://www.linkedin.com/oauth/v2/accessToken'
        self.auth_url = 'https://www.linkedin.com/oauth/v2/authorization'
        self.api_url = 'https://api.linkedin.com/v2/userinfo'
        self.firestore_client = firestore_client
        logger.info("LinkedInOAuthHelper initialized")

    def get_authorization_url(self, redirect_uri=None):
        """Generate the LinkedIn authorization URL."""
        redirect_uri = redirect_uri or self.redirect_uri
        auth_url = f"{self.auth_url}?response_type=code&client_id={self.client_id}&redirect_uri={redirect_uri}&scope={self.scopes}"
        logger.info(f"Authorization URL: {auth_url}")
        return auth_url

    def exchange_code_for_token(self, authorization_code, redirect_uri=None):
        """Exchange the authorization code for an access token."""
        redirect_uri = redirect_uri or self.redirect_uri
        data = {
            'grant_type': 'authorization_code',
            'code': authorization_code,
            'redirect_uri': redirect_uri,
            'client_id': self.client_id,
            'client_secret': self.client_secret,
        }
        logger.info("Exchanging authorization code for token")
        response = requests.post(self.token_url, data=data)
        response.raise_for_status()
        token_data = response.json()
        if not token_data.get('access_token'):
            raise ValueError("Access token not found in the response.")
        logger.info("Token exchange successful")
        return token_data

    def save_token(self, user_id, token_data):
        """Save user tokens to Firestore."""
        user_tokens_ref = self.firestore_client.collection('user_tokens')
        user_tokens_ref.document(user_id).set(token_data)
        logger.info(f"Token saved for user {user_id}")

    def get_token(self, user_id):
        """Retrieve user tokens from Firestore."""
        user_tokens_ref = self.firestore_client.collection('user_tokens')
        token_doc = user_tokens_ref.document(user_id).get()
        if token_doc.exists:
            logger.info(f"Retrieved token for user {user_id}")
            return token_doc.to_dict()
        logger.warning(f"No token found for user {user_id}")
        return None
    
    def refresh_token(self, user_id):
        """Refresh the user's access token using the refresh token."""
        try:
            token_data = self.get_token(user_id)
            if not token_data:
                raise ValueError("No token found for user.")

            refresh_token = token_data.get('access_token')
            if not refresh_token:
                raise ValueError("No refresh token available.")

            data = {
                'grant_type': 'refresh_token',
                'refresh_token': refresh_token,
                'client_id': self.client_id,
                'client_secret': self.client_secret,
            }
            logger.info(f"Refreshing token for user {user_id}")
            response = requests.post(self.token_url, data=data)
            response.raise_for_status()
            new_token_data = response.json()
            self.save_token(user_id, new_token_data)
            logger.info(f"Token refreshed for user {user_id}")
            return new_token_data.get('access_token')
        except requests.exceptions.RequestException as e:
            logger.error(f"Error refreshing token for user {user_id}: {e}")
            raise

    def get_user_urn(self, access_token):
        """Fetch the user URN using the LinkedIn 'userinfo' endpoint."""
        headers = {'Authorization': f'Bearer {access_token}'}
        response = requests.get(self.api_url, headers=headers)
        response.raise_for_status()
        user_info = response.json()
        user_urn = user_info.get('sub')
        if not user_urn:
            raise ValueError("User URN not found in the LinkedIn API response.")
        logger.info(f"User URN: {user_urn}")
        return user_urn

    def complete_authentication_flow(self, user_id):
        """
        Complete the full authentication flow:
        1. Print the authorization URL for user login.
        2. Accept the authorization code from the user.
        3. Exchange the code for access tokens.
        4. Fetch the user URN.
        5. Save tokens under the given user_id.
        """
        try:
            # Step 1: Generate and display authorization URL
            logger.info("Step 1: Generating authorization URL")
            auth_url = self.get_authorization_url()
            print(f"Please go to this URL and authorize the application:\n{auth_url}")
            
            # Step 2: Get authorization code from user
            authorization_code = input("Enter the authorization code from LinkedIn: ")

            # Step 3: Exchange authorization code for tokens
            logger.info("Step 2: Exchanging code for token")
            token_data = self.exchange_code_for_token(authorization_code)

            # Step 5: Save tokens with user ID
            self.save_token(user_id, token_data)
            logger.info(f"Authentication flow completed for user: {user_id}")
            return
        except Exception as e:
            logger.error(f"Error in authentication flow: {e}")
            raise
