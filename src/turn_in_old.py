# importing sentry sdk for error reporting
import sentry_sdk

sentry_sdk.init("https://39a7dcc277c54f658ddf7c47deda2a9e@o238115.ingest.sentry.io/5236153")

# ssh tunnel, socket and paramiko for the ssh and sftp commands for the turn in
import sshtunnel
import paramiko

# tools to encrypt and save the username and password
import json
from cryptography.fernet import Fernet
from cryptography.fernet import InvalidToken

import keyring
import base64

import requests

# os for the path basename to get the name and other controls
import os
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QLabel, QLineEdit, QGridLayout, QMessageBox, \
    QFileDialog, QInputDialog

from PyQt5 import QtGui, QtCore
from PyQt5.QtGui import QDesktopServices
# system, for the exit function and to get wether the platform is windows or linux
from sys import platform, exit

# Define the host keys
ssh_keys = [
    ("scylla.cs.uoi.gr", "ssh-rsa",
     "AAAAB3NzaC1yc2EAAAADAQABAAABAQC4FBvewUk/bWUNOZ4ZQEQ76+Rlodr/ZPDCTPcWhHL+Z4z3plDo/BMoEs21vtsFviI4XDOntQXzUlgG8Ro0xk8tNmXztG9C5AHhl0g6axyvFyRy6hFDx1K+LFWaF7KdtdfOtAUdeP4DRPr+wX9dL6M0j/D5OVGaY3SQD+YJMed8IjmWgqOxMTjSerluTET/L0+VBo82ng2Y/dYxLLFAtimkbzfK0tgEd61cayo4Aymt3XHSBmDQm7g9nnrFMLIyYEFsMoBy7vrOOFSYvP0ejIeLOzHxlUKs9SzKDXiISDfXfLPGzoNjw7t3UpgnAv+Zb+gk4O+iMVAgCGubBuFu6iq3"),
    ("scylla.cs.uoi.gr", "ecdsa-sha2-nistp256",
     "AAAAE2VjZHNhLXNoYTItbmlzdHAyNTYAAAAIbmlzdHAyNTYAAABBBHRcr33y6VL9eRyZRetzPWKHW2Djp6loH+/Kw0bckdR7lkiLGFlfcZ8jXhlvf9ieglZkqgH0xTOE6Pwq4F1CweA="),
    ("dl380ws01", "ecdsa-sha2-nistp256",
     "AAAAE2VjZHNhLXNoYTItbmlzdHAyNTYAAAAIbmlzdHAyNTYAAABBBMli3FZmz2PlHCGinbPc7yYHGdjj037UPzoBuNlKwOyDO5JfHE3G81PheGIiuqcaZSYqxnTysa/X0fnNAuZRejI="),
    ("dl380ws01", "ssh-ed25519", "AAAAC3NzaC1lZDI1NTE5AAAAILq44YUHEbz9LGd2Fbuaaxkh1rIjxyF0ElStXODKhGfE"),
    ("dl380ws01", "ssh-rsa",
     "AAAAB3NzaC1yc2EAAAADAQABAAABgQCimHCSTUTVOdr6/Egw8O9Y7/q6jmFYDMDm8gPbfecaQB+Gtp+2+FmLv30D5rA5uEhqgND8xuM1FI1zpXhu/MChdA3SA/GMwPSGRz8B45gLQCjdd7O9Jn+rVetSKxNOXJaKMKmoQLKWCTbyTi5VRsG6HPWtiWcVcmlfBt8nrx/RW4ZDidr6kGTjjxpBYdjsUuyCtVG85OIwD9GdYSwKWPInUYWl6adh/9V4nrwuGfjgr47+9PR5Qi35DyNP1lzLqSbyiGMRBSUueuVIb6ZGNgxRnxjiO7dBToh8GaYLN/3MHTqptV8F/zNZ+yqakAIM9efVMdx3tp/CNYFRd/lMc7GGzD28N+1RqRwlvwqQlXG3H5Ay9+1kOFBa+rhFt8iUG1AMv5VyQPTa2rlIGW3sdL8pnkl4wf9D1VitC4CFl0s7OYPinfM0R3bBHq0LvPQaSqJRH2vXv3aA5akcEANQKs8W+Bq5a698+ghMF83wd/cU4Ghe+5higrsDMZsAAZMb3ic="),
    ("dl380ws02", "ecdsa-sha2-nistp256",
     "AAAAB3NzaC1yc2EAAAADAQABAAABgQCimHCSTUTVOdr6/Egw8O9Y7/q6jmFYDMDm8gPbfecaQB+Gtp+2+FmLv30D5rA5uEhqgND8xuM1FI1zpXhu/MChdA3SA/GMwPSGRz8B45gLQCjdd7O9Jn+rVetSKxNOXJaKMKmoQLKWCTbyTi5VRsG6HPWtiWcVcmlfBt8nrx/RW4ZDidr6kGTjjxpBYdjsUuyCtVG85OIwD9GdYSwKWPInUYWl6adh/9V4nrwuGfjgr47+9PR5Qi35DyNP1lzLqSbyiGMRBSUueuVIb6ZGNgxRnxjiO7dBToh8GaYLN/3MHTqptV8F/zNZ+yqakAIM9efVMdx3tp/CNYFRd/lMc7GGzD28N+1RqRwlvwqQlXG3H5Ay9+1kOFBa+rhFt8iUG1AMv5VyQPTa2rlIGW3sdL8pnkl4wf9D1VitC4CFl0s7OYPinfM0R3bBHq0LvPQaSqJRH2vXv3aA5akcEANQKs8W+Bq5a698+ghMF83wd/cU4Ghe+5higrsDMZsAAZMb3ic="),
    ("dl380ws03", "ecdsa-sha2-nistp256",
     "AAAAB3NzaC1yc2EAAAADAQABAAABgQCimHCSTUTVOdr6/Egw8O9Y7/q6jmFYDMDm8gPbfecaQB+Gtp+2+FmLv30D5rA5uEhqgND8xuM1FI1zpXhu/MChdA3SA/GMwPSGRz8B45gLQCjdd7O9Jn+rVetSKxNOXJaKMKmoQLKWCTbyTi5VRsG6HPWtiWcVcmlfBt8nrx/RW4ZDidr6kGTjjxpBYdjsUuyCtVG85OIwD9GdYSwKWPInUYWl6adh/9V4nrwuGfjgr47+9PR5Qi35DyNP1lzLqSbyiGMRBSUueuVIb6ZGNgxRnxjiO7dBToh8GaYLN/3MHTqptV8F/zNZ+yqakAIM9efVMdx3tp/CNYFRd/lMc7GGzD28N+1RqRwlvwqQlXG3H5Ay9+1kOFBa+rhFt8iUG1AMv5VyQPTa2rlIGW3sdL8pnkl4wf9D1VitC4CFl0s7OYPinfM0R3bBHq0LvPQaSqJRH2vXv3aA5akcEANQKs8W+Bq5a698+ghMF83wd/cU4Ghe+5higrsDMZsAAZMb3ic="),
    ("dl380ws03", "ssh-ed25519", "AAAAC3NzaC1lZDI1NTE5AAAAILq44YUHEbz9LGd2Fbuaaxkh1rIjxyF0ElStXODKhGfE"),
    ("dl380ws03", "ssh-rsa",
     "AAAAB3NzaC1yc2EAAAADAQABAAABgQCimHCSTUTVOdr6/Egw8O9Y7/q6jmFYDMDm8gPbfecaQB+Gtp+2+FmLv30D5rA5uEhqgND8xuM1FI1zpXhu/MChdA3SA/GMwPSGRz8B45gLQCjdd7O9Jn+rVetSKxNOXJaKMKmoQLKWCTbyTi5VRsG6HPWtiWcVcmlfBt8nrx/RW4ZDidr6kGTjjxpBYdjsUuyCtVG85OIwD9GdYSwKWPInUYWl6adh/9V4nrwuGfjgr47+9PR5Qi35DyNP1lzLqSbyiGMRBSUueuVIb6ZGNgxRnxjiO7dBToh8GaYLN/3MHTqptV8F/zNZ+yqakAIM9efVMdx3tp/CNYFRd/lMc7GGzD28N+1RqRwlvwqQlXG3H5Ay9+1kOFBa+rhFt8iUG1AMv5VyQPTa2rlIGW3sdL8pnkl4wf9D1VitC4CFl0s7OYPinfM0R3bBHq0LvPQaSqJRH2vXv3aA5akcEANQKs8W+Bq5a698+ghMF83wd/cU4Ghe+5higrsDMZsAAZMb3ic="),
    ("dl380ws04", "ecdsa-sha2-nistp256",
     "AAAAE2VjZHNhLXNoYTItbmlzdHAyNTYAAAAIbmlzdHAyNTYAAABBBMli3FZmz2PlHCGinbPc7yYHGdjj037UPzoBuNlKwOyDO5JfHE3G81PheGIiuqcaZSYqxnTysa/X0fnNAuZRejI="),
    ("dl380ws04", "ssh-ed25519", "AAAAC3NzaC1lZDI1NTE5AAAAILq44YUHEbz9LGd2Fbuaaxkh1rIjxyF0ElStXODKhGfE"),
    ("dl380ws04", "ssh-rsa",
     "AAAAB3NzaC1yc2EAAAADAQABAAABgQCimHCSTUTVOdr6/Egw8O9Y7/q6jmFYDMDm8gPbfecaQB+Gtp+2+FmLv30D5rA5uEhqgND8xuM1FI1zpXhu/MChdA3SA/GMwPSGRz8B45gLQCjdd7O9Jn+rVetSKxNOXJaKMKmoQLKWCTbyTi5VRsG6HPWtiWcVcmlfBt8nrx/RW4ZDidr6kGTjjxpBYdjsUuyCtVG85OIwD9GdYSwKWPInUYWl6adh/9V4nrwuGfjgr47+9PR5Qi35DyNP1lzLqSbyiGMRBSUueuVIb6ZGNgxRnxjiO7dBToh8GaYLN/3MHTqptV8F/zNZ+yqakAIM9efVMdx3tp/CNYFRd/lMc7GGzD28N+1RqRwlvwqQlXG3H5Ay9+1kOFBa+rhFt8iUG1AMv5VyQPTa2rlIGW3sdL8pnkl4wf9D1VitC4CFl0s7OYPinfM0R3bBHq0LvPQaSqJRH2vXv3aA5akcEANQKs8W+Bq5a698+ghMF83wd/cU4Ghe+5higrsDMZsAAZMb3ic="),
    ("dl380ws05", "ecdsa-sha2-nistp256",
     "AAAAE2VjZHNhLXNoYTItbmlzdHAyNTYAAAAIbmlzdHAyNTYAAABBBMli3FZmz2PlHCGinbPc7yYHGdjj037UPzoBuNlKwOyDO5JfHE3G81PheGIiuqcaZSYqxnTysa/X0fnNAuZRejI="),
    ("dl380ws05", "ssh-ed25519", "AAAAC3NzaC1lZDI1NTE5AAAAILq44YUHEbz9LGd2Fbuaaxkh1rIjxyF0ElStXODKhGfE"),
    ("dl380ws05", "ssh-rsa",
     "AAAAB3NzaC1yc2EAAAADAQABAAABgQCimHCSTUTVOdr6/Egw8O9Y7/q6jmFYDMDm8gPbfecaQB+Gtp+2+FmLv30D5rA5uEhqgND8xuM1FI1zpXhu/MChdA3SA/GMwPSGRz8B45gLQCjdd7O9Jn+rVetSKxNOXJaKMKmoQLKWCTbyTi5VRsG6HPWtiWcVcmlfBt8nrx/RW4ZDidr6kGTjjxpBYdjsUuyCtVG85OIwD9GdYSwKWPInUYWl6adh/9V4nrwuGfjgr47+9PR5Qi35DyNP1lzLqSbyiGMRBSUueuVIb6ZGNgxRnxjiO7dBToh8GaYLN/3MHTqptV8F/zNZ+yqakAIM9efVMdx3tp/CNYFRd/lMc7GGzD28N+1RqRwlvwqQlXG3H5Ay9+1kOFBa+rhFt8iUG1AMv5VyQPTa2rlIGW3sdL8pnkl4wf9D1VitC4CFl0s7OYPinfM0R3bBHq0LvPQaSqJRH2vXv3aA5akcEANQKs8W+Bq5a698+ghMF83wd/cU4Ghe+5higrsDMZsAAZMb3ic="),
    ("dl380ws06", "ecdsa-sha2-nistp256",
     "AAAAE2VjZHNhLXNoYTItbmlzdHAyNTYAAAAIbmlzdHAyNTYAAABBBMli3FZmz2PlHCGinbPc7yYHGdjj037UPzoBuNlKwOyDO5JfHE3G81PheGIiuqcaZSYqxnTysa/X0fnNAuZRejI="),
    ("dl380ws06", "ssh-ed25519", "AAAAC3NzaC1lZDI1NTE5AAAAILq44YUHEbz9LGd2Fbuaaxkh1rIjxyF0ElStXODKhGfE"),
    ("dl380ws06", "ssh-rsa",
     "AAAAB3NzaC1yc2EAAAADAQABAAABgQCimHCSTUTVOdr6/Egw8O9Y7/q6jmFYDMDm8gPbfecaQB+Gtp+2+FmLv30D5rA5uEhqgND8xuM1FI1zpXhu/MChdA3SA/GMwPSGRz8B45gLQCjdd7O9Jn+rVetSKxNOXJaKMKmoQLKWCTbyTi5VRsG6HPWtiWcVcmlfBt8nrx/RW4ZDidr6kGTjjxpBYdjsUuyCtVG85OIwD9GdYSwKWPInUYWl6adh/9V4nrwuGfjgr47+9PR5Qi35DyNP1lzLqSbyiGMRBSUueuVIb6ZGNgxRnxjiO7dBToh8GaYLN/3MHTqptV8F/zNZ+yqakAIM9efVMdx3tp/CNYFRd/lMc7GGzD28N+1RqRwlvwqQlXG3H5Ay9+1kOFBa+rhFt8iUG1AMv5VyQPTa2rlIGW3sdL8pnkl4wf9D1VitC4CFl0s7OYPinfM0R3bBHq0LvPQaSqJRH2vXv3aA5akcEANQKs8W+Bq5a698+ghMF83wd/cU4Ghe+5higrsDMZsAAZMb3ic=")
]


