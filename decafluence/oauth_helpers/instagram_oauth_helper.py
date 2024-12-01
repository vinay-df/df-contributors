import requests
from firebase_admin import firestore
from decafluence.oauth_helpers.base_oauth import BaseOAuthHelper

class InstagramOAuthHelper(BaseOAuthHelper):
    def __init__(self):
        self.client_id = None
        self.client_secret = None
        self.redirect_uri = None
        self.token_url = 'https://api.instagram.com/oauth/access_token'
        self.auth_url = 'https://api.instagram.com/oauth/authorize'
        self.firestore_client = firestore.client()

    def get_authorization_url(self, state=None):
        """
        Constructs the authorization URL for Instagram OAuth.

        Args:
            state (str, optional): An optional state parameter to prevent CSRF.

        Returns:
            str: The URL where the user should be redirected to authenticate.
        """
        url = f"{self.auth_url}?client_id={self.client_id}&redirect_uri={self.redirect_uri}&scope=user_profile,user_media&response_type=code"
        if state:
            url += f"&state={state}"
        return url

    def exchange_code_for_token(self, authorization_code):
        """
        Exchanges the authorization code for an access token.

        Args:
            authorization_code (str): The authorization code received from Instagram.

        Returns:
            dict: The token data including access_token and user_id.
        """
        data = {
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'grant_type': 'authorization_code',
            'redirect_uri': self.redirect_uri,
            'code': authorization_code
        }
        response = requests.post(self.token_url, data=data)
        response.raise_for_status()
        return response.json()

    def save_token(self, user_id, token_data):
        """
        Saves the token data to Firestore under the specified user ID.

        Args:
            user_id (str): The user ID to associate the token with.
            token_data (dict): The token data to save.
        """
        user_tokens_ref = self.firestore_client.collection('user_tokens')
        user_tokens_ref.document(user_id).set(token_data)

    def get_token(self, user_id):
        """
        Retrieves the saved token data for a user.

        Args:
            user_id (str): The user ID to fetch the token for.

        Returns:
            dict: The token data, or None if no data exists.
        """
        user_tokens_ref = self.firestore_client.collection('user_tokens')
        token_doc = user_tokens_ref.document(user_id).get()
        return token_doc.to_dict() if token_doc.exists else None

    def refresh_token(self, user_id):
        """
        Retrieves the current access token for a user.

        Args:
            user_id (str): The user ID to fetch the token for.

        Returns:
            str: The access token.

        Raises:
            ValueError: If no token is found or access_token is missing.
        """
        token_data = self.get_token(user_id)
        if not token_data:
            raise ValueError("No token found for user.")
        
        access_token = token_data.get('access_token')
        if not access_token:
            raise ValueError("No access token available.")
        
        return access_token

    def complete_authentication_flow(self, user_id):
        """
        Completes the authentication flow: exchanges the code for a token and saves it.

        Args:
            user_id (str): The user ID to associate the token with.
        """
        print(f"Visit the following URL to authenticate: {self.get_authorization_url()}")
        authorization_code = input("Enter the authorization code you received: ")
        token_data = self.exchange_code_for_token(authorization_code)
        self.save_token(user_id, token_data)
        print("Authentication completed successfully!")
