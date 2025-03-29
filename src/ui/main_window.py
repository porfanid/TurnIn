"""
Main window for the TurnIn application
"""
import os
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QPushButton, QLabel, QComboBox, QFileDialog,
                             QListWidget, QMessageBox, QSplitter, QGroupBox, QScrollArea, QLineEdit)
from PyQt6.QtCore import Qt
from src.utils.ssh import submit_files, connect_to_proxy
from src.ui.about_window import AboutWindow


class MainWindow(QMainWindow):
    """
    Main window for file selection and assignment submission
    """

    def __init__(self, username, password, proxy_host, host_to_connect, temp_dir, ssh=None):
        super().__init__()
        self.username = username
        self.password = password
        self.proxy_host = proxy_host
        self.host_to_connect = host_to_connect
        self.temp_dir = temp_dir
        self.ssh = ssh
        self.selected_files = []

        self.setWindowTitle("TurnIn - Assignment Submission")
        self.resize(800, 600)

        self.init_ui()

    def init_ui(self):
        """Initialize the user interface"""
        # Main widget and layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout(main_widget)

        # Header with user info
        header = QLabel(f"Logged in as: {self.username}")
        header.setStyleSheet("font-size: 16px; font-weight: bold; padding: 10px;")
        main_layout.addWidget(header)

        # Create a splitter to divide the window
        splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(splitter)

        # Left panel - Assignment selection
        left_panel = QGroupBox("Assignment Selection")
        left_layout = QVBoxLayout(left_panel)

        # Assignment input field (text input instead of dropdown)
        assignment_label = QLabel("Assignment Name:")
        self.assignment_input = QLineEdit()
        self.assignment_input.setPlaceholderText("Enter assignment name (e.g., hw1)")

        left_layout.addWidget(assignment_label)
        left_layout.addWidget(self.assignment_input)
        left_layout.addStretch(1)

        # Right panel - File selection and submission
        right_panel = QGroupBox("File Submission")
        right_layout = QVBoxLayout(right_panel)

        # File selection buttons
        file_btns_layout = QHBoxLayout()

        add_file_btn = QPushButton("Add Files")
        add_file_btn.clicked.connect(self.add_files)

        add_dir_btn = QPushButton("Add Directory")
        add_dir_btn.clicked.connect(self.add_directory)

        clear_btn = QPushButton("Clear Selection")
        clear_btn.clicked.connect(self.clear_files)

        file_btns_layout.addWidget(add_file_btn)
        file_btns_layout.addWidget(add_dir_btn)
        file_btns_layout.addWidget(clear_btn)

        right_layout.addLayout(file_btns_layout)

        # Selected files list
        files_label = QLabel("Selected Files:")
        self.file_list = QListWidget()
        self.file_list.setSelectionMode(QListWidget.SelectionMode.ExtendedSelection)

        remove_btn = QPushButton("Remove Selected")
        remove_btn.clicked.connect(self.remove_selected_files)

        right_layout.addWidget(files_label)
        right_layout.addWidget(self.file_list)
        right_layout.addWidget(remove_btn)

        # Add panels to splitter
        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        splitter.setSizes([200, 600])

        # Submit button
        submit_btn = QPushButton("Submit Assignment")
        submit_btn.setMinimumHeight(50)
        submit_btn.setStyleSheet("font-size: 16px; font-weight: bold;")
        submit_btn.clicked.connect(self.submit_assignment)

        main_layout.addWidget(submit_btn)

        self.setup_menu()

    def setup_menu(self):
        """Set up the application menu bar."""
        menu_bar = self.menuBar()

        # Help menu
        help_menu = menu_bar.addMenu("Help")

        # About action
        about_action = help_menu.addAction("About")
        about_action.triggered.connect(self.show_about_dialog)

    def show_about_dialog(self):
        """Show the About dialog."""
        dialog = AboutWindow(self)
        dialog.exec()

    def add_files(self):
        """Open a file dialog to select multiple files"""
        files, _ = QFileDialog.getOpenFileNames(
            self, "Select Files to Submit", "", "All Files (*)"
        )

        if files:
            for file_path in files:
                if file_path not in self.selected_files:
                    self.selected_files.append(file_path)
                    self.file_list.addItem(file_path)

    def add_directory(self):
        """Open a directory dialog to select a folder"""
        directory = QFileDialog.getExistingDirectory(
            self, "Select Directory to Submit", ""
        )

        if directory:
            # Add directory itself
            if directory not in self.selected_files:
                self.selected_files.append(directory)
                self.file_list.addItem(directory)

    def remove_selected_files(self):
        """Remove selected files from the list"""
        selected_items = self.file_list.selectedItems()
        if not selected_items:
            return

        for item in selected_items:
            row = self.file_list.row(item)
            file_path = item.text()
            self.file_list.takeItem(row)
            self.selected_files.remove(file_path)

    def clear_files(self):
        """Clear all selected files"""
        self.file_list.clear()
        self.selected_files = []

    def submit_assignment(self):
                    """Submit the selected files for the chosen assignment"""
                    if not self.selected_files:
                        QMessageBox.warning(self, "Submission Error", "No files selected for submission.")
                        return

                    assignment = self.assignment_input.text().strip()
                    if not assignment:
                        QMessageBox.warning(self, "Submission Error", "Please enter an assignment name.")
                        return

                    # Confirmation dialog
                    reply = QMessageBox.question(
                        self,
                        "Confirm Submission",
                        f"Are you sure you want to submit {len(self.selected_files)} file(s) for assignment '{assignment}'?",
                        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                    )

                    if reply == QMessageBox.StandardButton.Yes:
                        try:
                            submit_files(
                                self.proxy_host,
                                self.host_to_connect,
                                self.username,
                                self.password,
                                assignment,
                                self.selected_files,
                                self.temp_dir,
                                self.ssh
                            )
                            QMessageBox.information(self, "Success", "Assignment submitted successfully!")
                        except Exception as e:
                            QMessageBox.critical(self, "Submission Error", f"Error submitting files: {str(e)}")