#################################################################################
# Function to implement the login method for the gui
#################################################################################
class LoginForm(QWidget):
    # Creates the login form and adds the function to call when the login button is pressed
    def __init__(self, host, temp_dir):
        super().__init__()
        self.temp_dir = temp_dir
        self.host = host
        self.setWindowTitle('Login Form')
        self.resize(500, 120)

        layout = QGridLayout()

        label_name = QLabel('<font size="4"> Όνομα Χρήστη: </font>')
        self.lineEdit_username = QLineEdit()
        self.lineEdit_username.setPlaceholderText('Παρακαλώ εισάγετε το όνομα χρήστη σας.')
        layout.addWidget(label_name, 0, 0)
        layout.addWidget(self.lineEdit_username, 0, 1)

        label_password = QLabel('<font size="4"> Κωδικός Πρόσβασης: </font>')
        self.lineEdit_password = QLineEdit()
        self.lineEdit_password.setEchoMode(QLineEdit.Password)
        self.lineEdit_password.setPlaceholderText('Παρακαλώ εισάγετε τον κωδικό πρόσβασής σας.')
        layout.addWidget(label_password, 1, 0)
        layout.addWidget(self.lineEdit_password, 1, 1)

        button_login = QPushButton('Είσοδος')
        button_login.setDefault(True)
        button_login.clicked.connect(self.send)
        layout.addWidget(button_login, 2, 0, 1, 2)
        layout.setRowMinimumHeight(2, 75)
        self.lineEdit_password.returnPressed.connect(self.send)
        self.lineEdit_username.returnPressed.connect(self.send)
        self.setLayout(layout)

    def send(self):
        username = self.lineEdit_username.text()
        password = self.lineEdit_password.text()
        turn_in(username, password, self.host, self.temp_dir, True)

    # def upload_files(files, username, password, ssh, host, temp_dir):


