import threading
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from . import capi
class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Luna")
        self.geometry("860x560")
        self.store = []
        top = ttk.Frame(self, padding=8)
        top.pack(fill="x")
        ttk.Label(top, text="Luna", font=("SF Pro", 18, "bold")).pack(side="left")
        self.ver = ttk.Label(top, text="v" + capi.version())
        self.ver.pack(side="left", padx=8)
        ttk.Button(top, text="Refresh", command=self.refresh).pack(side="right", padx=2)
        ttk.Button(top, text="Update All", command=self.update_all).pack(side="right", padx=2)
        ttk.Button(top, text="Add", command=self.add_pkg).pack(side="right", padx=2)
        mid = ttk.Frame(self, padding=8)
        mid.pack(fill="both", expand=True)
        self.listbox = tk.Listbox(mid, width=32)
        self.listbox.pack(side="left", fill="y")
        self.listbox.bind("<<ListboxSelect>>", lambda e: self.show_detail())
        right = ttk.Frame(mid)
        right.pack(side="left", fill="both", expand=True, padx=8)
        self.detail = tk.Text(right, height=14)
        self.detail.pack(fill="x")
        btns = ttk.Frame(right)
        btns.pack(fill="x", pady=4)
        ttk.Button(btns, text="Install", command=self.install_sel).pack(side="left", padx=2)
        ttk.Button(btns, text="Remove", command=self.remove_sel).pack(side="left", padx=2)
        self.log = tk.Text(right, height=10)
        self.log.pack(fill="both", expand=True)
        self.refresh()
    def logline(self, s):
        self.log.insert("end", s + "\n")
        self.log.see("end")
    def refresh(self):
        try:
            self.store = capi.list_packages()
        except Exception as e:
            messagebox.showerror("Error", str(e))
            return
        self.listbox.delete(0, "end")
        for p in self.store:
            mark = "● " if p["installed"] else "○ "
            self.listbox.insert("end", mark + p["name"])
        self.logline(f"loaded {len(self.store)} packages")
        self.show_detail()
    def selected(self):
        i = self.listbox.curselection()
        if not i:
            return None
        return self.store[i[0]]
    def show_detail(self):
        p = self.selected()
        self.detail.delete("1.0", "end")
        if not p:
            return
        self.detail.insert("end", f"{p['name']}\nURL: {p['url']}\nCommit: {p['commit'] or 'not built'}\nConfig: {p['config'] or '-'}\nCompile: {p['compile'] or '-'}\nInstall: {p['install'] or '-'}\n")
    def add_pkg(self):
        name = simpledialog.askstring("Add", "Name:")
        if not name:
            return
        url = simpledialog.askstring("Add", "Git URL:")
        if not url:
            return
        compile_cmd = simpledialog.askstring("Add", "Compile command:", initialvalue="make -j") or ""
        try:
            capi.add(name, url, compile_cmd)
            self.logline(f"added {name}")
        except Exception as e:
            messagebox.showerror("Error", str(e))
        self.refresh()
    def install_sel(self):
        p = self.selected()
        if not p:
            return
        self.logline(f"installing {p['name']}...")
        threading.Thread(target=self._install, args=(p["name"],), daemon=True).start()
    def _install(self, name):
        try:
            capi.install(name, log_cb=lambda m: self.after(0, self.logline, m))
            self.after(0, self.logline, f"installed {name}")
        except Exception as e:
            self.after(0, self.logline, f"install failed: {e}")
        self.after(0, self.refresh)
    def remove_sel(self):
        p = self.selected()
        if not p:
            return
        try:
            capi.remove(p["name"])
            self.logline(f"removed {p['name']}")
        except Exception as e:
            messagebox.showerror("Error", str(e))
        self.refresh()
    def update_all(self):
        self.logline("updating all...")
        threading.Thread(target=self._update, daemon=True).start()
    def _update(self):
        try:
            n = capi.update_all(log_cb=lambda m: self.after(0, self.logline, m))
            self.after(0, self.logline, f"updated {n}")
        except Exception as e:
            self.after(0, self.logline, f"update failed: {e}")
        self.after(0, self.refresh)
def main():
    App().mainloop()
if __name__ == "__main__":
    main()
