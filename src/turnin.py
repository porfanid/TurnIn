#!/usr/bin/env python3
"""
Main entry point for the TurnIn application.
This application allows students to submit assignments through an SSH proxy.
"""
import sys
import os
import logging
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QIcon
import sentry_sdk

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('turnin.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Add src to path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

from ui.login_window import LoginWindow
from utils.version_check import check_version
from config import APP_NAME, APP_VERSION, SENTRY_DSN


def initialize_sentry():
    """Initialize Sentry error reporting"""
    try:
        sentry_sdk.init(SENTRY_DSN)
        logger.info("Sentry initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize Sentry: {e}")


def main():
    """Main entry point for the application"""
    logger.info(f"Starting {APP_NAME} v{APP_VERSION}")

    # Initialize error reporting
    initialize_sentry()

    # Create application instance
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setApplicationVersion(APP_VERSION)

    # Set application icon
    icon_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'cse.logo.png')
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))
        logger.debug(f"Application icon set from {icon_path}")
    else:
        logger.warning(f"Icon file not found at {icon_path}")

    # Check for updates
    check_version()

    # Show login window
    login_window = LoginWindow()
    if not login_window.check_saved_credentials():
        login_window.show()
    logger.info("Application UI initialized and displayed")

    # Start application event loop
    return_code = app.exec()
    logger.info(f"Application exiting with code {return_code}")
    sys.exit(return_code)


if __name__ == "__main__":
    main()