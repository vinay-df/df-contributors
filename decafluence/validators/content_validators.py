import json
import os
import re

class ContentValidationError(Exception):
    """Custom exception for content validation errors."""
    pass

class ContentValidator:
    """Validates content based on platform-specific requirements."""

    def __init__(self, platform):
        self.platform = platform
        self.PLATFORM_LIMITS = self.load_limits()

    def load_limits(self):
        with open('decafluence/validators/platform_limits.json') as f:
            return json.load(f)

    def validate_text(self, content):
        max_length = self.PLATFORM_LIMITS[self.platform]['max_text_length']
        if len(content) > max_length:
            raise ContentValidationError(f"{self.platform.capitalize()} content exceeds the maximum length of {max_length} characters.")

    def validate_image(self, image_path):
        self._validate_file(image_path, 'image')
        
        if os.path.getsize(image_path) > self.PLATFORM_LIMITS[self.platform]['max_image_size']:
            raise ContentValidationError(f"{self.platform.capitalize()} image exceeds the maximum size of {self.PLATFORM_LIMITS[self.platform]['max_image_size'] / (1024 * 1024)} MB.")

    def validate_video(self, video_path):
        self._validate_file(video_path, 'video')
        
        if os.path.getsize(video_path) > self.PLATFORM_LIMITS[self.platform]['max_video_size']:
            raise ContentValidationError(f"{self.platform.capitalize()} video exceeds the maximum size of {self.PLATFORM_LIMITS[self.platform]['max_video_size'] / (1024 * 1024)} MB.")

    def validate_document(self, document_path):
        self._validate_file(document_path, 'document')

        if os.path.getsize(document_path) > self.PLATFORM_LIMITS[self.platform]['max_document_size']:
            raise ContentValidationError(f"{self.platform.capitalize()} document exceeds the maximum size of {self.PLATFORM_LIMITS[self.platform]['max_document_size'] / (1024 * 1024)} MB.")

    def validate_url(self, url):
        """
        Validates the URL to check if it is well-formed.
        It also ensures the URL is not too long and that it is supported by the platform.
        """
        # Check if the URL is well-formed
        regex = re.compile(
            r'^(?:http|ftp)s?://'  # http:// or https://
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]*[A-Z0-9])?\.)+(?:[A-Z]{2,})'  # domain (supporting all TLDs)
            r'|'  # or
            r'localhost|'  # localhost
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}|'  # or IPv4
            r'\[?[A-F0-9]*:[A-F0-9:]+\]?)'  # or IPv6
            r'(?::\d+)?'  # optional port
            r'(?:/?|[/?]\S+)$', re.IGNORECASE  # path (optional)
        )

        
        if not re.match(regex, url):
            raise ContentValidationError(f"Invalid URL format: {url}")
        
        # Validate URL length
        max_url_length = self.PLATFORM_LIMITS[self.platform].get('max_url_length', 2000)
        if len(url) > max_url_length:
            raise ContentValidationError(f"URL exceeds the maximum length of {max_url_length} characters.")
        
        # You could add further checks based on platform restrictions, e.g., supported domains.
        # For example:
        supported_domains = self.PLATFORM_LIMITS[self.platform].get('supported_url_domains', [])
        if supported_domains:
            domain = url.split('/')[2]
            if domain not in supported_domains:
                raise ContentValidationError(f"The URL domain {domain} is not supported by {self.platform.capitalize()}.")

    def _validate_file(self, file_path, file_type):
        if not os.path.isfile(file_path):
            raise ContentValidationError(f"{file_type.capitalize()} file not found: {file_path}")

        if file_type == 'image' and not file_path.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
            raise ContentValidationError(f"Invalid image format for {self.platform.capitalize()}. Only PNG, JPG, and GIF are allowed.")

        if file_type == 'video' and not file_path.lower().endswith(('.mp4', '.mov', '.avi')):
            raise ContentValidationError(f"Invalid video format for {self.platform.capitalize()}. Only MP4, MOV, and AVI are allowed.")

        if file_type == 'document' and not file_path.lower().endswith(('.pdf', '.docx', '.pptx')):
            raise ContentValidationError(f"Invalid document format for {self.platform.capitalize()}. Only PDF, DOCX, and PPTX are allowed.")
