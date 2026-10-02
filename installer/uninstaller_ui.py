#!/usr/bin/env python3
"""
Face Folio - Uninstaller UI
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

CustomTkinter-based uninstaller with themed UI.

Features:
- Loads installation info from install_info.json
- Removes application directory
- Removes desktop and Start Menu shortcuts
- Removes Windows Registry entries
- Does NOT remove shared model cache (intentional)

Author: Jampani Komal
Version: 1.0
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

import customtkinter as ctk
from tkinter import messagebox
import os
import shutil
import json

try:
    import winreg
except ImportError:
    winreg = None
    print("Warning: winreg not available for uninstallation.")


DARK_THEME = {
    "BG_COLOR": "#000000",
    "TEXT_COLOR": "#FFFFFF",
    "BTN_COLOR": "#FFFFFF",
    "BTN_TEXT_COLOR": "#000000",
    "BTN_HOVER_COLOR": "#E0E0E0",
}

LIGHT_THEME = {
    "BG_COLOR": "#EAEAEA",
    "TEXT_COLOR": "#000000",
    "BTN_COLOR": "#000000",
    "BTN_TEXT_COLOR": "#FFFFFF",
    "BTN_HOVER_COLOR": "#333333",
}

class UninstallerApp(ctk.CTk):
    """
    Main uninstaller window.
    
    Provides a simple UI to confirm and execute uninstallation.
    Reads installation metadata from install_info.json file.
    """
    
    def __init__(self):
        super().__init__()
        
        self.APP_NAME = "Face Folio"
        self.APP_VERSION = "v1.0"
        self.install_location = None
        
        # Try multiple methods to find install location
        self.install_info_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "install_info.json")
        
        self.title(f"{self.APP_NAME} - Uninstall")
        self.geometry("400x300")
        self.resizable(False, False)
        
        # Set window icon
        try:
            icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "app_logo.ico")
            if os.path.exists(icon_path):
                self.iconbitmap(icon_path)
                self.after(100, lambda: self.iconbitmap(icon_path))
        except Exception as e:
            print(f"Could not load icon: {e}")
        
        ctk.set_appearance_mode("system")
        self.current_theme = DARK_THEME if ctk.get_appearance_mode() == "Dark" else LIGHT_THEME
        self.configure(fg_color=self.current_theme["BG_COLOR"])
        
        self.load_install_info()
        self.create_ui()

    def load_install_info(self):
        """Load installation metadata from install_info.json file or registry."""
        # Method 1: Try to load from install_info.json
        if os.path.exists(self.install_info_path):
            try:
                with open(self.install_info_path, 'r') as f:
                    info = json.load(f)
                    self.install_location = info.get("install_location")
                    if self.install_location:
                        return
            except Exception as e:
                print(f"Error reading install info: {e}")
        
        # Method 2: Try to get from Windows Registry
        if winreg:
            try:
                key_path = r"Software\Microsoft\Windows\CurrentVersion\Uninstall\FaceFolio"
                key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_READ)
                self.install_location, _ = winreg.QueryValueEx(key, "InstallLocation")
                winreg.CloseKey(key)
            except Exception as e:
                print(f"Error reading registry: {e}")
        
        # Method 3: Use the directory where Uninstall.exe is located
        if not self.install_location:
            self.install_location = os.path.dirname(os.path.abspath(__file__))

    def create_ui(self):
        """Build the uninstaller user interface."""
        
        title = ctk.CTkLabel(
            self,
            text=f"Uninstall {self.APP_NAME}",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color=self.current_theme["TEXT_COLOR"]
        )
        title.pack(pady=(40, 20))
        
        if self.install_location and os.path.isdir(self.install_location):
            message = (
                f"Are you sure you want to completely remove {self.APP_NAME}?\n"
                f"All files will be deleted from:\n{self.install_location}"
            )
            btn_text = "Uninstall"
            btn_color = "red" 
            btn_command = self.start_uninstall
        else:
            message = (
                f"{self.APP_NAME} appears to already be uninstalled.\n"
                f"Please close this window."
            )
            btn_text = "Close"
            btn_color = self.current_theme["BTN_COLOR"]
            btn_command = self.destroy

        desc = ctk.CTkLabel(
            self,
            text=message,
            font=ctk.CTkFont(size=12),
            text_color=self.current_theme["TEXT_COLOR"],
            justify="center",
            wraplength=350
        )
        desc.pack(pady=10, padx=20)

        uninstall_btn = ctk.CTkButton(
            self,
            text=btn_text,
            width=150,
            command=btn_command,
            fg_color=btn_color,
            text_color=self.current_theme["BTN_TEXT_COLOR"] if btn_color == "red" else self.current_theme["TEXT_COLOR"],
            hover_color=self.current_theme["BTN_HOVER_COLOR"],
            corner_radius=8,
            font=ctk.CTkFont(size=14, weight="bold")
        )
        uninstall_btn.pack(pady=30)

    def start_uninstall(self):
        """
        Execute the complete uninstallation process.
        
        Steps:
        1. Confirm with user
        2. Remove installation directory
        3. Remove shortcuts
        4. Remove registry entry
        5. Show completion message
        
        Note: Does NOT remove shared model cache in user's home directory.
        """
        if not self.install_location or not os.path.isdir(self.install_location):
            messagebox.showinfo("Uninstall Complete", f"{self.APP_NAME} directory not found. Uninstallation finished.")
            self.remove_registry_entry()
            self.destroy()
            return
        
        if messagebox.askyesno("Confirm Uninstall", "This action will permanently delete the application folder. Continue?"):
            try:
                shutil.rmtree(self.install_location, ignore_errors=True)
                
                self.remove_shortcuts()
                self.remove_registry_entry()
                
                messagebox.showinfo("Uninstall Complete", f"{self.APP_NAME} has been successfully uninstalled.")
                self.destroy()
                
            except Exception as e:
                messagebox.showerror("Uninstall Error", f"An error occurred while deleting files. Please try manually deleting the folder:\n\n{self.install_location}\n\nError: {e}")
    
    def remove_registry_entry(self):
        """Remove the Windows Registry entry from Add/Remove Programs."""
        if not winreg: return
        try:
            key_path = r"Software\Microsoft\Windows\CurrentVersion\Uninstall\FaceFolio"
            winreg.DeleteKey(winreg.HKEY_CURRENT_USER, key_path)
        except Exception as e:
            print(f"Warning: Could not remove registry entry: {e}")
    
    def remove_shortcuts(self):
        """Remove desktop shortcut and Start Menu folder."""
        
        desktop = os.path.join(os.path.expanduser("~"), "Desktop")
        desktop_link = os.path.join(desktop, f"{self.APP_NAME}.lnk")
        if os.path.exists(desktop_link):
            os.remove(desktop_link)

        start_menu = os.path.join(os.path.expanduser("~"), "AppData", "Roaming", "Microsoft", "Windows", "Start Menu", "Programs")
        app_folder = os.path.join(start_menu, self.APP_NAME)
        if os.path.isdir(app_folder):
            shutil.rmtree(app_folder, ignore_errors=True)


def main():
    """Entry point for the uninstaller."""
    app = UninstallerApp()
    app.mainloop()

if __name__ == "__main__":
    main()