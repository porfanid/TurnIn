"""
SSH utilities for handling connections and file transfers
"""
import os
import socket
import paramiko
import sshtunnel
import hashlib
import base64

# Try to import PyQt6 widgets, but handle gracefully if not available
try:
    from PyQt6.QtWidgets import QMessageBox, QDialog, QVBoxLayout, QLabel, QPushButton, QHBoxLayout, QApplication
    PYQT_AVAILABLE = True
except ImportError:
    PYQT_AVAILABLE = False


class FallbackHostKeyPolicy(paramiko.MissingHostKeyPolicy):
    """
    Fallback policy that uses hardcoded keys when secure verification fails
    """
    
    def __init__(self):
        try:
            from config import SSH_KEYS
            self.ssh_keys = SSH_KEYS
        except ImportError:
            # If config module is not available (e.g., during testing), use empty list
            self.ssh_keys = []
    
    def missing_host_key(self, client, hostname, key):
        """
        Check if the host key matches any of our known hardcoded keys
        """
        key_type = key.get_name()
        key_data = key.get_base64()
        
        # Check against hardcoded keys
        for host, stored_type, stored_key in self.ssh_keys:
            if host == hostname and stored_type == key_type and stored_key == key_data:
                print(f"Using hardcoded key for {hostname} (fallback mode)")
                return  # Accept the key
        
        # If no match found, reject
        raise paramiko.SSHException(f"Host key verification failed for {hostname} - no matching hardcoded key found")


