"""
Version check utility for ensuring the application is up to date
"""
import requests
from PyQt6.QtWidgets import QMessageBox
from PyQt6.QtGui import QDesktopServices
from PyQt6.QtCore import QUrl
import sys

from src.config import APP_VERSION, REPO_OWNER, REPO_NAME


def check_version():
    """
    Check if the current version of the application is up to date.

    If a newer version is available, show a dialog and offer to
    download the latest version.
    """
    # GitHub repository information
    github_repo = f"{REPO_OWNER}/{REPO_NAME}"
    github_token = None  # Use this for GitHub Personal Access Token if needed

    # Current version of the software
    current_version = APP_VERSION

    # Construct the API URL
    api_url = f"https://api.github.com/repos/{github_repo}/releases/latest"

    # Include GitHub token if specified
    headers = {}
    if github_token:
        headers["Authorization"] = f"token {github_token}"

    try:
        # Send GET request to GitHub API
        response = requests.get(api_url, headers=headers)

        if response.status_code == 200:
            latest_release = response.json()
            latest_version = latest_release["tag_name"]

            if latest_version != f"version{current_version}":
                # Newer version is available
                link = f"https://github.com/{github_repo}/releases/tag/{latest_version}"

                # Create update message dialog
                update_message = QMessageBox()
                update_message.setWindowTitle("Update Required")
                update_message.setText(
                    f"A newer version ({latest_version}) is available.\nYour version: version{current_version}")
                update_message.setInformativeText("Would you like to download the latest version?")
                update_message.setIcon(QMessageBox.Icon.Information)

                # Add custom buttons
                download_button = update_message.addButton("Download", QMessageBox.ButtonRole.AcceptRole)
                cancel_button = update_message.addButton("Continue Anyway", QMessageBox.ButtonRole.RejectRole)

                # Show dialog and handle response
                result = update_message.exec()

                if update_message.clickedButton() == download_button:
                    QDesktopServices.openUrl(QUrl(link))
                    sys.exit(0)
            else:
                print("Application is up to date.")
        else:
            print(f"Failed to retrieve release information. Status code: {response.status_code}")

    except Exception as e:
        print(f"Error checking version: {e}")
        # Continue execution if version check fails