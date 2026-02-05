"""
Logging utilities for the agentic scraper
"""
import logging
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional

class ColoredFormatter(logging.Formatter):
    """Custom formatter with colors for console output"""
    
    COLORS = {
        'DEBUG': '\033[36m',    # Cyan
        'INFO': '\033[32m',     # Green
        'WARNING': '\033[33m',  # Yellow
        'ERROR': '\033[31m',    # Red
        'CRITICAL': '\033[35m', # Magenta
    }
    RESET = '\033[0m'
    
    def format(self, record):
        log_color = self.COLORS.get(record.levelname, self.RESET)
        record.levelname = f"{log_color}{record.levelname}{self.RESET}"
        record.name = f"\033[34m{record.name}{self.RESET}"  # Blue for logger name
        return super().format(record)

def setup_logger(name: str, log_dir: str = "logs", level: str = "INFO") -> logging.Logger:
    """
    Setup a logger with both file and console handlers
    
    Args:
        name: Logger name (typically agent name)
        log_dir: Directory for log files
        level: Logging level
        
    Returns:
        Configured logger instance
    """
    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper()))
    
    # Avoid duplicate handlers
    if logger.handlers:
        return logger
    
    # Create log directory
    log_path = Path(log_dir)
    log_path.mkdir(parents=True, exist_ok=True)
    
    # File handler - detailed logs
    timestamp = datetime.now().strftime("%Y%m%d")
    file_handler = logging.FileHandler(
        log_path / f"{name}_{timestamp}.log",
        encoding='utf-8'
    )
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter(
        '%(asctime)s | %(name)s | %(levelname)s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(file_formatter)
    
    # Console handler - colored output
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, level.upper()))
    console_formatter = ColoredFormatter(
        '%(asctime)s | %(name)s | %(levelname)s | %(message)s',
        datefmt='%H:%M:%S'
    )
    console_handler.setFormatter(console_formatter)
    
    # Add handlers
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger

class AgentLogger:
    """Logger wrapper for agents with structured logging"""
    
    def __init__(self, agent_name: str, log_dir: str = "logs", level: str = "INFO"):
        self.agent_name = agent_name
        self.logger = setup_logger(agent_name, log_dir, level)
        
    def debug(self, message: str, **kwargs):
        """Log debug message"""
        extra_info = " | ".join(f"{k}={v}" for k, v in kwargs.items())
        full_message = f"{message} | {extra_info}" if extra_info else message
        self.logger.debug(full_message)
        
    def info(self, message: str, **kwargs):
        """Log info message"""
        extra_info = " | ".join(f"{k}={v}" for k, v in kwargs.items())
        full_message = f"{message} | {extra_info}" if extra_info else message
        self.logger.info(full_message)
        
    def warning(self, message: str, **kwargs):
        """Log warning message"""
        extra_info = " | ".join(f"{k}={v}" for k, v in kwargs.items())
        full_message = f"{message} | {extra_info}" if extra_info else message
        self.logger.warning(full_message)
        
    def error(self, message: str, **kwargs):
        """Log error message"""
        extra_info = " | ".join(f"{k}={v}" for k, v in kwargs.items())
        full_message = f"{message} | {extra_info}" if extra_info else message
        self.logger.error(full_message)
        
    def critical(self, message: str, **kwargs):
        """Log critical message"""
        extra_info = " | ".join(f"{k}={v}" for k, v in kwargs.items())
        full_message = f"{message} | {extra_info}" if extra_info else message
        self.logger.critical(full_message)
        
    def state_change(self, old_state: str, new_state: str):
        """Log state transition"""
        self.info(f"State transition: {old_state} → {new_state}")
        
    def agent_action(self, action: str, **details):
        """Log agent action"""
        self.info(f"Action: {action}", **details)
        
    def data_collected(self, data_type: str, count: int = 1):
        """Log data collection"""
        self.info(f"Data collected: {data_type}", count=count)
