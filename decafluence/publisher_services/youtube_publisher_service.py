import os
import requests
from decafluence.oauth_helpers.youtube_oauth_helper import YouTubeOAuthHelper
from decafluence.publisher_services.base_publisher import BasePublisherService
from decafluence.validators.content_validators import ContentValidationError, ContentValidator

class YouTubePublisherService(BasePublisherService):
    def __init__(self, oauth_helper: YouTubeOAuthHelper):
        self.oauth_helper = oauth_helper
        self.api_url = 'https://www.googleapis.com/upload/youtube/v3/videos'
        self.validator = ContentValidator(platform='youtube')

    def _get_auth_header(self, user_id):
        """Get the authorization header to interact with YouTube API."""
        access_token = self.oauth_helper.refresh_token(user_id)
        return {'Authorization': f'Bearer {access_token}'}

    def post_text(self, user_id, content):
        """Posting text-only content is not directly supported by YouTube."""
        raise NotImplementedError("YouTube does not support text-only posts. Please use videos or other media.")

    def post_image(self, user_id, content, image_path):
        """YouTube does not support direct image posts, so this is not implemented."""
        raise NotImplementedError("YouTube does not support direct image uploads. Please use videos.")

    def post_video(self, user_id, content, video_path):
        """Post a video to YouTube."""
        try:
            self.validator.validate_video(video_path)  # Validate the video
            self.validator.validate_text(content)  # Validate the content
            access_token = self.oauth_helper.refresh_token(user_id)

            # Step 1: Upload the video
            video_url = self._upload_video(access_token, video_path, content)

            # Step 2: Return the response from the YouTube API
            return video_url  # The URL or details of the uploaded video
        except ContentValidationError as e:
            raise e  # Reraise the validation error
        except requests.HTTPError as e:
            raise Exception(f"Failed to post video on YouTube: {str(e)}")

    def post_document(self, user_id, content, document_path):
        """YouTube does not support document uploads."""
        raise NotImplementedError("YouTube does not allow document uploads directly.")

    def _upload_video(self, access_token, video_path, title):
        """Upload a video to YouTube."""
        video_metadata = {
            'snippet': {
                'title': title,
                'description': 'Test video upload using YouTube API',
                'tags': ['test', 'video', 'upload']
            },
            'status': {
                'privacyStatus': 'public'  # You can change this to 'private' or 'unlisted'
            }
        }

        headers = self._get_auth_header(user_id)

        # Upload the video file
        with open(video_path, 'rb') as video_file:
            files = {
                'media': video_file,
                'metadata': (None, str(video_metadata), 'application/json')
            }

            response = requests.post(self.api_url, headers=headers, files=files)
            if response.status_code != 200:
                raise Exception(f"Failed to upload video: {response.text}")
            
            return response.json()  # Return the response (video details)
