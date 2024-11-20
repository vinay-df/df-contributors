import logging
import os

def setup_logger(log_dir="logs", log_level=logging.INFO):
    # Create log directory if it doesn't exist
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    # Define log format with filename, line number, and log level
    log_format = '%(asctime)s - %(filename)s - Line: %(lineno)d - %(levelname)s - %(message)s'

    # Set up file handler to write logs to a file
    log_file = os.path.join(log_dir, 'application.log')
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(log_level)
    file_handler.setFormatter(logging.Formatter(log_format))

    # Set up console handler for logging to the console
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_handler.setFormatter(logging.Formatter(log_format))

    # Set up the logger
    logger = logging.getLogger()
    logger.setLevel(log_level)
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger
