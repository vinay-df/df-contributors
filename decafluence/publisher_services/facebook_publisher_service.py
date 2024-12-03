import os
import requests
from decafluence.oauth_helpers.facebook_oauth_helper import FacebookOAuthHelper
from decafluence.publisher_services.base_publisher import BasePublisherService
from decafluence.validators.content_validators import ContentValidationError, ContentValidator
from logger_config import setup_logger

class FacebookPublisherService(BasePublisherService):
    def __init__(self, oauth_helper: FacebookOAuthHelper):
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

    def select_page(self, user_id):
        """
        Prompts the user to select a page to post to if multiple pages exist.
        If only one page is available, it posts automatically.
        """
        try:
            # Fetch user's pages
            pages = self.oauth_helper.fetch_user_pages(self.oauth_helper.refresh_token(user_id))
            
            if not pages:
                raise Exception("User does not manage any pages.")
            
            if len(pages) == 1:
                selected_page = pages[0]
                self.logger.info(f"Only one page available, posting to: {selected_page['name']}")
            else:
                self.logger.info("Multiple pages found. Please select a page to post to:")
                for index, page in enumerate(pages):
                    self.logger.info(f"{index + 1}. {page['name']}")
                
                # Let the user choose a page
                selected_page_index = int(input(f"Select a page (1-{len(pages)}): ")) - 1
                if selected_page_index < 0 or selected_page_index >= len(pages):
                    raise ValueError("Invalid page selection.")
                
                selected_page = pages[selected_page_index]

            # Fetch the page access token for the selected page
            page_access_token = self.get_page_access_token(selected_page['id'], user_id)
            selected_page['access_token'] = page_access_token
            
            return selected_page
        except Exception as e:
            self.logger.error(f"Error selecting page: {e}")
            raise

    def get_page_access_token(self, page_id, user_id):
        """
        Fetches the page access token for a specific page.
        """
        try:
            user_access_token = self.oauth_helper.refresh_token(user_id)
            url = f"https://graph.facebook.com/v11.0/{page_id}?fields=access_token&access_token={user_access_token}"
            response = requests.get(url)
            response.raise_for_status()
            page_data = response.json()

            # Extract the page access token
            page_access_token = page_data.get("access_token")
            if not page_access_token:
                raise Exception(f"Unable to fetch page access token for page {page_id}.")
            
            self.logger.info(f"Page access token fetched for page {page_id}.")
            return page_access_token
        except requests.HTTPError as e:
            self.logger.error(f"Failed to fetch page access token: {str(e)}")
            raise
        except Exception as e:
            self.logger.error(f"Error fetching page access token: {str(e)}")
            raise

    def post_text(self, user_id, content):
        """
        Posts a text-only update to the selected Facebook page.
        """
        try:
            self.logger.info("Validating text content...")
            self.validator.validate_text(content)

            # Select the page to post to
            selected_page = self.select_page(user_id)

            data = {
                "message": content,
                "access_token": selected_page['access_token'],  # Use page access token
            }

            self.logger.info(f"Sending text post request to page: {selected_page['name']}...")
            response = requests.post(f"{self.api_url}{selected_page['id']}/feed", data=data)
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
        Posts an image with a caption to the selected Facebook page.
        """
        try:
            self.logger.info("Validating image and text content...")
            self.validator.validate_image(image_path)
            self.validator.validate_text(content)

            # Select the page to post to
            selected_page = self.select_page(user_id)

            data = {
                "message": content,
                "access_token": selected_page['access_token'],  # Use page access token
            }

            self.logger.info(f"Sending image post request to page: {selected_page['name']}...")
            with open(image_path, "rb") as image_file:
                files = {"file": image_file}
                response = requests.post(f"{self.api_url}{selected_page['id']}/photos", data=data, files=files)
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
        Posts a video with a description to the selected Facebook page.
        """
        try:
            self.logger.info("Validating video and text content...")
            self.validator.validate_video(video_path)
            self.validator.validate_text(content)

            # Select the page to post to
            selected_page = self.select_page(user_id)

            data = {
                "description": content,
                "access_token": selected_page['access_token'],  # Use page access token
            }

            self.logger.info(f"Sending video post request to page: {selected_page['name']}...")
            with open(video_path, "rb") as video_file:
                files = {"file": video_file}
                response = requests.post(f"{self.api_url}{selected_page['id']}/videos", data=data, files=files)
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
        Posts a link with a description to the selected Facebook page.
        """
        try:
            self.logger.info("Validating link and text content...")
            # self.validator.validate_url(link_url)
            self.validator.validate_text(content)

            # Select the page to post to
            selected_page = self.select_page(user_id)

            data = {
                "message": content,
                "link": link_url,
                "access_token": selected_page['access_token'],  # Use page access token
            }

            self.logger.info(f"Sending link post request to page: {selected_page['name']}...")
            response = requests.post(f"{self.api_url}{selected_page['id']}/feed", data=data)
            response.raise_for_status()

            self.logger.info("Link post successful.")
            return response.json()
        except ContentValidationError as e:
            self.logger.error(f"Content validation failed: {e}")
            raise
        except requests.HTTPError as e:
            self.logger.error(f"Failed to post link on Facebook: {str(e)}")
            raise

    def post_document(self, user_id, content, document_path):
        """
        Posts a document (as a file) to the selected Facebook page.
        Upload it as an image for the time being, as Facebook doesn't support documents directly.
        """
        try:
            # Check if file exists
            if not os.path.exists(document_path):
                raise FileNotFoundError(f"Document file not found: {document_path}")

            # Get the access token
            access_token = self.oauth_helper.refresh_token(user_id)

            # Select the page to post to
            selected_page = self.select_page(user_id)

            data = {
                "message": content,
                "access_token": access_token,
            }

            # Log the document upload
            self.logger.info(f"Uploading document as image to page: {selected_page['name']}...")

            # Open the document and send it as a file
            with open(document_path, "rb") as doc_file:
                files = {"file": doc_file}
                response = requests.post(f"{self.api_url}{selected_page['id']}/photos", data=data, files=files)
                response.raise_for_status()

            # Log successful post
            self.logger.info("Document post successful.")
            return response.json()

        except FileNotFoundError as e:
            self.logger.error(f"File error: {e}")
            raise
        except requests.HTTPError as e:
            self.logger.error(f"Failed to post document: {str(e)}")
            raise
