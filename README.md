# TurnIn

This is a program designed to be used with the turn in system at the [University of Ioannina](https://www.uoi.gr/).

## Use the app

To use the app you need to have python installed on your system.

After you have done this, you are going to have to install the dependencies. Yu can do this by going to the project using a terminal and the command cd and entering the following command:
```bash
pip install -r requirements.txt
```
This will take some time, as it needs to check the dependencies for the GUI and make sure that everything has been installed successfully


Every time you need to use the app, you are going to have to run one of these commands based on the operating system you have installd on your computer:

On Windows:
```bash
py turnin.py
```
On Linux:
```bash
python3 turnin.py
```

And you start entering what the app asks you to enter. Pease refer to the screenshots for a more detailed preview.


## Test turnin

You can test the turnin app by using the assignment: `test@cse74134`.

> Please remember that in this particular assignment you cannot turn in binary files. See the notes [George Zachos](https://gzachos.com/) made for the [TurnIn](https://www.cse.uoi.gr/~gzachos/turnin/students.html)


## Screenshots

1. First you are presented with the login screen![enter credentials](images/insert_username.png)
1. You enter the credentials that you use in the computer lab(ΠΕΠ 1, ΠΕΠ 2, ΠΕΛΣ)![credentials](images/username.png)
1. You select the files you want to upload(You are to select all the files you want to turnin in this step)![select files](images/select_files.png)
1. You are presented with a box to enter the assignement![enter assignment code](images/insert_assignment.png)
1. You write the assignment code![assignment code](images/assignment.png)
1. You are presented with the output of the turnin command![turnin result](images/turn_in_result.png)