#################################################################################
# Functions to implement the functionality of the turnin application
#################################################################################

def turn_in(username, password, host, temp_dir, ask_to_save=False):
    result, host_to_connect, ssh = get_host(username, password, host, ask_to_save)
    if not result:
        msg = QMessageBox()
        msg.setText('Wrong Password! Please try again.')
        msg.exec_()
        return -1
    files = getFiles()
    remote_dir, remote_paths = upload_files(files, username, password, ssh, host, temp_dir)
    ssh.close()
    assignment, okPressed = QInputDialog.getText(None, "Άσκηση:", "Ο κωδικός της άσκησης:", QLineEdit.Normal, "")
    if okPressed and assignment != '':
        run_command_to_turn_in(host, username, password, host_to_connect, remote_dir, assignment, remote_paths)


def add_ssh_keys(ssh):
    known_hosts_path = "known_hosts_file"
    if not os.path.exists(known_hosts_path):
        with open(known_hosts_path, "a") as known_hosts_file:
            for host_key in ssh_keys:
                # Format the host key entry
                host_key_entry = f"{host_key[0]} {host_key[1]} {host_key[2]}\n"

                # Write the host key entry to the known_hosts file
                known_hosts_file.write(host_key_entry)

    ssh.load_host_keys(known_hosts_path)
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())


