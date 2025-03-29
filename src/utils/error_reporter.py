"""
Error reporting utilities for capturing and handling exceptions
"""
import sys
from os import path
import traceback
import sentry_sdk
from PyQt6.QtWidgets import QMessageBox
sys.path.insert(0, path.abspath(path.join(path.dirname(__file__), '..')))
from config import SENTRY_DSN


def init_error_reporting():
    """
    Initialize the error reporting system with Sentry
    """
    try:
        sentry_sdk.init(SENTRY_DSN)
    except Exception as e:
        print(f"Failed to initialize error reporting: {e}")


def report_error(e, context="", user_info=None):
    """
    Report an error to Sentry and show a dialog to the user

    Args:
        e (Exception): The exception to report
        context (str): Additional context about where the error occurred
        user_info (dict): User information to include with the error
    """
    try:
        # Set user context if provided
        if user_info:
            sentry_sdk.set_user(user_info)

        # Add extra context data
        with sentry_sdk.configure_scope() as scope:
            scope.set_extra("context", context)

        # Capture the exception
        sentry_sdk.capture_exception(e)

        # Log to console
        print(f"Error in {context}: {str(e)}")
        traceback.print_exc()

        # Show error message to user
        error_dialog = QMessageBox()
        error_dialog.setWindowTitle("Error")
        error_dialog.setText(f"An error occurred: {str(e)}")
        error_dialog.setDetailedText(traceback.format_exc())
        error_dialog.setIcon(QMessageBox.Icon.Critical)
        error_dialog.exec()

    except Exception as report_error:
        # Failsafe if error reporting itself fails
        print(f"Error in error reporting: {report_error}")

        # Basic error dialog
        error_dialog = QMessageBox()
        error_dialog.setWindowTitle("Error")
        error_dialog.setText(f"An error occurred: {str(e)}")
        error_dialog.setIcon(QMessageBox.Icon.Critical)
        error_dialog.exec()