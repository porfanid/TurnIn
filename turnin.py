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

# os for the path basename to get the name and other controls
import os
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QLabel, QLineEdit, QGridLayout, QMessageBox, QFileDialog, QInputDialog

from PyQt5 import QtGui, QtCore
# system, for the exit function and to get wether the platform is windows or linux
from sys import platform, exit

class LoginForm(QWidget):
# Creates the login form and adds the function to call when the login button is pressed
	def __init__(self,host,temp_dir):
		super().__init__()
		self.temp_dir=temp_dir
		self.host=host
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
		turn_in(username, password, self.host, self.temp_dir)
		
		#def upload_files(files, username, password, ssh, host, temp_dir):


def turn_in(username, password, host, temp_dir):
	result, host_to_connect, ssh = get_host(username, password, host)
	if not result:
		msg=QMessageBox()
		msg.setText('Wrong Password! Please try again.')
		msg.exec_()
		return -1
	files=getFiles()
	remote_dir, remote_paths = upload_files(files, username, password, ssh, host, temp_dir)
	assignment, okPressed = QInputDialog.getText(None, "Άσκηση:","Ο κωδικός της άσκησης:", QLineEdit.Normal, "")
	if okPressed and assignment != '':
		run_command_to_turn_in(host, username, password, host_to_connect, remote_dir, assignment, remote_paths)

def getFiles():
	options = QFileDialog.Options()
	files, _ = QFileDialog.getOpenFileNames(None,"Επιλέξτε τα αρχεία που θέλετε να παραδώσετε:", "","All Files (*)", options=options)
	while True:
		if files:
		# Ask for confirmation
			confirm_msg = QMessageBox()
			confirm_msg.setIcon(QMessageBox.Question)
			filelist="\n".join(files)
			confirm_msg.setText("Are you sure you want to upload the selected files?\n\n"+filelist)

			confirm_msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
			confirm_response = confirm_msg.exec_()

			if confirm_response == QMessageBox.Yes:
				break
			files, _ = QFileDialog.getOpenFileNames(None,"Επιλέξτε τα αρχεία που θέλετε να παραδώσετε:", "","All Files (*)", options=options)
		else:
			break
	return files

def get_host(username, password, host):
	try:
		ssh = paramiko.SSHClient()
		ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())		
		ssh.connect(proxy, username=username, password=password)
		_, ssh_stdout, ssh_stderr = ssh.exec_command("rupt")
		servers=ssh_stdout.readlines()
		host_to_connect = None
		for server in servers:
			server=server.split()
			host_name=server[0]
			host_is_up=(server[1]=="up")
			if host_is_up and ("dl" in host_name):
				host_to_connect=host_name
				print(f"{host_name} -> is up: {host_is_up}")
				break
		if not host_to_connect:
			print("No host to connect to has been found. Aborting...")
			exit(-1)
		else:
			
			
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
	home_dir=ssh_stdout.readlines()[0][:-1]
	transport = paramiko.Transport((host,22))
	transport.connect(None,username,password)
	sftp = paramiko.SFTPClient.from_transport(transport)
	if files:
		remote_dir=f"{home_dir}/{temp_dir}/"
		print(remote_dir)
		try:
			sftp.mkdir(remote_dir)
		except:
			print("Could not create directory.")
		remote_paths=[]
		for localpath in files:
			name=os.path.basename(localpath)
			filepath = "{}{}".format(remote_dir,name)
			try:
				sftp.put(localpath,filepath)
				remote_paths.append(name)
				print("Localpath was successfully uploaded to server.")
			except Exception as e:
				print("Could not upload file: "+str(e))
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
			client = paramiko.SSHClient()
			client.load_system_host_keys()
			client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
			client.connect('127.0.0.1', 10022, username=username, password=password)
			turn_in_command = f"cd {remote_dir}&&yes|turnin {assignment} {' '.join(remote_paths)}"
			_, ssh_stdout, ssh_stderr = client.exec_command(turn_in_command)
			client.exec_command(f"rm -R {remote_dir}")
			msg = QMessageBox()
			msg.setText(f"{''.join(ssh_stdout.readlines())}\n\n{''.join(ssh_stderr.readlines())}")
			msg.exec_()
			
			client.close()

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

if __name__ == '__main__':
	app = QApplication([])
	proxy="scylla.cs.uoi.gr"
	temp_dir="turnin"


	if os.path.exists("creds.bin"):
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

		msg = QMessageBox()
		msg.setText("Credentials where found on disk. Continuing with the turn in.")
		msg.exec_()

		turn_in(username, password, proxy, temp_dir)
		app.quit()
		exit()

	
	form = LoginForm(proxy,temp_dir)
	form.show()

	exit(app.exec_())
