import logging
import os
import zipfile
from datetime import datetime
from typing import Dict, List

from PySide6.QtCore import QObject, Signal


class LogManager(QObject):
    """
    Manages logs for the application, supporting both global and device-specific logs.
    Emits signals when new logs are added.
    Features:
    - Fresh logs on each start
    - Automatic backup of old logs when size exceeds threshold
    - Real-time signal updates
    """
    # Signals for log updates
    app_log_updated = Signal()
    device_log_updated = Signal(str)  # device_name

    def __init__(self):
        super().__init__()
        self.loggers: Dict[str, logging.Logger] = {}
        self.log_dir = "logs"
        self.backup_dir = os.path.join(self.log_dir, "backup")
        self.ensure_log_directory()

        # Check log size and backup if needed before creating new loggers
        self.check_and_backup_logs()

        # Initialize the main application logger
        self.initialize_logger("app", "app.log")

    def ensure_log_directory(self):
        """Ensure the log directory and backup directory exist"""
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir)

        if not os.path.exists(self.backup_dir):
            os.makedirs(self.backup_dir)

    def check_and_backup_logs(self):
        """
        Check the total size of all log files and backup if exceeds threshold.
        Creates fresh log files for this session.
        """
        # Store old log files that need to be backed up
        log_files_to_backup = []

        # Calculate total size of log files in the logs directory
        total_size = 0
        for filename in os.listdir(self.log_dir):
            if filename.endswith('.log'):
                file_path = os.path.join(self.log_dir, filename)
                # Add to backup list
                log_files_to_backup.append(file_path)
                # Add to total size
                total_size += os.path.getsize(file_path)

        # If total size is greater than 10MB (10 * 1024 * 1024 bytes), backup and clear logs
        if total_size > 10 * 1024 * 1024:
            self.backup_logs(log_files_to_backup)

        # Clear existing log files for fresh start (regardless of backup)
        for file_path in log_files_to_backup:
            # Don't delete, just clear the content by opening in write mode
            with open(file_path, 'w', encoding='utf-8') as f:
                pass

    def backup_logs(self, log_files):
        """Backup log files to a zip archive"""
        if not log_files:
            return

        # Create timestamped zip filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        zip_filename = os.path.join(self.backup_dir, f"logs_backup_{timestamp}.zip")

        # Create zip file
        with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for file_path in log_files:
                if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
                    # Add file to zip with just the filename (not the full path)
                    zipf.write(file_path, os.path.basename(file_path))

    def initialize_logger(self, name: str, log_file: str) -> logging.Logger:
        """Initialize a logger with the given name and file"""
        if name in self.loggers:
            return self.loggers[name]

        logger = logging.getLogger(name)
        logger.setLevel(logging.INFO)

        # Remove any existing handlers to avoid duplicates
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)

        # Create file handler
        file_handler = logging.FileHandler(
            os.path.join(self.log_dir, log_file),
            encoding='utf-8',
            mode='a'  # Use append mode
        )

        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

        # Set formatter and add handler
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

        # Add signal handler for this logger
        if name == "app":
            logger.addHandler(AppLogSignalHandler(self))
        elif name.startswith("device_"):
            device_name = name[7:]  # Remove "device_" prefix
            logger.addHandler(DeviceLogSignalHandler(device_name, self))

        # Store the logger
        self.loggers[name] = logger
        return logger

    def get_device_logger(self, device_name: str) -> logging.Logger:
        """Get or create a logger for a specific device"""
        logger_name = f"device_{device_name}"
        log_file = f"{device_name}.log"

        if logger_name not in self.loggers:
            return self.initialize_logger(logger_name, log_file)

        return self.loggers[logger_name]

    def get_app_logger(self) -> logging.Logger:
        """Get the main application logger"""
        return self.loggers.get("app")

    def log_device_info(self, device_name: str, message: str):
        """Log an info message for a device and to the app log"""
        device_logger = self.get_device_logger(device_name)
        device_logger.info(message)

        # Also log to the main app log with device name prefix
        app_logger = self.get_app_logger()
        if app_logger:
            app_logger.info(f"[{device_name}] {message}")

    def log_device_error(self, device_name: str, message: str):
        """Log an error message for a device and to the app log"""
        device_logger = self.get_device_logger(device_name)
        device_logger.error(message)

        # Also log to the main app log with device name prefix
        app_logger = self.get_app_logger()
        if app_logger:
            app_logger.error(f"[{device_name}] {message}")

    def get_device_logs(self, device_name: str, max_lines: int = 100) -> List[str]:
        """Retrieve recent logs for a specific device"""
        log_file = os.path.join(self.log_dir, f"{device_name}.log")
        if not os.path.exists(log_file):
            return []

        with open(log_file, 'r', encoding='utf-8') as f:
            # Get the last max_lines lines
            lines = f.readlines()
            return lines[-max_lines:] if len(lines) > max_lines else lines

    def get_all_logs(self, max_lines: int = 100) -> List[str]:
        """Retrieve recent logs from the main application log"""
        log_file = os.path.join(self.log_dir, "app.log")
        if not os.path.exists(log_file):
            return []

        with open(log_file, 'r', encoding='utf-8') as f:
            # Get the last max_lines lines
            lines = f.readlines()
            return lines[-max_lines:] if len(lines) > max_lines else lines


class AppLogSignalHandler(logging.Handler):
    """Custom logging handler that emits a signal when app logs are updated"""

    def __init__(self, log_manager):
        super().__init__()
        self.log_manager = log_manager

    def emit(self, record):
        # Emit the signal to notify that app logs have been updated
        self.log_manager.app_log_updated.emit()


class DeviceLogSignalHandler(logging.Handler):
    """Custom logging handler that emits a signal when device logs are updated"""

    def __init__(self, device_name, log_manager):
        super().__init__()
        self.device_name = device_name
        self.log_manager = log_manager

    def emit(self, record):
        # Emit the signal to notify that device logs have been updated
        self.log_manager.device_log_updated.emit(self.device_name)


# Create a singleton instance
log_manager = LogManager()