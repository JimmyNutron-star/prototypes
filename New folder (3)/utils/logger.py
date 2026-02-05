"""
Centralized logging system
"""

import logging
import os
from datetime import datetime
from config import DATA_DIR

class ScraperLogger:
    def __init__(self, scraper_name):
        self.scraper_name = scraper_name
        self.logger = self._setup_logger()
    
    def _setup_logger(self):
        """Setup logger with file and console handlers"""
        logger = logging.getLogger(self.scraper_name)
        logger.setLevel(logging.INFO)
        
        # Clear existing handlers
        logger.handlers.clear()
        
        # Create formatters
        detailed_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        simple_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        
        # File handler (detailed)
        log_file = os.path.join(DATA_DIR, "logs", f"{self.scraper_name}_{datetime.now().strftime('%Y%m%d')}.log")
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(detailed_formatter)
        
        # Console handler (simple)
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(simple_formatter)
        
        # Add handlers
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
        
        return logger
    
    def info(self, message):
        self.logger.info(message)
    
    def warning(self, message):
        self.logger.warning(message)
    
    def error(self, message):
        self.logger.error(message)
    
    def critical(self, message):
        self.logger.critical(message)