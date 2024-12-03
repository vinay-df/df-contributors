import os
from dotenv import load_dotenv
from decafluence.oauth_helpers.facebook_oauth_helper import FacebookOAuthHelper
from decafluence.publisher_services.facebook_publisher_service import FacebookPublisherService
from firebase_config import initialize_firebase
from logger_config import setup_logger  # Assuming your setup_logger function is here

# Load environment variables from .env file
load_dotenv()

# Facebook App Credentials and Test User ID from environment variables
FACEBOOK_CLIENT_ID = os.getenv('FACEBOOK_CLIENT_ID')
FACEBOOK_CLIENT_SECRET = os.getenv('FACEBOOK_CLIENT_SECRET')
REDIRECT_URI = os.getenv('REDIRECT_URI')
TEST_USER_ID = os.getenv('TEST_USER_ID')  # Replace with a Facebook user ID or Page ID

# Initialize the logger
logger = setup_logger()

def test_facebook_connector():
    try:
        # Step 1: Initialize OAuth Helper
        logger.info("Initializing Facebook OAuth Helper...")
        oauth_helper = FacebookOAuthHelper()
        oauth_helper.client_id = FACEBOOK_CLIENT_ID
        oauth_helper.client_secret = FACEBOOK_CLIENT_SECRET
        oauth_helper.redirect_uri = REDIRECT_URI

        # Step 2: Complete the authentication flow
        logger.info("Authenticating user...")
        oauth_helper.complete_authentication_flow(TEST_USER_ID)

        # Step 3: Initialize Facebook Publisher Service
        logger.info("Initializing Facebook Publisher Service...")
        publisher_service = FacebookPublisherService(oauth_helper)

        # Step 4: Test posting text
        # logger.info("Testing text post...")
        # text_post_content = "This is a test text post from my Facebook integration!"
        # response = publisher_service.post_text(TEST_USER_ID, text_post_content)
        # logger.info(f"Text Post Response: {response}")

        # # Step 5: Test posting an image (optional)
        # image_path = 'E:/Projects/Decafluence/decafluence/decafluence_social_package/OfficialMeetLogo.jpg'  # Provide a valid image path
        # if os.path.exists(image_path):
        #     logger.info("Testing image post...")
        #     image_post_content = "This is a test post with an image!"
        #     response = publisher_service.post_image(TEST_USER_ID, image_post_content, image_path)
        #     logger.info(f"Image Post Response: {response}")
        # else:
        #     logger.warning(f"Image file not found at path: {image_path}. Skipping image post test.")

        # # Step 6: Test posting a video (optional)
        # video_path = 'E:/Projects/Decafluence/decafluence/decafluence_social_package/applebananavideo.mp4'  # Provide a valid video path
        # if os.path.exists(video_path):
        #     logger.info("Testing video post...")
        #     video_post_content = "This is a test post with a video!"
        #     response = publisher_service.post_video(TEST_USER_ID, video_post_content, video_path)
        #     logger.info(f"Video Post Response: {response}")
        # else:
        #     logger.warning(f"Video file not found at path: {video_path}. Skipping video post test.")

        # # Step 7: Test posting a link (optional)
        # test_link_url = "https://www.example.com"  # Provide a valid link
        # logger.info("Testing link post...")
        # link_post_content = "Check out this link shared via the Facebook API!"
        # response = publisher_service.post_link(TEST_USER_ID, link_post_content, test_link_url)
        # logger.info(f"Link Post Response: {response}")

    #     # Test Step 8: Test posting a document
    #     document_path = "E:/Projects/Decafluence/decafluence/decafluence_social_package/Question bank Answers for NLP.pdf"
    #     if os.path.exists(document_path):
    #         logger.info("Testing document post...")
    #         document_post_content = "This is a test post with a document!"
    #         try:
    #             response = publisher_service.post_document(TEST_USER_ID, document_post_content, document_path)
    #             logger.info(f"Document Post Response: {response}")
    #         except Exception as e:
    #             logger.error(f"Error posting document: {e}")
    #     else:
    #         logger.warning(f"Document file not found at path: {document_path}. Skipping document post test.")

    except Exception as e:
        logger.error(f"An error occurred during Facebook connector testing: {e}")

if __name__ == '__main__':
    # Initialize Firebase if needed
    initialize_firebase()
    test_facebook_connector()
