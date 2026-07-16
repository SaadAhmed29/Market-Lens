import logging
import os
import sys

def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    if not logger.handlers:
        # Create ml/logs/ directory if it doesn't exist
        log_dir = os.path.join("ml", "logs")
        os.makedirs(log_dir, exist_ok=True)

        # Formatter
        formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(name)s — %(message)s')

        # Console handler (INFO)
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)

        # File handler (DEBUG)
        # Using __name__ as parameter for the file handler might give issues like '__main__' instead of file name.
        # So we sanitize 'name' to not conflict. Wait, the instructions say 'ml/logs/{name}.log'
        log_file = os.path.join(log_dir, f"{name}.log")
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)

        logger.addHandler(console_handler)
        logger.addHandler(file_handler)

    return logger
