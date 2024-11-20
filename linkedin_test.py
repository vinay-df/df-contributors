import os
from dotenv import load_dotenv
from decafluence.oauth_helpers.linkedin_oauth_helper import LinkedInOAuthHelper
from decafluence.publisher_services.linkedin_publisher_service import LinkedInPublisherService
from firebase_config import initialize_firebase
from logger_config import setup_logger  # Assuming your setup_logger function is here

# Load environment variables from .env file
load_dotenv()

# Get LinkedIn app credentials and test user ID from environment variables
LINKEDIN_CLIENT_ID = os.getenv('LINKEDIN_CLIENT_ID')
LINKEDIN_CLIENT_SECRET = os.getenv('LINKEDIN_CLIENT_SECRET')
REDIRECT_URI = os.getenv('REDIRECT_URI')
TEST_USER_ID = os.getenv('TEST_USER_ID')  # Replace with a LinkedIn user URN like 'person:abc123'

# Initialize the logger
logger = setup_logger()

def test_linkedin_connector():
    try:
        # Initialize OAuth helper with environment variables
        oauth_helper = LinkedInOAuthHelper()
        oauth_helper.client_id = LINKEDIN_CLIENT_ID
        oauth_helper.client_secret = LINKEDIN_CLIENT_SECRET
        oauth_helper.redirect_uri = REDIRECT_URI

        # Step 1: Complete the authentication flow and save tokens under TEST_USER_ID
        logger.info("Step 1: Authenticating user...")
        oauth_helper.complete_authentication_flow(TEST_USER_ID)

        # Initialize LinkedIn Publisher Service
        publisher_service = LinkedInPublisherService(oauth_helper)

        # Step 2: Test posting text
        # logger.info("Step 2: Testing text post...")
        # response = publisher_service.post_text(TEST_USER_ID, "This is a test post from my LinkedIn integration!")
        # logger.info(f"Text Post Response: {response}")

        # Optional: Uncomment and test other media post methods if required

        # Step 3: Test posting an image (optional)
        image_path = 'E:/Projects/Decafluence/decafluence/decafluence_social_package/OfficialMeetLogo.jpg'  # Provide a valid image path
        if os.path.exists(image_path):
            logger.info("Step 3: Testing image post...")
            response = publisher_service.post_image(TEST_USER_ID, "This is a test post with an image!", image_path)
            logger.info(f"Image Post Response: {response}")
        else:
            logger.warning("Image path not found. Skipping image post test.")

        # Step 4: Test posting a video (optional)
        # video_path = 'path_to_your_test_video.mp4'  # Provide a valid video path
        # if os.path.exists(video_path):
        #     logger.info("Step 4: Testing video post...")
        #     response = publisher_service.post_video(TEST_USER_ID, "This is a test post with a video!", video_path)
        #     logger.info(f"Video Post Response: {response}")
        # else:
        #     logger.warning("Video path not found. Skipping video post test.")

        # Step 5: Test posting a document (optional)
        # document_path = 'path_to_your_test_document.pdf'  # Provide a valid document path
        # if os.path.exists(document_path):
        #     logger.info("Step 5: Testing document post...")
        #     response = publisher_service.post_document(TEST_USER_ID, "This is a test post with a document!", document_path)
        #     logger.info(f"Document Post Response: {response}")
        # else:
        #     logger.warning("Document path not found. Skipping document post test.")

    except Exception as e:
        logger.error(f"An error occurred: {e}")

if __name__ == '__main__':
    # Initialize Firebase if needed
    initialize_firebase()
    test_linkedin_connector()
