import requests
from decafluence.oauth_helpers.instagram_oauth_helper import InstagramOAuthHelper
from decafluence.publisher_services.base_publisher import BasePublisherService
from decafluence.validators.content_validators import ContentValidationError, ContentValidator


class InstagramPublisherService(BasePublisherService):
    def __init__(self, oauth_helper: InstagramOAuthHelper):
        """
        Initializes the Instagram Publisher Service.

        Args:
            oauth_helper (InstagramOAuthHelper): Helper for handling OAuth functionality.
        """
        self.oauth_helper = oauth_helper
        self.api_url = 'https://graph.facebook.com/v12.0/'  # Instagram Graph API base URL
        self.validator = ContentValidator(platform='instagram')

    def _get_access_token(self, user_id):
        """
        Retrieves the access token for a user.

        Args:
            user_id (str): User ID to fetch the token for.

        Returns:
            str: The access token.
        """
        return self.oauth_helper.refresh_token(user_id)

    def post_text(self, user_id, content):
        """
        Instagram does not support posting plain text directly.

        Raises:
            NotImplementedError: Posting plain text is not supported.
        """
        raise NotImplementedError("Posting plain text directly is not supported on Instagram. Please use media.")

    def post_image(self, user_id, content, image_path):
        """
        Posts an image to Instagram with a caption.

        Args:
            user_id (str): The user ID posting the image.
            content (str): The caption text.
            image_path (str): Path to the image file.

        Returns:
            dict: Response from the Instagram API.
        """
        try:
            self.validator.validate_image(image_path)
            self.validator.validate_text(content)

            access_token = self._get_access_token(user_id)

            # Step 1: Upload the image
            image_upload_response = self._create_media_object(
                access_token, image_path, media_type="image", caption=content
            )

            # Step 2: Publish the media
            media_id = image_upload_response.get("id")
            return self._publish_media(access_token, media_id)

        except ContentValidationError as e:
            raise e
        except requests.HTTPError as e:
            raise Exception(f"Failed to post image on Instagram: {str(e)}")

    def post_video(self, user_id, content, video_path):
        """
        Posts a video to Instagram with a caption.

        Args:
            user_id (str): The user ID posting the video.
            content (str): The caption text.
            video_path (str): Path to the video file.

        Returns:
            dict: Response from the Instagram API.
        """
        try:
            self.validator.validate_video(video_path)
            self.validator.validate_text(content)

            access_token = self._get_access_token(user_id)

            # Step 1: Upload the video
            video_upload_response = self._create_media_object(
                access_token, video_path, media_type="video", caption=content
            )

            # Step 2: Publish the media
            media_id = video_upload_response.get("id")
            return self._publish_media(access_token, media_id)

        except ContentValidationError as e:
            raise e
        except requests.HTTPError as e:
            raise Exception(f"Failed to post video on Instagram: {str(e)}")

    def _create_media_object(self, access_token, file_path, media_type, caption):
        """
        Creates a media object for an image or video.

        Args:
            access_token (str): The access token for API calls.
            file_path (str): Path to the media file.
            media_type (str): Type of media, either 'image' or 'video'.
            caption (str): The caption text.

        Returns:
            dict: Response from the Instagram API.
        """
        endpoint = "me/media"
        data = {"access_token": access_token, "caption": caption}

        if media_type == "image":
            files = {"file": open(file_path, "rb")}
        elif media_type == "video":
            files = {"file": open(file_path, "rb")}
        else:
            raise ValueError("Invalid media type. Must be 'image' or 'video'.")

        response = requests.post(f"{self.api_url}{endpoint}", data=data, files=files)
        response.raise_for_status()
        return response.json()

    def _publish_media(self, access_token, media_id):
        """
        Publishes a media object to Instagram.

        Args:
            access_token (str): The access token for API calls.
            media_id (str): The ID of the media object.

        Returns:
            dict: Response from the Instagram API.
        """
        endpoint = "me/media_publish"
        data = {"creation_id": media_id, "access_token": access_token}

        response = requests.post(f"{self.api_url}{endpoint}", data=data)
        response.raise_for_status()
        return response.json()

    def post_document(self, user_id, content, document_path):
        """
        Instagram does not support posting documents.

        Raises:
            NotImplementedError: Posting documents is not supported on Instagram.
        """
        raise NotImplementedError("Instagram does not allow document uploads directly.")
