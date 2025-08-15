"""
SSH utilities for handling connections and file transfers
"""
import os
import paramiko
import sshtunnel

try:
    from PyQt6.QtWidgets import QMessageBox
except ImportError:
    # For testing environments without GUI support
    QMessageBox = None

def validate_files(files):
    """
    Validate files before upload according to TurnIn requirements.
    
    Args:
        files (list): List of file paths to validate
        
    Returns:
        tuple: (valid_files, invalid_files, error_messages)
    """
    valid_files = []
    invalid_files = []
    error_messages = []
    
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB in bytes
    
    # Common binary file extensions (not exhaustive but covers common cases)
    BINARY_EXTENSIONS = {
        '.exe', '.dll', '.so', '.dylib', '.bin', '.out', '.o', '.obj',
        '.zip', '.rar', '.7z', '.tar', '.gz', '.bz2',
        '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.ico', '.svg',
        '.mp3', '.wav', '.mp4', '.avi', '.mov', '.mkv',
        '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx'
    }
    
    for file_path in files:
        if os.path.isdir(file_path):
            # For directories, check all files recursively
            for root, dirs, filenames in os.walk(file_path):
                for filename in filenames:
                    full_path = os.path.join(root, filename)
                    relative_path = os.path.relpath(full_path, file_path)
                    
                    # Check file size
                    try:
                        file_size = os.path.getsize(full_path)
                        if file_size > MAX_FILE_SIZE:
                            invalid_files.append(full_path)
                            error_messages.append(f"File too large: {relative_path} ({file_size / (1024*1024):.1f}MB > 10MB)")
                            continue
                    except OSError as e:
                        invalid_files.append(full_path)
                        error_messages.append(f"Cannot access file: {relative_path} - {str(e)}")
                        continue
                    
                    # Check if binary file
                    file_ext = os.path.splitext(filename)[1].lower()
                    if file_ext in BINARY_EXTENSIONS:
                        invalid_files.append(full_path)
                        error_messages.append(f"Binary file not allowed: {relative_path}")
                        continue
                        
                    # Try to detect binary content for files without extensions or unknown extensions
                    if not file_ext or file_ext not in ['.txt', '.py', '.java', '.c', '.cpp', '.h', '.hpp', '.js', '.html', '.css', '.xml', '.json', '.md', '.rst']:
                        try:
                            with open(full_path, 'rb') as f:
                                chunk = f.read(8192)  # Read first 8KB
                                if b'\x00' in chunk:  # Null bytes typically indicate binary content
                                    invalid_files.append(full_path)
                                    error_messages.append(f"Binary content detected: {relative_path}")
                                    continue
                        except OSError:
                            # If we can't read the file, skip binary detection but keep the file
                            pass
                    
                    valid_files.append(full_path)
        else:
            # Single file validation
            try:
                file_size = os.path.getsize(file_path)
                if file_size > MAX_FILE_SIZE:
                    invalid_files.append(file_path)
                    error_messages.append(f"File too large: {os.path.basename(file_path)} ({file_size / (1024*1024):.1f}MB > 10MB)")
                    continue
            except OSError as e:
                invalid_files.append(file_path)
                error_messages.append(f"Cannot access file: {os.path.basename(file_path)} - {str(e)}")
                continue
            
            # Check if binary file
            file_ext = os.path.splitext(file_path)[1].lower()
            if file_ext in BINARY_EXTENSIONS:
                invalid_files.append(file_path)
                error_messages.append(f"Binary file not allowed: {os.path.basename(file_path)}")
                continue
                
            # Try to detect binary content for files without extensions or unknown extensions
            if not file_ext or file_ext not in ['.txt', '.py', '.java', '.c', '.cpp', '.h', '.hpp', '.js', '.html', '.css', '.xml', '.json', '.md', '.rst']:
                try:
                    with open(file_path, 'rb') as f:
                        chunk = f.read(8192)  # Read first 8KB
                        if b'\x00' in chunk:  # Null bytes typically indicate binary content
                            invalid_files.append(file_path)
                            error_messages.append(f"Binary content detected: {os.path.basename(file_path)}")
                            continue
                except OSError:
                    # If we can't read the file, skip binary detection but keep the file
                    pass
            
            valid_files.append(file_path)
    
    return valid_files, invalid_files, error_messages

def add_ssh_keys(ssh):
    """
    Add known SSH host keys to the client

    Args:
        ssh (paramiko.SSHClient): The SSH client to configure
    """
    # This needs to be fixed to not rely on SSH_KEYS from config
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
    try:
        ssh = paramiko.SSHClient()
        add_ssh_keys(ssh)
        ssh.connect(proxy_host, username=username, password=password)

        # Find available host
        host_to_connect = get_available_server(ssh)
        if not host_to_connect:
            if QMessageBox:
                QMessageBox.critical(None, "Error", "No available hosts found. Aborting...")
            return False, None, None

        return True, host_to_connect, ssh
    except paramiko.AuthenticationException:
        return False, None, None
    except paramiko.ssh_exception.SSHException as e:
        if QMessageBox:
            QMessageBox.critical(None, "SSH Error", str(e))
        return False, None, None

