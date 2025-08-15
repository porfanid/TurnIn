"""
Main window for the TurnIn application
"""
import os
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QPushButton, QLabel, QComboBox, QFileDialog,
                             QListWidget, QMessageBox, QSplitter, QGroupBox, QScrollArea, QLineEdit, QProgressBar)
from PyQt6.QtCore import Qt, QObject, pyqtSignal, QThread
from src.utils.ssh import submit_files, connect_to_proxy, validate_files
from src.ui.about_window import AboutWindow

class UploadWorker(QObject):
    """Worker to handle file uploads in a background thread"""
    progress_updated = pyqtSignal(float, str)
    upload_finished = pyqtSignal(bool, str)
    command_output = pyqtSignal(str)

    def __init__(self, proxy_host, host_to_connect, username, password,
                 assignment, files, temp_dir, ssh=None):
        super().__init__()
        self.proxy_host = proxy_host
        self.host_to_connect = host_to_connect
        self.username = username
        self.password = password
        self.assignment = assignment
        self.files = files
        self.temp_dir = temp_dir
        self.ssh = ssh

    def run(self):
        """Run the upload process"""
        try:
            success, output = submit_files(
                self.proxy_host,
                self.host_to_connect,
                self.username,
                self.password,
                self.assignment,
                self.files,
                self.temp_dir,
                self.ssh,
                progress_callback=self.update_progress
            )

            # Emit the command output
            self.command_output.emit(output)

            if success:
                self.upload_finished.emit(True, "Please check the output message of the turnin for any errors")
            else:
                self.upload_finished.emit(False, f"Error during submission: {output}")
        except Exception as e:
            self.upload_finished.emit(False, f"Error submitting files: {str(e)}")

    def update_progress(self, percent, message):
        """Update progress display"""
        self.progress_updated.emit(percent, message)


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
        self.submit_btn = QPushButton("Submit Assignment")  # Store as self.submit_btn
        self.submit_btn.setMinimumHeight(50)
        self.submit_btn.setStyleSheet("font-size: 16px; font-weight: bold;")
        self.submit_btn.clicked.connect(self.submit_assignment)

        main_layout.addWidget(self.submit_btn)

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

        # Validate files before submission
        valid_files, invalid_files, error_messages = validate_files(self.selected_files)
        
        if invalid_files:
            # Show file validation errors
            error_dialog = QMessageBox(self)
            error_dialog.setIcon(QMessageBox.Icon.Warning)
            error_dialog.setWindowTitle("File Validation Errors")
            
            if valid_files:
                # Some files are valid
                error_dialog.setText(f"Found {len(invalid_files)} invalid file(s). Do you want to continue with the {len(valid_files)} valid file(s)?")
                error_dialog.setDetailedText("\n".join(error_messages))
                error_dialog.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
                error_dialog.setDefaultButton(QMessageBox.StandardButton.No)
                
                reply = error_dialog.exec()
                if reply != QMessageBox.StandardButton.Yes:
                    return
                
                # Update files list to only include valid files
                files_to_submit = valid_files
            else:
                # No valid files
                error_dialog.setText("All selected files are invalid and cannot be submitted.")
                error_dialog.setDetailedText("\n".join(error_messages))
                error_dialog.setStandardButtons(QMessageBox.StandardButton.Ok)
                error_dialog.exec()
                return
        else:
            files_to_submit = valid_files

        # Confirmation dialog
        reply = QMessageBox.question(
            self,
            "Confirm Submission",
            f"Are you sure you want to submit {len(files_to_submit)} file(s) for assignment '{assignment}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            # Setup UI for progress
            self.setup_progress_ui()
            self.submit_btn.setEnabled(False)

            # Create output area if it doesn't exist
            if not hasattr(self, 'output_area'):
                self.output_area = QScrollArea()
                self.output_text = QLabel()
                self.output_text.setWordWrap(True)
                self.output_area.setWidget(self.output_text)
                self.output_area.setWidgetResizable(True)
                main_layout = self.centralWidget().layout()
                main_layout.insertWidget(main_layout.count() - 1, self.output_area)
                self.output_area.hide()

            # Create worker and thread
            self.thread = QThread()
            self.worker = UploadWorker(
                self.proxy_host,
                self.host_to_connect,
                self.username,
                self.password,
                assignment,
                files_to_submit,  # Use validated files
                self.temp_dir,
                self.ssh
            )

            # Set up connections
            self.worker.moveToThread(self.thread)
            self.thread.started.connect(self.worker.run)

            # Use queued connections for thread safety
            self.worker.progress_updated.connect(self.update_progress, Qt.ConnectionType.QueuedConnection)
            self.worker.upload_finished.connect(self.handle_upload_finished, Qt.ConnectionType.QueuedConnection)
            self.worker.command_output.connect(self.display_command_output, Qt.ConnectionType.QueuedConnection)

            # Clean up connections
            self.worker.upload_finished.connect(self.thread.quit)
            self.worker.upload_finished.connect(self.worker.deleteLater)
            self.thread.finished.connect(self.thread.deleteLater)
            # Start the thread
            self.thread.start()

    def display_command_output(self, text):
        """Display command output in the output area"""
        self.output_text.setText(text)
        self.output_area.show()

    def setup_progress_ui(self):
        """Set up progress bar and status label"""
        # Create progress widget if it doesn't exist
        if not hasattr(self, 'progress_widget'):
            self.progress_widget = QWidget(self)
            progress_layout = QVBoxLayout(self.progress_widget)

            # Progress bar
            self.progress_bar = QProgressBar()
            self.progress_bar.setRange(0, 100)
            self.progress_bar.setValue(0)

            # Status label
            self.status_label = QLabel("Preparing to upload...")

            # Add to layout
            progress_layout.addWidget(self.status_label)
            progress_layout.addWidget(self.progress_bar)

            # Add to main layout - place before the submit button
            main_layout = self.centralWidget().layout()
            main_layout.insertWidget(main_layout.count() - 1, self.progress_widget)
        # Show the progress widget
        self.progress_widget.show()
        # Disable submit button during upload

    def update_progress(self, percent, message):
        """Update progress bar and status message"""
        self.progress_bar.setValue(int(percent))
        self.status_label.setText(message)

    def handle_upload_finished(self, success, message):
        """Handle upload completion"""
        # Re-enable submit button
        self.submit_btn.setEnabled(True)

        if success:
            # Parse message to see if there were warnings
            if message.startswith("Warning:"):
                # Success but with warnings
                QMessageBox.information(self, "Success with Warnings", message)
            else:
                QMessageBox.information(self, "Success", message)
        else:
            # Create a detailed error dialog
            error_dialog = QMessageBox(self)
            error_dialog.setIcon(QMessageBox.Icon.Critical)
            error_dialog.setWindowTitle("Submission Error")
            
            # Split message into main message and technical details if available
            parts = message.split("\n\nTechnical details:\n", 1)
            main_message = parts[0]
            
            error_dialog.setText(main_message)
            
            if len(parts) > 1:
                error_dialog.setDetailedText(parts[1])
            
            error_dialog.setStandardButtons(QMessageBox.StandardButton.Ok)
            error_dialog.exec()