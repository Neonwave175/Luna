import json
import os
import shutil
import subprocess

from rich.console import Console


class package:
    def __init__(self, nme, console: Console | None = None) -> None:
        self.name = nme
        self.compile = ""
        self.cfg = ""
        self.install = ""
        self.origin = ""
        self.curcom = ""
        self.console = console or Console()

    def jsonparse(self) -> bool:
        dir_path = os.path.expanduser("~/.local/lunaorigin")
        recipe_path = os.path.join(dir_path, f"{self.name}.json")
        if not os.path.isfile(recipe_path):
            self.console.print(f"[yellow]Package '{self.name}' not found[/yellow]")
            return False
        with open(recipe_path, "r") as j:
            dat = json.load(j)
        self.compile = dat.get("Compile", "")
        self.cfg = dat.get("Config", "")
        self.curcom = dat.get("Commit", "")
        self.install = dat.get("Install", "")
        self.origin = dat.get("URL", "")
        return True

    def get_commit(self) -> str:
        if not self.origin:
            return ""
        result = subprocess.run(
            ["git", "ls-remote", self.origin, "HEAD"],
            capture_output=True, text=True, check=True
        )
        parts = result.stdout.split()
        return parts[0] if parts else ""

    def jsonupdate(self) -> None:
        dat = {
            "URL": self.origin,
            "Commit": self.curcom,
            "Config": self.cfg,
            "Compile": self.compile,
            "Install": self.install
        }
        dir_path = os.path.expanduser("~/.local/lunaorigin")
        os.makedirs(dir_path, exist_ok=True)
        with open(os.path.join(dir_path, f"{self.name}.json"), "w") as j:
            json.dump(dat, j, indent=4)

    def cmpl(self) -> None:
        if not self.jsonparse():
            return
        latest = self.get_commit()
        if not latest:
            self.console.print(f"[red]Could not fetch remote commit for {self.name}[/red]")
            return
        dest = os.path.expanduser(f"~/.local/lunasource/{self.name}")

        if latest == self.curcom and os.path.isdir(dest):
            return
        self.curcom = latest

        os.makedirs(os.path.expanduser("~/.local/lunasource"), exist_ok=True)

        if os.path.exists(dest):
            shutil.rmtree(dest)

        subprocess.run(["git", "clone", "--depth", "1", self.origin, dest], check=True)
        self.console.print(f"[cyan]downloaded[/cyan] {self.name}")

        if self.cfg:
            subprocess.run(self.cfg, cwd=dest, shell=True, check=True)
        if self.compile:
            subprocess.run(self.compile, cwd=dest, shell=True, check=True)
            self.console.print(f"[cyan]compiled[/cyan] {self.name}")

    def ins(self) -> None:
        dest = os.path.expanduser(f"~/.local/lunasource/{self.name}")
        if not os.path.isdir(dest):
            return
        if self.install:
            subprocess.run(self.install, cwd=dest, shell=True, check=True)
        self.jsonupdate()
        self.console.print(f"[green]installed[/green] {self.name}")
