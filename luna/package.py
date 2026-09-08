import json
import subprocess
import os

class package:
    def __init__(self, nme) -> None:
        self.name = nme
        self.compile = ""
        self.cfg = ""
        self.install = ""
        self.origin = ""
        self.curcom = ""

    def jsonparse(self) -> None:
        dir_path = os.path.expanduser("~/.local/lunaorigin")
        try:
            with open(f"{dir_path}/{self.name}.json", "r") as j:
                dat = json.load(j)
        except FileNotFoundError:
            print("Package Not Found")
        self.compile = dat["Compile"]
        self.cfg = dat["Config"]
        self.curcom = dat["Commit"]
        self.install = dat["Install"]
        self.origin = dat["URL"]

    def get_commit(self) -> str:
        result = subprocess.run(
            ["git", "ls-remote", self.origin, "HEAD"],
            capture_output=True, text=True, check=True
        )
        return result.stdout.split()[0]

    def jsonupdate(self) -> None:
        dat = {
            "URL": self.origin,
            "Commit": self.curcom,
            "Config": self.cfg,
            "Compile": self.compile,
            "Install": self.install
        }
        dir_path = os.path.expanduser("~/.local/lunaorigin")
        subprocess.run(["mkdir", "-p", dir_path], check=True,
                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        with open(f"{dir_path}/{self.name}.json", "w") as j:
            json.dump(dat, j, indent=4)

    def cmpl(self) -> None:
        self.jsonparse()
        latest = self.get_commit()
        dest = os.path.expanduser(f"~/.local/lunasource/{self.name}")

        if latest == self.curcom and os.path.isdir(dest):
            return
        self.curcom = latest

        subprocess.run(["mkdir", "-p", os.path.expanduser("~/.local/lunasource")],
                        check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        try:
            subprocess.run(["git", "clone", "--depth", "1", self.origin, dest], check=True,
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except subprocess.CalledProcessError:
            subprocess.run(["rm", "-rf", dest], check=True,
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            subprocess.run(["git", "clone", "--depth", "1", self.origin, dest], check=True,
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print(f"downloaded {self.name}")

        if self.cfg:
            subprocess.run(self.cfg, cwd=dest, shell=True, check=True,
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run(self.compile, cwd=dest, shell=True, check=True,
                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print(f"compiled {self.name}")


    def ins(self) -> None:
        dest = os.path.expanduser(f"~/.local/lunasource/{self.name}")
        subprocess.run(self.install, cwd=dest, shell=True, check=True,
                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        self.jsonupdate()
        print(f"installed {self.name}")
