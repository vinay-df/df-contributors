import os
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

    def post_document(self, user_id, commentary, document_path):
        """Posts a document on LinkedIn.

        Args:
            user_id (str): The user's LinkedIn ID.
            commentary (str): The text to accompany the document.
            document_path (str): The path to the document to be uploaded.

        Returns:
            dict: The JSON response from the LinkedIn API.

        Raises:
            ValueError: If access token or user URN is not found.
            requests.exceptions.RequestException: If a request to the LinkedIn API fails.
            Exception: If an unexpected error occurs.
        """
        try:
            # Step 1: Retrieve Access Token
            access_token = self.oauth_helper.get_token(user_id).get('access_token')
            if not access_token:
                raise ValueError("Access token not found.")
            self.logger.info(f"Access token retrieved for user {user_id}")

            user_urn = self.oauth_helper.get_user_urn(access_token)
            if not user_urn:
                raise ValueError("User URN not found.")
            self.logger.info(f"Attempting to post document for user {user_urn}")

            # Headers for LinkedIn API requests
            headers = {
                'Authorization': f'Bearer {access_token}',
                'LinkedIn-Version': '202307',  # Update this as per the latest version
                'X-Restli-Protocol-Version': '2.0.0',
                'Content-Type': 'application/json'
            }

            # Step 2: Validate Inputs
            self.validator.validate_document(document_path)
            self.validator.validate_text(commentary)

            # Step 3: Initialize Document Upload
            document_name = os.path.basename(document_path)
            initialize_upload_body = {
                "initializeUploadRequest": {
                    "owner": f"urn:li:person:{user_urn}"
                }
            }
            initialize_response = requests.post(
                f"https://api.linkedin.com/rest/documents?action=initializeUpload",
                headers=headers, json=initialize_upload_body
            )
            initialize_response.raise_for_status()
            initialize_result = initialize_response.json()

            # Extract Upload URL and Document ID
            upload_url = initialize_result["value"]["uploadUrl"]
            document_id = initialize_result["value"]["document"]
            
            self.logger.info(f"Document initialized for upload. Document ID: {document_id}, Upload URL: {upload_url}")

            # Step 4: Upload the Document
            with open(document_path, 'rb') as document_file:
                upload_headers = {'Authorization': f'Bearer {access_token}'}
                upload_response = requests.put(upload_url, headers=upload_headers, data=document_file)
                upload_response.raise_for_status()

            self.logger.info(f"Document uploaded successfully. Document ID: {document_id}")

            # Step 5: Create the Post with Uploaded Document
            post_body = {
                "author": f"urn:li:person:{user_urn}",
                "commentary": commentary,
                "visibility": "PUBLIC",
                "distribution": {
                    "feedDistribution": "MAIN_FEED",
                    "targetEntities": [],
                    "thirdPartyDistributionChannels": []
                },
                "content": {
                    "media": {
                        "title": document_name,
                        "id": document_id
                    }
                },
                "lifecycleState": "PUBLISHED",
                "isReshareDisabledByAuthor": False
            }
            post_response = requests.post(
                f"https://api.linkedin.com/rest/posts",
                headers=headers, json=post_body
            )
            # Log status and response for debugging
            self.logger.info(f"Post response status: {post_response.status_code}")
            self.logger.info(f"Post response body: {post_response.text}")

            if post_response.status_code == 201:
                post_id = post_response.headers.get('x-restli-id')
                if post_id:
                    self.logger.info(f"Document post created successfully. Post ID: {post_id}")
                    return {"post_id": post_id}
                else:
                    self.logger.error("Post ID not found in response headers.")
                    raise Exception("Post creation failed: Post ID missing in response headers.")
            else:
                self.logger.error(f"Failed to create post. Response: {post_response.text}")
                raise Exception(f"Error in creating post: {post_response.text}")

        except requests.exceptions.RequestException as e:
            self.logger.error(f"Request error during document post: {e}")
            raise Exception(f"Failed to post document on LinkedIn: {e}")
        except Exception as e:
            self.logger.error(f"Unexpected error during document post: {e}")
            raise
