import unittest
import os
import tempfile
import json
from unittest.mock import patch, MagicMock
from cryptography.fernet import Fernet

# Import module to test
from src.utils.credential_manager import (
    get_credentials_path, generate_key, get_key,
    save_credentials, load_credentials, clear_credentials
)

class TestCredentialManager(unittest.TestCase):

    @patch('src.utils.credential_manager.keyring')
    def test_generate_key(self, mock_keyring):
        """Test that generate_key generates a valid Fernet key and stores it"""
        # Call the function
        key = generate_key()

        # Verify key is valid Fernet key
        self.assertEqual(len(key), 44)  # Fernet keys are 44 bytes when base64 encoded

        # Verify the key was stored in keyring
        mock_keyring.set_password.assert_called_once_with(
            "turnin", "encryption_key", key.decode("utf-8"))

    @patch('src.utils.credential_manager.keyring')
    def test_get_key_existing(self, mock_keyring):
        """Test that get_key returns the existing key from keyring"""
        # Setup mock
        mock_keyring.get_password.return_value = "test_key_data"

        # Call the function
        key = get_key()

        # Verify the returned key matches
        self.assertEqual(key, b"test_key_data")
        mock_keyring.get_password.assert_called_once_with("turnin", "encryption_key")

    @patch('src.utils.credential_manager.keyring')
    @patch('src.utils.credential_manager.generate_key')
    def test_get_key_new(self, mock_generate, mock_keyring):
        """Test that get_key generates a new key if none exists"""
        # Setup mock
        mock_keyring.get_password.return_value = None
        mock_generate.return_value = b"new_generated_key"

        # Call the function
        key = get_key()

        # Verify a new key was generated
        self.assertEqual(key, b"new_generated_key")
        mock_keyring.get_password.assert_called_once_with("turnin", "encryption_key")
        mock_generate.assert_called_once()

    @patch('src.utils.credential_manager.get_credentials_path')
    @patch('src.utils.credential_manager.get_key')
    def test_save_credentials(self, mock_get_key, mock_get_path):
        """Test saving credentials to encrypted file"""
        # Setup mocks
        temp_file = tempfile.NamedTemporaryFile(delete=False)
        mock_get_path.return_value = temp_file.name
        mock_get_key.return_value = Fernet.generate_key()  # Generate real key for testing

        try:
            # Call the function
            save_credentials("testuser", "testpass")

            # Verify file was written
            self.assertTrue(os.path.exists(temp_file.name))

            # Verify content can be decrypted
            with open(temp_file.name, 'rb') as f:
                encrypted_data = f.read()

            # Decrypt and verify
            cipher_suite = Fernet(mock_get_key.return_value)
            decrypted = cipher_suite.decrypt(encrypted_data)
            data = json.loads(decrypted.decode('utf-8'))

            self.assertEqual(data['username'], "testuser")
            self.assertEqual(data['password'], "testpass")

        finally:
            # Clean up
            if os.path.exists(temp_file.name):
                os.unlink(temp_file.name)

    @patch('src.utils.credential_manager.QMessageBox')
    @patch('src.utils.credential_manager.get_credentials_path')
    @patch('src.utils.credential_manager.get_key')
    def test_load_credentials(self, mock_get_key, mock_get_path, mock_msgbox):
        """Test loading credentials from encrypted file"""
        # Setup mocks and create test encrypted file
        temp_file = tempfile.NamedTemporaryFile(delete=False)
        mock_get_path.return_value = temp_file.name

        # Generate a real key for encryption/decryption
        key = Fernet.generate_key()
        mock_get_key.return_value = key

        # Create test data
        test_data = {'username': 'testuser', 'password': 'testpass'}
        serialized = json.dumps(test_data).encode('utf-8')

        # Encrypt and save test data
        cipher_suite = Fernet(key)
        encrypted = cipher_suite.encrypt(serialized)
        with open(temp_file.name, 'wb') as f:
            f.write(encrypted)

        try:
            # Call the function
            username, password = load_credentials()

            # Verify results
            self.assertEqual(username, 'testuser')
            self.assertEqual(password, 'testpass')

        finally:
            # Clean up
            if os.path.exists(temp_file.name):
                os.unlink(temp_file.name)

    @patch('src.utils.credential_manager.QMessageBox')
    @patch('src.utils.credential_manager.get_credentials_path')
    def test_load_credentials_missing_file(self, mock_get_path, mock_msgbox):
        """Test loading credentials when file doesn't exist"""
        # Set the path to a file that doesn't exist
        mock_get_path.return_value = "/path/that/doesnt/exist"

        # Call the function
        result = load_credentials()

        # Verify results
        self.assertIsNone(result)

    @patch('src.utils.credential_manager.keyring')
    @patch('src.utils.credential_manager.get_credentials_path')
    def test_clear_credentials(self, mock_get_path, mock_keyring):
        """Test clearing saved credentials"""
        # Create a temporary file
        temp_file = tempfile.NamedTemporaryFile(delete=False)
        mock_get_path.return_value = temp_file.name
        
        try:
            # Verify file exists
            self.assertTrue(os.path.exists(temp_file.name))
            
            # Call clear_credentials
            result = clear_credentials()
            
            # Verify file was deleted
            self.assertFalse(os.path.exists(temp_file.name))
            
            # Verify keyring deletion was attempted
            mock_keyring.delete_password.assert_called_once_with("turnin", "encryption_key")
            
            # Verify function returned True
            self.assertTrue(result)
            
        finally:
            # Clean up in case the function failed
            if os.path.exists(temp_file.name):
                os.unlink(temp_file.name)

    @patch('src.utils.credential_manager.QMessageBox')
    @patch('src.utils.credential_manager.get_credentials_path')
    @patch('src.utils.credential_manager.get_key')
    def test_load_credentials_invalid_token(self, mock_get_key, mock_get_path, mock_msgbox):
        """Test loading credentials with invalid token shows improved error message"""
        # Setup mocks and create test file with invalid encrypted data
        temp_file = tempfile.NamedTemporaryFile(delete=False)
        mock_get_path.return_value = temp_file.name
        
        # Write invalid encrypted data
        with open(temp_file.name, 'wb') as f:
            f.write(b"invalid_encrypted_data")
        
        # Generate a real key
        key = Fernet.generate_key()
        mock_get_key.return_value = key
        
        try:
            # Call the function
            result = load_credentials()
            
            # Verify result is None
            self.assertIsNone(result)
            
            # Verify improved error message was shown
            mock_msgbox.critical.assert_called_once()
            call_args = mock_msgbox.critical.call_args[0]
            
            # Check title is in Greek
            self.assertEqual(call_args[1], "Σφάλμα Διαπιστευτηρίων")
            
            # Check message contains expected Greek phrases
            message = call_args[2]
            self.assertIn("διαπιστευτήρια δεν μπορούν να αναγνωστούν", message)
            self.assertIn("συνδεθείτε ξανά", message)
            
        finally:
            # Clean up
            if os.path.exists(temp_file.name):
                os.unlink(temp_file.name)

if __name__ == '__main__':
    unittest.main()