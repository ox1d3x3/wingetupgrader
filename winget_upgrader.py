import subprocess
import sys
import os
import tkinter as tk
from tkinter import scrolledtext, messagebox
import threading
import ctypes
import queue

class WingetUpgrader:
    def __init__(self, root):
        self.root = root
        self.root.title("Winget Upgrader By Ox1d3x3 V 0.7")
        
        # Set up the frames
        frame1 = tk.Frame(self.root)
        frame1.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        frame2 = tk.Frame(self.root)
        frame2.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        frame3 = tk.Frame(self.root)
        frame3.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Info box for upgradable apps
        self.upgradable_text = scrolledtext.ScrolledText(frame1, wrap=tk.WORD, height=10, width=50)
        self.upgradable_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        tk.Label(frame1, text="Upgradable Apps").pack(side=tk.LEFT, padx=5, pady=5)
        
        # Info box for currently upgrading app
        self.current_upgrading_text = tk.StringVar()
        self.current_upgrading_label = tk.Label(frame2, textvariable=self.current_upgrading_text, height=5, width=50)
        self.current_upgrading_label.pack(side=tk.LEFT, padx=5, pady=5)
        tk.Label(frame2, text="< Status").pack(side=tk.LEFT, padx=5, pady=5)
        
        # Info box for upgraded apps
        self.upgraded_text = scrolledtext.ScrolledText(frame3, wrap=tk.WORD, height=10, width=50)
        self.upgraded_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        tk.Label(frame3, text="Upgraded Apps").pack(side=tk.LEFT, padx=5, pady=5)
        
        # Upgrade button
        self.upgrade_button = tk.Button(self.root, text="Start Upgrade", command=self.start_upgrade_thread)
        self.upgrade_button.pack(pady=10)
        
        self.queue = queue.Queue()

    def start_upgrade_thread(self):
        thread = threading.Thread(target=self.start_upgrade)
        thread.start()
        self.root.after(100, self.process_queue)

    def process_queue(self):
        try:
            message = self.queue.get_nowait()
        except queue.Empty:
            self.root.after(100, self.process_queue)
            return
        if message == "done":
            self.current_upgrading_text.set("All upgrades completed. You can Close this app now")
            self.upgrade_button.config(state=tk.NORMAL)
        else:
            self.current_upgrading_text.set(message)
            self.root.after(100, self.process_queue)
        
    def start_upgrade(self):
        self.upgrade_button.config(state=tk.DISABLED)
        
        # List upgradable apps
        self.current_upgrading_text.set("Checking for upgradable apps...")
        result = subprocess.run(["winget", "upgrade", "--include-unknown", "--accept-source-agreements"], capture_output=True, text=True)
        upgradable_apps = result.stdout
        self.upgradable_text.insert(tk.END, upgradable_apps)
        
        if "No installed package found matching input criteria." in upgradable_apps:
            self.current_upgrading_text.set("No upgradable apps found.")
            self.upgrade_button.config(state=tk.NORMAL)
            return
        
        # Upgrade all upgradable apps
        self.queue.put("Upgrading all apps...")
        process = subprocess.Popen(["winget", "upgrade", "--all", "--include-unknown", "--accept-source-agreements", "--accept-package-agreements"],
                                   stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

        for line in iter(process.stdout.readline, ''):
            self.queue.put(line.strip())
            self.upgraded_text.insert(tk.END, line.strip() + "\n")
        
        process.stdout.close()
        process.wait()

        if process.returncode != 0:
            for line in iter(process.stderr.readline, ''):
                self.upgraded_text.insert(tk.END, f"Error: {line.strip()}\n")
            process.stderr.close()
        
        self.queue.put("done")

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def run_as_admin():
    if not is_admin():
        root = tk.Tk()
        root.withdraw()  # Hide the main window
        if messagebox.askyesno("Permission Required", "This script needs to be run as an administrator. Do you want to restart it as admin?"):
            root.destroy()
            # Re-run the script with admin rights
            script = os.path.abspath(sys.argv[0])
            params = " ".join([script] + sys.argv[1:])
            ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, params, None, 1)
            sys.exit()
        root.destroy()
    else:
        root = tk.Tk()
        app = WingetUpgrader(root)
        root.mainloop()

if __name__ == "__main__":
    run_as_admin()