class SecureHostKeyPolicy(paramiko.MissingHostKeyPolicy):
    """
    Custom host key policy that prompts user for verification and saves accepted keys
    """
    
    def __init__(self, fallback_policy=None):
        self.fallback_policy = fallback_policy or FallbackHostKeyPolicy()
    
    def missing_host_key(self, client, hostname, key):
        """
        Called when an unknown host key is encountered.
        Shows the key fingerprint to the user and asks for confirmation.
        Falls back to hardcoded keys if verification fails or times out.
        """
        try:
            # Try secure verification first
            self._secure_verification(client, hostname, key)
        except (paramiko.SSHException, Exception) as e:
            print(f"Secure verification failed for {hostname}: {e}")
            print("Falling back to hardcoded key verification...")
            # Fall back to hardcoded keys
            self.fallback_policy.missing_host_key(client, hostname, key)
    
    def _secure_verification(self, client, hostname, key):
        """
        Perform secure host key verification with user interaction
        """
        # Generate key fingerprint
        key_type = key.get_name()
        key_data = key.get_base64()
        
        # Generate SHA256 fingerprint (modern standard)
        key_bytes = base64.b64decode(key_data)
        sha256_hash = hashlib.sha256(key_bytes).digest()
        sha256_fingerprint = base64.b64encode(sha256_hash).decode().rstrip('=')
        
        # Generate MD5 fingerprint (legacy, for compatibility)
        md5_hash = hashlib.md5(key_bytes).digest()
        md5_fingerprint = ':'.join(f'{b:02x}' for b in md5_hash)
        
        # Create verification dialog
        if PYQT_AVAILABLE:
            try:
                if QApplication.instance() is not None:
                    # GUI mode - show dialog with timeout
                    return self._gui_prompt(hostname, key_type, sha256_fingerprint, md5_fingerprint, key)
                else:
                    # Console mode fallback
                    return self._console_prompt(hostname, key_type, sha256_fingerprint, md5_fingerprint, key)
            except Exception as e:
                print(f"GUI prompt failed: {e}")
                # Fallback to console if GUI fails
                return self._console_prompt(hostname, key_type, sha256_fingerprint, md5_fingerprint, key)
        else:
            # PyQt6 not available - use console prompt
            return self._console_prompt(hostname, key_type, sha256_fingerprint, md5_fingerprint, key)
    
    def _gui_prompt(self, hostname, key_type, sha256_fingerprint, md5_fingerprint, key):
        """
        GUI-based prompt for host key verification with timeout
        """
        dialog = QDialog()
        dialog.setWindowTitle("SSH Host Key Verification")
        dialog.setModal(True)
        
        layout = QVBoxLayout()
        
        # Warning message
        warning_label = QLabel(
            f"<b>WARNING: Unknown SSH host key for {hostname}</b><br><br>"
            f"The authenticity of host '{hostname}' can't be established.<br>"
            f"Key type: {key_type}<br><br>"
            f"SHA256 fingerprint: {sha256_fingerprint}<br>"
            f"MD5 fingerprint: {md5_fingerprint}<br><br>"
            f"Are you sure you want to continue connecting and save this key?"
        )
        warning_label.setWordWrap(True)
        layout.addWidget(warning_label)
        
        # Button layout
        button_layout = QHBoxLayout()
        accept_button = QPushButton("Accept and Save")
        reject_button = QPushButton("Reject")
        fallback_button = QPushButton("Use Hardcoded Keys")
        
        button_layout.addWidget(accept_button)
        button_layout.addWidget(fallback_button)
        button_layout.addWidget(reject_button)
        layout.addLayout(button_layout)
        
        dialog.setLayout(layout)
        
        # Connect button signals
        result = [None]  # Use list to allow modification in nested function
        
        def accept_key():
            result[0] = 'accept'
            dialog.accept()
        
        def reject_key():
            result[0] = 'reject'
            dialog.reject()
        
        def use_fallback():
            result[0] = 'fallback'
            dialog.reject()
        
        accept_button.clicked.connect(accept_key)
        reject_button.clicked.connect(reject_key)
        fallback_button.clicked.connect(use_fallback)
        
        # Show dialog and get result with timeout handling
        dialog_result = dialog.exec()
        
        if result[0] == 'accept':
            # User accepted - save the key
            self._save_host_key(hostname, key)
            return
        elif result[0] == 'fallback':
            # User chose to use hardcoded keys
            raise paramiko.SSHException("User chose fallback to hardcoded keys")
        else:
            # User rejected or dialog was cancelled
            raise paramiko.SSHException(f"Host key verification rejected for {hostname}")
        
    def _console_prompt(self, hostname, key_type, sha256_fingerprint, md5_fingerprint, key):
        """
        Console-based prompt for host key verification
        """
        print(f"\nWARNING: Unknown SSH host key for {hostname}")
        print(f"The authenticity of host '{hostname}' can't be established.")
        print(f"Key type: {key_type}")
        print(f"SHA256 fingerprint: {sha256_fingerprint}")
        print(f"MD5 fingerprint: {md5_fingerprint}")
        
        while True:
            response = input("Are you sure you want to continue connecting? (yes/no/fallback): ").lower().strip()
            if response in ['yes', 'y']:
                # Save the key and continue
                self._save_host_key(hostname, key)
                return
            elif response in ['no', 'n']:
                raise paramiko.SSHException(f"Host key verification rejected for {hostname}")
            elif response in ['fallback', 'f']:
                raise paramiko.SSHException("User chose fallback to hardcoded keys")
            else:
                print("Please type 'yes', 'no', or 'fallback'")
    
    def _save_host_key(self, hostname, key):
        """
        Save the accepted host key to the user's known_hosts file
        """
        try:
            # Get the user's known_hosts file path
            known_hosts_path = os.path.expanduser("~/.ssh/known_hosts")
            
            # Ensure .ssh directory exists
            ssh_dir = os.path.dirname(known_hosts_path)
            os.makedirs(ssh_dir, mode=0o700, exist_ok=True)
            
            # Format the host key entry
            key_type = key.get_name()
            key_data = key.get_base64()
            host_key_entry = f"{hostname} {key_type} {key_data}\n"
            
            # Append to known_hosts file
            with open(known_hosts_path, 'a') as f:
                f.write(host_key_entry)
            
            print(f"Host key for {hostname} saved to {known_hosts_path}")
            
        except Exception as e:
            print(f"Warning: Could not save host key to known_hosts: {e}")


