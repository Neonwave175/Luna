import json
import os
import subprocess
import sys

from .package import package

LUNAORIGIN = os.path.expanduser("~/.local/lunaorigin")


def cmd_install(names: list[str]) -> None:
    for name in names:
        pkg = package(name)
        try:
            pkg.cmpl()
            pkg.ins()
        except subprocess.CalledProcessError as e:
            print(f"✗ {name} failed: {e}")


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
    print(f"added {name}")


def cmd_list() -> None:
    if not os.path.isdir(LUNAORIGIN):
        print("no packages registered")
        return
    names = sorted(f[:-5] for f in os.listdir(LUNAORIGIN) if f.endswith(".json"))
    if not names:
        print("no packages registered")
        return
    for name in names:
        with open(f"{LUNAORIGIN}/{name}.json") as j:
            dat = json.load(j)
        status = "installed" if dat.get("Commit", "") else "not built"
        print(f"  {name}  [{status}]")


def cmd_update() -> None:
    if not os.path.isdir(LUNAORIGIN):
        print("no packages registered")
        return
    names = sorted(f[:-5] for f in os.listdir(LUNAORIGIN) if f.endswith(".json"))
    if not names:
        print("no packages registered")
        return

    updated = []
    skipped = []
    failed = []

    for name in names:
        pkg = package(name)
        pkg.jsonparse()

        if pkg.curcom == "":
            skipped.append(name)
            continue

        try:
            latest = pkg.get_commit()
            dest = os.path.expanduser(f"~/.local/lunasource/{name}")

            if latest == pkg.curcom and os.path.isdir(dest):
                continue

            pkg.cmpl()
            pkg.ins()
            updated.append(name)

        except subprocess.CalledProcessError as e:
            failed.append(name)
            print(f"✗ {name} failed: {e}")

    if updated:
        print(f"updated: {', '.join(updated)}")
    else:
        print("everything up to date")
    if failed:
        print(f"failed: {', '.join(failed)}")




def print_usage() -> None:
    print("usage:")
    print("  luna install <package> [package2] ...")
    print("  luna add <name> <url> <compile_cmd> [config_cmd] [install_cmd]")
    print("  luna list")
    print("  luna update")


def main() -> None:
    if len(sys.argv) < 2:
        print_usage()
        sys.exit(1)

    command = sys.argv[1]

    if command == "install":
        if len(sys.argv) < 3:
            print_usage()
            sys.exit(1)
        cmd_install(sys.argv[2:])

    elif command == "add":
        if len(sys.argv) < 5:
            print_usage()
            sys.exit(1)
        name = sys.argv[2]
        url = sys.argv[3]
        compile_cmd = sys.argv[4]
        config_cmd = sys.argv[5] if len(sys.argv) > 5 else ""
        install_cmd = sys.argv[6] if len(sys.argv) > 6 else ""
        cmd_add(name, url, compile_cmd, config_cmd, install_cmd)

    elif command == "list":
        cmd_list()

    elif command == "update":
        cmd_update()

    else:
        print_usage()
        sys.exit(1)


if __name__ == "__main__":
    main()
