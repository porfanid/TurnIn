"""
Interactive dialog for handling turnin command execution with user prompts
"""
import re
from PyQt6.QtWidgets import (QDialog, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                            QTextEdit, QLineEdit, QLabel, QGroupBox, QScrollArea)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont


class InteractiveTurninDialog(QDialog):
    """Dialog for interactive turnin command execution"""
    
    # Signals for communication with the SSH worker
    user_response = pyqtSignal(str)  # Emitted when user provides a response
    dialog_closed = pyqtSignal()     # Emitted when dialog is closed
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Turnin Command Execution")
        self.setModal(True)
        self.resize(700, 500)
        
        # Track if we're waiting for user input
        self.waiting_for_input = False
        
        self.init_ui()
        
    def init_ui(self):
        """Initialize the user interface"""
        layout = QVBoxLayout(self)
        
        # Title label
        title = QLabel("Turnin Command Output")
        title.setStyleSheet("font-size: 16px; font-weight: bold; padding: 10px;")
        layout.addWidget(title)
        
        # Output display area
        output_group = QGroupBox("Command Output")
        output_layout = QVBoxLayout(output_group)
        
        self.output_display = QTextEdit()
        self.output_display.setReadOnly(True)
        self.output_display.setFont(QFont("Courier", 10))
        self.output_display.setStyleSheet("background-color: #f8f8f8; border: 1px solid #ccc;")
        output_layout.addWidget(self.output_display)
        
        layout.addWidget(output_group)
        
        # User input area (initially hidden)
        self.input_group = QGroupBox("Your Response")
        input_layout = QVBoxLayout(self.input_group)
        
        # Prompt label
        self.prompt_label = QLabel("")
        self.prompt_label.setWordWrap(True)
        self.prompt_label.setStyleSheet("font-weight: bold; color: #0066cc;")
        input_layout.addWidget(self.prompt_label)
        
        # Yes/No buttons (for yes/no questions)
        self.yn_widget = QWidget()
        yn_layout = QHBoxLayout(self.yn_widget)
        yn_layout.setContentsMargins(0, 0, 0, 0)
        
        self.yes_button = QPushButton("Yes")
        self.no_button = QPushButton("No")
        self.yes_button.clicked.connect(lambda: self.send_response("y"))
        self.no_button.clicked.connect(lambda: self.send_response("n"))
        
        yn_layout.addWidget(self.yes_button)
        yn_layout.addWidget(self.no_button)
        yn_layout.addStretch()
        
        input_layout.addWidget(self.yn_widget)
        
        # Text input (for other questions)
        self.text_input_widget = QWidget()
        text_layout = QHBoxLayout(self.text_input_widget)
        text_layout.setContentsMargins(0, 0, 0, 0)
        
        self.text_input = QLineEdit()
        self.text_input.returnPressed.connect(self.send_text_response)
        
        self.send_button = QPushButton("Send")
        self.send_button.clicked.connect(self.send_text_response)
        
        text_layout.addWidget(self.text_input)
        text_layout.addWidget(self.send_button)
        
        input_layout.addWidget(self.text_input_widget)
        
        # Initially hide input area
        self.input_group.setVisible(False)
        layout.addWidget(self.input_group)
        
        # Control buttons
        button_layout = QHBoxLayout()
        
        self.close_button = QPushButton("Close")
        self.close_button.clicked.connect(self.close_dialog)
        
        button_layout.addStretch()
        button_layout.addWidget(self.close_button)
        
        layout.addLayout(button_layout)
        
    def add_output(self, text):
        """Add text to the output display"""
        self.output_display.append(text)
        # Auto-scroll to bottom
        scrollbar = self.output_display.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
        
    def show_prompt(self, prompt_text):
        """Show a prompt and wait for user input"""
        self.waiting_for_input = True
        self.prompt_label.setText(f"Prompt: {prompt_text}")
        
        # Detect if this is a yes/no question
        if self.is_yes_no_prompt(prompt_text):
            self.yn_widget.setVisible(True)
            self.text_input_widget.setVisible(False)
            self.yes_button.setFocus()
        else:
            self.yn_widget.setVisible(False)
            self.text_input_widget.setVisible(True)
            self.text_input.setFocus()
            self.text_input.clear()
        
        self.input_group.setVisible(True)
        
    def is_yes_no_prompt(self, text):
        """Detect if a prompt is asking for yes/no response"""
        # Look for common yes/no patterns
        yes_no_patterns = [
            r'\[y/n\]',
            r'\[Y/N\]',
            r'\[yes/no\]',
            r'\[Yes/No\]',
            r'\(y/n\)',
            r'\(Y/N\)',
            r'\(yes/no\)',
            r'\(Yes/No\)',
            r'y/n',
            r'Y/N',
            r'yes/no',
            r'Yes/No'
        ]
        
        for pattern in yes_no_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return True
                
        # Also check for common yes/no question phrases
        if any(phrase in text.lower() for phrase in [
            'continue?', 'proceed?', 'confirm?', 'sure?', 'ok?', 'submit?', 'turn in?'
        ]):
            return True
            
        return False
        
    def send_response(self, response):
        """Send a yes/no response"""
        if self.waiting_for_input:
            self.waiting_for_input = False
            self.input_group.setVisible(False)
            self.add_output(f"> {response}")
            self.user_response.emit(response)
            
    def send_text_response(self):
        """Send a text response"""
        if self.waiting_for_input:
            response = self.text_input.text().strip()
            if response:  # Only send non-empty responses
                self.waiting_for_input = False
                self.input_group.setVisible(False)
                self.add_output(f"> {response}")
                self.user_response.emit(response)
                
    def close_dialog(self):
        """Close the dialog"""
        self.dialog_closed.emit()
        self.accept()
        
    def show_completion_message(self, success, message):
        """Show completion message and enable close"""
        if success:
            self.add_output(f"\n✓ Success: {message}")
        else:
            self.add_output(f"\n✗ Error: {message}")
            
        # Hide input area if still visible
        self.input_group.setVisible(False)
        self.waiting_for_input = False
        
    def closeEvent(self, event):
        """Handle window close event"""
        self.dialog_closed.emit()
        super().closeEvent(event)
