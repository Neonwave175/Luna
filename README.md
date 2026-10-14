# Luna

Build your own tools from source and keep them updated. Recipes live in `~/.local/lunaorigin`, sources build in `~/.local/lunasource`, binaries land in `~/.local/luna`.

## Install

```sh
./setup.sh
```

This creates the required folders, installs Luna with pip, and adds `~/.local/luna` to your `PATH`. To update Luna itself later:

```sh
luna-update
```

Or install directly with pip:

```sh
pip install git+https://github.com/Neonwave175/Luna.git
```

Requires Python 3.10+, `git`, and whatever build tools your packages need (`make`, `cargo`, `go`, `cmake`, ...).

## CLI

```sh
luna add <name> <url> <compile_cmd> [config_cmd] [install_cmd]
luna install <name>...
luna list
luna update
luna remove <name>
```

Example:

```sh
luna add fzf https://github.com/junegunn/fzf.git "go build -o fzf ." "" "mkdir -p ~/.local/luna && cp fzf ~/.local/luna/"
luna install fzf
```

`add` registers a recipe with an empty commit. `install` clones at the latest remote commit, runs the config/compile/install commands, and records the commit. `update` reinstalls every package whose remote moved (removed packages are skipped). `remove` deletes the source and binary and clears the recorded commit.

## GUI

```sh
luna-gui
```

Tkinter frontend over the same operations: package list with installed status, detail view, Install / Remove / Add / Update All, and a live activity log. Long builds run in background threads.

## Python + C API

`luna/capi.py` exposes the same operations to Python (`add`, `remove`, `get`, `list_packages`, `install`, `update_all`, `needs_update`, `get_remote_commit`) through a shared native core, auto-building it on first import:

```python
from luna import capi
capi.list_packages()
capi.install("fzf", log_cb=print)
```

Set `LUNA_LIB` to point at a prebuilt library, or build it manually from the (git-ignored) `native/` sources.
