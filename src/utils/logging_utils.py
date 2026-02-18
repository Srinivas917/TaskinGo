import logging
from pathlib import Path


class ColorFormatter(logging.Formatter):
    """Custom logging formatter that adds color codes based on log type."""
    COLORS = {
        logging.DEBUG: "\033[94m",  # Blue
        logging.INFO: "\033[92m",  # Green
        logging.WARNING: "\033[93m",  # Yellow
        logging.ERROR: "\033[91m",  # Red
        logging.CRITICAL: "\033[95m"  # Magenta
    }
    RESET = "\033[0m"

    def format(self, record):
        """
        Format log record with different colors based on log type.

        Args:
            record: LogRecord instance containing log event details

        Returns:
            Formatted log message string wrapped with ANSI color codes
        """
        log_color = self.COLORS.get(record.levelno, self.RESET)
        message = super().format(record)
        return f"{log_color}{message}{self.RESET}"


def get_logger(name: str, file: str, logging_level="INFO") -> logging.Logger:
    """
    Create a logger that logs to a file named after the script file.
    
    Args:
        name (str): usually __name__
        file (str): usually __file__
        debug_level (int): logging.DEBUG, logging.INFO, etc.
    
    Returns:
        Configured logging.Logger instance with File handler and Stream handler
    """
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)

    file_name = Path(file).stem  # get script file name without extension
    log_file = log_dir / f"{file_name}.log"

    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, logging_level.upper(), logging.INFO))

    if not logger.handlers:
        formatter = ColorFormatter("%(asctime)s | %(levelname)s | %(message)s")
        file_formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setFormatter(file_formatter)

        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(formatter)

        logger.addHandler(file_handler)
        logger.addHandler(stream_handler)

    return logger