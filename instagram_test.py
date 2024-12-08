import os
from dotenv import load_dotenv
from decafluence.oauth_helpers.instagram_oauth_helper import InstagramOAuthHelper
from decafluence.publisher_services.instagram_publisher_service import InstagramPublisherService
from firebase_config import initialize_firebase  # Initialize Firebase
from google.cloud import storage as gcp_storage  # Initialize GCP Storage
from gcp_config import initialize_gcp_storage
from logger_config import setup_logger

# Load environment variables from .env file
load_dotenv()

# Instagram App Credentials and Test User ID from environment variables
INSTAGRAM_CLIENT_ID = os.getenv('INSTAGRAM_CLIENT_ID')
INSTAGRAM_CLIENT_SECRET = os.getenv('INSTAGRAM_CLIENT_SECRET')
REDIRECT_URI = os.getenv('REDIRECT_URI')
TEST_USER_ID = os.getenv('TEST_USER_ID')  # Replace with an Instagram user ID or URN

# Initialize the logger
logger = setup_logger()

def test_instagram_connector():
    try:
        # Step 1: Initialize OAuth Helper
        logger.info("Initializing Instagram OAuth Helper...")
        oauth_helper = InstagramOAuthHelper()
        oauth_helper.client_id = INSTAGRAM_CLIENT_ID
        oauth_helper.client_secret = INSTAGRAM_CLIENT_SECRET
        oauth_helper.redirect_uri = REDIRECT_URI

        # Step 2: Authenticate user
        logger.info("Authenticating user...")
        oauth_helper.complete_authentication_flow(TEST_USER_ID)

        # Step 3: Initialize Instagram Publisher Service
        logger.info("Initializing Instagram Publisher Service...")
        publisher_service = InstagramPublisherService(oauth_helper)

        # Step 4: Test posting an image
        image_path = 'E:/Projects/Decafluence/decafluence/decafluence_social_package/OfficialMeetLogo.jpg'
        logger.info("Testing image post...")
        if os.path.exists(image_path):
            logger.info(f"Image found at {image_path}. Posting to Instagram...")
            response = publisher_service.post_image(TEST_USER_ID, "This is a test post with an image!", image_path)
            logger.info(f"Image Post Response: {response}")
        else:
            logger.error(f"Image file not found at {image_path}. Skipping image post test.")

        # Step 5: Test posting a video
        video_path = 'E:/Projects/Decafluence/decafluence/decafluence_social_package/applebananavideo.mp4'
        logger.info("Testing video post...")
        if os.path.exists(video_path):
            logger.info(f"Video found at {video_path}. Posting to Instagram...")
            response = publisher_service.post_video(TEST_USER_ID, "This is a test post with a video!", video_path)
            logger.info(f"Video Post Response: {response}")
        else:
            logger.error(f"Video file not found at {video_path}. Skipping video post test.")

        # Step 6: Test posting a carousel (multiple images)
        carousel_images = [
            'E:/Projects/Decafluence/decafluence/decafluence_social_package/OfficialMeetLogo.jpg',
            'E:/Projects/Decafluence/decafluence/decafluence_social_package/OfficialMeetLogo.jpg'
        ]
        logger.info("Testing carousel post...")
        if all(os.path.exists(image) for image in carousel_images):
            logger.info(f"All carousel images found. Posting to Instagram...")
            response = publisher_service.post_carousel(TEST_USER_ID, "This is a test carousel post!", carousel_images)
            logger.info(f"Carousel Post Response: {response}")
        else:
            missing_images = [image for image in carousel_images if not os.path.exists(image)]
            logger.error(f"Some carousel images are missing: {missing_images}. Skipping carousel post test.")

    except Exception as e:
        logger.error(f"An error occurred during Instagram connector testing: {e}")

if __name__ == '__main__':
    # Initialize Firebase and GCP Storage if needed
    initialize_firebase()  # Firebase initialization (from firebase_config)
    gcp_storage_client = initialize_gcp_storage()  # GCP Storage initialization
    test_instagram_connector()  # Run the Instagram connector test
