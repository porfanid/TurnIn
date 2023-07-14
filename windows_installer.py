import os

workingDirPath = os.getcwd()

nameOfApp = "TurninApp"
instFolder = f"{workingDirPath}\\installerTemp"

answer = input("Do you want to create a Desktop Icon? Y/N\n")
desktop:bool = answer.upper() == "Y"

if desktop: 
    answer = input(f"Do you want to rename the file? (Default : {nameOfApp}.exe) Y/N\n")
    rename:bool = answer.upper() == "Y"
    if rename: 
        answer = input("Insert new name : ")
        nameOfApp = answer.removesuffix(".exe")

iconpath = "" # TODO

options = f"-w -y -n {nameOfApp} --distpath {instFolder}\\dist --workpath {instFolder}\\build --specpath {instFolder}"

pyInstallerCommand = f"pyinstaller --onefile --clean {options} {workingDirPath}\\turnin.py"

os.system(f'cmd /c "{pyInstallerCommand}"')

if desktop:
    # doesnt always work.
    # For example if user has remapped the Desktop Folder to another location or user has renamed the folder / uses another language.
    # Better implementation uses Windows Registries to fetch the path
    # Also doesnt work for Linux, TODO
    desktopPath = os.path.join(os.path.join(os.environ['USERPROFILE']), 'Desktop')

    if os.path.exists(f"{desktopPath}\\{nameOfApp}.exe"):
        os.remove(f"{desktopPath}\\{nameOfApp}.exe")

    os.rename(f"{instFolder}\\dist\\{nameOfApp}.exe", f"{desktopPath}\\{nameOfApp}.exe")
instFolder = instFolder + "\\dist"
print(f"\nFile '{nameOfApp}.exe' created at location path : {desktopPath if desktop else instFolder}")