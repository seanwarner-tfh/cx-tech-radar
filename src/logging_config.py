"""Logging configuration for CX Tech Radar"""
import logging
import os
import sys
from logging.handlers import RotatingFileHandler


def setup_logging(
    log_level: str = None,
    log_file: str = None,
    log_dir: str = "logs"
) -> logging.Logger:
    """Set up logging configuration for the application
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
                  Defaults to INFO, or LOG_LEVEL env var
        log_file: Path to log file. Defaults to 'cx_tech_radar.log' in log_dir
        log_dir: Directory for log files. Created if it doesn't exist.
    
    Returns:
        Configured logger instance
    """
    # Determine log level
    if log_level is None:
        log_level = os.getenv("LOG_LEVEL", "INFO").upper()
    
    level = getattr(logging, log_level, logging.INFO)
    
    # Create log directory if it doesn't exist
    if log_file is None:
        os.makedirs(log_dir, exist_ok=True)
        log_file = os.path.join(log_dir, "cx_tech_radar.log")
    else:
        log_dir = os.path.dirname(log_file) or log_dir
        os.makedirs(log_dir, exist_ok=True)
    
    # Create logger
    logger = logging.getLogger("cx_tech_radar")
    logger.setLevel(level)
    
    # Clear existing handlers
    logger.handlers.clear()
    
    # Create formatters
    detailed_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    simple_formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Console handler (INFO and above)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(simple_formatter)
    logger.addHandler(console_handler)
    
    # File handler (all levels, rotating)
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5
    )
    file_handler.setLevel(level)
    file_handler.setFormatter(detailed_formatter)
    logger.addHandler(file_handler)
    
    # Error file handler (ERROR and above)
    error_log_file = os.path.join(log_dir, "cx_tech_radar_errors.log")
    error_handler = RotatingFileHandler(
        error_log_file,
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(detailed_formatter)
    logger.addHandler(error_handler)
    
    logger.info(f"Logging initialized - Level: {log_level}, File: {log_file}")
    
    return logger


def get_logger(name: str = "cx_tech_radar") -> logging.Logger:
    """Get a logger instance
    
    Args:
        name: Logger name (defaults to 'cx_tech_radar')
    
    Returns:
        Logger instance
    """
    return logging.getLogger(name)

