import os
import requests
from decafluence.oauth_helpers.instagram_oauth_helper import InstagramOAuthHelper
from decafluence.publisher_services.base_publisher import BasePublisherService
from decafluence.validators.content_validators import ContentValidator
from google.cloud import storage
from firebase_config import initialize_firebase  # Import Firebase initialization function
from logger_config import setup_logger
import time

class InstagramPublisherService(BasePublisherService):
    def __init__(self, oauth_helper: InstagramOAuthHelper):
        """
        Initializes the Instagram Publisher Service with Firebase and GCP Storage setup.
        """
        self.oauth_helper = oauth_helper
        self.api_url = 'https://graph.instagram.com/v20.0'  # Instagram Graph API base URL
        self.validator = ContentValidator(platform='instagram')
        self.logger = setup_logger()

        # Initialize Firebase (Firestore) and GCP storage
        self.firestore_client = initialize_firebase()  # Initialize Firestore client from Firebase config
        self.client = storage.Client()  # Initialize GCP Storage client
        self.bucket = self.client.get_bucket(os.getenv('GCP_BUCKET_NAME'))  # Replace with your GCP bucket name
        if not self.bucket:
            raise ValueError("Failed to initialize GCP bucket.")

    def post_image(self, system_user_id, content, image_file):
        """
        Posts an image to Instagram with a caption.
        """
        if not image_file:
            raise ValueError("Parameter 'image_file' is required for posting an image.")
        return self._post_media(system_user_id, content, media_file=image_file, media_type="IMAGE")

    def post_video(self, system_user_id, content, video_file):
        """
        Posts a video to Instagram with a caption.
        """
        if not video_file:
            raise ValueError("Parameter 'video_file' is required for posting a video.")
        return self._post_media(system_user_id, content, media_file=video_file, media_type="VIDEO")

    def post_reels(self, system_user_id, content, video_file):
        """
        Posts a reel to Instagram with a caption.
        """
        if not video_file:
            raise ValueError("Parameter 'video_file' is required for posting a reel.")
        return self._post_media(system_user_id, content, media_file=video_file, media_type="REELS")

    def post_carousel(self, system_user_id, content, media_files):
        """
        Posts a carousel to Instagram with a caption.
        """
        if not media_files or len(media_files) < 2:
            raise ValueError("Parameter 'media_files' is required for posting a carousel and must contain at least 2 items.")

        try:
            self.logger.info("Fetching access token and Instagram user ID...")
            access_token, instagram_user_id = self._get_access_token_and_user_id(system_user_id)

            self.logger.info("Uploading media to GCP Storage...")
            media_urls = [self._upload_to_gcp(file) for file in media_files]

            self.logger.info("Creating media containers for carousel items...")
            container_ids = []
            for media_url in media_urls:
                container_id = self._create_carousel_item_container(access_token, instagram_user_id, media_url)
                container_ids.append(container_id)

            self.logger.info("Creating carousel container...")
            carousel_container_id = self._create_carousel_container(
                access_token, instagram_user_id, container_ids, caption=content
            )

            self.logger.info("Publishing carousel...")
            response = self._publish_media(access_token, carousel_container_id, instagram_user_id)

            # Cleanup: Delete media from GCP storage
            self.logger.info("Deleting uploaded media from GCP storage...")
            media_urls = list(set(media_urls))
            for url in media_urls:
                self._delete_from_gcp(url)

            self.logger.info("Carousel post successful.")
            return response
        except Exception as e:
            self.logger.error(f"Error posting carousel: {e}")
            raise

    def _create_carousel_item_container(self, access_token, user_id, media_url):
        """
        Creates an Instagram media container for a carousel item.
        """
        try:
            url = f"{self.api_url}/{user_id}/media"
            payload = {
                "is_carousel_item": "true",
                "image_url": media_url,
                "access_token": access_token
            }
            response = requests.post(url, params=payload)
            response.raise_for_status()
            container_id = response.json().get("id")
            if not container_id:
                raise Exception("Failed to create carousel item container.")
            return container_id
        except requests.HTTPError as e:
            self.logger.error(f"HTTP error while creating carousel item container: {e.response.text}")
            raise
        except Exception as e:
            self.logger.error(f"Error creating carousel item container: {e}")
            raise


    def _create_carousel_container(self, access_token, user_id, container_ids, caption):
        """
        Creates a carousel container with multiple media containers.
        """
        try:
            url = f"{self.api_url}/{user_id}/media"
            payload = {
                "media_type": "CAROUSEL",
                "children": ",".join(container_ids),
                "caption": caption,
                "access_token": access_token
            }
            response = requests.post(url, params=payload)
            response.raise_for_status()
            container_id = response.json().get("id")
            if not container_id:
                raise Exception("Failed to create carousel container.")
            return container_id
        except requests.HTTPError as e:
            self.logger.error(f"HTTP error while creating carousel container: {e.response.text}")
            raise
        except Exception as e:
            self.logger.error(f"Error creating carousel container: {e}")
            raise


    def _post_media(self, system_user_id, content, media_file=None, media_files=None, media_type=None):
        """
        General method to post media to Instagram.
        """
        try:
            self.logger.info(f"Validating content for {media_type}...")
            self.validator.validate_text(content)

            self.logger.info("Fetching access token and Instagram user ID...")
            access_token, instagram_user_id = self._get_access_token_and_user_id(system_user_id)

            self.logger.info("Uploading media to GCP Storage...")
            if media_files:
                media_urls = [self._upload_to_gcp(file) for file in media_files]
            else:
                media_urls = [self._upload_to_gcp(media_file)]

            self.logger.info(f"Creating {media_type} media container...")
            media_response = self._create_media_container(
                access_token, media_urls, caption=content, user_id=instagram_user_id, media_type=media_type
            )

            media_id = media_response.get("id")
            if not media_id:
                self.logger.error(f"Failed to create {media_type} media container.")
                raise Exception("Media container creation failed.")

            self.logger.info(f"Publishing {media_type}...")
            response = self._publish_media(access_token, media_id, instagram_user_id)
            self.logger.info(f"{media_type} post successful.")

            # Cleanup: Delete media from GCP storage
            self.logger.info("Deleting uploaded media from GCP storage...")
            for url in media_urls:
                self._delete_from_gcp(url)

            return response
        except Exception as e:
            self.logger.error(f"Unexpected error: {e}")
            raise

    def _get_access_token_and_user_id(self, system_user_id):
        """
        Retrieves the access token and Instagram user ID from Firestore.
        """
        try:
            self.logger.info("Fetching access token and Instagram user ID from Firestore...")
            user_ref = self.firestore_client.collection('user_tokens').document(system_user_id)
            user_data = user_ref.get().to_dict()

            if user_data and 'token_data' in user_data:
                access_token = user_data['token_data'].get('access_token')
                instagram_user_id = user_data['user_info'].get('id')

                if not access_token or not instagram_user_id:
                    raise ValueError("Access token or Instagram user ID not found in the stored data.")

                self.logger.info("Access token and Instagram user ID retrieved successfully.")
                return access_token, instagram_user_id
            else:
                raise ValueError(f"No token data found for user ID {system_user_id}")
        except Exception as e:
            self.logger.error(f"Error fetching access token or Instagram user ID: {e}")
            raise

    def _upload_to_gcp(self, media_file):
        """
        Upload media to GCP Storage and return the public URL.
        Handles local files.
        """
        try:
            # Check if media_file is a local file path (not a URL)
            if isinstance(media_file, str):  # Check if it's a file path
                # Open the file for reading in binary mode
                with open(media_file, 'rb') as file:
                    file_name = os.path.basename(media_file)  # Get the file name from the path
                    blob = self.bucket.blob(f"instagram-media/{file_name}")
                    blob.upload_from_file(file)
                    blob.make_public()
                    self.logger.info(f"Uploaded {file_name} to GCP Storage.")
                    return blob.public_url
            else:
                raise ValueError("Invalid media file. Expected a file path (string).")

        except Exception as e:
            self.logger.error(f"Error uploading media to GCP: {e}")
            raise

    def _delete_from_gcp(self, media_url):
        """
        Delete media from GCP Storage.
        """
        try:
            media_name = media_url.split("/")[-1]
            blob = self.bucket.blob(f"instagram-media/{media_name}")
            blob.delete()

            self.logger.info(f"Deleted {media_name} from GCP Storage.")
        except Exception as e:
            self.logger.error(f"Error deleting media from GCP: {e}")
            raise

    def _create_media_container(self, access_token, media_urls, caption, user_id, media_type):
        """
        Creates a media container for Instagram posts, including images, videos, reels, and carousels.
        """
        try:
            self.logger.info(f"Creating media container for user {user_id}...")

            url = f"{self.api_url}/{user_id}/media"

            # Prepare media container payload
            if media_type == "CAROUSEL":
                media_payload = {
                    "media_type": "CAROUSEL",
                    "children": ','.join(media_urls),
                    "caption": caption,
                    "access_token": access_token
                }
            elif media_type == "IMAGE":
                media_payload = {
                    "media_type": "IMAGE",
                    "image_url": media_urls[0],
                    "caption": caption,
                    "access_token": access_token
                }
            elif media_type == "VIDEO" or media_type == "REELS":
                media_payload = {
                    "media_type": "REELS",
                    "video_url": media_urls[0],
                    "caption": caption,
                    "access_token": access_token
                }
            else:
                raise ValueError("Unsupported media type. Use 'IMAGE', 'VIDEO', 'REELS', or 'CAROUSEL'.")

            response = requests.post(url, params=media_payload)
            response.raise_for_status()

            self.logger.info(f"{media_type} media container created successfully.")
            return response.json()
        except requests.HTTPError as e:
            self.logger.error(f"HTTP error while creating {media_type} container: {e.response.text}")
            raise
        except Exception as e:
            self.logger.error(f"Error creating {media_type} container: {e}")
            raise

    def _publish_media(self, access_token, media_id, user_id):
        """
        Publishes media on Instagram using the media_publish endpoint, with a polling mechanism
        to ensure the media container is ready.
        """
        try:
            self.logger.info(f"Publishing media ID {media_id} for user {user_id}...")
            url = f"{self.api_url}/{user_id}/media_publish"

            # Polling configuration
            max_retries = 10  # Number of retries
            delay = 5  # Delay between retries in seconds

            for attempt in range(max_retries):
                self.logger.info(f"Checking readiness of media ID {media_id} (Attempt {attempt + 1}/{max_retries})...")
                
                # Check the media container status
                status_response = self._check_media_status(access_token, media_id)
                if status_response.get("status") == "READY" or status_response.get("status") == "FINISHED":
                    self.logger.info("Media container is ready. Proceeding to publish.")
                    break
                else:
                    self.logger.warning(f"Media container is not ready. Waiting {delay} seconds...")
                    time.sleep(delay)
            else:
                raise TimeoutError("Media container did not become ready within the maximum retry limit.")

            # Publish the media
            params = {
                "creation_id": media_id,
                "access_token": access_token
            }
            response = requests.post(url, params=params)
            response.raise_for_status()

            self.logger.info("Media published successfully.")
            return response.json()

        except requests.HTTPError as e:
            self.logger.error(f"HTTP error while publishing media: {e.response.text}")
            raise
        except Exception as e:
            self.logger.error(f"Error publishing media: {e}")
            raise

    def _check_media_status(self, access_token, media_id):
        """
        Checks the status of the media container.
        """
        try:
            url = f"{self.api_url}/{media_id}"
            params = {"access_token": access_token}

            response = requests.get(url, params=params)
            response.raise_for_status()

            return response.json()
        except requests.HTTPError as e:
            self.logger.error(f"HTTP error while checking media status: {e.response.text}")
            raise
        except Exception as e:
            self.logger.error(f"Error checking media status: {e}")
            raise

    # Unsupported methods for Instagram
    def post_document(self, *args, **kwargs):
        raise NotImplementedError("Instagram does not support posting documents.")

    def post_text(self, *args, **kwargs):
        raise NotImplementedError("Instagram does not support posting text as a separate operation.")
