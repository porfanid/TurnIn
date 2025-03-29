"""
SSH utilities for handling connections and file transfers
"""
import os
import paramiko
import sshtunnel
from PyQt6.QtWidgets import QMessageBox
from config import SSH_KEYS

def add_ssh_keys(ssh):
    """
    Add known SSH host keys to the client

    Args:
        ssh (paramiko.SSHClient): The SSH client to configure
    """
    known_hosts_path = "known_hosts_file"
    if not os.path.exists(known_hosts_path):
        with open(known_hosts_path, "a") as known_hosts_file:
            for host_key in SSH_KEYS:
                # Format the host key entry
                host_key_entry = f"{host_key[0]} {host_key[1]} {host_key[2]}\n"
                # Write the host key entry to the known_hosts file
                known_hosts_file.write(host_key_entry)

    ssh.load_host_keys(known_hosts_path)
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
            QMessageBox.critical(None, "Error", "No available hosts found. Aborting...")
            return False, None, None

        return True, host_to_connect, ssh
    except paramiko.AuthenticationException:
        return False, None, None
    except paramiko.ssh_exception.SSHException as e:
        QMessageBox.critical(None, "SSH Error", str(e))
        return False, None, None

def upload_files(files, username, password, ssh, host, temp_dir):
    """
    Upload files to the remote server

    Args:
        files (list): List of local file paths to upload
        username (str): SSH username
        password (str): SSH password
        ssh (paramiko.SSHClient): SSH client
        host (str): Host to connect to
        temp_dir (str): Remote temporary directory

    Returns:
        tuple: (remote_dir (str), remote_paths (list))
    """
    if not files:
        QMessageBox.warning(None, "No Files", "No files were selected. Cannot continue.")
        return None, None

    _, ssh_stdout, _ = ssh.exec_command("pwd")
    home_dir = ssh_stdout.readlines()[0].strip()

    transport = paramiko.Transport((host, 22))
    transport.connect(None, username, password)
    sftp = paramiko.SFTPClient.from_transport(transport)

    remote_dir = f"{home_dir}/{temp_dir}/"

    try:
        sftp.mkdir(remote_dir)
    except:
        pass  # Directory might already exist

    remote_paths = []
    for localpath in files:
        name = os.path.basename(localpath)
        filepath = f"{remote_dir}{name}"
        try:
            sftp.put(localpath, filepath)
            remote_paths.append(name)
        except Exception as e:
            QMessageBox.warning(None, "Upload Error", f"Could not upload {name}: {str(e)}")

    return remote_dir, remote_paths

def submit_assignment(host, username, password, host_to_connect, remote_dir, assignment, remote_paths):
    """
    Submit assignment through SSH tunnel

    Args:
        host (str): Proxy host
        username (str): SSH username
        password (str): SSH password
        host_to_connect (str): Target host
        remote_dir (str): Remote directory with files
        assignment (str): Assignment identifier
        remote_paths (list): List of remote file paths
    """
    with sshtunnel.open_tunnel(
            (host, 22),
            ssh_username=username,
            ssh_password=password,
            remote_bind_address=(host_to_connect, 22),
            local_bind_address=('0.0.0.0', 10022)
    ) as _:
        ssh = paramiko.SSHClient()
        ssh.load_system_host_keys()
        add_ssh_keys(ssh)

        try:
            ssh.connect('127.0.0.1', 10022, username=username, password=password)
            turn_in_command = f"cd {remote_dir} && yes | turnin {assignment} {' '.join(remote_paths)}"
            _, ssh_stdout, ssh_stderr = ssh.exec_command(turn_in_command)

            # Clean up temporary directory
            ssh.exec_command(f"rm -R {remote_dir}")

            # Show results
            stdout = ''.join(ssh_stdout.readlines())
            stderr = ''.join(ssh_stderr.readlines())
            QMessageBox.information(None, "Submission Result", f"{stdout}\n\n{stderr}")

            ssh.close()
        except paramiko.ssh_exception.SSHException as e:
            QMessageBox.critical(None, "SSH Error", str(e))



def submit_files(proxy_host, host_to_connect, username, password, assignment,
                file_list, temp_dir, ssh_client=None):
    """
    Submit files to the assignment submission server

    Args:
        proxy_host (str): SSH proxy hostname
        host_to_connect (str): Target host to connect through proxy
        username (str): SSH username
        password (str): SSH password
        assignment (str): Assignment name/ID
        file_list (list): List of files to submit
        temp_dir (str): Temporary directory for processing
        ssh_client (paramiko.SSHClient, optional): Existing SSH client connection

    Returns:
        bool: True if submission was successful
    """
    # Use existing SSH client or create a new one
    ssh = ssh_client or connect_to_proxy(username, password, proxy_host)[2]

    # Upload files to the server
    remote_dir, remote_paths = upload_files(file_list, username, password, ssh, proxy_host, temp_dir)

    if not remote_dir or not remote_paths:
        return False

    # Submit the assignment
    try:
        submit_assignment(
            proxy_host,
            username,
            password,
            host_to_connect,
            remote_dir,
            assignment,
            remote_paths
        )
        return True
    except Exception as e:
        QMessageBox.critical(None, "Submission Error", f"Error submitting files: {str(e)}")
        return False