def add_ssh_keys(ssh):
    """
    Add known SSH host keys to the client using secure practices

    Args:
        ssh (paramiko.SSHClient): The SSH client to configure
    """
    # Load system and user known_hosts files
    try:
        # Load system-wide known_hosts
        ssh.load_system_host_keys()
    except Exception as e:
        print(f"Warning: Could not load system host keys: {e}")
    
    try:
        # Load user's known_hosts file
        user_known_hosts = os.path.expanduser("~/.ssh/known_hosts")
        if os.path.exists(user_known_hosts):
            ssh.load_host_keys(user_known_hosts)
    except Exception as e:
        print(f"Warning: Could not load user host keys: {e}")
    
    # Set secure host key policy
    ssh.set_missing_host_key_policy(SecureHostKeyPolicy())

def get_available_server(ssh):
    """
    Find an available server from the cluster

    Args:
        ssh (paramiko.SSHClient): SSH client connected to proxy

    Returns:
        str or None: Hostname of available server or None if no server is available
    """
    _, ssh_stdout, _ = ssh.exec_command("rupt")
    servers = ssh_stdout.readlines()
    for server in servers:
        server = server.split()
        host_name = server[0]
        host_is_up = (server[1] == "up")
        if host_is_up and ("dl" in host_name):
            return host_name
    return None

def connect_to_proxy(username, password, proxy_host):
    """
    Connect to the SSH proxy

    Args:
        username (str): SSH username
        password (str): SSH password
        proxy_host (str): Proxy hostname

    Returns:
        tuple: (success (bool), host_to_connect (str), ssh_client (paramiko.SSHClient))
    """
    ssh = None
    try:
        ssh = paramiko.SSHClient()
        add_ssh_keys(ssh)
        
        # Set connection timeout to prevent hanging
        ssh.connect(
            proxy_host, 
            username=username, 
            password=password, 
            timeout=15,  # Reduced to 15 second connection timeout
            banner_timeout=10  # Reduced to 10 second banner timeout
        )

        # Find available host
        host_to_connect = get_available_server(ssh)
        if not host_to_connect:
            if PYQT_AVAILABLE:
                try:
                    QMessageBox.critical(None, "Error", "No available hosts found. Aborting...")
                except:
                    print("Error: No available hosts found. Aborting...")
            else:
                print("Error: No available hosts found. Aborting...")
            return False, None, None

        return True, host_to_connect, ssh
    except paramiko.AuthenticationException:
        if ssh:
            try:
                ssh.close()
            except:
                pass
        return False, None, None
    except paramiko.ssh_exception.SSHException as e:
        if ssh:
            try:
                ssh.close()
            except:
                pass
        # Handle specific banner timeout errors more gracefully
        if "banner" in str(e).lower() or "timeout" in str(e).lower():
            error_msg = f"SSH connection timed out. Please check your network connection and try again."
        else:
            error_msg = f"SSH Error: {e}"
        
        if PYQT_AVAILABLE:
            try:
                QMessageBox.critical(None, "SSH Error", error_msg)
            except:
                print(error_msg)
        else:
            print(error_msg)
        return False, None, None
    except (socket.timeout, OSError, ConnectionError) as e:
        if ssh:
            try:
                ssh.close()
            except:
                pass
        error_msg = f"Network connection failed: {e}"
        if PYQT_AVAILABLE:
            try:
                QMessageBox.critical(None, "Connection Error", error_msg)
            except:
                print(error_msg)
        else:
            print(error_msg)
        return False, None, None
    except Exception as e:
        if ssh:
            try:
                ssh.close()
            except:
                pass
        error_msg = f"Connection Error: {e}"
        if PYQT_AVAILABLE:
            try:
                QMessageBox.critical(None, "Connection Error", error_msg)
            except:
                print(error_msg)
        else:
            print(error_msg)
        return False, None, None

