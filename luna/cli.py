import argparse
import json
import os
import subprocess
import sys

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
        recipe_path = f"{LUNAORIGIN}/{name}.json"
        if os.path.isfile(recipe_path):
            try:
                with open(recipe_path, "r") as j:
                    dat = json.load(j)
                dat["Commit"] = ""
                with open(recipe_path, "w") as j:
                    json.dump(dat, j, indent=4)
            except (json.JSONDecodeError, OSError) as e:
                console.print(f"[yellow]warning: could not clear commit for '{name}': {e}[/yellow]")
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


def _looks_like_lunafile(path: str) -> bool:
    if path.endswith(".json") or path.endswith(".luna"):
        return True
    if os.path.isfile(path):
        try:
            with open(path) as f:
                return isinstance(json.load(f), list)
        except Exception:
            return False
    return False


def cmd_sync(path: str) -> None:
    if not os.path.isfile(path):
        console.print(f"[red]'{path}' not found[/red]")
        raise SystemExit(1)
    try:
        with open(path) as f:
            data = json.load(f)
    except Exception as e:
        console.print(f"[red]could not parse '{path}': {e}[/red]")
        raise SystemExit(1)
    if not isinstance(data, list):
        console.print(f"[red]'{path}' must contain a JSON array of packages[/red]")
        raise SystemExit(1)
    names: list = []
    for spec in data:
        if not isinstance(spec, dict):
            continue
        name = spec.get("Name", "")
        url = spec.get("URL", "")
        if not name or not url:
            console.print("[yellow]skipping entry without Name/URL[/yellow]")
            continue
        cmd_add(name, url, spec.get("Compile", ""), spec.get("Config", ""), spec.get("Install", ""))
        names.append(name)
    if not names:
        console.print(f"[yellow]no packages found in '{path}'[/yellow]")
        return
    cmd_install(names)


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

    p_sync = subparsers.add_parser("sync", help="register and install every package in a JSON lunafile")
    p_sync.add_argument("file", help="path to a JSON lunafile")

    return parser


def main() -> None:
    if len(sys.argv) == 2 and _looks_like_lunafile(sys.argv[1]):
        cmd_sync(sys.argv[1])
        return
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
    elif args.command == "sync":
        cmd_sync(args.file)


if __name__ == "__main__":
    main()
