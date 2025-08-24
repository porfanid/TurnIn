"""
SSH utilities for handling connections and file transfers
"""
import os
import socket
import paramiko
import threading
import select
import hashlib
import base64

try:
    from PyQt6.QtWidgets import QMessageBox, QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTextEdit
    from PyQt6.QtCore import Qt
    PYQT_AVAILABLE = True
    
    class HostKeyVerificationDialog(QDialog):
        """Dialog for verifying unknown SSH host keys"""
        
        def __init__(self, hostname, key_type, key_fingerprint, parent=None):
            super().__init__(parent)
            self.setWindowTitle("SSH Host Key Verification")
            self.setModal(True)
            self.resize(500, 300)
            
            layout = QVBoxLayout(self)
            
            # Warning message
            warning_label = QLabel("WARNING: Unknown SSH host key detected!")
            warning_label.setStyleSheet("color: red; font-weight: bold;")
            layout.addWidget(warning_label)
            
            # Host information
            info_text = f"""
    The authenticity of host '{hostname}' can't be established.
    {key_type} key fingerprint is:
    {key_fingerprint}

    Are you sure you want to continue connecting?
    """
            info_label = QLabel(info_text)
            info_label.setWordWrap(True)
            layout.addWidget(info_label)
            
            # Key details
            key_details = QTextEdit()
            key_details.setPlainText(f"Host: {hostname}\nKey Type: {key_type}\nFingerprint: {key_fingerprint}")
            key_details.setReadOnly(True)
            key_details.setMaximumHeight(100)
            layout.addWidget(key_details)
            
            # Save option
            save_label = QLabel("If you choose 'Yes', the key will be saved to your known_hosts file for future connections.")
            save_label.setWordWrap(True)
            save_label.setStyleSheet("font-style: italic;")
            layout.addWidget(save_label)
            
            # Buttons
            button_layout = QHBoxLayout()
            
            self.yes_button = QPushButton("Yes, accept and save key")
            self.yes_button.clicked.connect(self.accept)
            self.yes_button.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold;")
            
            self.no_button = QPushButton("No, reject connection")
            self.no_button.clicked.connect(self.reject)
            self.no_button.setStyleSheet("background-color: #f44336; color: white; font-weight: bold;")
            
            button_layout.addWidget(self.no_button)
            button_layout.addWidget(self.yes_button)
            layout.addLayout(button_layout)
            
            # Default to No for security
            self.no_button.setDefault(True)
            self.no_button.setFocus()

except ImportError:
    PYQT_AVAILABLE = False
    
    # Define a dummy class when PyQt6 is not available
    class HostKeyVerificationDialog:
        def __init__(self, *args, **kwargs):
            pass


def save_host_key_to_known_hosts(hostname, key):
    """Save a host key to the user's known_hosts file"""
    try:
        # Get the user's .ssh directory
        ssh_dir = os.path.expanduser("~/.ssh")
        if not os.path.exists(ssh_dir):
            os.makedirs(ssh_dir, mode=0o700)
        
        known_hosts_path = os.path.join(ssh_dir, "known_hosts")
        
        # Format the key entry
        key_type = key.get_name()
        key_data = key.get_base64()
        key_entry = f"{hostname} {key_type} {key_data}\n"
        
        # Append to known_hosts file
        with open(known_hosts_path, "a") as f:
            f.write(key_entry)
        
        print(f"Host key for {hostname} saved to {known_hosts_path}")
        return True
    except Exception as e:
        print(f"Error saving host key: {e}")
        return False


def get_key_fingerprint(key):
    """Get the fingerprint of an SSH key"""
    try:
        # Get the key in the format needed for fingerprinting
        key_data = base64.b64decode(key.get_base64())
        
        # Create SHA256 fingerprint
        digest = hashlib.sha256(key_data).digest()
        fingerprint = base64.b64encode(digest).decode().rstrip('=')
        
        return f"SHA256:{fingerprint}"
    except Exception as e:
        print(f"Error generating fingerprint: {e}")
        return f"(Unable to generate fingerprint: {e})"


