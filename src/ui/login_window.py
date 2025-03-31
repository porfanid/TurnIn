"""
Login window for the TurnIn application
"""
import os
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QGridLayout,
                            QLabel, QLineEdit, QPushButton, QMessageBox)


from src.utils.credential_manager import save_credentials, load_credentials
from src.utils.ssh import connect_to_proxy
from src.config import PROXY_HOST, TEMP_DIR

class LoginWindow(QMainWindow):
    """
    Login window for user authentication
    """
    def __init__(self):
        super().__init__()
        self.setWindowTitle("TurnIn - Login")
        self.resize(400, 150)

        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Main layout
        main_layout = QVBoxLayout(central_widget)

        # Form layout
        form_layout = QGridLayout()

        # Username field
        label_name = QLabel('Username:')
        label_name.setStyleSheet("font-size: 14px;")
        self.lineEdit_username = QLineEdit()
        self.lineEdit_username.setPlaceholderText('Please enter your username')
        form_layout.addWidget(label_name, 0, 0)
        form_layout.addWidget(self.lineEdit_username, 0, 1)

        # Password field
        label_password = QLabel('Password:')
        label_password.setStyleSheet("font-size: 14px;")
        self.lineEdit_password = QLineEdit()
        self.lineEdit_password.setEchoMode(QLineEdit.EchoMode.Password)
        self.lineEdit_password.setPlaceholderText('Please enter your password')
        form_layout.addWidget(label_password, 1, 0)
        form_layout.addWidget(self.lineEdit_password, 1, 1)

        # Login button
        button_login = QPushButton('Login')
        button_login.setDefault(True)
        button_login.clicked.connect(self.login)
        form_layout.addWidget(button_login, 2, 0, 1, 2)
        form_layout.setRowMinimumHeight(2, 50)

        # Connect enter key to login function
        self.lineEdit_password.returnPressed.connect(self.login)
        self.lineEdit_username.returnPressed.connect(self.login)

        main_layout.addLayout(form_layout)

    def check_saved_credentials(self):
        """Check for saved credentials and offer to use them"""
        credentials = load_credentials()
        if credentials:
            username, _ = credentials
            reply = QMessageBox.question(
                self,
                "Saved Credentials",
                f"Do you want to use the saved account '{username}'?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )

            if reply == QMessageBox.StandardButton.Yes:
                # Hide the login window immediately when using saved credentials
                self.hide()
                self.use_saved_credentials(credentials)
                return True
        return False

    def use_saved_credentials(self, credentials):
        """Use saved credentials to login"""
        username, password = credentials
        self.perform_login(username, password, from_saved=True)

    def login(self):
        """Handle login button click"""
        username = self.lineEdit_username.text()
        password = self.lineEdit_password.text()

        if not username or not password:
            QMessageBox.warning(self, "Login Error", "Please enter both username and password")
            return

        self.perform_login(username, password)

    def perform_login(self, username, password, from_saved=False):
        """Perform the actual login process"""
        result, host_to_connect, ssh = connect_to_proxy(username, password, PROXY_HOST)

        if not result:
            QMessageBox.warning(self, "Login Error", "Authentication failed. Please check your credentials.")
            return

        # Only ask to save credentials if they weren't loaded from saved credentials
        if not from_saved:
            reply = QMessageBox.question(
                self,
                "Save Credentials",
                "Do you want to save your credentials for future use?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )

            if reply == QMessageBox.StandardButton.Yes:
                save_credentials(username, password)
        self.hide()
        # Open main window
        from src.ui.main_window import MainWindow
        self.main_window = MainWindow(
            username=username,
            password=password,
            proxy_host=PROXY_HOST,
            host_to_connect=host_to_connect,
            temp_dir=TEMP_DIR,
            ssh=ssh
        )

        self.main_window.show()
        self.close()
