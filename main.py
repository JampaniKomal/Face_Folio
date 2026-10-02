#!/usr/bin/env python3
"""
Face Folio - Main Entry Point
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

This is the main entry point for the Face Folio application. It handles:
- Application initialization and startup
- Resource path management for both development and PyInstaller builds
- Window icon loading with fallback support
- Error handling and user-friendly error messages

The application uses the face_recognition library (dlib-based) for face detection
and matching, NOT DeepFace as mentioned in some documentation.

Author: Jampani Komal
Version: 1.0
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

import sys
import os
from PIL import Image, ImageTk
import customtkinter as ctk

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

try:
    from ui.main_window import App
except ImportError as e:
    print("Error: Failed to import main_window.py.")
    print(f"Details: {e}")
    root = ctk.CTk()
    root.withdraw()
    import tkinter as tk
    tk.messagebox.showerror("Import Error", f"Failed to import App from ui.main_window.\n\n{e}")
    sys.exit(1)


def resource_path(relative_path):
    """
    Get absolute path to resource files.
    
    Works for both development (running from source) and production
    (PyInstaller bundled .exe). PyInstaller creates a temp folder and 
    stores the path in sys._MEIPASS.
    
    Args:
        relative_path (str): Relative path to the resource file
        
    Returns:
        str: Absolute path to the resource file
    """
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    
    return os.path.join(base_path, relative_path)


def main():
    """Main entry point for the application."""
    print("Face Folio v1.0 - Starting application...")

    try:
        app = App(resource_path_func=resource_path)

        try:
            icon_path = resource_path(os.path.join("assets", "app_logo.ico"))
            
            if os.path.exists(icon_path):
                print(f"Loading icon from: {icon_path}")
                app.iconbitmap(icon_path)
            else:
                print(f"Warning: app_logo.ico not found at {icon_path}.")
                png_path = resource_path(os.path.join("assets", "app_logo.png"))
                if os.path.exists(png_path):
                    print(f"Loading fallback icon from: {png_path}")
                    icon_image = ImageTk.PhotoImage(Image.open(png_path))
                    app.iconphoto(False, icon_image)
                else:
                    print("Warning: No app_logo.png or app_logo.ico found.")
                    
        except Exception as e:
            print(f"Error loading icon: {e}")

        app.mainloop()

    except Exception as e:
        print("Fatal Error: Failed to start application.")
        print(f"Details: {e}")
        import tkinter as tk
        root = tk.Tk()
        root.withdraw()
        tk.messagebox.showerror("Application Error", f"A fatal error occurred:\n\n{e}")
        sys.exit(1)


if __name__ == "__main__":
    main()