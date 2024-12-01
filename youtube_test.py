import os
from dotenv import load_dotenv
from decafluence.oauth_helpers.youtube_oauth_helper import YouTubeOAuthHelper
from decafluence.publisher_services.youtube_publisher_service import YouTubePublisherService
from firebase_config import initialize_firebase
from logger_config import setup_logger  # Assuming your setup_logger function is here

# Load environment variables from .env file
load_dotenv()

# Get YouTube app credentials and test user ID from environment variables
YOUTUBE_CLIENT_ID = os.getenv('YOUTUBE_CLIENT_ID')
YOUTUBE_CLIENT_SECRET = os.getenv('YOUTUBE_CLIENT_SECRET')
REDIRECT_URI = os.getenv('REDIRECT_URI')
TEST_USER_ID = os.getenv('TEST_USER_ID')  # Replace with a YouTube user ID (you may need to find a valid one)

# Initialize the logger
logger = setup_logger()

def test_youtube_connector():
    try:
        # Initialize OAuth helper with environment variables
        oauth_helper = YouTubeOAuthHelper(
            client_id=YOUTUBE_CLIENT_ID,
            client_secret=YOUTUBE_CLIENT_SECRET,
            auth_url="https://accounts.google.com/o/oauth2/auth",
            token_url="https://accounts.google.com/o/oauth2/token",
            scope="https://www.googleapis.com/auth/youtube.upload"
        )

        # Step 1: Complete the authentication flow and save tokens under TEST_USER_ID
        logger.info("Step 1: Authenticating user...")
        oauth_helper.complete_authentication_flow(TEST_USER_ID)

        # Initialize YouTube Publisher Service
        publisher_service = YouTubePublisherService(oauth_helper)

        # Step 2: Test posting text (will raise NotImplementedError)
        try:
            logger.info("Step 2: Testing text post...")
            response = publisher_service.post_text(TEST_USER_ID, "This is a test post from my YouTube integration!")
            logger.info(f"Text Post Response: {response}")
        except NotImplementedError:
            logger.info("Text post is not supported on YouTube. Skipping text post test.")

        # Step 3: Test posting a video
        video_path = 'path/to/your/video.mp4'  # Provide a valid video path
        if os.path.exists(video_path):
            logger.info("Step 3: Testing video post...")
            response = publisher_service.post_video(TEST_USER_ID, "This is a test post with a video!", video_path)
            logger.info(f"Video Post Response: {response}")
        else:
            logger.warning("Video path not found. Skipping video post test.")

        # Step 4: Test posting an image (optional, not supported by YouTube)
        try:
            logger.info("Step 4: Testing image post...")
            image_path = 'path/to/your/image.jpg'  # Provide a valid image path
            response = publisher_service.post_image(TEST_USER_ID, "This is a test post with an image!", image_path)
            logger.info(f"Image Post Response: {response}")
        except NotImplementedError:
            logger.info("Image post is not supported on YouTube. Skipping image post test.")

        # Step 5: Test posting a document (optional, not supported by YouTube)
        try:
            logger.info("Step 5: Testing document post...")
            document_path = 'path/to/your/document.pdf'  # Provide a valid document path
            response = publisher_service.post_document(TEST_USER_ID, "This is a test post with a document!", document_path)
            logger.info(f"Document Post Response: {response}")
        except NotImplementedError:
            logger.info("Document post is not supported on YouTube. Skipping document post test.")

    except Exception as e:
        logger.error(f"An error occurred: {e}")

if __name__ == '__main__':
    # Initialize Firebase if needed
    initialize_firebase()
    test_youtube_connector()
