# importing sentry sdk for error reporting
import sentry_sdk
sentry_sdk.init("https://39a7dcc277c54f658ddf7c47deda2a9e@o238115.ingest.sentry.io/5236153")
# ssh tunnel, socket and paramiko for the ssh and sftp commands for the turn in
import sshtunnel
import paramiko
import socket

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
		button_login.clicked.connect(self.check_password)
		layout.addWidget(button_login, 2, 0, 1, 2)
		layout.setRowMinimumHeight(2, 75)
		self.lineEdit_password.returnPressed.connect(self.check_password)
		self.lineEdit_username.returnPressed.connect(self.check_password)
		self.setLayout(layout)

	def check_password(self):
		# creates the message object and reads the username and the password from the textboxes
		msg = QMessageBox()
		username = self.lineEdit_username.text()
		password = self.lineEdit_password.text()
		
		# tries to connect to ssh server and if not, shows the wr
		try:
			ssh = paramiko.SSHClient()
			ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())		
			ssh.connect(proxy, username=username, password=password)
			_, ssh_stdout, ssh_stderr = ssh.exec_command("rupt")
			servers=ssh_stdout.readlines()
			_, ssh_stdout, ssh_stderr = ssh.exec_command("pwd")
			home_dir=ssh_stdout.readlines()[0][:-1]
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
				
         
			options = QFileDialog.Options()
			files, _ = QFileDialog.getOpenFileNames(self,"Επιλέξτε τα αρχεία που θέλετε να παραδώσετε:", "","All Files (*)", options=options)
			transport = paramiko.Transport((self.host,22))
			transport.connect(None,username,password)
			sftp = paramiko.SFTPClient.from_transport(transport)
			if files:
				remote_dir=f"{home_dir}/{self.temp_dir}/"
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
				text, okPressed = QInputDialog.getText(self, "Άσκηση:","Ο κωδικός της άσκησης:", QLineEdit.Normal, "")
				if okPressed and text != '':
					turn_in_command = f"cd {remote_dir}&&yes|turnin {text} {' '.join(remote_paths)}"
					print(turn_in_command)
					
					with sshtunnel.open_tunnel(
						(self.host, 22),
						ssh_username=username,
						ssh_password=password,
						remote_bind_address=(host_to_connect, 22),
						local_bind_address=('0.0.0.0', 10022)
					) as _:
						client = paramiko.SSHClient()
						client.load_system_host_keys()
						client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
						client.connect('127.0.0.1', 10022, username=username, password=password)
						_, ssh_stdout, ssh_stderr = client.exec_command(turn_in_command)
						client.exec_command(f"rm -R {remote_dir}")
						msg.setText(f"{''.join(ssh_stdout.readlines())}\n\n{''.join(ssh_stderr.readlines())}")
						msg.exec_()
						
						client.close()
			else:
				msg.setText('No Files were selected! Cannot continue with the turn in.')
				msg.exec_()
				app.quit()
		except paramiko.AuthenticationException:
			msg.setText('Wrong Password! Please try again.')
			msg.exec_()
	

if __name__ == '__main__':
	proxy="scylla.cs.uoi.gr"
	app = QApplication([])
	form = LoginForm(proxy,"turnin")
	form.show()

	exit(app.exec_())
