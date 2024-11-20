import requests
from decafluence.oauth_helpers.instagram_oauth_helper import InstagramOAuthHelper
from decafluence.publisher_services.base_publisher import BasePublisherService
from decafluence.validators.content_validators import ContentValidationError, ContentValidator

class InstagramPublisherService(BasePublisherService):
    def __init__(self, oauth_helper: InstagramOAuthHelper):
        self.oauth_helper = oauth_helper
        self.api_url = 'https://graph.instagram.com/'
        self.validator = ContentValidator(platform='instagram')

    def _get_auth_header(self, user_id):
        access_token = self.oauth_helper.refresh_token(user_id)
        return {'Authorization': f'Bearer {access_token}'}

    def post_text(self, user_id, content):
        # Instagram Graph API requires a media object to post.
        raise NotImplementedError("Posting plain text directly is not supported on Instagram. Please use media.")

    def post_image(self, user_id, content, image_path):
        try:
            self.validator.validate_image(image_path)  # Validate image
            self.validator.validate_text(content)
            access_token = self.oauth_helper.refresh_token(user_id)

            # Step 1: Upload the image
            image_url = self._upload_image(access_token, image_path)
            
            # Step 2: Create a media object
            media_data = {
                "caption": content,
                "image_url": image_url,
                "access_token": access_token
            }
            response = requests.post(f"{self.api_url}me/media", data=media_data)
            media_id = response.json().get("id")

            # Step 3: Publish the media object
            publish_data = {
                "creation_id": media_id,
                "access_token": access_token
            }
            publish_response = requests.post(f"{self.api_url}me/media_publish", data=publish_data)
            return publish_response.json()
        except ContentValidationError as e:
            raise e  # Reraise the validation error
        except requests.HTTPError as e:
            raise Exception(f"Failed to post text on Instagram: {str(e)}")

    def _upload_image(self, access_token, image_path):
        with open(image_path, 'rb') as image_file:
            files = {'file': image_file}
            response = requests.post(f"https://graph.facebook.com/v12.0/me/photos?access_token={access_token}", files=files)
            if response.status_code != 200:
                raise Exception("Failed to upload image")
            return response.json().get("link")  # URL of uploaded image

    def post_video(self, user_id, content, video_path):
        try:
            self.validator.validate_video(video_path)  # Validate video
            self.validator.validate_text(content)
            access_token = self.oauth_helper.refresh_token(user_id)

            # Step 1: Upload the video
            video_url = self._upload_video(access_token, video_path)

            # Step 2: Create a media object
            media_data = {
                "caption": content,
                "video_url": video_url,
                "access_token": access_token
            }
            response = requests.post(f"{self.api_url}me/media", data=media_data)
            media_id = response.json().get("id")

            # Step 3: Publish the media object
            publish_data = {
                "creation_id": media_id,
                "access_token": access_token
            }
            publish_response = requests.post(f"{self.api_url}me/media_publish", data=publish_data)
            return publish_response.json()
        except ContentValidationError as e:
            raise e  # Reraise the validation error
        except requests.HTTPError as e:
            raise Exception(f"Failed to post text on Instagram: {str(e)}")

    def _upload_video(self, access_token, video_path):
        with open(video_path, 'rb') as video_file:
            files = {'file': video_file}
            response = requests.post(f"https://graph.facebook.com/v12.0/me/videos?access_token={access_token}", files=files)
            if response.status_code != 200:
                raise Exception("Failed to upload video")
            return response.json().get("link")  # URL of uploaded video

    def post_document(self, user_id, content, document_path):
        # Instagram does not support document uploads directly.
        raise NotImplementedError("Instagram does not allow document uploads directly.")
