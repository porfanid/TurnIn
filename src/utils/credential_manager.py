"""
Credential management utilities for securely storing and retrieving user credentials
"""
import json
import keyring
from cryptography.fernet import Fernet, InvalidToken
from PyQt6.QtWidgets import QMessageBox

def generate_key():
    """
    Generate a new encryption key and store it in keyring

    Returns:
        bytes: Generated encryption key
    """
    key = Fernet.generate_key()
    keyring.set_password("turnin", "encryption_key", key.decode("utf-8"))
    return key

def get_key():
    """
    Get the encryption key from keyring or generate a new one

    Returns:
        bytes: The encryption key
    """
    key = keyring.get_password("turnin", "encryption_key")
    if key is None:
        return generate_key()
    return key.encode("utf-8") if isinstance(key, str) else key

def save_credentials(username, password):
    """
    Encrypt and save credentials

    Args:
        username (str): The username to save
        password (str): The password to save
    """
    data = {
        'username': username,
        'password': password
    }
    serialized_data = json.dumps(data).encode('utf-8')

    # Get or generate encryption key
    key = get_key()
    cipher_suite = Fernet(key)

    # Encrypt the serialized data
    encrypted_data = cipher_suite.encrypt(serialized_data)

    # Save the encrypted data to file
    with open('creds.bin', 'wb') as f:
        f.write(encrypted_data)

def load_credentials():
    """
    Load and decrypt credentials from file

    Returns:
        tuple or None: (username, password) if successful, None otherwise
    """
    try:
        with open('creds.bin', 'rb') as f:
            encrypted_data = f.read()

        # Get encryption key
        key = get_key()
        cipher_suite = Fernet(key)

        # Decrypt the data
        try:
            decrypted_data = cipher_suite.decrypt(encrypted_data)
            deserialized_data = json.loads(decrypted_data.decode('utf-8'))

            username = deserialized_data['username']
            password = deserialized_data['password']
            return username, password
        except InvalidToken:
            QMessageBox.critical(None, "Error", "Could not decrypt saved credentials.")
            return None
    except FileNotFoundError:
        return None
    except Exception as e:
        QMessageBox.critical(None, "Error", f"Error loading credentials: {str(e)}")
        return None