import requests
import logging
from decafluence.oauth_helpers.linkedin_oauth_helper import LinkedInOAuthHelper
from decafluence.publisher_services.base_publisher import BasePublisherService
from decafluence.validators.content_validators import ContentValidationError, ContentValidator

class LinkedInPublisherService(BasePublisherService):
    def __init__(self, oauth_helper: LinkedInOAuthHelper):
        self.oauth_helper = oauth_helper
        self.api_url = 'https://api.linkedin.com/v2/'
        self.validator = ContentValidator(platform='linkedin')
        self.logger = logging.getLogger(__name__)

    def _get_auth_header(self, user_id):
        """Helper to get the authorization headers using access token."""
        try:
            tokens = self.oauth_helper.get_token(user_id)
            access_token = tokens.get('access_token')
            if not access_token:
                raise ValueError("Access token not found")
            self.logger.debug(f"Access token retrieved for user {user_id}")
            return {'Authorization': f'Bearer {access_token}'}
        except Exception as e:
            self.logger.error(f"Error getting auth header for user {user_id}: {e}")
            raise Exception(f"Error getting auth header for user {user_id}: {e}")

    def post_text(self, user_id, content):
        """Post a text message to LinkedIn."""
        try:
            access_token = self.oauth_helper.get_token(user_id).get('access_token')
            user_urn = self.oauth_helper.get_user_urn(access_token)  # Use the get_user_urn method
            self.logger.info(f"Attempting to post text for user {user_urn}")
            self.validator.validate_text(content)
            headers = { 
                        'X-Restli-Protocol-Version': '2.0.0',
                        'Content-Type': 'application/json',
                        'Authorization': f'Bearer {access_token}'
                    }

            # Post the text content
            # Prepare the request body
            post_data = {
                "author": f"urn:li:person:{user_urn}",  # Ensure the URN is correctly formatted
                "lifecycleState": "PUBLISHED",  # Set post to be immediately published
                "specificContent": {
                    "com.linkedin.ugc.ShareContent": {
                        "shareCommentary": {
                            "text": content  # Main post content
                        },
                        "shareMediaCategory": "NONE"  # No media attached
                    }
                },
                "visibility": {
                    "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"  # Visible to everyone
                }
            }
            post_response = requests.post(f"{self.api_url}ugcPosts", headers=headers, json=post_data)
            post_response.raise_for_status()
            self.logger.info(f"Text post successful for user {user_urn}")
            return post_response.json()

        except ContentValidationError as e:
            self.logger.error(f"Content validation failed for text post: {e}")
            raise e
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Request failed during text post for user {user_urn}: {e}")
            raise Exception(f"Failed to post text on LinkedIn: {e}")

    def post_image(self, user_id, content, image_path):
        """Post an image to LinkedIn."""
        try:
            access_token = self.oauth_helper.get_token(user_id).get('access_token')
            user_urn = self.oauth_helper.get_user_urn(access_token)  # Use the get_user_urn method
            self.logger.info(f"Attempting to post image for user {user_urn}")
            self.validator.validate_image(image_path)
            self.validator.validate_text(content)
            headers = {'Authorization': f'Bearer {access_token}'}

            # Register image for upload
            register_data = {
                "registerUploadRequest": {
                    "owner": f"urn:li:person:{user_urn}",
                    "recipes": ["urn:li:digitalmediaRecipe:feedshare-image"],
                    "serviceRelationships": [{"identifier": "urn:li:userGeneratedContent", "relationshipType": "OWNER"}]
                }
            }
            register_response = requests.post(f"{self.api_url}assets?action=registerUpload", headers=headers, json=register_data).json()
            upload_url = register_response['value']['uploadMechanism']['com.linkedin.digitalmedia.uploading.MediaUploadHttpRequest']['uploadUrl']
            asset = register_response['value']['asset']

            # Upload the image file
            with open(image_path, 'rb') as image_file:
                upload_response = requests.put(upload_url, headers={'Authorization': headers['Authorization'], 'Content-Type': 'image/jpeg'}, data=image_file)

            if upload_response.status_code != 201:
                self.logger.error(f"Image upload failed for user {user_urn}")
                return {"error": "Image upload failed"}

            # Publish the post with image
            post_data = {
                "author": f"urn:li:person:{user_urn}",
                "commentary": content,
                "visibility": {"com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"},
                "content": {
                    "contentEntities": [{"entityLocation": asset, "thumbnails": [{"resolvedUrl": asset}]}],
                    "shareMediaCategory": "IMAGE"
                },
                "lifecycleState": "PUBLISHED",
                "isReshareDisabledByAuthor": False
            }
            post_response = requests.post(f"{self.api_url}ugcPosts", headers=headers, json=post_data)
            post_response.raise_for_status()
            self.logger.info(f"Image post successful for user {user_urn}")
            return post_response.json()

        except ContentValidationError as e:
            self.logger.error(f"Content validation failed for image post: {e}")
            raise e
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Request failed during image post for user {user_urn}: {e}")
            raise Exception(f"Failed to post image on LinkedIn: {e}")

    def post_video(self, user_id, content, video_path):
        """Post a video to LinkedIn."""
        try:
            access_token = self.oauth_helper.get_token(user_id).get('access_token')
            user_urn = self.oauth_helper.get_user_urn(access_token)  # Use the get_user_urn method
            self.logger.info(f"Attempting to post video for user {user_urn}")
            self.validator.validate_video(video_path)
            self.validator.validate_text(content)
            headers = {'Authorization': f'Bearer {access_token}'}

            # Register video for upload
            register_data = {
                "registerUploadRequest": {
                    "owner": f"urn:li:person:{user_urn}",
                    "recipes": ["urn:li:digitalmediaRecipe:feedshare-video"],
                    "serviceRelationships": [{"identifier": "urn:li:userGeneratedContent", "relationshipType": "OWNER"}]
                }
            }
            register_response = requests.post(f"{self.api_url}assets?action=registerUpload", headers=headers, json=register_data).json()
            upload_url = register_response['value']['uploadMechanism']['com.linkedin.digitalmedia.uploading.MediaUploadHttpRequest']['uploadUrl']
            asset = register_response['value']['asset']

            # Upload the video file
            with open(video_path, 'rb') as video_file:
                upload_response = requests.put(upload_url, headers={'Authorization': headers['Authorization'], 'Content-Type': 'video/mp4'}, data=video_file)

            if upload_response.status_code != 201:
                self.logger.error(f"Video upload failed for user {user_urn}")
                return {"error": "Video upload failed"}

            # Publish the post with video
            post_data = {
                "author": f"urn:li:person:{user_urn}",
                "commentary": content,
                "visibility": {"com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"},
                "content": {
                    "contentEntities": [{"entityLocation": asset, "thumbnails": [{"resolvedUrl": asset}]}],
                    "shareMediaCategory": "VIDEO"
                },
                "lifecycleState": "PUBLISHED",
                "isReshareDisabledByAuthor": False
            }
            post_response = requests.post(f"{self.api_url}ugcPosts", headers=headers, json=post_data)
            post_response.raise_for_status()
            self.logger.info(f"Video post successful for user {user_urn}")
            return post_response.json()

        except ContentValidationError as e:
            self.logger.error(f"Content validation failed for video post: {e}")
            raise e
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Request failed during video post for user {user_urn}: {e}")
            raise Exception(f"Failed to post video on LinkedIn: {e}")

    def post_document(self, user_id, content, document_path):
        """Post a document to LinkedIn."""
        try:
            access_token = self.oauth_helper.get_token(user_id).get('access_token')
            user_urn = self.oauth_helper.get_user_urn(access_token)  # Use the get_user_urn method
            self.logger.info(f"Attempting to post document for user {user_urn}")
            self.validator.validate_document(document_path)
            self.validator.validate_text(content)
            headers = {'Authorization': f'Bearer {access_token}'}

            # Register document for upload
            register_data = {
                "registerUploadRequest": {
                    "owner": f"urn:li:person:{user_urn}",
                    "recipes": ["urn:li:digitalmediaRecipe:feedshare-document"],
                    "serviceRelationships": [{"identifier": "urn:li:userGeneratedContent", "relationshipType": "OWNER"}]
                }
            }
            register_response = requests.post(f"{self.api_url}assets?action=registerUpload", headers=headers, json=register_data).json
            upload_url = register_response['value']['uploadMechanism']['com.linkedin.digitalmedia.uploading.MediaUploadHttpRequest']['uploadUrl']
            asset = register_response['value']['asset']

            # Upload the document file
            with open(document_path, 'rb') as document_file:
                upload_response = requests.put(upload_url, headers={'Authorization': headers['Authorization'], 'Content-Type': 'application/pdf'}, data=document_file)

            if upload_response.status_code != 201:
                self.logger.error(f"Document upload failed for user {user_urn}")
                return {"error": "Document upload failed"}

            # Publish the post with document
            post_data = {
                "author": f"urn:li:person:{user_urn}",
                "commentary": content,
                "visibility": {"com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"},
                "content": {
                    "contentEntities": [{"entityLocation": asset, "thumbnails": [{"resolvedUrl": asset}]}],
                    "shareMediaCategory": "DOCUMENT"
                },
                "lifecycleState": "PUBLISHED",
                "isReshareDisabledByAuthor": False
            }
            post_response = requests.post(f"{self.api_url}ugcPosts", headers=headers, json=post_data)
            post_response.raise_for_status()
            self.logger.info(f"Document post successful for user {user_urn}")
            return post_response.json()

        except ContentValidationError as e:
            self.logger.error(f"Content validation failed for document post: {e}")
            raise e
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Request failed during document post for user {user_urn}: {e}")
            raise Exception(f"Failed to post document on LinkedIn: {e}")