class KnownHostKeyPolicy(paramiko.MissingHostKeyPolicy):
    """
    Host key policy that verifies against known hosts and hardcoded keys
    """
    
    def __init__(self, actual_hostname=None):
        try:
            from config import SSH_KEYS
            self.ssh_keys = SSH_KEYS
        except ImportError:
            # If config module is not available (e.g., during testing), use empty list
            self.ssh_keys = []
        
        # Store the actual hostname for tunneled connections
        self.actual_hostname = actual_hostname
    
    def missing_host_key(self, client, hostname, key):
        """
        Check if the host key matches any of our known hardcoded keys, or ask user to accept
        """
        key_type = key.get_name()
        key_data = key.get_base64()
        
        # Use actual hostname for display and saving if this is a tunneled connection
        display_hostname = self.actual_hostname if self.actual_hostname else hostname
        save_hostname = self.actual_hostname if self.actual_hostname else hostname
        
        # Check against hardcoded keys
        for host, stored_type, stored_key in self.ssh_keys:
            if host == display_hostname and stored_type == key_type and stored_key == key_data:
                print(f"Host key verified for {display_hostname} using known keys")
                return  # Accept the key
        
        # If no match found, ask user if PyQt6 is available
        if PYQT_AVAILABLE:
            try:
                fingerprint = get_key_fingerprint(key)
                dialog = HostKeyVerificationDialog(display_hostname, key_type, fingerprint)
                result = dialog.exec()
                
                if result == QDialog.Accepted:
                    # User accepted the key, save it to known_hosts using the actual hostname
                    if save_host_key_to_known_hosts(save_hostname, key):
                        print(f"Host key accepted and saved for {save_hostname}")
                        return  # Accept the key
                    else:
                        print(f"Warning: Host key accepted but could not be saved for {save_hostname}")
                        return  # Accept anyway
                else:
                    # User rejected the key
                    raise paramiko.SSHException(f"Host key verification failed for {display_hostname} - user rejected unknown host key")
                    
            except Exception as e:
                # If there's an error with the dialog, fall back to rejection
                print(f"Error showing host key dialog: {e}")
                raise paramiko.SSHException(f"Host key verification failed for {display_hostname} - unknown host key")
        else:
            # If PyQt6 is not available, reject as before
            raise paramiko.SSHException(f"Host key verification failed for {display_hostname} - unknown host key")


# SSHTunnelForwarder class removed - using direct channel forwarding instead


def add_ssh_keys(ssh, actual_hostname=None):
    """
    Configure SSH client with host key verification and password-only authentication

    Args:
        ssh (paramiko.SSHClient): The SSH client to configure
        actual_hostname (str, optional): The actual hostname for tunneled connections
    """
    # Load system and user known_hosts files for host key verification
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
    
    # Set host key verification policy (falls back to hardcoded keys for known servers)
    ssh.set_missing_host_key_policy(KnownHostKeyPolicy(actual_hostname))

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
    Connect to the SSH proxy with support for both password and keyboard-interactive authentication

    Args:
        username (str): SSH username
        password (str): SSH password
        proxy_host (str): Proxy hostname

    Returns:
        tuple: (success (bool), host_to_connect (str), ssh_client (paramiko.SSHClient), error_type (str))
        error_type can be: None (success), 'auth' (authentication failed), 'timeout' (connection timeout), 'other' (other errors)
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
            banner_timeout=10,  # Reduced to 10 second banner timeout
            allow_agent=False,  # Disable SSH agent key usage
            look_for_keys=False,  # Disable automatic private key discovery
            auth_timeout=30  # Set authentication timeout
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
            return False, None, None, 'other'

        return True, host_to_connect, ssh, None
    except paramiko.AuthenticationException:
        # Try keyboard-interactive authentication as fallback
        try:
            if ssh:
                ssh.close()
            ssh = paramiko.SSHClient()
            add_ssh_keys(ssh)
            
            # Connect without authentication first
            transport = paramiko.Transport((proxy_host, 22))
            transport.connect()
            
            # Try keyboard-interactive authentication
            try:
                def auth_handler(title, instructions, prompt_list):
                    # For keyboard-interactive, return the password for all prompts
                    if prompt_list:
                        return [password] * len(prompt_list)
                    return []
                
                transport.auth_interactive(username, auth_handler)
                ssh._transport = transport
                
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
                    return False, None, None, 'other'

                return True, host_to_connect, ssh, None
            except:
                # If keyboard-interactive also fails, return auth error
                if ssh:
                    try:
                        ssh.close()
                    except:
                        pass
                return False, None, None, 'auth'
        except:
            if ssh:
                try:
                    ssh.close()
                except:
                    pass
            return False, None, None, 'auth'
    except paramiko.ssh_exception.SSHException as e:
        if ssh:
            try:
                ssh.close()
            except:
                pass
        # Handle specific banner timeout errors more gracefully
        if "banner" in str(e).lower() or "timeout" in str(e).lower():
            error_msg = f"SSH connection timed out. Please check your network connection and try again."
            error_type = 'timeout'
        else:
            error_msg = f"SSH Error: {e}"
            error_type = 'other'
        
        if PYQT_AVAILABLE:
            try:
                QMessageBox.critical(None, "SSH Error", error_msg)
            except:
                print(error_msg)
        else:
            print(error_msg)
        return False, None, None, error_type
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
        return False, None, None, 'timeout'
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
        return False, None, None, 'other'