def getFiles():
    options = QFileDialog.Options()
    files, _ = QFileDialog.getOpenFileNames(None, "Επιλέξτε τα αρχεία που θέλετε να παραδώσετε:", "", "All Files (*)",
                                            options=options)
    while True:
        if files:
            # Ask for confirmation
            confirm_msg = QMessageBox()
            confirm_msg.setIcon(QMessageBox.Question)
            filelist = "\n".join(files)
            confirm_msg.setText("Are you sure you want to upload the selected files?\n\n" + filelist)

            confirm_msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
            confirm_response = confirm_msg.exec_()

            if confirm_response == QMessageBox.Yes:
                break
            files, _ = QFileDialog.getOpenFileNames(None, "Επιλέξτε τα αρχεία που θέλετε να παραδώσετε:", "",
                                                    "All Files (*)", options=options)
        else:
            break
    return files


def get_host(username, password, host, ask_to_save=False):
    try:
        ssh = paramiko.SSHClient()
        add_ssh_keys(ssh)
        try:
            ssh.connect(proxy, username=username, password=password)
        except paramiko.ssh_exception.SSHException as e:
            print("Wrong key")
            message = QMessageBox()
            message.setText(str(e))
            message.setIcon(QMessageBox.Critical)
            message.exec_()
            exit()
        _, ssh_stdout, ssh_stderr = ssh.exec_command("rupt")
        servers = ssh_stdout.readlines()
        host_to_connect = None
        for server in servers:
            server = server.split()
            host_name = server[0]
            host_is_up = (server[1] == "up")
            if host_is_up and ("dl" in host_name):
                host_to_connect = host_name
                print(f"{host_name} -> is up: {host_is_up}")
                break
        if not host_to_connect:
            print("No host to connect to has been found. Aborting...")
            exit(-1)
        else:

            if ask_to_save:
                confirm_msg = QMessageBox()
                confirm_msg.setIcon(QMessageBox.Question)
                confirm_msg.setText("Do you want to save your credentials?")

                confirm_msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
                confirm_response = confirm_msg.exec_()

                if confirm_response == QMessageBox.Yes:
                    # store the data in an encrypted format
                    data = {
                        'username': username,
                        'password': password
                    }
                    serialized_data = json.dumps(data).encode('utf-8')
                    # Generate or retrieve encryption key
                    key = get_key()
                    cipher_suite = Fernet(key)
                    # Encrypt the serialized data
                    encrypted_data = cipher_suite.encrypt(serialized_data)
                    # Save the encrypted data to a file
                    with open('creds.bin', 'wb') as f:
                        f.write(encrypted_data)
            return True, host_to_connect, ssh
    except paramiko.AuthenticationException:
        return False, None, None


