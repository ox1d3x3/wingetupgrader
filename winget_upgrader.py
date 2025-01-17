import subprocess
import sys
import os
import tkinter as tk
from tkinter import scrolledtext, messagebox
import threading
import ctypes
from tkinter.ttk import Progressbar, Style
import logging

# Configure logging
logging.basicConfig(
    filename="upgrade_manager.log",
    filemode="w",
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

class UpgradeManager:
    def __init__(self, root):
        self.root = root
        self.root.title("Upgrade Manager by Ox1d3x3 v0.9.2")
        self.root.geometry("800x600")
        self.root.resizable(True, True)

        # Load Upgrade Icon
        icon_path = "upgrade_icon.png"  # Ensure this is the correct path
        try:
            from PIL import Image, ImageTk
            icon = Image.open(icon_path).resize((64, 64), Image.Resampling.LANCZOS)
            self.icon_image = ImageTk.PhotoImage(icon)
            self.icon_label = tk.Label(self.root, image=self.icon_image)
            self.icon_label.pack(pady=10)
        except Exception as e:
            logging.error(f"Error loading icon: {e}")

        # Current Status
        self.status_frame = tk.LabelFrame(self.root, text="Current Status", padx=10, pady=10)
        self.status_frame.pack(fill=tk.BOTH, padx=10, pady=5, expand=True)
        self.current_status_label = tk.Label(self.status_frame, text="Waiting to start...", anchor="w")
        self.current_status_label.pack(fill=tk.BOTH, padx=5, pady=5)
        self.progress = Progressbar(self.status_frame, orient=tk.HORIZONTAL, length=100, mode="indeterminate")
        self.progress.pack(fill=tk.BOTH, padx=5, pady=5)

        # Output Log
        self.log_frame = tk.LabelFrame(self.root, text="Output Log", padx=10, pady=10)
        self.log_frame.pack(fill=tk.BOTH, padx=10, pady=5, expand=True)
        self.log_text = scrolledtext.ScrolledText(self.log_frame, wrap=tk.WORD, height=20, font=("Courier", 10))
        self.log_text.pack(fill=tk.BOTH, expand=True)

        # Start Button
        self.start_button = tk.Button(self.root, text="Start Upgrade", command=self.start_upgrade_thread, bg="#0078D7", fg="#ffffff", font=("Arial", 12, "bold"))
        self.start_button.pack(pady=10)

    def start_upgrade_thread(self):
        thread = threading.Thread(target=self.start_upgrade)
        thread.start()

    def start_upgrade(self):
        self.start_button.config(state=tk.DISABLED)
        self.current_status_label.config(text="Starting upgrade process...")
        self.progress.start()

        try:
            # Run winget upgrade --all
            process = subprocess.Popen(
                ["winget", "upgrade", "--all", "--include-unknown", "--accept-source-agreements", "--accept-package-agreements"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            # Read live output
            for line in iter(process.stdout.readline, ""):
                self.log_text.insert(tk.END, line)
                self.log_text.see(tk.END)  # Auto-scroll to the latest output

            process.stdout.close()
            process.wait()

            # Check for errors
            if process.returncode != 0:
                for error_line in iter(process.stderr.readline, ""):
                    self.log_text.insert(tk.END, f"ERROR: {error_line}", "error")
                    self.log_text.see(tk.END)
                process.stderr.close()
                logging.error("Upgrade process completed with errors.")
            else:
                logging.info("Upgrade process completed successfully.")

        except Exception as e:
            error_message = f"An error occurred: {e}"
            self.log_text.insert(tk.END, error_message + "\n")
            logging.error(error_message)

        self.current_status_label.config(text="Upgrade process complete.")
        self.progress.stop()
        self.start_button.config(state=tk.NORMAL)


def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def run_as_admin():
    if not is_admin():
        root = tk.Tk()
        root.withdraw()
        if messagebox.askyesno("Permission Required", "This script needs to be run as an administrator. Do you want to restart it as admin?"):
            root.destroy()
            script = os.path.abspath(sys.argv[0])
            params = " ".join([script] + sys.argv[1:])
            ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, params, None, 1)
            sys.exit()
        root.destroy()
    else:
        root = tk.Tk()
        app = UpgradeManager(root)
        root.mainloop()

if __name__ == "__main__":
    run_as_admin()