def upload_files(files, username, password, ssh, host, temp_dir, progress_callback=None):
    """Upload files with progress reporting and detailed error tracking"""
    if not files:
        return None, None, [], []
    
    # Get home directory
    _, ssh_stdout, _ = ssh.exec_command("pwd")
    home_dir = ssh_stdout.readlines()[0].strip()

    # Setup SFTP connection
    transport = paramiko.Transport((host, 22))
    transport.connect(None, username, password)
    sftp = paramiko.SFTPClient.from_transport(transport)

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
    failed_uploads = []
    upload_errors = []
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
            failed_uploads.append(name)
            upload_errors.append(f"Failed to upload {name}: {str(e)}")
            print(f"Upload error: {str(e)}")

    return remote_dir, remote_paths, failed_uploads, upload_errors


def analyze_turnin_output(stdout, stderr):
    """
    Analyze turnin command output to provide specific error messages.
    
    Args:
        stdout (str): Standard output from turnin command
        stderr (str): Standard error from turnin command
        
    Returns:
        tuple: (is_success, user_message, technical_details)
    """
    output = stdout + stderr
    output_lower = output.lower()
    
    # Check for common error patterns
    if "you have already turned in" in output_lower:
        return False, "You have already submitted this assignment. Multiple submissions are not allowed.", output
    
    if "no such assignment" in output_lower or "assignment not found" in output_lower:
        return False, "Assignment not found. Please check the assignment name and try again.", output
    
    if "permission denied" in output_lower:
        return False, "Permission denied. Please check your credentials and try again.", output
    
    if "disk quota exceeded" in output_lower or "no space left" in output_lower:
        return False, "Storage quota exceeded. Please contact your instructor or system administrator.", output
    
    if "file not found" in output_lower:
        return False, "Some files could not be found on the server. Please try uploading again.", output
    
    if "connection" in output_lower and ("timeout" in output_lower or "refused" in output_lower or "failed" in output_lower):
        return False, "Connection error occurred. Please check your network connection and try again.", output
    
    if stderr and stderr.strip():
        # If there's stderr content but no specific pattern matched, it's likely an error
        return False, "An error occurred during submission. Please check the details below.", output
    
    # Check for success indicators
    if any(success_phrase in output_lower for success_phrase in ["submitted successfully", "submission successful", "turned in", "assignment submitted"]):
        return True, "Assignment submitted successfully!", output
    
    # If no clear success/error pattern, default to success if no stderr
    if not stderr.strip():
        return True, "Assignment submitted successfully!", output
    
    # Default case - unclear result
    return False, "Submission completed but result is unclear. Please check the output below.", output


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

    # Upload files to the server and get detailed results
    upload_result = upload_files(file_list, username, password, ssh, proxy_host, temp_dir, progress_callback)
    
    if len(upload_result) == 4:
        # New format with error tracking
        remote_dir, remote_paths, failed_uploads, upload_errors = upload_result
    else:
        # Fallback to old format (for compatibility)
        remote_dir, remote_paths = upload_result
        failed_uploads, upload_errors = [], []

    if not remote_dir or not remote_paths:
        error_msg = "Failed to upload files"
        if upload_errors:
            error_msg += ":\n" + "\n".join(upload_errors)
        return False, error_msg

    # If some files failed to upload, inform the user but continue with successful uploads
    if failed_uploads:
        if not remote_paths:
            # All files failed
            error_msg = f"All {len(failed_uploads)} files failed to upload:\n" + "\n".join(upload_errors)
            return False, error_msg
        else:
            # Some files failed - we'll include this in the final message
            partial_failure_msg = f"Warning: {len(failed_uploads)} file(s) failed to upload: {', '.join(failed_uploads)}\n"
    else:
        partial_failure_msg = ""

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
            target_ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

            # Connect through the tunnel
            target_ssh.connect('127.0.0.1',
                             port=tunnel.local_bind_port,
                             username=username,
                             password=password)

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

            # Close connection
            target_ssh.close()

        # Analyze the turnin command output
        is_success, user_message, technical_output = analyze_turnin_output(output_stdout, output_stderr)
        
        # Combine partial failure message if any
        if partial_failure_msg:
            user_message = partial_failure_msg + user_message
        
        if progress_callback:
            try:
                if is_success:
                    progress_callback(100, "Assignment submitted successfully!")
                else:
                    progress_callback(100, "Submission completed with issues")
            except Exception as e:
                return False, f"Error updating progress bar: {str(e)}"

        return is_success, user_message if is_success else f"{user_message}\n\nTechnical details:\n{technical_output}"
    except Exception as e:
        return False, f"Error executing turnin command: {str(e)}"