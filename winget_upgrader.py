import subprocess
import sys
import os
import tkinter as tk
from tkinter import messagebox
import threading
import ctypes
from tkinter.ttk import Progressbar, Entry, Button, Style
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
        self.root.title("Winget Upgrader v.0.9.4")
        self.root.geometry("800x1000")
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

        # Search Bar
        self.search_frame = tk.LabelFrame(self.root, text="Search and Install Apps", padx=10, pady=10)
        self.search_frame.pack(fill=tk.BOTH, padx=10, pady=5, expand=True)

        self.search_entry = Entry(self.search_frame, width=50)
        self.search_entry.pack(side=tk.LEFT, padx=5, pady=5)

        self.search_button = Button(self.search_frame, text="Search", command=self.search_apps)
        self.search_button.pack(side=tk.LEFT, padx=5, pady=5)

        self.install_button = Button(self.search_frame, text="Install Selected", command=self.install_selected_app)
        self.install_button.pack(side=tk.LEFT, padx=5, pady=5)

        self.search_results_list = tk.Listbox(self.search_frame, height=10, width=70)
        self.search_results_list.pack(fill=tk.BOTH, expand=True, pady=5)

        # Upgradable Apps List
        self.upgradable_apps_frame = tk.LabelFrame(self.root, text="Upgradable Apps", padx=10, pady=10)
        self.upgradable_apps_frame.pack(fill=tk.BOTH, padx=10, pady=5, expand=True)
        self.upgradable_apps_list = tk.Listbox(self.upgradable_apps_frame, height=15, width=70)
        self.upgradable_apps_list.pack(fill=tk.BOTH, expand=True)

        # Current Status
        self.status_frame = tk.LabelFrame(self.root, text="Current Status", padx=10, pady=10)
        self.status_frame.pack(fill=tk.BOTH, padx=10, pady=5, expand=True)
        self.current_status_label = tk.Label(self.status_frame, text="Waiting to start...", anchor="w")
        self.current_status_label.pack(fill=tk.BOTH, padx=5, pady=5)
        self.progress = Progressbar(self.status_frame, orient=tk.HORIZONTAL, length=100, mode="determinate")
        self.progress.pack(fill=tk.BOTH, padx=5, pady=5)

        # Upgraded Apps
        self.upgraded_apps_frame = tk.LabelFrame(self.root, text="Upgraded Apps", padx=10, pady=10)
        self.upgraded_apps_frame.pack(fill=tk.BOTH, padx=10, pady=5, expand=True)
        self.upgraded_apps_list = tk.Listbox(self.upgraded_apps_frame, height=15, width=70)
        self.upgraded_apps_list.pack(fill=tk.BOTH, expand=True)

        # Start Button
        self.start_button = tk.Button(self.root, text="Upgrade All Apps", command=self.start_upgrade_thread, bg="#0078D7", fg="#ffffff", font=("Arial", 12, "bold"))
        self.start_button.pack(pady=10)

        self.total_apps = 0
        self.completed_apps = 0

        # Check and install Chocolatey if needed
        self.ensure_chocolatey_installed()

    def ensure_chocolatey_installed(self):
        """Check if Chocolatey is installed and install it if not."""
        try:
            result = subprocess.run(["choco", "--version"], capture_output=True, text=True)
            if result.returncode == 0:
                logging.info("Chocolatey is already installed.")
                return
        except FileNotFoundError:
            logging.info("Chocolatey is not installed. Proceeding with installation...")

        install_script = "https://community.chocolatey.org/install.ps1"
        command = ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", f"Invoke-Expression ((New-Object System.Net.WebClient).DownloadString('{install_script}'))"]

        try:
            subprocess.run(command, check=True)
            logging.info("Chocolatey installed successfully.")
        except subprocess.CalledProcessError as e:
            logging.error(f"Failed to install Chocolatey: {e}")
            messagebox.showerror("Error", "Failed to install Chocolatey. Please install it manually and restart the application.")
            sys.exit(1)

    def search_apps(self):
        """Search for apps using winget."""
        query = self.search_entry.get().strip()
        if not query:
            messagebox.showwarning("Input Required", "Please enter an app name to search.")
            return

        logging.info(f"Searching for apps matching: {query}")
        result = subprocess.run(["winget", "search", query, "--accept-source-agreements"], capture_output=True, text=True)
        output = result.stdout

        self.search_results_list.delete(0, tk.END)

        if result.returncode != 0 or not output.strip():
            self.search_results_list.insert(tk.END, "No results found.")
            logging.warning(f"No results found for query: {query}")
            return

        # Parse and display results
        lines = output.splitlines()
        for line in lines:
            if len(line.strip()) > 0 and not line.startswith("-") and not line.startswith("Name"):
                self.search_results_list.insert(tk.END, line)

    def install_selected_app(self):
        """Install the selected app from the search results."""
        selected = self.search_results_list.curselection()
        if not selected:
            messagebox.showwarning("Selection Required", "Please select an app to install.")
            return

        selected_app = self.search_results_list.get(selected[0])
        app_id = selected_app.split()[0]  # Extract the app ID (verify this format matches winget output)

        logging.info(f"Installing app: {app_id}")
        self.current_status_label.config(text=f"Installing {app_id}...")

        # Try to install using winget
        result = subprocess.run(
            ["winget", "install", "--id", app_id, "--accept-source-agreements", "--accept-package-agreements"],
            capture_output=True, text=True
        )

        if result.returncode == 0:
            messagebox.showinfo("Success", f"Successfully installed {app_id}.")
            logging.info(f"Successfully installed {app_id} with winget.")
        else:
            # Log winget error details
            logging.error(f"Winget install failed for {app_id}. stdout: {result.stdout}, stderr: {result.stderr}")

            # Try to install using Chocolatey
            logging.warning(f"Attempting installation of {app_id} using Chocolatey as fallback...")
            choco_result = subprocess.run(["choco", "install", app_id, "-y"], capture_output=True, text=True)

            if choco_result.returncode == 0:
                messagebox.showinfo("Success", f"Successfully installed {app_id} with Chocolatey.")
                logging.info(f"Successfully installed {app_id} with Chocolatey.")
            else:
                # Log Chocolatey error details
                logging.error(f"Chocolatey install failed for {app_id}. stdout: {choco_result.stdout}, stderr: {choco_result.stderr}")
                error_message = choco_result.stderr.strip()
                messagebox.showerror("Error", f"Failed to install {app_id}: {error_message}")

        self.current_status_label.config(text="Ready.")

    def export_raw_output(self):
        """Fetch and export the raw output from winget."""
        logging.info("Fetching raw winget output...")
        result = subprocess.run(["winget", "upgrade", "--include-unknown", "--accept-source-agreements"], capture_output=True, text=True)
        raw_output = result.stdout

        with open("raw_upgrade_list.txt", "w") as f:
            f.write(raw_output)

        logging.info("Raw output exported to raw_upgrade_list.txt.")
        return raw_output

    def parse_upgradable_apps(self, raw_output):
        """Parses the winget output to extract app details."""
        lines = raw_output.splitlines()
        apps = []
        for line in lines:
            if len(line.strip()) > 0 and not line.startswith("-") and not line.startswith("Name"):
                columns = line.split()
                if len(columns) >= 4 and "." in columns[1]:
                    app_name = " ".join(columns[:-4])  # Handles multi-word app names
                    app_id = columns[-4]
                    current_version = columns[-3]
                    available_version = columns[-2]
                    apps.append((app_name, app_id, current_version, available_version))
        return apps

    def start_upgrade_thread(self):
        thread = threading.Thread(target=self.start_upgrade)
        thread.start()

    def start_upgrade(self):
        self.start_button.config(state=tk.DISABLED)

        # Export and parse apps
        raw_output = self.export_raw_output()
        apps = self.parse_upgradable_apps(raw_output)

        if not apps:
            logging.info("No upgradable apps found.")
            self.current_status_label.config(text="No upgradable apps found.")
            self.start_button.config(state=tk.NORMAL)
            return

        # Display parsed apps in the GUI
        for app_name, app_id, current_version, available_version in apps:
            self.upgradable_apps_list.insert(tk.END, f"{app_name} - {app_id} - Current: {current_version} -> Available: {available_version}")

        self.total_apps = len(apps)
        self.progress["value"] = 0
        progress_increment = 100 / self.total_apps

        # Upgrade apps
        for i, (app_name, app_id, current_version, available_version) in enumerate(apps, 1):
            self.current_status_label.config(text=f"Upgrading {app_name} ({i}/{self.total_apps})...")
            self.progress["value"] += progress_increment

            logging.info(f"Starting upgrade for {app_name} ({app_id}) with Winget...")
            winget_result = subprocess.run(["winget", "upgrade", "--id", app_id, "--accept-source-agreements", "--accept-package-agreements"], capture_output=True, text=True)

            if winget_result.returncode == 0:
                self.upgraded_apps_list.insert(tk.END, f"{app_name} upgraded successfully with Winget")
                logging.info(f"Successfully upgraded {app_name} ({app_id}) with Winget.")
            else:
                # Try fallback with Chocolatey
                logging.warning(f"Winget failed for {app_name} ({app_id}), attempting with Chocolatey...")
                choco_result = subprocess.run(["choco", "upgrade", app_id, "-y"], capture_output=True, text=True)

                if choco_result.returncode == 0:
                    self.upgraded_apps_list.insert(tk.END, f"{app_name} upgraded successfully with Chocolatey")
                    logging.info(f"Successfully upgraded {app_name} ({app_id}) with Chocolatey.")
                else:
                    error_message = winget_result.stderr.strip() or choco_result.stderr.strip()
                    self.upgraded_apps_list.insert(tk.END, f"Error upgrading {app_name} ({app_id}): {error_message}")
                    logging.error(f"Error upgrading {app_name} ({app_id}): {error_message}")

        self.current_status_label.config(text="Upgrade process complete.")
        self.start_button.config(state=tk.NORMAL)
        logging.info("Upgrade process completed.")


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