def upload_files(files, username, password, ssh, host, temp_dir, progress_callback=None):
    """Upload files with progress reporting using existing SSH connection"""
    if not files:
        return None, None

    # Get home directory using existing SSH connection
    _, ssh_stdout, _ = ssh.exec_command("pwd")
    home_dir = ssh_stdout.readlines()[0].strip()

    # Use existing SSH connection to create SFTP channel (reuses the single connection)
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
                 file_list, temp_dir, ssh_client=None, progress_callback=None,
                 interactive_callback=None):
    """Submit files to the assignment submission server using minimal SSH connections"""
    # Use existing SSH client or create a new one
    if ssh_client:
        ssh = ssh_client
    else:
        result, _, ssh, error_type = connect_to_proxy(username, password, proxy_host)
        if not result:
            if error_type == 'timeout':
                return False, "SSH connection timed out. Please check your network connection and try again."
            elif error_type == 'auth':
                return False, "Authentication failed. Please check your credentials."
            else:
                return False, "Connection failed. Please try again."

    if progress_callback:
        try:
            progress_callback(10, "Connected to SSH server...")
        except Exception:
            pass

    # Upload files to the server using the same SSH connection
    remote_dir, remote_paths = upload_files(file_list, username, password, ssh, proxy_host, temp_dir, progress_callback)

    if not remote_dir or not remote_paths:
        return False, "Failed to upload files"

    if progress_callback:
        try:
            progress_callback(80, "Files uploaded. Creating connection to target host...")
        except Exception:
            pass

    # Execute the turnin command on the target host using a single SSH connection with channel forwarding
    try:
        if progress_callback:
            try:
                progress_callback(85, "Connecting to target host and running turnin command...")
            except Exception:
                pass

        # Create a direct channel to the target host using the existing SSH connection
        transport = ssh.get_transport()
        
        # Open a channel to the target host through the proxy
        try:
            target_channel = transport.open_channel(
                'direct-tcpip',
                (host_to_connect, 22),
                ('127.0.0.1', 0)
            )
        except Exception as e:
            return False, f"Failed to create channel to target host: {str(e)}"
        
        # Create a new SSH client for the target host using the channel
        target_ssh = paramiko.SSHClient()
        add_ssh_keys(target_ssh, host_to_connect)  # Pass actual hostname for proper key verification
        
        # Use the channel as a transport
        target_transport = paramiko.Transport(target_channel)
        target_transport.start_client()
        
        # Authenticate to the target host
        try:
            target_transport.auth_password(username, password)
        except paramiko.AuthenticationException:
            # Try keyboard-interactive authentication as fallback
            def auth_handler(title, instructions, prompt_list):
                if prompt_list:
                    return [password] * len(prompt_list)
                return []
            
            target_transport.auth_interactive(username, auth_handler)
        
        # Attach the transport to the SSH client
        target_ssh._transport = target_transport

        # Build and execute the turnin command with automatic yes responses 
        # Since the user mentioned the interactive system isn't working and prefers simplicity
        cmd = f"cd {remote_dir} && yes | turnin {assignment} {' '.join(remote_paths)}"
        print(f"Executing command: {cmd}")
        
        if interactive_callback:
            interactive_callback("output", f"Executing: {cmd}\n")
        
        stdin, stdout, stderr = target_ssh.exec_command(cmd, timeout=60)
        
        # Read all output
        output_lines = []
        
        # Read stdout
        for line in stdout:
            line = line.strip()
            if line:
                output_lines.append(line)
                if interactive_callback:
                    interactive_callback("output", line + "\n")
        
        # Read stderr  
        for line in stderr:
            line = line.strip()
            if line:
                output_lines.append(f"ERROR: {line}")
                if interactive_callback:
                    interactive_callback("output", f"ERROR: {line}\n")
        
        output = "\n".join(output_lines)

        # Close target connection
        try:
            target_ssh.close()
        except:
            pass
        
        try:
            target_channel.close()
        except:
            pass

        if progress_callback:
            try:
                progress_callback(100, "Assignment submission completed!")
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


# Interactive execution handling removed - using automatic responses instead
