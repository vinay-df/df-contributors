import os
from dotenv import load_dotenv
from decafluence.oauth_helpers.instagram_oauth_helper import InstagramOAuthHelper
from decafluence.publisher_services.instagram_publisher_service import InstagramPublisherService
from firebase_config import initialize_firebase
from logger_config import setup_logger  # Assuming your setup_logger function is here

# Load environment variables from .env file
load_dotenv()

# Get Instagram app credentials and test user ID from environment variables
INSTAGRAM_CLIENT_ID = os.getenv('INSTAGRAM_CLIENT_ID')
INSTAGRAM_CLIENT_SECRET = os.getenv('INSTAGRAM_CLIENT_SECRET')
REDIRECT_URI = os.getenv('REDIRECT_URI')
TEST_USER_ID = os.getenv('TEST_USER_ID')  # Replace with an Instagram user ID or user URN like 'user:abc123'

# Initialize the logger
logger = setup_logger()

def test_instagram_connector():
    try:
        # Initialize OAuth helper with environment variables
        oauth_helper = InstagramOAuthHelper()
        oauth_helper.client_id = INSTAGRAM_CLIENT_ID
        oauth_helper.client_secret = INSTAGRAM_CLIENT_SECRET
        oauth_helper.redirect_uri = REDIRECT_URI

        # Step 1: Complete the authentication flow and save tokens under TEST_USER_ID
        logger.info("Step 1: Authenticating user...")
        oauth_helper.complete_authentication_flow(TEST_USER_ID)

        # Initialize Instagram Publisher Service
        publisher_service = InstagramPublisherService(oauth_helper)

        # Step 2: Test posting an image
        image_path = 'path/to/your/image.jpg'  # Provide a valid image path
        if os.path.exists(image_path):
            logger.info("Step 2: Testing image post...")
            response = publisher_service.post_image(TEST_USER_ID, "This is a test post with an image!", image_path)
            logger.info(f"Image Post Response: {response}")
        else:
            logger.warning("Image path not found. Skipping image post test.")

        # Step 3: Test posting a video (optional)
        video_path = 'path/to/your/video.mp4'  # Provide a valid video path
        if os.path.exists(video_path):
            logger.info("Step 3: Testing video post...")
            response = publisher_service.post_video(TEST_USER_ID, "This is a test post with a video!", video_path)
            logger.info(f"Video Post Response: {response}")
        else:
            logger.warning("Video path not found. Skipping video post test.")

        # Step 4: Test posting text (Not implemented for Instagram, will raise NotImplementedError)
        try:
            logger.info("Step 4: Testing text post...")
            response = publisher_service.post_text(TEST_USER_ID, "This is a test post with text!")
        except NotImplementedError:
            logger.info("Text posting is not supported on Instagram, as expected.")

        # Step 5: Test posting a document (Not implemented for Instagram, will raise NotImplementedError)
        try:
            logger.info("Step 5: Testing document post...")
            document_path = 'path/to/your/document.pdf'  # Provide a valid document path
            if os.path.exists(document_path):
                response = publisher_service.post_document(TEST_USER_ID, "This is a test post with a document!", document_path)
                logger.info(f"Document Post Response: {response}")
            else:
                logger.warning("Document path not found. Skipping document post test.")
        except NotImplementedError:
            logger.info("Document posting is not supported on Instagram, as expected.")

    except Exception as e:
        logger.error(f"An error occurred: {e}")

if __name__ == '__main__':
    # Initialize Firebase if needed
    initialize_firebase()
    test_instagram_connector()
