import logging
import os

LOG_DIR = "logs"

def get_logger(module_name: str) -> logging.Logger:
    # Create logs folder if not exists
    if not os.path.exists(LOG_DIR):
        os.makedirs(LOG_DIR)

    # Extract filename from module path
    file_name = module_name.split(".")[-1]
    log_file_path = os.path.join(LOG_DIR, f"{file_name}.log")

    logger = logging.getLogger(module_name)
    logger.setLevel(logging.INFO)

    # Prevent duplicate handlers
    if not logger.handlers:
        file_handler = logging.FileHandler(log_file_path)
        formatter = logging.Formatter(
            "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
        )
        file_handler.setFormatter(formatter)
        
        combined_handler = logging.FileHandler(os.path.join(LOG_DIR, "news_agent.log"))
        combined_handler.setFormatter(formatter)
        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(formatter)

        logger.addHandler(combined_handler)
        logger.addHandler(file_handler)
        logger.addHandler(stream_handler)
        
        logger.propagate = False

    return logger
