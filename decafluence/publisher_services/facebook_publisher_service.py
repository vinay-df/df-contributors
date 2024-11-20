import requests
from decafluence.oauth_helpers.facebook_oauth_helper import FacebookOAuthHelper
from decafluence.publisher_services.base_publisher import BasePublisherService
from decafluence.validators.content_validators import ContentValidationError, ContentValidator


class FacebookPublisherService(BasePublisherService):
    def __init__(self, oauth_helper: FacebookOAuthHelper):
        self.oauth_helper = oauth_helper
        self.api_url = 'https://graph.facebook.com/v11.0/'
        self.validator = ContentValidator(platform='facebook')

    def _get_auth_header(self, user_id):
        access_token = self.oauth_helper.refresh_token(user_id)
        return {'Authorization': f'Bearer {access_token}'}

    def post_text(self, user_id, content):
        try:
            self.validator.validate_text(content)
            access_token = self.oauth_helper.refresh_token(user_id)
            data = {
                "message": content,
                "access_token": access_token
            }
            response = requests.post(f"{self.api_url}me/feed", data=data)
            return response.json()
        except ContentValidationError as e:
            raise e  # Reraise the validation error
        except requests.HTTPError as e:
            raise Exception(f"Failed to post text on Facebook: {str(e)}")

    def post_image(self, user_id, content, image_path):
        try:
            self.validator.validate_image(image_path)  # Validate image
            self.validator.validate_text(content)
            access_token = self.oauth_helper.refresh_token(user_id)
            data = {
                "message": content,
                "access_token": access_token
            }
            
            with open(image_path, 'rb') as image_file:
                files = {'file': image_file}
                response = requests.post(f"{self.api_url}me/photos", data=data, files=files)

            return response.json()
        except ContentValidationError as e:
            raise e  # Reraise the validation error
        except requests.HTTPError as e:
            raise Exception(f"Failed to post text on Facebook: {str(e)}")

    def post_video(self, user_id, content, video_path):
        try:
            self.validator.validate_video(video_path)  # Validate video
            self.validator.validate_text(content)
            access_token = self.oauth_helper.refresh_token(user_id)
            data = {
                "description": content,
                "access_token": access_token
            }

            with open(video_path, 'rb') as video_file:
                files = {'file': video_file}
                response = requests.post(f"{self.api_url}me/videos", data=data, files=files)

            return response.json()
        except ContentValidationError as e:
            raise e  # Reraise the validation error
        except requests.HTTPError as e:
            raise Exception(f"Failed to post text on Facebook: {str(e)}")

    def post_document(self, user_id, content, document_path):
        # Facebook does not support document uploads directly. You may need to upload to a service
        # and share the link or consider posting it as a link.
        raise NotImplementedError("Facebook does not allow document uploads directly.")
