from abc import ABC, abstractmethod

class BaseOAuthHelper(ABC):
    def __init__(self, client_id, client_secret, auth_url, token_url, scope):
        self.client_id = client_id
        self.client_secret = client_secret
        self.auth_url = auth_url
        self.token_url = token_url
        self.scope = scope

    @abstractmethod
    def get_authorization_url(self, redirect_uri):
        """Generate authorization URL for OAuth."""
        pass

    @abstractmethod
    def exchange_code_for_token(self, authorization_code, redirect_uri):
        """Exchange authorization code for access token."""
        pass

    @abstractmethod
    def refresh_token(self, user_id):
        """Refresh access token."""
        pass

    @abstractmethod
    def save_token(self, user_id, token_data):
        """Save token data to persistent storage."""
        pass
