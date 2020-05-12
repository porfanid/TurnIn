from os import system as execute
from os.path import isdir
from sys import exit

def yes_or_no(message):
	x=input(message)
	while(x!="yes" and x!="no"):
		print("Wrong input Please try again.")
		x=input(message)
	return (x=="yes")

if not (isdir('./.git')):
	x=yes_or_no("Do you want to create a new git repository here?(yes/no) ")
	if (x):
		link=input("Please enter the repository you want to clone(https link prefered): ")
		execute("git clone {}".format(link))
	else:
		print("I cannot run the settings here. You need to run this script in a repository.")
		exit(1)
else:
	upload=yes_or_no("Do you want to upload to git?(yes/no) ")
	if upload:
		execute("git add *")
		message=input("Please enter a message for the upload: ")
		execute("git commit -m '{}'".format(message))
		execute("git push master")
