# Luna Package Manager
Fast, quirky and experimental like Luna Lovegood

![Logo](LunaLogo.png)

## Instalation
**Requirements:** Zsh as the shell, all the stuff needed to compule the software you install (cmake, swift, cargo, go and so on)
Kinda simple: Just run 
`wget https://raw.githubusercontent.com/Neonwave175/Luna/refs/heads/main/setup.sh lunasetup.sh && bash lunasetup.sh`

## CLI
 * `luna install <package name>`: installs the package or lunfile
 * `luna remove <package name>`: removes the package name
 * `luna add <package name> <git url> <compile command> <configure command> <install command>`: adds the originfile for a new package
 * `luna list`: lists all packages
 * `luna update`: updates all packages
 * `luna-update`: alias to update luna itself

## GUI
launch from the terminal by using `luna-gui`
This is self-explanatory hopefully
If not, don't use it

**NOTE** SwiftUI based GUI comming in the future, that is the reason for the C API

## API
Python
``` python
from luna import lunaapi as luna
packagelist = luna.list_packages() #returns a list
luna.install("neovim", log_cb=print) #Installs
luna.add("tokei", "https://github.com/XAMPPRocky/tokei.git", "cargo build --release", "mkdir -p ~/.local/luna && cp target/release/tokei ~/.local/luna/") #adds originfile
luna.remove("cmatrix") #removes
btop = luna.get("btop") #returns info
commitofbtop = luna.get_remote_commit(btop["url"]) #takes in URL
checkupdate = luna.needs_update("argon2") #Yes the hashing algorithm, returns false of not on the latest version
luna.update_all() #updates all
luna.version() #returns the current verion
```
