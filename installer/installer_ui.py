#!/usr/bin/env python3
"""
Face Folio - Setup Installer UI
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

A professional CustomTkinter-based installer wizard for Face Folio.

Features:
- 5-page installation wizard (Welcome, Location, Options, Installing, Complete)
- Customizable installation location
- Optional desktop and Start Menu shortcuts
- Windows Registry integration (Add/Remove Programs)
- Retry logic for file copy operations (handles antivirus file locks)
- Creates uninstaller with matching UI

Installation Steps:
1. Creates installation directory
2. Copies FaceFolio application bundle
3. Creates uninstaller files
4. Creates shortcuts (if selected)
5. Registers in Windows Registry

Author: Jampani Komal
Version: 1.0
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog, messagebox
import os
import shutil
import json
import sys
from pathlib import Path
import threading
import time 

try:
    import win32com.client
    import winreg
except ImportError:
    win32com = None
    winreg = None
    print("Warning: win32com or winreg not found. Shortcuts/Registry will be skipped.")


DARK_THEME = {
    "BG_COLOR": "#000000",
    "MENU_COLOR": "#1C1C1C",
    "ENTRY_COLOR": "#1C1C1C",
    "TEXT_COLOR": "#FFFFFF",
    "BTN_COLOR": "#FFFFFF",
    "BTN_TEXT_COLOR": "#000000",
    "BTN_HOVER_COLOR": "#E0E0E0",
    "DISABLED_COLOR": "#555555",
    "BORDER_COLOR": "#FFFFFF",
    "PROGRESS_COLOR": "#FFFFFF",
}

LIGHT_THEME = {
    "BG_COLOR": "#EAEAEA",
    "MENU_COLOR": "#F5F5F5",
    "ENTRY_COLOR": "#FFFFFF",
    "TEXT_COLOR": "#000000",
    "BTN_COLOR": "#000000",
    "BTN_TEXT_COLOR": "#FFFFFF",
    "BTN_HOVER_COLOR": "#333333",
    "DISABLED_COLOR": "#AAAAAA",
    "BORDER_COLOR": "#000000",
    "PROGRESS_COLOR": "#000000",
}


class InstallerApp(ctk.CTk):
    def __init__(self, source_folder=None):
        super().__init__()
        
        self.APP_NAME = "Face Folio"
        self.APP_VERSION = "v1.0"
        self.source_folder = source_folder or self.get_source_folder()
        self.install_location = os.path.join(os.environ.get('LOCALAPPDATA', os.path.expanduser('~')), 'Face Folio')
        self.current_page = 0
        self.is_installing = False
        
        self.title(f"{self.APP_NAME} {self.APP_VERSION} - Setup")
        self.geometry("450x450")
        self.resizable(False, False)
        
        try:
            # --- FIX 1: Corrected icon path ---
            # The --icon flag bundles it at the root of _MEIPASS
            icon_path = os.path.join(self.source_folder, "app_logo.ico")
            
            # Dev fallback: check original assets folder if not bundled
            if not os.path.exists(icon_path):
                 icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets", "app_logo.ico")

            if os.path.exists(icon_path):
                self.iconbitmap(icon_path)
                self.after(100, lambda: self.iconbitmap(icon_path))
            else:
                 print(f"Icon not found at {icon_path}")
                    
        except Exception as e:
            print(f"Could not load icon: {e}")
        
        ctk.set_appearance_mode("system")
        self.current_theme = DARK_THEME if ctk.get_appearance_mode() == "Dark" else LIGHT_THEME
        self.configure(fg_color=self.current_theme["BG_COLOR"])
        
        self.create_pages()
        self.show_page(0)
        
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def get_source_folder(self):
        """Get the folder containing installer files (where the main EXE is bundled)"""
        if hasattr(sys, '_MEIPASS'):
            return sys._MEIPASS
        else:
            # Dev path: 'Face_Folio/installer/' -> 'Face_Folio/'
            return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    def create_pages(self):
        """Create all installer pages"""
        self.main_frame = ctk.CTkFrame(self, corner_radius=0, fg_color=self.current_theme["BG_COLOR"])
        self.main_frame.pack(fill="both", expand=True)
        
        self.pages = []
        self.pages.append(self.create_welcome_page())
        self.pages.append(self.create_location_page())
        self.pages.append(self.create_options_page())
        self.pages.append(self.create_installing_page())
        self.pages.append(self.create_complete_page())
        
        # Bottom navigation frame
        self.nav_frame = ctk.CTkFrame(self.main_frame, corner_radius=0, fg_color=self.current_theme["BG_COLOR"], height=60)
        self.nav_frame.pack(side="bottom", fill="x", padx=20, pady=20)
        
        self.back_btn = ctk.CTkButton(
            self.nav_frame,
            text="< Back",
            width=100,
            command=self.go_back,
            fg_color=self.current_theme["BTN_COLOR"],
            text_color=self.current_theme["BTN_TEXT_COLOR"],
            hover_color=self.current_theme["BTN_HOVER_COLOR"],
            corner_radius=8,
            font=ctk.CTkFont(size=13, weight="bold")
        )
        self.back_btn.pack(side="left", padx=5)
        
        self.next_btn = ctk.CTkButton(
            self.nav_frame,
            text="Next >",
            width=100,
            command=self.go_next,
            fg_color=self.current_theme["BTN_COLOR"],
            text_color=self.current_theme["BTN_TEXT_COLOR"],
            hover_color=self.current_theme["BTN_HOVER_COLOR"],
            corner_radius=8,
            font=ctk.CTkFont(size=13, weight="bold")
        )
        self.next_btn.pack(side="right", padx=5)
        
        self.cancel_btn = ctk.CTkButton(
            self.nav_frame,
            text="Cancel",
            width=100,
            command=self.on_closing,
            fg_color=self.current_theme["BTN_COLOR"],
            text_color=self.current_theme["BTN_TEXT_COLOR"],
            hover_color=self.current_theme["BTN_HOVER_COLOR"],
            corner_radius=8,
            font=ctk.CTkFont(size=13, weight="bold")
        )
        self.cancel_btn.pack(side="right", padx=5)
    
    def create_welcome_page(self):
        """Page 0: Welcome screen"""
        page = ctk.CTkFrame(self.main_frame, corner_radius=0, fg_color=self.current_theme["BG_COLOR"])
        
        title = ctk.CTkLabel(
            page,
            text=f"Welcome to {self.APP_NAME} Setup",
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color=self.current_theme["TEXT_COLOR"]
        )
        title.pack(pady=(60, 20))
        
        version = ctk.CTkLabel(
            page,
            text=self.APP_VERSION,
            font=ctk.CTkFont(size=16),
            text_color=self.current_theme["DISABLED_COLOR"]
        )
        version.pack(pady=(0, 40))
        
        desc_text = (
            "This wizard will guide you through the installation of\n"
            f"{self.APP_NAME}, a Photo Organizer for event photos.\n\n"
            "Face Folio uses the face_recognition library (dlib-based)\n"
            "to automatically sort images by person.\n\n"
            "Click Next to continue."
        )
        desc = ctk.CTkLabel(
            page,
            text=desc_text,
            font=ctk.CTkFont(size=13),
            text_color=self.current_theme["TEXT_COLOR"],
            justify="center"
        )
        desc.pack(pady=20)
        
        return page
    
    def create_location_page(self):
        """Page 1: Installation location"""
        page = ctk.CTkFrame(self.main_frame, corner_radius=0, fg_color=self.current_theme["BG_COLOR"])
        
        title = ctk.CTkLabel(
            page,
            text="Choose Installation Location",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=self.current_theme["TEXT_COLOR"]
        )
        title.pack(pady=(40, 10), padx=40, anchor="w")
        
        desc = ctk.CTkLabel(
            page,
            text="Setup will install the application in the following folder.",
            font=ctk.CTkFont(size=12),
            text_color=self.current_theme["TEXT_COLOR"]
        )
        desc.pack(pady=(0, 20), padx=40, anchor="w")
        
        loc_frame = ctk.CTkFrame(page, fg_color="transparent")
        loc_frame.pack(pady=20, padx=40, fill="x")
        
        self.location_entry = ctk.CTkEntry(
            loc_frame,
            width=260,
            height=32,
            fg_color=self.current_theme["ENTRY_COLOR"],
            text_color=self.current_theme["TEXT_COLOR"],
            border_color=self.current_theme["BORDER_COLOR"],
            border_width=1,
            corner_radius=8,
            font=ctk.CTkFont(size=9)
        )
        self.location_entry.pack(side="left", padx=(0, 10))
        self.location_entry.insert(0, self.install_location)
        
        browse_btn = ctk.CTkButton(
            loc_frame,
            text="Browse...",
            width=100,
            command=self.browse_location,
            fg_color=self.current_theme["BTN_COLOR"],
            text_color=self.current_theme["BTN_TEXT_COLOR"],
            hover_color=self.current_theme["BTN_HOVER_COLOR"],
            corner_radius=8,
            font=ctk.CTkFont(size=12, weight="bold")
        )
        browse_btn.pack(side="left")
        
        space_info = ctk.CTkLabel(
            page,
            text="Disk space required: ~80 MB",
            font=ctk.CTkFont(size=12),
            text_color=self.current_theme["DISABLED_COLOR"]
        )
        space_info.pack(pady=(30, 0), padx=40, anchor="w")
        
        return page
    
    def create_options_page(self):
        """Page 2: Installation options"""
        page = ctk.CTkFrame(self.main_frame, corner_radius=0, fg_color=self.current_theme["BG_COLOR"])
        
        title = ctk.CTkLabel(
            page,
            text="Select Additional Tasks",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=self.current_theme["TEXT_COLOR"]
        )
        title.pack(pady=(40, 10), padx=40, anchor="w")
        
        desc = ctk.CTkLabel(
            page,
            text="Select the additional tasks you would like Setup to perform:",
            font=ctk.CTkFont(size=12),
            text_color=self.current_theme["TEXT_COLOR"]
        )
        desc.pack(pady=(0, 30), padx=40, anchor="w")
        
        opts_frame = ctk.CTkFrame(page, fg_color="transparent")
        opts_frame.pack(pady=10, padx=60, fill="x")
        
        # --- Using the fix from our previous conversation ---
        self.create_desktop_shortcut = tk.BooleanVar(value=True)
        desktop_cb = ctk.CTkCheckBox(
            opts_frame,
            text="Create a desktop shortcut",
            variable=self.create_desktop_shortcut,
            text_color=self.current_theme["TEXT_COLOR"],
            fg_color=self.current_theme["BTN_COLOR"],
            hover_color=self.current_theme["BTN_HOVER_COLOR"],
            border_color=self.current_theme["BORDER_COLOR"],
            border_width=2,
            checkmark_color=self.current_theme["BTN_TEXT_COLOR"],
            font=ctk.CTkFont(size=13)
        )
        desktop_cb.pack(pady=10, anchor="w")
        
        # --- Using the fix from our previous conversation ---
        self.create_startmenu_shortcut = tk.BooleanVar(value=True)
        startmenu_cb = ctk.CTkCheckBox(
            opts_frame,
            text="Create a Start Menu folder",
            variable=self.create_startmenu_shortcut,
            text_color=self.current_theme["TEXT_COLOR"],
            fg_color=self.current_theme["BTN_COLOR"],
            hover_color=self.current_theme["BTN_HOVER_COLOR"],
            border_color=self.current_theme["BORDER_COLOR"],
            border_width=2,
            checkmark_color=self.current_theme["BTN_TEXT_COLOR"],
            font=ctk.CTkFont(size=13)
        )
        startmenu_cb.pack(pady=10, anchor="w")

        model_note = ctk.CTkLabel(
            page,
            text="Note: Face recognition models will be initialized on first run.",
            font=ctk.CTkFont(size=11, slant="italic"),
            text_color=self.current_theme["DISABLED_COLOR"]
        )
        model_note.pack(pady=(50, 0), padx=40, anchor="w")
        
        return page
    
    def create_installing_page(self):
        """Page 3: Installation progress"""
        page = ctk.CTkFrame(self.main_frame, corner_radius=0, fg_color=self.current_theme["BG_COLOR"])
        
        title = ctk.CTkLabel(
            page,
            text="Installing Face Folio",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=self.current_theme["TEXT_COLOR"]
        )
        title.pack(pady=(60, 30), padx=40, anchor="w")
        
        self.progress_bar = ctk.CTkProgressBar(
            page,
            width=350,
            height=20,
            corner_radius=10,
            progress_color=self.current_theme["PROGRESS_COLOR"],
            fg_color=self.current_theme["ENTRY_COLOR"],
            border_width=1,
            border_color=self.current_theme["BORDER_COLOR"]
        )
        self.progress_bar.set(0)
        # --- Using the fix from our previous conversation (not packed) ---
        
        self.status_label = ctk.CTkLabel(
            page,
            text="Click Install to begin...",
            font=ctk.CTkFont(size=13),
            text_color=self.current_theme["TEXT_COLOR"]
        )
        self.status_label.pack(pady=80, padx=40) 
        
        self.details_label = ctk.CTkLabel(
            page,
            text="",
            font=ctk.CTkFont(size=11),
            text_color=self.current_theme["DISABLED_COLOR"]
        )
        self.details_label.pack(pady=5, padx=40)
        
        return page
    
    def create_complete_page(self):
        """Page 4: Installation complete"""
        page = ctk.CTkFrame(self.main_frame, corner_radius=0, fg_color=self.current_theme["BG_COLOR"])
        
        title = ctk.CTkLabel(
            page,
            text="Installation Complete!",
            font=ctk.CTkFont(size=22, weight="bold"),
            text_color=self.current_theme["TEXT_COLOR"]
        )
        title.pack(pady=(80, 30))
        
        desc_text = (
            f"{self.APP_NAME} has been successfully installed\n"
            "on your computer.\n\n"
            "Click Finish to exit Setup."
        )
        desc = ctk.CTkLabel(
            page,
            text=desc_text,
            font=ctk.CTkFont(size=12),
            text_color=self.current_theme["TEXT_COLOR"],
            justify="center"
        )
        desc.pack(pady=20)
        
        self.launch_after_install = tk.BooleanVar(value=True)
        launch_cb = ctk.CTkCheckBox(
            page,
            text=f"Launch {self.APP_NAME}",
            variable=self.launch_after_install,
            text_color=self.current_theme["TEXT_COLOR"],
            fg_color=self.current_theme["BTN_COLOR"],
            hover_color=self.current_theme["BTN_HOVER_COLOR"],
            border_color=self.current_theme["BORDER_COLOR"],
            border_width=2,
            checkmark_color=self.current_theme["BTN_TEXT_COLOR"],
            font=ctk.CTkFont(size=13, weight="bold")
        )
        launch_cb.pack(pady=30)
        
        return page
    
    def show_page(self, page_num):
        """Display specific page"""
        for page in self.pages:
            page.pack_forget()
        
        self.current_page = page_num
        self.pages[page_num].pack(fill="both", expand=True, before=self.nav_frame)
        
        self.update_navigation_buttons()

        # --- Using the fix from our previous conversation ---
        if self.current_page == len(self.pages) - 2:
            self.status_label.pack_configure(pady=80) 
        else:
            self.progress_bar.pack_forget()
            self.status_label.pack_configure(pady=80)
    
    def update_navigation_buttons(self):
        """Update button states based on current page"""
        if self.current_page == 0:
            self.back_btn.configure(state="disabled")
        else:
            self.back_btn.configure(state="normal")
        
        if self.current_page == len(self.pages) - 1:
            self.next_btn.configure(text="Finish", state="normal")
            self.cancel_btn.configure(state="disabled")
            self.back_btn.configure(state="disabled")
        elif self.current_page == len(self.pages) - 2:
            self.next_btn.configure(text="Install", state="disabled" if self.is_installing else "normal")
            self.back_btn.configure(state="disabled" if self.is_installing else "normal")
            self.cancel_btn.configure(state="disabled" if self.is_installing else "normal")
        else:
            self.next_btn.configure(text="Next >", state="normal")
            self.cancel_btn.configure(state="normal")
    
    def go_back(self):
        """Navigate to previous page"""
        if self.current_page > 0:
            self.show_page(self.current_page - 1)
    
    def go_next(self):
        """Navigate to next page or execute action"""
        if self.current_page == len(self.pages) - 1:
            self.finish_installation()
        elif self.current_page == len(self.pages) - 2:
            self.start_installation()
        else:
            if self.current_page == 1:
                self.install_location = self.location_entry.get()
                if not self.validate_install_path():
                    return
            self.show_page(self.current_page + 1)
    
    def browse_location(self):
        """Browse for installation directory"""
        folder = filedialog.askdirectory(
            title="Select Installation Folder",
            initialdir=os.path.dirname(self.install_location)
        )
        if folder:
            self.location_entry.delete(0, tk.END)
            self.location_entry.insert(0, folder)
    
    def validate_install_path(self):
        """
        Validate installation path.
        - Checks for invalid characters.
        - Checks if it's a file.
        - Checks if it's non-empty and warns user.
        """
        path = self.install_location
        try:
            p = Path(path)
            # Check for invalid path
            if not p.parent.exists():
                messagebox.showerror("Invalid Path", "The installation path is invalid.")
                return False
        except Exception:
            messagebox.showerror("Invalid Path", "The installation path contains invalid characters.")
            return False
        
        # Check if it's a file
        if os.path.exists(path) and not os.path.isdir(path):
            messagebox.showerror("Invalid Path", "The selected path is a file. Please select a folder.")
            return False
            
        # Check if directory exists and is NOT empty
        if os.path.exists(path) and os.path.isdir(path) and len(os.listdir(path)) > 0:
            result = messagebox.askyesno(
                "Warning: Directory Not Empty",
                f"The directory is not empty:\n{path}\n\nFiles may be overwritten. Do you want to continue anyway?"
            )
            if not result:
                return False
        
        return True
    
    def start_installation(self):
        """Start installation process in background thread"""
        self.is_installing = True
        self.update_navigation_buttons()
        
        # --- Using the fix from our previous conversation ---
        self.progress_bar.pack(pady=20, padx=40)
        self.status_label.pack_configure(pady=10) 
        
        install_thread = threading.Thread(target=self.install_files, daemon=True)
        install_thread.start()
    
    def install_files(self):
        """Install application files (runs in background thread)"""
        try:
            total_steps = 5
            current_step = 0
            
            # Step 1: Create installation directory
            self.update_progress(current_step / total_steps, "Creating installation directory...", "")
            try:
                os.makedirs(self.install_location, exist_ok=True)
            except PermissionError:
                raise Exception("Permission denied. Please choose a different installation location.")
            except Exception as e:
                 raise Exception(f"Could not create directory: {e}")
            current_step += 1
            
            # ------------------------------------------------------------------
            # Step 2: Copy application bundle (Copying the extracted folder)
            self.update_progress(current_step / total_steps, "Copying application files (Folder copy)...", "Waiting for system file lock release...")

            app_bundle_src = os.path.join(self.source_folder, "FaceFolio")

            if not os.path.exists(app_bundle_src):
                raise Exception("Application bundle folder not found inside installer package. Please ensure Step 1 created the 'dist/FaceFolio' folder.")

            # --- DEFENSIVE COPY LOOP FOR SHUTIL.COPYTREE ---
            copied_successfully = False
            for attempt in range(10): # Try up to 10 times
                try:
                    shutil.copytree(app_bundle_src, self.install_location, dirs_exist_ok=True)
                    copied_successfully = True
                    break
                except PermissionError:
                    self.update_progress(current_step / total_steps, f"Directory Locked (Attempt {attempt+1}/10). Retrying...", "Security scan is in progress.")
                    time.sleep(1) 
                except Exception as e:
                    raise Exception(f"Copy failed on attempt {attempt+1}: {e}")

            if not copied_successfully:
                raise Exception("Failed to copy FaceFolio application folder after 10 attempts. Files remain locked.")

            current_step += 1
            # ------------------------------------------------------------------
            
            # Step 3: Create uninstaller script 
            self.update_progress(current_step / total_steps, "Creating uninstaller...", "")
            self.create_uninstaller()
            current_step += 1

            # Step 4: Create shortcuts 
            self.update_progress(current_step / total_steps, "Creating shortcuts...", "")
            self.create_shortcuts()
            current_step += 1
            
            # Step 5: Register installation 
            self.update_progress(current_step / total_steps, "Registering installation...", "")
            self.register_installation()
            current_step += 1
            
            # Complete
            self.update_progress(1.0, "Installation complete!", "Model will download on first app launch.")
            self.after(500, self.installation_complete)
            
        except Exception as e:
            error_msg = str(e)
            self.after(0, lambda: self.show_error_dialog("Installation Error", f"An error occurred during installation:\n\n{error_msg}"))
            self.is_installing = False
            self.after(0, lambda: self.show_page(1))
            self.after(0, self.update_navigation_buttons)
    
    def update_progress(self, progress, status, details):
        """Update progress bar and status (thread-safe)"""
        self.after(0, self._update_progress_ui, progress, status, details)
    
    def _update_progress_ui(self, progress, status, details):
        """Update UI elements (must be called from main thread)"""
        self.progress_bar.set(progress)
        self.status_label.configure(text=status)
        self.details_label.configure(text=details)
    
    def create_shortcuts(self):
        """Create desktop and start menu shortcuts (Windows only)"""
        if not win32com:
            return 
            
        try:
            shell = win32com.client.Dispatch("WScript.Shell")
            
            exe_path = os.path.join(self.install_location, "FaceFolio.exe")
            icon_path = os.path.join(self.install_location, "assets", "app_logo.ico")
            
            if self.create_desktop_shortcut.get():
                desktop = shell.SpecialFolders("Desktop")
                shortcut_path = os.path.join(desktop, f"{self.APP_NAME}.lnk")
                shortcut = shell.CreateShortCut(shortcut_path)
                shortcut.Targetpath = exe_path
                shortcut.WorkingDirectory = self.install_location
                if os.path.exists(icon_path):
                    shortcut.IconLocation = icon_path
                shortcut.save()
            
            if self.create_startmenu_shortcut.get():
                start_menu = shell.SpecialFolders("Programs")
                app_folder = os.path.join(start_menu, self.APP_NAME)
                os.makedirs(app_folder, exist_ok=True)
                
                shortcut_path = os.path.join(app_folder, f"{self.APP_NAME}.lnk")
                shortcut = shell.CreateShortCut(shortcut_path)
                shortcut.Targetpath = exe_path
                shortcut.WorkingDirectory = self.install_location
                if os.path.exists(icon_path):
                    shortcut.IconLocation = icon_path
                shortcut.save()
                
                uninstall_launcher_path = os.path.join(self.install_location, "uninstall_launcher.py")
                if os.path.exists(uninstall_launcher_path):
                    uninstall_shortcut_path = os.path.join(app_folder, f"Uninstall {self.APP_NAME}.lnk")
                    uninstall_shortcut = shell.CreateShortCut(uninstall_shortcut_path)
                    uninstall_shortcut.Targetpath = os.path.join(self.install_location, "FaceFolio.exe")
                    uninstall_shortcut.Arguments = f'"{uninstall_launcher_path}"'
                    uninstall_shortcut.WorkingDirectory = self.install_location
                    uninstall_shortcut.save()
        
        # --- Using the fix from our previous conversation ---
        except Exception as e:
            print(f"Warning: Could not create shortcuts: {e}. Installation will continue.")

    
    def create_uninstaller(self):
        """Copies the Uninstall.exe to installation directory."""
        # Copy Uninstall.exe from the bundled resources
        uninstaller_src = os.path.join(self.source_folder, "Uninstall.exe")
        
        # Dev fallback
        if not os.path.exists(uninstaller_src):
            uninstaller_src = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "dist", "Uninstall.exe")
            
        if os.path.exists(uninstaller_src):
            uninstaller_dest = os.path.join(self.install_location, "Uninstall.exe")
            shutil.copy2(uninstaller_src, uninstaller_dest)
        else:
            print(f"Warning: Uninstall.exe not found at {uninstaller_src}")

    def register_installation(self):
        """Register installation in Windows Registry (Add/Remove Programs)"""
        if not winreg:
            return 

        try:
            key_path = r"Software\Microsoft\Windows\CurrentVersion\Uninstall\FaceFolio"
            
            key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, key_path)
            
            winreg.SetValueEx(key, "DisplayName", 0, winreg.REG_SZ, f"{self.APP_NAME} {self.APP_VERSION}")
            winreg.SetValueEx(key, "DisplayVersion", 0, winreg.REG_SZ, self.APP_VERSION)
            winreg.SetValueEx(key, "Publisher", 0, winreg.REG_SZ, "Jampani Komal")
            winreg.SetValueEx(key, "InstallLocation", 0, winreg.REG_SZ, self.install_location)
            
            # Point to Uninstall.exe
            uninstaller_path = os.path.join(self.install_location, "Uninstall.exe")
            winreg.SetValueEx(key, "UninstallString", 0, winreg.REG_SZ, f'"{uninstaller_path}"')
            
            icon_path = os.path.join(self.install_location, "assets", "app_logo.ico")
            if os.path.exists(icon_path):
                winreg.SetValueEx(key, "DisplayIcon", 0, winreg.REG_SZ, icon_path)
            
            winreg.CloseKey(key)
            
            install_info = {
                "app_name": self.APP_NAME,
                "version": self.APP_VERSION,
                "install_location": self.install_location,
                "desktop_shortcut": self.create_desktop_shortcut.get(),
                "startmenu_shortcut": self.create_startmenu_shortcut.get()
            }
            
            with open(os.path.join(self.install_location, "install_info.json"), 'w') as f:
                json.dump(install_info, f, indent=2)
        
        except Exception as e:
            print(f"Error registering installation: {e}")
    
    def installation_complete(self):
        """Handle installation completion"""
        self.is_installing = False
        self.show_page(len(self.pages) - 1)
    
    def finish_installation(self):
        """Finish installation and launch app if requested"""
        if self.launch_after_install.get():
            try:
                exe_path = os.path.join(self.install_location, "FaceFolio.exe")
                if os.path.exists(exe_path):
                    os.startfile(exe_path)
                else:
                    print(f"App executable not found at: {exe_path}")
            except Exception as e:
                print(f"Error launching app: {e}")
        
        self.destroy()
    
    def show_error_dialog(self, title, message):
        """Show themed error dialog"""
        messagebox.showerror(title, message) 
    
    def on_closing(self):
        """Handle window close"""
        if self.is_installing:
            result = messagebox.askyesno(
                "Installation in Progress",
                "Installation is currently in progress.\nAre you sure you want to cancel?"
            )
            if not result:
                return
        
        self.quit()


def main():
    """Main entry point when run as an EXE"""
    app = InstallerApp()
    app.mainloop()


if __name__ == "__main__":
    main()