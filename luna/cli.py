import argparse
import json
import os
import subprocess

from rich.console import Console
from .package import package

LUNAORIGIN = os.path.expanduser("~/.local/lunaorigin")
console = Console()


def cmd_install(names: list[str]) -> None:
    for name in names:
        pkg = package(name, console=console)
        try:
            with console.status(f"[cyan]building {name}...", spinner="dots"):
                pkg.cmpl()
            with console.status(f"[cyan]installing {name}...", spinner="dots"):
                pkg.ins()
            console.print(f"[green]✓[/green] {name} installed")
        except subprocess.CalledProcessError as e:
            console.print(f"[red]✗[/red] {name} failed: {e}")


def cmd_remove(name: str) -> None:
    source_path = os.path.expanduser(f"~/.local/lunasource/{name}")
    bin_path = os.path.expanduser(f"~/.local/luna/{name}")
    removed_something = False
    if os.path.isdir(source_path):
        subprocess.run(["rm", "-rf", source_path], check=True)
        removed_something = True

    if os.path.isfile(bin_path) or os.path.islink(bin_path):
        os.remove(bin_path)
        removed_something = True

    if removed_something:
        console.print(f"[green]removed[/green] {name}")
    else:
        console.print(f"[yellow]'{name}' not found[/yellow]")


def cmd_add(name: str, url: str, compile_cmd: str, config_cmd: str = "", install_cmd: str = "") -> None:
    os.makedirs(LUNAORIGIN, exist_ok=True)
    dat = {
        "URL": url,
        "Commit": "",
        "Config": config_cmd,
        "Compile": compile_cmd,
        "Install": install_cmd
    }
    with open(f"{LUNAORIGIN}/{name}.json", "w") as j:
        json.dump(dat, j, indent=4)
    console.print(f"[green]added[/green] {name}")


def cmd_list() -> None:
    if not os.path.isdir(LUNAORIGIN):
        console.print("no packages registered")
        return
    names = sorted(f[:-5] for f in os.listdir(LUNAORIGIN) if f.endswith(".json"))
    if not names:
        console.print("no packages registered")
        return
    for name in names:
        with open(f"{LUNAORIGIN}/{name}.json") as j:
            dat = json.load(j)
        status = "[green]installed[/green]" if dat.get("Commit", "") else "[yellow]not built[/yellow]"
        console.print(f"  {name}  [{status}]")


def cmd_update() -> None:
    if not os.path.isdir(LUNAORIGIN):
        console.print("no packages registered")
        return
    names = sorted(f[:-5] for f in os.listdir(LUNAORIGIN) if f.endswith(".json"))
    if not names:
        console.print("no packages registered")
        return

    updated = []
    failed = []

    for name in names:
        pkg = package(name, console=console)
        pkg.jsonparse()

        if pkg.curcom == "":
            continue

        try:
            with console.status(f"[cyan]checking {name}...", spinner="dots"):
                latest = pkg.get_commit()
                dest = os.path.expanduser(f"~/.local/lunasource/{name}")
                needs_update = not (latest == pkg.curcom and os.path.isdir(dest))

            if not needs_update:
                continue

            with console.status(f"[cyan]updating {name}...", spinner="dots"):
                pkg.cmpl()
                pkg.ins()
            updated.append(name)

        except subprocess.CalledProcessError as e:
            failed.append(name)
            console.print(f"[red]✗[/red] {name} failed: {e}")

    if updated:
        console.print(f"[green]updated:[/green] {', '.join(updated)}")
    else:
        console.print("everything up to date")
    if failed:
        console.print(f"[red]failed:[/red] {', '.join(failed)}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="luna", description="Luna package manager")
    subparsers = parser.add_subparsers(dest="command")

    p_install = subparsers.add_parser("install", help="build and install one or more packages")
    p_install.add_argument("packages", nargs="+", help="package name(s) to install")

    p_add = subparsers.add_parser("add", help="register a new package source")
    p_add.add_argument("name", help="package name")
    p_add.add_argument("url", help="source repository URL")
    p_add.add_argument("compile_cmd", help="command used to compile the package")
    p_add.add_argument("config_cmd", nargs="?", default="", help="optional configure command")
    p_add.add_argument("install_cmd", nargs="?", default="", help="optional install command")

    subparsers.add_parser("list", help="list registered packages")

    subparsers.add_parser("update", help="update all installed packages")

    p_remove = subparsers.add_parser("remove", help="remove a package")
    p_remove.add_argument("package", help="package name to remove")

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        raise SystemExit(1)

    if args.command == "install":
        cmd_install(args.packages)
    elif args.command == "add":
        cmd_add(args.name, args.url, args.compile_cmd, args.config_cmd, args.install_cmd)
    elif args.command == "list":
        cmd_list()
    elif args.command == "update":
        cmd_update()
    elif args.command == "remove":
        cmd_remove(args.package)


if __name__ == "__main__":
    main()