def upload_files(files, username, password, ssh, host, temp_dir, progress_callback=None):
    """Upload files with progress reporting using existing SSH connection"""
    if not files:
        return None, None

    # Get home directory using existing SSH connection
    _, ssh_stdout, _ = ssh.exec_command("pwd")
    home_dir = ssh_stdout.readlines()[0].strip()

    # Use existing SSH connection to create SFTP channel (avoids multiple connections)
    sftp = ssh.open_sftp()

    remote_dir = f"{home_dir}/{temp_dir}/"

    # Try to create directory (ignore if exists)
    try:
        sftp.mkdir(remote_dir)
    except:
        pass

    # Safe progress reporting
    if progress_callback:
        try:
            progress_callback(20, "Starting file uploads...")
        except Exception:
            pass  # Ignore callback errors

    remote_paths = []
    total_files = len(files)
    progress_range = 60  # Progress from 20% to 80%

    for idx, localpath in enumerate(files):
        name = os.path.basename(localpath)
        filepath = f"{remote_dir}{name}"

        if progress_callback:
            current_progress = 20 + (idx * progress_range / total_files)
            try:
                progress_callback(current_progress, f"Uploading file {idx+1}/{total_files}: {name}")
            except Exception:
                pass  # Ignore callback errors

        # Upload the file
        try:
            sftp.put(localpath, filepath)
            remote_paths.append(name)

            if progress_callback:
                current_progress = 20 + ((idx + 1) * progress_range / total_files)
                try:
                    progress_callback(current_progress, f"Uploaded {idx+1}/{total_files} files")
                except Exception:
                    pass
        except Exception as e:
            print(f"Upload error: {str(e)}")

    # Close SFTP connection
    try:
        sftp.close()
    except:
        pass

    return remote_dir, remote_paths


def submit_files(proxy_host, host_to_connect, username, password, assignment,
                 file_list, temp_dir, ssh_client=None, progress_callback=None):
    """Submit files to the assignment submission server"""
    # Use existing SSH client or create a new one
    ssh = ssh_client or connect_to_proxy(username, password, proxy_host)[2]

    if progress_callback:
        try:
            progress_callback(10, "Connected to SSH server...")
        except Exception:
            pass

    # Upload files to the server
    remote_dir, remote_paths = upload_files(file_list, username, password, ssh, proxy_host, temp_dir, progress_callback)

    if not remote_dir or not remote_paths:
        return False, "Failed to upload files"

    if progress_callback:
        try:
            progress_callback(80, "Files uploaded. Creating SSH tunnel...")
        except Exception:
            pass

    # Run the turnin command through SSH tunnel
    try:
        # Create SSH tunnel to the target host through the proxy
        with sshtunnel.SSHTunnelForwarder(
            (proxy_host, 22),
            ssh_username=username,
            ssh_password=password,
            remote_bind_address=(host_to_connect, 22),
            local_bind_address=('127.0.0.1', 0)  # Let system choose port
        ) as tunnel:
            # Create a new SSH client to connect to the tunneled host
            target_ssh = paramiko.SSHClient()
            add_ssh_keys(target_ssh)

            # Connect through the tunnel with timeout
            target_ssh.connect('127.0.0.1',
                             port=tunnel.local_bind_port,
                             username=username,
                             password=password,
                             timeout=15,  # Reduced to 15 second connection timeout
                             banner_timeout=10)  # Reduced to 10 second banner timeout

            if progress_callback:
                try:
                    progress_callback(85, "Tunnel created. Running turnin command...")
                except Exception:
                    pass

            # Build and execute the turnin command
            cmd = f"cd {remote_dir} && turnin {assignment} {' '.join(remote_paths)}"
            print(cmd)
            stdin, stdout, stderr = target_ssh.exec_command(cmd, timeout=30)
            # Send "y" to the command to confirm any prompts
            stdin.write('y\n')
            stdin.flush()
            stdin.write('y\n')
            stdin.flush()


            # Gather output
            output_stdout = stdout.read().decode('utf-8', errors='replace')
            output_stderr = stderr.read().decode('utf-8', errors='replace')
            output = output_stdout + output_stderr

            # Close connection
            target_ssh.close()

        if progress_callback:
            try:
                progress_callback(100, "Assignment submitted successfully!")
            except Exception as e:
                return False, f"Error updating progress bar: {str(e)}"

        return True, output
    except paramiko.ssh_exception.SSHException as e:
        if "banner" in str(e).lower() or "timeout" in str(e).lower():
            return False, f"SSH connection timed out during submission. Please check your network connection and try again."
        else:
            return False, f"SSH error during submission: {str(e)}"
    except (socket.timeout, OSError, ConnectionError) as e:
        return False, f"Network connection failed during submission: {str(e)}"
    except Exception as e:
        return False, f"Error executing turnin command: {str(e)}"