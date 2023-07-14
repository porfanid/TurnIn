import os

print("Do you want to create a Desktop Icon?")
path = os.getcwd()
pyis = f"pyinstaller --onefile --clean -n TurninApp --distpath {path}\\installerTemp\\dist --workpath {path}\\installerTemp\\build --specpath {path}\\installerTemp {path}\\turnin.py"

os.system(f'cmd /c "{pyis}"')

print(path)
print(pyis)