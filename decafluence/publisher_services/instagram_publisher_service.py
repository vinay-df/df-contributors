import os
import requests
from decafluence.oauth_helpers.instagram_oauth_helper import InstagramOAuthHelper
from decafluence.publisher_services.base_publisher import BasePublisherService
from decafluence.validators.content_validators import ContentValidationError, ContentValidator
from logger_config import setup_logger


class InstagramPublisherService(BasePublisherService):
    def __init__(self, oauth_helper: InstagramOAuthHelper):
        """
        Initializes the Instagram Publisher Service.
        """
        self.oauth_helper = oauth_helper
        self.api_url = 'https://graph.facebook.com/v12.0/'  # Instagram Graph API base URL
        self.validator = ContentValidator(platform='instagram')
        self.logger = setup_logger()

    def _get_access_token(self, user_id):
        """
        Retrieves the access token for a user.
        """
        try:
            self.logger.info("Refreshing access token...")
            token = self.oauth_helper.refresh_token(user_id)
            self.logger.info("Access token retrieved successfully.")
            return token
        except Exception as e:
            self.logger.error(f"Error refreshing access token: {e}")
            raise

    def post_text(self, user_id, content):
        """
        Instagram does not support posting plain text directly.
        """
        self.logger.warning("Attempt to post plain text. Not supported on Instagram.")
        raise NotImplementedError("Posting plain text directly is not supported on Instagram. Please use media.")

    def post_image(self, user_id, content, image_path):
        """
        Posts an image to Instagram with a caption.
        """
        try:
            self.logger.info("Validating image and caption...")
            self.validator.validate_image(image_path)
            self.validator.validate_text(content)

            access_token = self._get_access_token(user_id)

            self.logger.info("Uploading image...")
            image_upload_response = self._create_media_object(
                access_token, image_path, media_type="image", caption=content
            )

            self.logger.info("Publishing image...")
            media_id = image_upload_response.get("id")
            response = self._publish_media(access_token, media_id)

            self.logger.info("Image post successful.")
            return response
        except ContentValidationError as e:
            self.logger.error(f"Content validation failed: {e}")
            raise
        except FileNotFoundError as e:
            self.logger.error(f"Image file not found: {image_path}")
            raise
        except requests.HTTPError as e:
            self.logger.error(f"Failed to post image on Instagram: {e}")
            raise

    def post_video(self, user_id, content, video_path):
        """
        Posts a video to Instagram with a caption.
        """
        try:
            self.logger.info("Validating video and caption...")
            self.validator.validate_video(video_path)
            self.validator.validate_text(content)

            access_token = self._get_access_token(user_id)

            self.logger.info("Uploading video...")
            video_upload_response = self._create_media_object(
                access_token, video_path, media_type="video", caption=content
            )

            self.logger.info("Publishing video...")
            media_id = video_upload_response.get("id")
            response = self._publish_media(access_token, media_id)

            self.logger.info("Video post successful.")
            return response
        except ContentValidationError as e:
            self.logger.error(f"Content validation failed: {e}")
            raise
        except FileNotFoundError as e:
            self.logger.error(f"Video file not found: {video_path}")
            raise
        except requests.HTTPError as e:
            self.logger.error(f"Failed to post video on Instagram: {e}")
            raise

    def _create_media_object(self, access_token, file_path, media_type, caption):
        """
        Creates a media object for an image or video.
        """
        try:
            self.logger.info("Creating media object...")
            endpoint = "me/media"
            data = {"access_token": access_token, "caption": caption}

            if not os.path.exists(file_path):
                raise FileNotFoundError(f"Media file not found: {file_path}")

            with open(file_path, "rb") as file:
                files = {"file": file}
                response = requests.post(f"{self.api_url}{endpoint}", data=data, files=files)
                response.raise_for_status()

            self.logger.info("Media object created successfully.")
            return response.json()
        except FileNotFoundError as e:
            self.logger.error(f"File error: {e}")
            raise
        except requests.HTTPError as e:
            self.logger.error(f"HTTP error while creating media object: {e}")
            raise

    def _publish_media(self, access_token, media_id):
        """
        Publishes a media object to Instagram.
        """
        try:
            self.logger.info(f"Publishing media ID: {media_id}...")
            endpoint = "me/media_publish"
            data = {"creation_id": media_id, "access_token": access_token}

            response = requests.post(f"{self.api_url}{endpoint}", data=data)
            response.raise_for_status()

            self.logger.info("Media published successfully.")
            return response.json()
        except requests.HTTPError as e:
            self.logger.error(f"HTTP error while publishing media: {e}")
            raise

    def post_document(self, user_id, content, document_path):
        """
        Instagram does not support posting documents.
        """
        self.logger.warning("Attempt to post a document. Not supported on Instagram.")
        raise NotImplementedError("Instagram does not allow document uploads directly.")
