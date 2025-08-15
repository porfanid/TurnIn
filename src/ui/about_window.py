from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton, QTextBrowser
from PyQt6.QtGui import QPixmap, QFont
from PyQt6.QtCore import Qt

from .config import APP_NAME, APP_VERSION


class AboutWindow(QDialog):
    """Dialog window showing information about the application and developer."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"About {APP_NAME}")
        self.setMinimumWidth(400)
        self.setMinimumHeight(500)
        self.setup_ui()

    def setup_ui(self):
        """Set up the user interface components."""
        layout = QVBoxLayout(self)

        # Application title
        title_label = QLabel(f"{APP_NAME} v{APP_VERSION}")
        title_font = QFont()
        title_font.setBold(True)
        title_font.setPointSize(16)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)

        # Description text
        about_text = QTextBrowser()
        about_text.setOpenExternalLinks(True)
        about_text.setHtml("""
            <p>TurnIn is an application that simplifies the process of submitting assignments 
            through scylla.cs.uoi.gr.</p>
            
            <p><b>Developer:</b> Pavlos Orfanidis</p>
            <p><b>Email:</b> <a href="mailto:pavlos@orfanidis.net.gr">pavlos@orfanidis.net.gr</a></p>
            <p><b>Website:</b> <a href="https://github.com/porfanid">GitHub</a></p>
            
            <p>This application was created to help students easily submit their assignments 
            to the university Of Ioannina CSE Department</p>
        """)
        layout.addWidget(about_text)

        # Close button
        close_button = QPushButton("Close")
        close_button.clicked.connect(self.accept)
        layout.addWidget(close_button)
