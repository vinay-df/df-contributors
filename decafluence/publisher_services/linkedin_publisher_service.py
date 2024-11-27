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
            user_urn = self.oauth_helper.get_user_urn(access_token)
            self.logger.info(f"Attempting to post text for user {user_urn}")
            self.validator.validate_text(content)
            headers = { 
                'X-Restli-Protocol-Version': '2.0.0',
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {access_token}'
            }

            post_data = {
                "author": f"urn:li:person:{user_urn}",
                "lifecycleState": "PUBLISHED",
                "specificContent": {
                    "com.linkedin.ugc.ShareContent": {
                        "shareCommentary": {"text": content},
                        "shareMediaCategory": "NONE"
                    }
                },
                "visibility": {"com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"}
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
            user_urn = self.oauth_helper.get_user_urn(access_token)
            self.logger.info(f"Attempting to post image for user {user_urn}")
            self.validator.validate_image(image_path)
            self.validator.validate_text(content)
            headers = {'Authorization': f'Bearer {access_token}'}

            # Step 1: Register image for upload
            register_data = {
                "registerUploadRequest": {
                    "owner": f"urn:li:person:{user_urn}",
                    "recipes": ["urn:li:digitalmediaRecipe:feedshare-image"],
                    "serviceRelationships": [
                        {"identifier": "urn:li:userGeneratedContent", "relationshipType": "OWNER"}
                    ]
                }
            }
            register_response = requests.post(f"{self.api_url}assets?action=registerUpload", headers=headers, json=register_data)
            register_response.raise_for_status()
            register_json = register_response.json()
            upload_url = register_json['value']['uploadMechanism']['com.linkedin.digitalmedia.uploading.MediaUploadHttpRequest']['uploadUrl']
            asset = register_json['value']['asset']

            # Step 2: Upload the image file
            with open(image_path, 'rb') as image_file:
                upload_headers = {
                    'Authorization': f'Bearer {access_token}',
                    'Content-Type': 'image/jpeg'
                }
                upload_response = requests.put(upload_url, headers=upload_headers, data=image_file)
                upload_response.raise_for_status()

            self.logger.info(f"Image uploaded successfully for user {user_urn}")

            # Step 3: Publish the post with image
            post_data = {
                "author": f"urn:li:person:{user_urn}",
                "lifecycleState": "PUBLISHED",
                "specificContent": {
                    "com.linkedin.ugc.ShareContent": {
                        "shareCommentary": {"text": content},
                        "shareMediaCategory": "IMAGE",
                        "media": [
                            {"status": "READY", "description": {"text": content}, "media": asset}
                        ]
                    }
                },
                "visibility": {"com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"}
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
            # Step 1: Retrieve Access Token and User URN
            access_token = self.oauth_helper.get_token(user_id).get('access_token')
            if not access_token:
                raise ValueError("Access token not found")
            user_urn = self.oauth_helper.get_user_urn(access_token)  # Use the get_user_urn method
            self.logger.info(f"Attempting to post video for user {user_urn}")

            # Step 2: Validate Input
            self.validator.validate_video(video_path)
            self.validator.validate_text(content)
            headers = {'Authorization': f'Bearer {access_token}', 'Content-Type': 'application/json'}

            # Step 3: Register Video for Upload
            register_data = {
                "registerUploadRequest": {
                    "owner": f"urn:li:person:{user_urn}",
                    "recipes": ["urn:li:digitalmediaRecipe:feedshare-video"],
                    "serviceRelationships": [
                        {"identifier": "urn:li:userGeneratedContent", "relationshipType": "OWNER"}
                    ]
                }
            }
            register_response = requests.post(
                f"{self.api_url}assets?action=registerUpload", headers=headers, json=register_data
            )
            register_response.raise_for_status()
            register_result = register_response.json()

            # Extract Upload URL and Asset ID
            upload_url = register_result['value']['uploadMechanism']['com.linkedin.digitalmedia.uploading.MediaUploadHttpRequest']['uploadUrl']
            asset = register_result['value']['asset']
            self.logger.debug(f"Video registered for upload. Asset: {asset}, Upload URL: {upload_url}")

            # Step 4: Upload the Video
            with open(video_path, 'rb') as video_file:
                upload_headers = {'Authorization': headers['Authorization'], 'Content-Type': 'video/mp4'}
                upload_response = requests.put(upload_url, headers=upload_headers, data=video_file)
                upload_response.raise_for_status()

            if upload_response.status_code != 201:
                self.logger.error(f"Video upload failed with status {upload_response.status_code}")
                raise Exception("Video upload failed")

            self.logger.info(f"Video upload successful for asset: {asset}")

            # Step 5: Publish the Post with Video
            post_data = {
                "author": f"urn:li:person:{user_urn}",
                "lifecycleState": "PUBLISHED",
                "specificContent": {
                    "com.linkedin.ugc.ShareContent": {
                        "shareCommentary": {"text": content},
                        "shareMediaCategory": "VIDEO",
                        "media": [
                            {
                                "status": "READY",
                                "description": {"text": content},
                                "media": asset,
                                "title": {"text": "Uploaded Video"}
                            }
                        ]
                    }
                },
                "visibility": {"com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"}
            }
            post_response = requests.post(
                f"{self.api_url}ugcPosts", headers=headers, json=post_data
            )
            post_response.raise_for_status()
            self.logger.info(f"Video post published successfully for user {user_urn}")
            return post_response.json()

        except ContentValidationError as e:
            self.logger.error(f"Content validation failed for video post: {e}")
            raise e
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Request failed during video post for user {user_urn}: {e}")
            raise Exception(f"Failed to post video on LinkedIn: {e}")
        except Exception as e:
            self.logger.error(f"Unexpected error during video post: {e}")
            raise

    def post_document(self, user_id, content, document_path):
        """Post a document to LinkedIn."""
        try:
            # Step 1: Retrieve Access Token and User URN
            access_token = self.oauth_helper.get_token(user_id).get('access_token')
            if not access_token:
                raise ValueError("Access token not found")
            user_urn = self.oauth_helper.get_user_urn(access_token)
            self.logger.info(f"Attempting to post document for user {user_urn}")

            # Step 2: Validate Inputs
            self.validator.validate_document(document_path)
            self.validator.validate_text(content)

            headers = {'Authorization': f'Bearer {access_token}', 'Content-Type': 'application/json'}

            # Step 3: Register the Document for Upload
            register_data = {
                "registerUploadRequest": {
                    "owner": f"urn:li:person:{user_urn}",
                    "recipes": ["urn:li:digitalmediaRecipe:feedshare-document"],
                    "serviceRelationships": [
                        {"identifier": "urn:li:userGeneratedContent", "relationshipType": "OWNER"}
                    ]
                }
            }
            register_response = requests.post(
                f"{self.api_url}assets?action=registerUpload",
                headers=headers,
                json=register_data
            )
            register_response.raise_for_status()
            register_result = register_response.json()

            # Extract Upload URL and Asset ID
            upload_url = register_result['value']['uploadMechanism']['com.linkedin.digitalmedia.uploading.MediaUploadHttpRequest']['uploadUrl']
            asset = register_result['value']['asset']

            self.logger.info(f"Document registered successfully. Asset: {asset}, Upload URL: {upload_url}")

            # Step 4: Upload the Document
            with open(document_path, 'rb') as document_file:
                upload_headers = {
                    'Authorization': headers['Authorization'],
                    'Content-Type': 'application/pdf'
                }
                upload_response = requests.put(upload_url, headers=upload_headers, data=document_file)
                upload_response.raise_for_status()

            if upload_response.status_code not in [200, 201]:
                self.logger.error(f"Document upload failed. Status: {upload_response.status_code}, Response: {upload_response.text}")
                raise Exception("Document upload failed")

            self.logger.info(f"Document uploaded successfully. Asset: {asset}")

            # Step 5: Publish the Post with the Document
            post_data = {
                "author": f"urn:li:person:{user_urn}",
                "lifecycleState": "PUBLISHED",
                "specificContent": {
                    "com.linkedin.ugc.ShareContent": {
                        "shareCommentary": {"text": content},
                        "shareMediaCategory": "DOCUMENT",
                        "media": [
                            {
                                "status": "READY",
                                "description": {"text": "Document shared on LinkedIn"},
                                "media": asset,
                                "title": {"text": "Uploaded Document"}
                            }
                        ]
                    }
                },
                "visibility": {"com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"}
            }
            post_response = requests.post(
                f"{self.api_url}ugcPosts",
                headers=headers,
                json=post_data
            )
            post_response.raise_for_status()

            self.logger.info(f"Document post published successfully for user {user_urn}")
            return post_response.json()

        except ContentValidationError as e:
            self.logger.error(f"Content validation failed for document post: {e}")
            raise e
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Request error during document post for user {user_urn}: {e}")
            raise Exception(f"Failed to post document on LinkedIn: {e}")
        except Exception as e:
            self.logger.error(f"Unexpected error during document post: {e}")
            raise
