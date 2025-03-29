"""
Encryption utilities for securely storing user credentials
"""
import json
import base64
import keyring
from cryptography.fernet import Fernet, InvalidToken
from PyQt6.QtWidgets import QMessageBox
import sys


def generate_key():
    """
    Generate a new encryption key and store it securely in the system keyring.

    Returns:
        bytes: The generated encryption key
    """
    key = Fernet.generate_key()
    keyring.set_password("turnin", "encryption_key", key.decode("utf-8"))
    return key


def get_key():
    """
    Retrieve the encryption key from the system keyring or generate a new one.

    Returns:
        bytes: The encryption key
    """
    key = keyring.get_password("turnin", "encryption_key")
    if key is None:
        key = generate_key()
    else:
        key = key.encode("utf-8")
    return key


def encrypt_credentials(username, password):
    """
    Encrypt user credentials and save them to a file.

    Args:
        username (str): The username to encrypt
        password (str): The password to encrypt

    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Prepare data
        data = {
            'username': username,
            'password': password
        }
        serialized_data = json.dumps(data).encode('utf-8')

        # Encrypt data
        key = get_key()
        cipher_suite = Fernet(key)
        encrypted_data = cipher_suite.encrypt(serialized_data)

        # Save to file
        with open('creds.bin', 'wb') as f:
            f.write(encrypted_data)

        return True
    except Exception as e:
        # Report error
        print(f"Error encrypting credentials: {e}")
        return False


def decrypt_credentials():
    """
    Decrypt user credentials from the credentials file.

    Returns:
        tuple: (username, password) if successful, (None, None) otherwise
    """
    try:
        with open('creds.bin', 'rb') as f:
            encrypted_data = f.read()

        # Retrieve encryption key
        key = get_key()
        cipher_suite = Fernet(key)

        # Decrypt the encrypted data
        try:
            decrypted_data = cipher_suite.decrypt(encrypted_data)
        except InvalidToken:
            msg = QMessageBox()
            msg.setWindowTitle("Error")
            msg.setText("Failed to decrypt the stored credentials.\nPlease log in again.")
            msg.setIcon(QMessageBox.Icon.Critical)
            msg.exec()
            return None, None

        # Deserialize the decrypted data
        deserialized_data = json.loads(decrypted_data.decode('utf-8'))

        # Access username and password
        username = deserialized_data['username']
        password = deserialized_data['password']
        return username, password
    except FileNotFoundError:
        return None, None
    except Exception as e:
        print(f"Error decrypting credentials: {e}")
        return None, None