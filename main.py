from __future__ import annotations
from platformdirs import AppDirs
from pathlib import Path
import subprocess
import os


def getDownloadsFolder() -> Path:
    osIsWindows = os.name == "nt"
    if osIsWindows:
        userprofile = os.getenv("USERPROFILE")
        if userprofile is None:
            raise TypeError("var userprofile should not be None!")
        downloads = Path(userprofile) / "Downloads"
    else:
        downloads = Path.home() / "Downloads"
    if downloads.exists() and downloads.is_dir():
        return downloads
    else:
        raise FileNotFoundError("Downloads folder not found")


def isGpgAvailable() -> bool:
    """
    Check if GPG is installed and accessible in the system's PATH.

    Returns:
        bool: True if GPG is available, False otherwise.
    """
    try:
        # Run 'gpg --version' and check for a successful return code
        subprocess.run(["gpg", "--version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def encryptWithGpg(input_file: str, output_file: str, password: str) -> None:
    subprocess.run([
        "gpg", "--symmetric", "--cipher-algo", "AES256", "--passphrase", password, 
        "--batch", "--yes", "-o", output_file, input_file
    ])


def decryptWithGpg(input_file: str, output_file: str, password: str) -> None:
    subprocess.run([
        "gpg", "--decrypt", "--passphrase", password, 
        "--batch", "--yes", "-o", output_file, input_file
    ])


class Tag:

    def __init__(self, name: str, children: list[Tag] = []) -> None:
        self.name: str = name
        self.children: list[Tag] = children

    def print(self, indAmt: int = 0) -> None:
        print(self.name)
        ind = "".join(["   " for _ in range(indAmt)])
        for i in self.children:
            print(f"{ind}|- ", end="")
            i.print(indAmt + 1)


class Task(Tag):

    def __init__(self, name: str, children: list[Tag] = []) -> None:
        super().__init__(name, children)


class TaggedTodo:

    class QuitProgram(Exception):
        pass

    def __init__(self) -> None:
        self.appDirs = AppDirs(appname="tagged_todo", appauthor="duom1")
        self.dataDir = self.appDirs.user_data_dir
        if not os.path.isdir(self.dataDir):
            try:
                os.mkdir(self.dataDir)
            except PermissionError as e:
                print(f"unable to create dir: {self.dataDir}\n{e}")
        self.downloadDir = getDownloadsFolder()
        self.dbPath = f"{self.dataDir}/database.txt"

    def helpPage(self) -> None:
        padding = 20
        print("\nThis an help page for tagged todo\nCommands available:\n"
              f"\t{"help" : <{padding}}Shows this page.\n"
              f"\t{"paths" : <{padding}}Shows the paths used by the program.\n"
              f"\t{"check-gpg" : <{padding}}Checks if gpg is available.\n"
              f"\t{"test" : <{padding}}for testing.\n"
              f"\t{"quit/exit" : <{padding}}Quits the program.\n")

    def backUp(self) -> None:
        pass

    def printPaths(self) -> None:
        print(f"{self.dataDir}\n{self.dbPath}\n{self.downloadDir}")

    def testGpg(self) -> None:
        if isGpgAvailable():
            print("GPG is available")
        else:
            print("GPG is NOT available")

    def run(self) -> None:
        print("Welcome to tagged todo!\nDo help to see help page.")
        while True:
            try:
                cmd = input("> ").lower()
                if cmd == "help":
                    self.helpPage()
                elif cmd in ["quit", "exit"]:
                    raise self.QuitProgram
                elif cmd == "paths":
                    self.printPaths()
                elif cmd == "check-gpg":
                    self.testGpg()
                elif cmd == "test":
                    with open(self.dbPath, "wt") as f:
                        f.write("hello world")
                else:
                    print("Unkown command please try again!")
            except (KeyboardInterrupt, self.QuitProgram):
                try:
                    if input("\nAre you sure you want to quit (y/n): ").lower() == "y":
                        break;
                except KeyboardInterrupt:
                    pass


def main() -> None:
    TaggedTodo().run()


if __name__ == "__main__":
    main()
