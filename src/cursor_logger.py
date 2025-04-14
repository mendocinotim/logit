#!/usr/bin/env python3
import os
import logging
from pathlib import Path
from datetime import datetime

def setup_cursor_logging():
    """Configure logging for Cursor operations"""
    # Create logs directory if it doesn't exist
    base_dir = Path(os.path.expanduser('~')) / '.logit'
    log_dir = base_dir / 'logs' / 'cursor'
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # Create a log file with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = log_dir / f"cursor_{timestamp}.log"
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()  # Also log to console
        ]
    )
    
    logger = logging.getLogger('cursor')
    logger.info(f"Cursor logging initialized. Log file: {log_file}")
    return logger

def generate_cursor_tag(description):
    """
    Generate a structured tag for Cursor code contributions.
    
    Args:
        description (str): A brief description of the code contribution
        
    Returns:
        str: A formatted tag string
    """
    date = datetime.now().strftime("%Y-%m-%d")
    return f"# [CURSOR: {date}] {description}"

# Create a global logger instance
cursor_logger = setup_cursor_logging() 