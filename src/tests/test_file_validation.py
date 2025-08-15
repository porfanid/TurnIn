import unittest
import os
import tempfile
from unittest.mock import patch, mock_open

# Import module to test
from src.utils.ssh import validate_files


class TestFileValidation(unittest.TestCase):

    def setUp(self):
        """Set up temporary files for testing"""
        self.temp_dir = tempfile.mkdtemp()
        
        # Create test files
        self.small_text_file = os.path.join(self.temp_dir, "small.txt")
        with open(self.small_text_file, 'w') as f:
            f.write("This is a small text file.")
        
        self.python_file = os.path.join(self.temp_dir, "script.py")
        with open(self.python_file, 'w') as f:
            f.write("print('Hello, world!')")
        
        # Create a file that appears binary (with null bytes)
        self.binary_like_file = os.path.join(self.temp_dir, "binary.dat")
        with open(self.binary_like_file, 'wb') as f:
            f.write(b"Some text\x00\x01\x02binary content")

    def tearDown(self):
        """Clean up temporary files"""
        import shutil
        shutil.rmtree(self.temp_dir)

    def test_validate_small_text_files(self):
        """Test validation of small text files (should pass)"""
        valid_files, invalid_files, error_messages = validate_files([self.small_text_file, self.python_file])
        
        self.assertEqual(len(valid_files), 2)
        self.assertEqual(len(invalid_files), 0)
        self.assertEqual(len(error_messages), 0)
        self.assertIn(self.small_text_file, valid_files)
        self.assertIn(self.python_file, valid_files)

    def test_validate_binary_file_rejection(self):
        """Test that binary files are rejected"""
        valid_files, invalid_files, error_messages = validate_files([self.binary_like_file])
        
        self.assertEqual(len(valid_files), 0)
        self.assertEqual(len(invalid_files), 1)
        self.assertEqual(len(error_messages), 1)
        self.assertIn(self.binary_like_file, invalid_files)
        self.assertIn("Binary content detected", error_messages[0])

    @patch('os.path.getsize')
    def test_validate_large_file_rejection(self, mock_getsize):
        """Test that files larger than 10MB are rejected"""
        # Mock file size to be larger than 10MB
        mock_getsize.return_value = 11 * 1024 * 1024  # 11MB
        
        valid_files, invalid_files, error_messages = validate_files([self.small_text_file])
        
        self.assertEqual(len(valid_files), 0)
        self.assertEqual(len(invalid_files), 1)
        self.assertEqual(len(error_messages), 1)
        self.assertIn(self.small_text_file, invalid_files)
        self.assertIn("File too large", error_messages[0])
        self.assertIn("11.0MB > 10MB", error_messages[0])

    def test_validate_binary_extension_rejection(self):
        """Test that files with binary extensions are rejected"""
        # Create temporary files with binary extensions
        pdf_file = os.path.join(self.temp_dir, "document.pdf")
        jpg_file = os.path.join(self.temp_dir, "image.jpg")
        exe_file = os.path.join(self.temp_dir, "program.exe")
        
        # Create the files (content doesn't matter for extension-based rejection)
        for filepath in [pdf_file, jpg_file, exe_file]:
            with open(filepath, 'w') as f:
                f.write("test content")
        
        valid_files, invalid_files, error_messages = validate_files([pdf_file, jpg_file, exe_file])
        
        self.assertEqual(len(valid_files), 0)
        self.assertEqual(len(invalid_files), 3)
        self.assertEqual(len(error_messages), 3)
        
        for error_msg in error_messages:
            self.assertIn("Binary file not allowed", error_msg)

    def test_validate_mixed_files(self):
        """Test validation with a mix of valid and invalid files"""
        # Create a binary extension file
        pdf_file = os.path.join(self.temp_dir, "document.pdf")
        with open(pdf_file, 'w') as f:
            f.write("fake pdf content")
        
        files_to_validate = [self.small_text_file, self.python_file, pdf_file, self.binary_like_file]
        valid_files, invalid_files, error_messages = validate_files(files_to_validate)
        
        self.assertEqual(len(valid_files), 2)
        self.assertEqual(len(invalid_files), 2)
        self.assertEqual(len(error_messages), 2)
        
        self.assertIn(self.small_text_file, valid_files)
        self.assertIn(self.python_file, valid_files)
        self.assertIn(pdf_file, invalid_files)
        self.assertIn(self.binary_like_file, invalid_files)

    def test_validate_empty_list(self):
        """Test validation with empty file list"""
        valid_files, invalid_files, error_messages = validate_files([])
        
        self.assertEqual(len(valid_files), 0)
        self.assertEqual(len(invalid_files), 0)
        self.assertEqual(len(error_messages), 0)

    @patch('os.path.getsize')
    def test_validate_file_access_error(self, mock_getsize):
        """Test handling of file access errors"""
        mock_getsize.side_effect = OSError("Permission denied")
        
        valid_files, invalid_files, error_messages = validate_files([self.small_text_file])
        
        self.assertEqual(len(valid_files), 0)
        self.assertEqual(len(invalid_files), 1)
        self.assertEqual(len(error_messages), 1)
        self.assertIn("Cannot access file", error_messages[0])
        self.assertIn("Permission denied", error_messages[0])


if __name__ == '__main__':
    unittest.main()