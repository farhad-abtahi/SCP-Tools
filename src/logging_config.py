"""
Logging configuration for SCP-ECG Tools

Author: Farhad Abtahi

Provides centralized logging configuration with:
- File logging for persistent records
- Console logging for immediate feedback
- Separate logs for different activities
- Rotation to prevent disk space issues
"""

import logging
import logging.handlers
import os
from datetime import datetime
from pathlib import Path


def setup_logging(name='scp_tools', log_dir=None, level=logging.INFO):
    """
    Set up comprehensive logging for the application
    
    Args:
        name: Logger name
        log_dir: Directory to store log files
        level: Logging level
        
    Returns:
        Configured logger instance
    """
    # Create logs directory if it doesn't exist
    if log_dir is None:
        # Find project root (where src/ is located)
        current_path = Path(__file__).parent.parent
        log_path = current_path / 'logs'
    else:
        log_path = Path(log_dir)
    log_path.mkdir(exist_ok=True)
    
    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Remove existing handlers to avoid duplicates
    logger.handlers.clear()
    
    # Create formatters
    detailed_formatter = logging.Formatter(
        '%(asctime)s | %(levelname)-8s | %(name)s | %(funcName)s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    simple_formatter = logging.Formatter(
        '%(asctime)s | %(levelname)-8s | %(message)s',
        datefmt='%H:%M:%S'
    )
    
    # File handler for all logs
    all_log_file = log_path / f'scp_tools_{datetime.now().strftime("%Y%m%d")}.log'
    file_handler = logging.handlers.RotatingFileHandler(
        all_log_file,
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(detailed_formatter)
    
    # File handler for errors only
    error_log_file = log_path / 'errors.log'
    error_handler = logging.handlers.RotatingFileHandler(
        error_log_file,
        maxBytes=5*1024*1024,  # 5MB
        backupCount=3
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(detailed_formatter)
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(simple_formatter)
    
    # Add handlers to logger
    logger.addHandler(file_handler)
    logger.addHandler(error_handler)
    logger.addHandler(console_handler)
    
    return logger


def get_activity_logger(activity_name):
    """
    Get a logger for a specific activity (read, anonymize, visualize, etc.)
    
    Args:
        activity_name: Name of the activity
        
    Returns:
        Logger configured for the activity
    """
    # Find project root
    current_path = Path(__file__).parent.parent
    log_dir = current_path / 'logs' / 'activities'
    log_dir.mkdir(parents=True, exist_ok=True)
    
    logger = logging.getLogger(f'scp_tools.{activity_name}')
    
    # Activity-specific file handler with daily logs
    log_file = log_dir / f'{activity_name}_{datetime.now().strftime("%Y%m%d")}.log'
    handler = logging.handlers.RotatingFileHandler(
        log_file,
        maxBytes=5*1024*1024,
        backupCount=3
    )
    handler.setFormatter(logging.Formatter(
        '%(asctime)s | %(levelname)s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    ))
    
    # Clear existing handlers and add new one
    logger.handlers.clear()
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    
    return logger


class ActivityLogger:
    """Context manager for logging activities with success/failure tracking"""
    
    def __init__(self, activity_name, description="", logger=None):
        self.activity_name = activity_name
        self.description = description
        self.logger = logger or get_activity_logger(activity_name)
        self.start_time = None
        self.success = False
        
    def __enter__(self):
        self.start_time = datetime.now()
        self.logger.info(f"START: {self.description or self.activity_name}")
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = (datetime.now() - self.start_time).total_seconds()
        
        if exc_type is None:
            self.success = True
            self.logger.info(
                f"SUCCESS: {self.description or self.activity_name} "
                f"(Duration: {duration:.2f}s)"
            )
        else:
            self.success = False
            self.logger.error(
                f"FAILED: {self.description or self.activity_name} "
                f"(Duration: {duration:.2f}s) - Error: {exc_val}"
            )
        
        # Don't suppress exceptions
        return False
    
    def log_info(self, message):
        """Log informational message"""
        self.logger.info(f"  {message}")
        
    def log_warning(self, message):
        """Log warning message"""
        self.logger.warning(f"  {message}")
        
    def log_error(self, message):
        """Log error message"""
        self.logger.error(f"  {message}")


def log_summary(logger=None):
    """
    Generate and log a summary of recent activities
    
    Args:
        logger: Logger to use (creates one if not provided)
    """
    if logger is None:
        logger = setup_logging()
    
    log_dir = Path('logs/activities')
    if not log_dir.exists():
        return
    
    summary = {
        'total_activities': 0,
        'successful': 0,
        'failed': 0,
        'by_type': {}
    }
    
    # Parse recent log files
    for log_file in log_dir.glob('*.log'):
        if log_file.stat().st_size == 0:
            continue
            
        activity_type = log_file.stem.split('_')[0]
        
        with open(log_file, 'r') as f:
            lines = f.readlines()
            
        for line in lines:
            if 'START:' in line:
                summary['total_activities'] += 1
                summary['by_type'][activity_type] = summary['by_type'].get(activity_type, 0) + 1
            elif 'SUCCESS:' in line:
                summary['successful'] += 1
            elif 'FAILED:' in line:
                summary['failed'] += 1
    
    # Log summary
    logger.info("="*60)
    logger.info("ACTIVITY SUMMARY")
    logger.info("="*60)
    logger.info(f"Total Activities: {summary['total_activities']}")
    logger.info(f"Successful: {summary['successful']}")
    logger.info(f"Failed: {summary['failed']}")
    
    if summary['total_activities'] > 0:
        success_rate = (summary['successful'] / summary['total_activities']) * 100
        logger.info(f"Success Rate: {success_rate:.1f}%")
    
    logger.info("Activities by Type:")
    for activity_type, count in summary['by_type'].items():
        logger.info(f"  {activity_type}: {count}")
    logger.info("="*60)


# Example usage functions
def example_usage():
    """Example of how to use the logging system"""
    
    # Basic logging
    logger = setup_logging()
    logger.info("Application started")
    logger.debug("Debug information")
    logger.warning("Warning message")
    logger.error("Error occurred")
    
    # Activity logging with context manager
    with ActivityLogger('read', 'Reading ECG file') as activity:
        activity.log_info("Opening file...")
        activity.log_info("Parsing sections...")
        activity.log_info("Extracting ECG data...")
        # Simulate work
        import time
        time.sleep(0.1)
    
    # Log summary
    log_summary()


if __name__ == "__main__":
    example_usage()