def upload_files(files, username, password, ssh, host, temp_dir):
    _, ssh_stdout, ssh_stderr = ssh.exec_command("pwd")
    home_dir = ssh_stdout.readlines()[0][:-1]
    transport = paramiko.Transport((host, 22))
    transport.connect(None, username, password)
    sftp = paramiko.SFTPClient.from_transport(transport)
    if files:
        remote_dir = f"{home_dir}/{temp_dir}/"
        print(remote_dir)
        try:
            sftp.mkdir(remote_dir)
        except:
            print("Could not create directory.")
        remote_paths = []
        for localpath in files:
            name = os.path.basename(localpath)
            filepath = "{}{}".format(remote_dir, name)
            try:
                sftp.put(localpath, filepath)
                remote_paths.append(name)
                print("Localpath was successfully uploaded to server.")
            except Exception as e:
                print("Could not upload file: " + str(e))
        return remote_dir, remote_paths
    else:
        msg = QMessageBox()
        msg.setText('No Files were selected! Cannot continue with the turn in.')
        msg.exec_()
        app.quit()
        exit()


def run_command_to_turn_in(host, username, password, host_to_connect, remote_dir, assignment, remote_paths):
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
        except paramiko.ssh_exception.SSHException as e:
            message = QMessageBox()
            message.setText(str(e))
            message.setIcon(QMessageBox.Critical)
            message.exec_()
            exit()
        turn_in_command = f"cd {remote_dir}&&yes|turnin {assignment} {' '.join(remote_paths)}"
        _, ssh_stdout, ssh_stderr = ssh.exec_command(turn_in_command)
        ssh.exec_command(f"rm -R {remote_dir}")
        msg = QMessageBox()
        msg.setText(f"{''.join(ssh_stdout.readlines())}\n\n{''.join(ssh_stderr.readlines())}")
        msg.exec_()

        ssh.close()


