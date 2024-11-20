from abc import ABC, abstractmethod

class BasePublisherService(ABC):
    def __init__(self, oauth_helper):
        self.oauth_helper = oauth_helper

    @abstractmethod
    def post_text(self, user_id, content):
        """Post a text-only update."""
        pass

    @abstractmethod
    def post_image(self, user_id, content, image_path):
        """Post an update with an image."""
        pass

    @abstractmethod
    def post_video(self, user_id, content, video_path):
        """Post an update with a video."""
        pass

    @abstractmethod
    def post_document(self, user_id, content, document_path):
        """Post an update with a document attachment."""
        pass
