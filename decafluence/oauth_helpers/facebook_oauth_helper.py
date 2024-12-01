import requests
from firebase_admin import firestore
from decafluence.oauth_helpers.base_oauth import BaseOAuthHelper
from logger_config import setup_logger  # Assuming your setup_logger function is here


class FacebookOAuthHelper(BaseOAuthHelper):
    def __init__(self):
        super().__init__()
        self.client_id = None
        self.client_secret = None
        self.redirect_uri = None
        self.auth_url = 'https://www.facebook.com/v11.0/dialog/oauth'
        self.token_url = 'https://graph.facebook.com/v11.0/oauth/access_token'
        self.debug_token_url = 'https://graph.facebook.com/debug_token'
        self.firestore_client = firestore.client()
        self.logger = setup_logger()

    def set_credentials(self, client_id, client_secret, redirect_uri):
        """
        Sets the client credentials dynamically.
        """
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.logger.info("Facebook OAuth credentials have been set.")

    def get_authorization_url(self, state=None):
        """
        Generates the Facebook authorization URL.
        """
        if not all([self.client_id, self.redirect_uri]):
            raise ValueError("Client ID and Redirect URI must be set before generating the authorization URL.")

        params = {
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "scope": "public_profile,email,pages_manage_posts,pages_read_engagement",
        }

        if state:
            params["state"] = state

        auth_url = requests.Request('GET', self.auth_url, params=params).prepare().url
        self.logger.info(f"Generated Facebook authorization URL: {auth_url}")
        return auth_url

    def exchange_code_for_token(self, authorization_code):
        """
        Exchanges the authorization code for an access token.
        """
        if not all([self.client_id, self.client_secret, self.redirect_uri]):
            raise ValueError("Client credentials must be set before exchanging the authorization code.")

        data = {
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "client_secret": self.client_secret,
            "code": authorization_code,
        }

        self.logger.info("Exchanging authorization code for access token...")
        response = requests.get(self.token_url, params=data)
        response.raise_for_status()
        token_data = response.json()
        self.logger.info(f"Token exchange successful: {token_data}")
        return token_data

    def save_token(self, user_id, token_data):
        """
        Saves the token data in Firestore under the given user ID.
        """
        if not user_id or not token_data:
            raise ValueError("User ID and token data are required to save the token.")

        user_tokens_ref = self.firestore_client.collection('user_tokens')
        user_tokens_ref.document(user_id).set(token_data)
        self.logger.info(f"Token data saved for user ID: {user_id}")

    def get_token(self, user_id):
        """
        Retrieves the token data for the specified user ID from Firestore.
        """
        if not user_id:
            raise ValueError("User ID is required to retrieve the token.")

        user_tokens_ref = self.firestore_client.collection('user_tokens')
        token_doc = user_tokens_ref.document(user_id).get()
        if token_doc.exists:
            self.logger.info(f"Token data retrieved for user ID: {user_id}")
            return token_doc.to_dict()
        else:
            self.logger.warning(f"No token data found for user ID: {user_id}")
            return None

    def validate_token(self, user_id):
        """
        Validates the access token by calling Facebook's token debugging endpoint.
        """
        token_data = self.get_token(user_id)
        if not token_data or "access_token" not in token_data:
            self.logger.warning(f"No valid access token found for user ID: {user_id}")
            return False

        access_token = token_data["access_token"]
        params = {
            "input_token": access_token,
            "access_token": f"{self.client_id}|{self.client_secret}",
        }

        self.logger.info("Validating access token with Facebook...")
        response = requests.get(self.debug_token_url, params=params)
        if response.status_code == 200:
            self.logger.info("Access token validation successful.")
            return True
        else:
            self.logger.warning(f"Access token validation failed: {response.text}")
            return False

    def refresh_token(self, user_id):
        """
        Facebook tokens do not support refreshing, so reuse the existing token.
        """
        token_data = self.get_token(user_id)
        if not token_data or "access_token" not in token_data:
            raise ValueError("No valid access token found for the user.")
        self.logger.info("Returning existing access token as Facebook does not use refresh tokens.")
        return token_data["access_token"]

    def complete_authentication_flow(self, user_id, authorization_code):
        """
        Completes the entire authentication flow:
        1. Exchanges the authorization code for a token.
        2. Saves the token data in Firestore under the given user ID.
        3. Validates the token.
        """
        self.logger.info("Completing authentication flow...")
        token_data = self.exchange_code_for_token(authorization_code)
        self.save_token(user_id, token_data)
        is_valid = self.validate_token(user_id)
        if is_valid:
            self.logger.info(f"Authentication flow completed successfully for user ID: {user_id}")
        else:
            self.logger.error(f"Token validation failed for user ID: {user_id}")
        return is_valid
