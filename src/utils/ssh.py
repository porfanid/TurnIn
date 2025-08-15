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
    from PyQt6.QtWidgets import QMessageBox
    PYQT_AVAILABLE = True
except ImportError:
    PYQT_AVAILABLE = False


class KnownHostKeyPolicy(paramiko.MissingHostKeyPolicy):
    """
    Host key policy that verifies against known hosts and hardcoded keys
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
                print(f"Host key verified for {hostname} using known keys")
                return  # Accept the key
        
        # If no match found, reject
        raise paramiko.SSHException(f"Host key verification failed for {hostname} - unknown host key")


class SSHTunnelForwarder:
    """Simple SSH tunnel forwarder using paramiko without DSSKey dependencies"""
    
    def __init__(self, ssh_host, ssh_port, ssh_username, ssh_password, 
                 remote_bind_address, local_bind_address=('127.0.0.1', 0)):
        self.ssh_host = ssh_host
        self.ssh_port = ssh_port
        self.ssh_username = ssh_username
        self.ssh_password = ssh_password
        self.remote_bind_address = remote_bind_address
        self.local_bind_address = local_bind_address
        
        self._ssh_client = None
        self._local_socket = None
        self.local_bind_port = None
        self._tunnel_thread = None
        self._stop_tunnel = False
    
    def __enter__(self):
        self.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()
    
    def start(self):
        """Start the SSH tunnel"""
        # Create SSH connection
        self._ssh_client = paramiko.SSHClient()
        add_ssh_keys(self._ssh_client)
        self._ssh_client.connect(
            self.ssh_host,
            port=self.ssh_port,
            username=self.ssh_username,
            password=self.ssh_password,
            timeout=15,
            banner_timeout=10,
            allow_agent=False,  # Disable SSH agent key usage
            look_for_keys=False  # Disable automatic private key discovery
        )
        
        # Create local socket
        self._local_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._local_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._local_socket.bind(self.local_bind_address)
        self.local_bind_port = self._local_socket.getsockname()[1]
        self._local_socket.listen(1)
        
        # Start tunnel thread
        self._stop_tunnel = False
        self._tunnel_thread = threading.Thread(target=self._tunnel_handler)
        self._tunnel_thread.daemon = True
        self._tunnel_thread.start()
    
    def stop(self):
        """Stop the SSH tunnel"""
        self._stop_tunnel = True
        
        if self._local_socket:
            try:
                self._local_socket.close()
            except:
                pass
        
        if self._ssh_client:
            try:
                self._ssh_client.close()
            except:
                pass
        
        if self._tunnel_thread and self._tunnel_thread.is_alive():
            self._tunnel_thread.join(timeout=1)
    
    def _tunnel_handler(self):
        """Handle tunnel connections"""
        try:
            while not self._stop_tunnel:
                try:
                    # Set a timeout for accept to allow checking stop condition
                    self._local_socket.settimeout(1.0)
                    client_socket, addr = self._local_socket.accept()
                    
                    # Handle connection in separate thread
                    connection_thread = threading.Thread(
                        target=self._handle_connection, 
                        args=(client_socket,)
                    )
                    connection_thread.daemon = True
                    connection_thread.start()
                    
                except socket.timeout:
                    continue
                except Exception:
                    break
        except Exception:
            pass
    
    def _handle_connection(self, client_socket):
        """Handle a single tunnel connection"""
        try:
            # Create channel through SSH connection
            channel = self._ssh_client.get_transport().open_channel(
                'direct-tcpip',
                self.remote_bind_address,
                client_socket.getpeername()
            )
            
            # Forward data between client and channel
            self._forward_data(client_socket, channel)
            
        except Exception:
            pass
        finally:
            try:
                client_socket.close()
            except:
                pass
    
    def _forward_data(self, client_socket, channel):
        """Forward data between client socket and SSH channel"""
        try:
            while True:
                ready, _, _ = select.select([client_socket, channel], [], [], 1.0)
                
                if self._stop_tunnel:
                    break
                
                if client_socket in ready:
                    data = client_socket.recv(4096)
                    if not data:
                        break
                    channel.send(data)
                
                if channel in ready:
                    data = channel.recv(4096)
                    if not data:
                        break
                    client_socket.send(data)
        
        except Exception:
            pass
        finally:
            try:
                channel.close()
            except:
                pass


def add_ssh_keys(ssh):
    """
    Configure SSH client with host key verification and password-only authentication

    Args:
        ssh (paramiko.SSHClient): The SSH client to configure
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
    ssh.set_missing_host_key_policy(KnownHostKeyPolicy())

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
            look_for_keys=False  # Disable automatic private key discovery
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
        with SSHTunnelForwarder(
            ssh_host=proxy_host,
            ssh_port=22,
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
                             banner_timeout=10,  # Reduced to 10 second banner timeout
                             allow_agent=False,  # Disable SSH agent key usage
                             look_for_keys=False)  # Disable automatic private key discovery

            if progress_callback:
                try:
                    progress_callback(85, "Tunnel created. Running turnin command...")
                except Exception:
                    pass

            # Build and execute the turnin command
            cmd = f"cd {remote_dir} && yes|turnin {assignment} {' '.join(remote_paths)}"
            print(cmd)
            stdin, stdout, stderr = target_ssh.exec_command(cmd, timeout=30)
            
            # Send responses to any prompts
            # Use stdin/stdout interaction instead of "yes | turnin" for better reliability
            try:
                # Send "y" to confirm prompts (typically asking for confirmation)
                stdin.write('y\n')
                stdin.flush()
                
                # Give the command a moment to process the first response
                import time
                time.sleep(0.1)
                
                # Send second "y" for any additional prompts
                stdin.write('y\n')
                stdin.flush()
                
                # Close stdin to signal no more input
                stdin.close()
                
            except Exception as e:
                print(f"Warning: Error sending input to turnin command: {e}")

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
