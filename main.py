from __future__ import annotations
from typing import Any
from platformdirs import AppDirs
from pathlib import Path
from getpass import getpass
import time
import toml
import shutil
import subprocess
import os


def getYN(text: str) -> bool:
    while True:
        yn = input(text).lower()
        if yn == "y":
            return True
        elif yn == "n":
            return False
        else:
            print("Invalid inpout please try again!")


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
        subprocess.run(["gpg", "--version"], stdout=subprocess.PIPE,
                       stderr=subprocess.PIPE, check=True)
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

    def addTags(self, tag: list[Tag]) -> None:
        self.children = [*self.children, *tag]

    def print(self, indAmt: int = 0) -> None:
        print(self.name)
        ind = "".join(["   " for _ in range(indAmt)])
        for i in self.children:
            print(f"{ind}|- ", end="")
            i.print(indAmt + 1)

    def getName(self) -> str:
        return self.name

    def getChilder(self) -> list[Tag]:
        return self.children


class Task(Tag):

    def __init__(self, name: str, children: list[Tag] = [], timeStamp: int | None = None) -> None:
        super().__init__(name, children)
        if timeStamp is None:
            self.createdOn = int(time.time())
        else:
            self.createdOn = timeStamp

    def print(self, indAmt: int = 0) -> None:
        print(f"Created on: {self.createdOn}")
        super().print(indAmt)


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
        self.dbPath = f"{self.dataDir}/tasks.toml"
        self.backUp()
        self.madeChanges = False
        self.db = self.openDb()
        self.taskList = self.getTasksFromDb(self.db)

    def treeToTags(self, tree: dict[str, Any]) -> list[Tag]:
        tags: list[Tag] = []
        for i in tree:
            tags.append(Tag(i))
            for j in tree[i]:
                tags[-1].addTags([Tag(j, self.treeToTags(tree[i][j]))])
        return tags

    def tagsToTree(self, tags: list[Tag]) -> dict[str, Any]:
        tree = {}
        for i in tags:
            itree = self.tagsToTree(i.getChilder())
            tree.update({i.getName(): itree})
        return tree

    def getTasksFromDb(self, db) -> list[Task]:
        tasks = []
        for i in db["tasks"]:
            tagsTree = db["tasks"][i]["tags"]
            time = db["tasks"][i]["time"]
            tags: list[Tag] = self.treeToTags(tagsTree)
            tasks.append(Task(i, tags, time))
        return tasks

    def addListToDb(self) -> None:
        for i in self.taskList:
            tree = self.tagsToTree(i.getChilder())
            self.db["tasks"].update({i.name: {"time": i.createdOn, "tags": tree}})

    def saveDb(self) -> None:
        self.addListToDb()
        data = toml.dumps(self.db)
        with open(self.dbPath, "w") as f:
            f.write(data)

    def openDb(self) -> dict[str, Any]:
        try:
            dataStr = open(self.dbPath, "r").read()
            data = toml.loads(dataStr)
            if not "description" in data:
                data["description"] = "This is a data file for tagged todo program written by duom1"
                self.madeChanges = True
            if not "tasks" in data:
                data["tasks"] = {}
                self.madeChanges = True
            return data
        except FileNotFoundError:
            open(self.dbPath, "a").close()
        self.openDb()
        return {"": None}

    def backUp(self) -> None:
        shutil.copyfile(self.dbPath, f"{self.dbPath}.bak")

    def helpPage(self) -> None:
        padding = 20
        print("\nThis an help page for tagged todo\nCommands available:\n"
              f"\t{"help": <{padding}}Shows this page.\n"
              f"\t{"paths": <{padding}}Shows the paths used by the program.\n"
              f"\t{"check-gpg": <{padding}}Checks if gpg is available.\n"
              f"\t{"export": <{padding}}Export an encrypted database file.\n"
              f"\t{"import": <{padding}}Import an encrypted database file.\n"
              f"\t{"backup": <{padding}}Creates a backup file.\n"
              f"\t{"qns": <{padding}}Stands for Quit No Save and it exists without saving.\n"
              f"\t{"save": <{padding}}Save changes to database file.\n"
              f"\t{"add": <{padding}}Adds a task.\n"
              f"\t{"print/list/ls": <{padding}}Lists out the tasks.\n"
              f"\t{"quit/exit": <{padding}}Quits the program.\n")

    def printPaths(self) -> None:
        print(f"{self.dataDir}\n{self.dbPath}\n{self.downloadDir}")

    def testGpg(self) -> None:
        if isGpgAvailable():
            print("GPG is available")
        else:
            print("GPG is NOT available")

    def exportDatabase(self) -> None:
        if not isGpgAvailable():
            print("Unable to use GPG, please make sure you have installed it!")
            return
        while True:
            try:
                passwd = getpass()
                passwd2 = getpass("Confirm: ")
                if passwd == passwd2:
                    break
                print("Passwords do not match, please try again!")
            except KeyboardInterrupt:
                print("\nAborted exporting!")
                return
        file = self.dbPath
        ef = f"{self.dbPath}.gpg"
        encryptWithGpg(file, ef, passwd)
        shutil.copyfile(
            ef, f"{self.downloadDir}/exported-tagged-todo-data.gpg")

    def addTask(self, task: Task) -> None:
        self.taskList.append(task)

    def getChilderCli(self, path: str) -> list[Tag]:
        tags: list[Tag] = []
        if getYN(f"Do you want to add tags to {path} (y/n): "):
            print("Press ctrl+c to stop.")
            while True:
                try:
                    tags.append(Tag(input(f"Adding tag to {path}: ")))
                    tags[-1].addTags(self.getChilderCli(f"{path}{tags[-1].getName()}/"))
                except KeyboardInterrupt:
                    print("")
                    break
        return tags

    def addTaskCli(self) -> None:
        name: str = input("Name: ")
        tags: list[Tag] = self.getChilderCli("/")
        task = Task(name, tags)
        self.addTask(task)

    def run(self) -> None:
        print("Welcome to tagged todo!\nDo help to see help page.")
        saveOnExit = True
        while True:
            try:
                cmd = input("> ").lower()

                if cmd == "help":
                    self.helpPage()
                elif cmd in ["quit", "exit", "exit()", "quit()"]:
                    raise self.QuitProgram
                elif cmd == "paths":
                    self.printPaths()
                elif cmd == "check-gpg":
                    self.testGpg()
                elif cmd == "export":
                    self.exportDatabase()
                elif cmd == "backup":
                    self.backUp()
                elif cmd == "qns":
                    saveOnExit = False
                    raise self.QuitProgram
                elif cmd in ["print", "list", "ls"]:
                    print("")
                    for i in self.taskList:
                        i.print(0)
                        print("")
                elif cmd == "add":
                    self.addTaskCli()
                    self.madeChanges = True
                elif cmd == "import":
                    print("oops not implemented")
                elif cmd == "save":
                    self.saveDb()
                    self.madeChanges = False

                else:
                    print("Unkown command please try again!")

            except (KeyboardInterrupt, self.QuitProgram):
                try:
                    if getYN("\nAre you sure you want to quit (y/n): "):
                        if saveOnExit and self.madeChanges and getYN("Do you want to save changes (y/n): "):
                            print("Autosaving changes!")
                            self.saveDb()
                        break
                except KeyboardInterrupt:
                    pass


def main() -> None:
    TaggedTodo().run()


if __name__ == "__main__":
    main()
