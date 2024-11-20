from datetime import time
import requests
from decafluence.oauth_helpers.x_oauth_helper import XOAuthHelper
from decafluence.publisher_services.base_publisher import BasePublisherService
import uuid

from decafluence.validators.content_validators import ContentValidationError, ContentValidator

class XPublisherService(BasePublisherService):
    def __init__(self, oauth_helper: XOAuthHelper):
        self.oauth_helper = oauth_helper
        self.api_url = 'https://api.twitter.com/1.1/'
        self.validator = ContentValidator(platform='x')

    def _get_auth_header(self, user_id):
        access_token, access_token_secret = self.oauth_helper.refresh_token(user_id)
        return {
            'Authorization': f'OAuth oauth_consumer_key="{self.oauth_helper.client_key}", '
                             f'oauth_token="{access_token}", '
                             f'oauth_signature_method="HMAC-SHA1", '
                             f'oauth_timestamp="{int(time.time())}", '
                             f'oauth_nonce="{uuid.uuid4()}", '
                             f'oauth_version="1.0", '
                             f'oauth_signature="{self._generate_signature(user_id, access_token)}"'
        }

    def _generate_signature(self, user_id, access_token):
        # This method will create the OAuth signature required for the request
        # You will need to implement this according to Twitter's requirements.
        # It requires creating a base string and signing it using HMAC-SHA1.
        pass  # Implement signature generation logic here

    def post_text(self, user_id, content):
        try:
            self.validator.validate_text(content)
            headers = self._get_auth_header(user_id)
            data = {
                "status": content
            }
            response = requests.post(f"{self.api_url}statuses/update.json", headers=headers, data=data)
            return response.json()
        except ContentValidationError as e:
            raise e  # Reraise the validation error
        except requests.HTTPError as e:
            raise Exception(f"Failed to post text on X: {str(e)}")

    def post_image(self, user_id, content, image_path):
        try:
            self.validator.validate_image(image_path)  # Validate image
            self.validator.validate_text(content)
            headers = self._get_auth_header(user_id)

            image_data = {'media': open(image_path, 'rb')}
            upload_response = requests.post(f"{self.api_url}media/upload.json", headers=headers, files=image_data)
            media_id = upload_response.json().get('media_id_string')

            tweet_data = {
                "status": content,
                "media_ids": media_id
            }
            response = requests.post(f"{self.api_url}statuses/update.json", headers=headers, data=tweet_data)
            return response.json()
        except ContentValidationError as e:
            raise e  # Reraise the validation error
        except requests.HTTPError as e:
            raise Exception(f"Failed to post text on X: {str(e)}")

    def post_video(self, user_id, content, video_path):
        raise NotImplementedError("Video uploads are complex and require chunked uploads.")

    def post_document(self, user_id, content, document_path):
        raise NotImplementedError("Twitter does not allow document uploads directly.")
