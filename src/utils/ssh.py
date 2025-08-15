"""
SSH utilities for handling connections and file transfers
"""
import os
import socket
import paramiko
import sshtunnel

# Try to import PyQt6 widgets, but handle gracefully if not available
try:
    from PyQt6.QtWidgets import QMessageBox
    PYQT_AVAILABLE = True
except ImportError:
    PYQT_AVAILABLE = False


def add_ssh_keys(ssh):
    """
    Configure SSH client for password-only authentication

    Args:
        ssh (paramiko.SSHClient): The SSH client to configure
    """
    # Use password authentication only - automatically accept host keys
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

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