#################################################################################
# Functions for the encryption and Decryption of the credentials
#################################################################################
# generate key to encrypt and decrypt the credentials
def generate_key():
    key = Fernet.generate_key()
    keyring.set_password("turnin", "encryption_key", key.decode("utf-8"))
    return key


# get the key if one has already been generated
def get_key():
    key = keyring.get_password("turnin", "encryption_key")
    if key is None:
        key = generate_key()
    return key


def get_credentials_from_file():
    with open('creds.bin', 'rb') as f:
        encrypted_data = f.read()

    # Retrieve encryption key
    key = get_key()
    cipher_suite = Fernet(key)

    # Decrypt the encrypted data
    try:
        decrypted_data = cipher_suite.decrypt(encrypted_data)
    except InvalidToken as e:
        msg = QMessageBox()
        msg.setText("Something went wrong while reading the encrypted password.\nExiting...")
        msg.exec_()
        exit()

    # Deserialize the decrypted data
    deserialized_data = json.loads(decrypted_data.decode('utf-8'))

    # Access username and password
    username = deserialized_data['username']
    password = deserialized_data['password']
    return username, password


def check_version():
    # GitHub repository information
    github_repo = "porfanid/TurnIn"  # Replace with the username and repository name
    github_token = None  # Replace with your GitHub Personal Access Token if needed, or set to None

    # Current version of your software
    # current_version = "version3.1"
    current_version = "version3.2"
    # Construct the API URL
    api_url = f"https://api.github.com/repos/{github_repo}/releases/latest"

    # Include your GitHub token if you have rate limiting issues or need authentication
    headers = {}
    if github_token:
        headers["Authorization"] = f"token {github_token}"

    # Send a GET request to the GitHub API
    response = requests.get(api_url, headers=headers)

    if response.status_code == 200:
        latest_release = response.json()
        latest_version = latest_release["tag_name"]
        print(latest_version)
        print(current_version)

        if latest_version != current_version:
            link = f"https://github.com/porfanid/TurnIn/releases/tag/{latest_version}"
            update_message = QMessageBox()
            update_message.setWindowTitle("Update Required")
            update_message.setText("Please update to the latest version")
            download_button = update_message.addButton("Download", QMessageBox.AcceptRole)

            def download_link(self):
                QDesktopServices.openUrl(QtCore.QUrl(link))

            download_button.clicked.connect(download_link)
            update_message.exec_()
            exit()
        else:
            print("Your software is up to date.")
    else:
        print(f"Failed to retrieve release information. Status code: {response.status_code}")


########################################################
# Main Application starting
########################################################
if __name__ == '__main__':
    app = QApplication([])
    check_version()
    proxy = "scylla.cs.uoi.gr"
    temp_dir = "turnin"

    if os.path.exists("creds.bin"):
        username, password = get_credentials_from_file()
        confirm_msg = QMessageBox()
        confirm_msg.setIcon(QMessageBox.Question)
        confirm_msg.setText(f"Do you want to use the account \"{username}\" saved in the creds.bin file?")

        confirm_msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        confirm_response = confirm_msg.exec_()

        if confirm_response == QMessageBox.Yes:
            turn_in(username, password, proxy, temp_dir)
            app.quit()
            exit()

    form = LoginForm(proxy, temp_dir)
    form.show()
    exit(app.exec_())