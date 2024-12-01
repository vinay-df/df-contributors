import os
import requests
from decafluence.oauth_helpers.facebook_oauth_helper import FacebookOAuthHelper
from decafluence.publisher_services.base_publisher import BasePublisherService
from decafluence.validators.content_validators import ContentValidationError, ContentValidator
from logger_config import setup_logger  # Assuming your logger setup is in logger_config


class FacebookPublisherService(BasePublisherService):
    def __init__(self, oauth_helper: FacebookOAuthHelper):
        super().__init__()
        self.oauth_helper = oauth_helper
        self.api_url = "https://graph.facebook.com/v11.0/"
        self.validator = ContentValidator(platform="facebook")
        self.logger = setup_logger()

    def _get_auth_header(self, user_id):
        """
        Constructs the Authorization header using the refreshed token.
        """
        access_token = self.oauth_helper.refresh_token(user_id)
        return {"Authorization": f"Bearer {access_token}"}

    def post_text(self, user_id, content):
        """
        Posts a text-only update to the user's Facebook feed.
        """
        try:
            self.logger.info("Validating text content...")
            self.validator.validate_text(content)

            self.logger.info("Fetching refreshed access token...")
            access_token = self.oauth_helper.refresh_token(user_id)

            data = {
                "message": content,
                "access_token": access_token,
            }

            self.logger.info("Sending text post request to Facebook...")
            response = requests.post(f"{self.api_url}me/feed", data=data)
            response.raise_for_status()

            self.logger.info("Text post successful.")
            return response.json()
        except ContentValidationError as e:
            self.logger.error(f"Content validation failed: {e}")
            raise
        except requests.HTTPError as e:
            self.logger.error(f"Failed to post text on Facebook: {str(e)}")
            raise

    def post_image(self, user_id, content, image_path):
        """
        Posts an image with a caption to the user's Facebook feed.
        """
        try:
            self.logger.info("Validating image and text content...")
            self.validator.validate_image(image_path)
            self.validator.validate_text(content)

            self.logger.info("Fetching refreshed access token...")
            access_token = self.oauth_helper.refresh_token(user_id)

            data = {
                "message": content,
                "access_token": access_token,
            }

            self.logger.info("Sending image post request to Facebook...")
            with open(image_path, "rb") as image_file:
                files = {"file": image_file}
                response = requests.post(f"{self.api_url}me/photos", data=data, files=files)
                response.raise_for_status()

            self.logger.info("Image post successful.")
            return response.json()
        except ContentValidationError as e:
            self.logger.error(f"Content validation failed: {e}")
            raise
        except FileNotFoundError:
            self.logger.error(f"Image file not found: {image_path}")
            raise
        except requests.HTTPError as e:
            self.logger.error(f"Failed to post image on Facebook: {str(e)}")
            raise

    def post_video(self, user_id, content, video_path):
        """
        Posts a video with a description to the user's Facebook feed.
        """
        try:
            self.logger.info("Validating video and text content...")
            self.validator.validate_video(video_path)
            self.validator.validate_text(content)

            self.logger.info("Fetching refreshed access token...")
            access_token = self.oauth_helper.refresh_token(user_id)

            data = {
                "description": content,
                "access_token": access_token,
            }

            self.logger.info("Sending video post request to Facebook...")
            with open(video_path, "rb") as video_file:
                files = {"file": video_file}
                response = requests.post(f"{self.api_url}me/videos", data=data, files=files)
                response.raise_for_status()

            self.logger.info("Video post successful.")
            return response.json()
        except ContentValidationError as e:
            self.logger.error(f"Content validation failed: {e}")
            raise
        except FileNotFoundError:
            self.logger.error(f"Video file not found: {video_path}")
            raise
        except requests.HTTPError as e:
            self.logger.error(f"Failed to post video on Facebook: {str(e)}")
            raise

    def post_link(self, user_id, content, link_url):
        """
        Posts a link with a description to the user's Facebook feed.
        """
        try:
            self.logger.info("Validating link and text content...")
            self.validator.validate_url(link_url)
            self.validator.validate_text(content)

            self.logger.info("Fetching refreshed access token...")
            access_token = self.oauth_helper.refresh_token(user_id)

            data = {
                "message": content,
                "link": link_url,
                "access_token": access_token,
            }

            self.logger.info("Sending link post request to Facebook...")
            response = requests.post(f"{self.api_url}me/feed", data=data)
            response.raise_for_status()

            self.logger.info("Link post successful.")
            return response.json()
        except ContentValidationError as e:
            self.logger.error(f"Content validation failed: {e}")
            raise
        except requests.HTTPError as e:
            self.logger.error(f"Failed to post link on Facebook: {str(e)}")
            raise
