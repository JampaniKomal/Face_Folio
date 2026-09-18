#!/usr/bin/env python3
"""
Face Folio - Main Application Window (UI)
(Final, working version - Fixes "No Faces Found" popup crash)
"""

import customtkinter as ctk
from customtkinter import CTkImage 
import os
import threading
from tkinter import filedialog, messagebox
from PIL import Image
from pathlib import Path
import time
import subprocess
import sys

from core.photo_organizer import run_reference_sort, run_auto_discovery


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

class App(ctk.CTk):
    """
    Main application window for Face Folio.
    """
    def __init__(self, resource_path_func=lambda p: p):
        super().__init__()

        self.resource_path = resource_path_func
        self.current_theme_name = ctk.get_appearance_mode()
        self.current_theme = DARK_THEME if self.current_theme_name == "Dark" else LIGHT_THEME

        # --- State Variables ---
        self.current_mode = ctk.StringVar(value="Reference Sort")
        self.reference_folder = ctk.StringVar()
        self.event_folder = ctk.StringVar()
        self.output_folder = ctk.StringVar()
        self.is_processing = False
        self.valid_extensions = ('.jpg', '.jpeg', '.png', '.bmp', '.zip')
        
        # --- State for in-app tagging ---
        self.portraits_to_tag = []
        self.current_portrait_index = 0
        self.tagging_event_folder = ""
        self.tagging_output_folder = ""

        # --- Window Configuration ---
        self.title("Face Folio - Photo Organizer")
        self.geometry("800x600") # Increased height for tagger
        self.minsize(600, 550)
        self.configure(fg_color=self.current_theme["BG_COLOR"])

        # --- Main Layout ---
        self.grid_rowconfigure(2, weight=1) # Row 2 (tagger) is expandable
        self.grid_columnconfigure(0, weight=1)

        # --- Title Label (NO CHANGE) ---
        self.title_label = ctk.CTkLabel(
            self,
            text="Face Folio",
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color=self.current_theme["TEXT_COLOR"]
        )
        self.title_label.grid(row=0, column=0, padx=20, pady=(20, 10))
        
        # --- Main Frame (for inputs) ---
        self.main_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.main_frame.grid(row=1, column=0, sticky="nsew", padx=40, pady=20)
        self.main_frame.grid_columnconfigure(1, weight=1)
        self.main_frame.grid_columnconfigure(2, weight=0)
        self.main_frame.grid_columnconfigure(3, weight=0)

        # 'text_color_selected' is intentionally omitted: it crashed on
        # customtkinter 5.2.2. Not reproduced on customtkinter 6.0.0.
        self.mode_switcher = ctk.CTkSegmentedButton(
            self.main_frame,
            values=["Reference Sort", "Auto-Discovery"],
            command=self.on_mode_change,
            variable=self.current_mode,
            font=ctk.CTkFont(size=14, weight="bold"),
            selected_color=self.current_theme["BTN_COLOR"],
            selected_hover_color=self.current_theme["BTN_HOVER_COLOR"],
            text_color=self.current_theme["BTN_TEXT_COLOR"],
            text_color_disabled=self.current_theme["DISABLED_COLOR"],
            unselected_color=self.current_theme["ENTRY_COLOR"],
            unselected_hover_color=self.current_theme["MENU_COLOR"],
            fg_color=self.current_theme["ENTRY_COLOR"]
        )
        self.mode_switcher.grid(row=0, column=0, columnspan=4, sticky="ew", padx=0, pady=(0, 15))
        # --- END FIX ---


        # --- Reference Folder (NO CHANGE) ---
        self.ref_label = ctk.CTkLabel(
            self.main_frame,
            text="1. Select Reference Input:",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=self.current_theme["TEXT_COLOR"]
        )
        self.ref_label.grid(row=1, column=0, sticky="w", padx=(0, 10), pady=10)

        self.ref_entry = ctk.CTkEntry(
            self.main_frame,
            textvariable=self.reference_folder,
            font=ctk.CTkFont(size=12),
            fg_color=self.current_theme["ENTRY_COLOR"],
            text_color=self.current_theme["TEXT_COLOR"],
            border_color=self.current_theme["BORDER_COLOR"],
            border_width=1
        )
        self.ref_entry.grid(row=1, column=1, sticky="ew", pady=10) 

        self.ref_btn_file = ctk.CTkButton(
            self.main_frame, text="Select File/ZIP...", font=ctk.CTkFont(size=12, weight="bold"),
            command=self.select_reference_file, fg_color=self.current_theme["BTN_COLOR"],
            text_color=self.current_theme["BTN_TEXT_COLOR"], hover_color=self.current_theme["BTN_HOVER_COLOR"], width=120
        )
        self.ref_btn_file.grid(row=1, column=2, sticky="e", padx=(10, 5), pady=10) 

        self.ref_btn_folder = ctk.CTkButton(
            self.main_frame, text="Select Folder...", font=ctk.CTkFont(size=12, weight="bold"),
            command=self.select_reference_folder, fg_color=self.current_theme["BTN_COLOR"],
            text_color=self.current_theme["BTN_TEXT_COLOR"], hover_color=self.current_theme["BTN_HOVER_COLOR"], width=120
        )
        self.ref_btn_folder.grid(row=1, column=3, sticky="e", padx=(0, 0), pady=10) 
        self.reference_widgets = [self.ref_label, self.ref_entry, self.ref_btn_file, self.ref_btn_folder]


        # --- Event Folder (NO CHANGE) ---
        self.event_label = ctk.CTkLabel(
            self.main_frame, text="2. Select Event Input:", font=ctk.CTkFont(size=14, weight="bold"),
            text_color=self.current_theme["TEXT_COLOR"]
        )
        self.event_label.grid(row=2, column=0, sticky="w", padx=(0, 10), pady=10) 

        self.event_entry = ctk.CTkEntry(
            self.main_frame, textvariable=self.event_folder, font=ctk.CTkFont(size=12),
            fg_color=self.current_theme["ENTRY_COLOR"], text_color=self.current_theme["TEXT_COLOR"],
            border_color=self.current_theme["BORDER_COLOR"], border_width=1
        )
        self.event_entry.grid(row=2, column=1, sticky="ew", pady=10) 

        self.event_btn_file = ctk.CTkButton(
            self.main_frame, text="Select File/ZIP...", font=ctk.CTkFont(size=12, weight="bold"),
            command=self.select_event_file, fg_color=self.current_theme["BTN_COLOR"],
            text_color=self.current_theme["BTN_TEXT_COLOR"], hover_color=self.current_theme["BTN_HOVER_COLOR"], width=120
        )
        self.event_btn_file.grid(row=2, column=2, sticky="e", padx=(10, 5), pady=10) 

        self.event_btn_folder = ctk.CTkButton(
            self.main_frame, text="Select Folder...", font=ctk.CTkFont(size=12, weight="bold"),
            command=self.select_event_folder, fg_color=self.current_theme["BTN_COLOR"],
            text_color=self.current_theme["BTN_TEXT_COLOR"], hover_color=self.current_theme["BTN_HOVER_COLOR"], width=120
        )
        self.event_btn_folder.grid(row=2, column=3, sticky="e", padx=(0, 0), pady=10) 


        # --- Output Folder (NO CHANGE) ---
        self.output_label = ctk.CTkLabel(
            self.main_frame, text="3. Select Output Folder:", font=ctk.CTkFont(size=14, weight="bold"),
            text_color=self.current_theme["TEXT_COLOR"]
        )
        self.output_label.grid(row=3, column=0, sticky="w", padx=(0, 10), pady=10) 

        self.output_entry = ctk.CTkEntry(
            self.main_frame, textvariable=self.output_folder, font=ctk.CTkFont(size=12),
            fg_color=self.current_theme["ENTRY_COLOR"], text_color=self.current_theme["TEXT_COLOR"],
            border_color=self.current_theme["BORDER_COLOR"], border_width=1
        )
        self.output_entry.grid(row=3, column=1, sticky="ew", pady=10) 

        self.output_btn = ctk.CTkButton(
            self.main_frame, text="Select Folder...", font=ctk.CTkFont(size=12, weight="bold"),
            command=self.select_output_folder, fg_color=self.current_theme["BTN_COLOR"],
            text_color=self.current_theme["BTN_TEXT_COLOR"], hover_color=self.current_theme["BTN_HOVER_COLOR"]
        )
        self.output_btn.grid(row=3, column=2, columnspan=2, sticky="ew", padx=(10, 0), pady=10) 

        # ---
        # --- IN-APP TAGGING FRAME ---
        # ---
        # This frame is now in row=2, and will be shown/hidden as needed
        self.tagging_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.tagging_frame.grid(row=2, column=0, sticky="nsew", padx=40, pady=10)
        self.tagging_frame.grid_columnconfigure(0, weight=1)
        
        self.tag_title = ctk.CTkLabel(self.tagging_frame, text="Tag Unique Faces", font=ctk.CTkFont(size=16, weight="bold"))
        self.tag_title.grid(row=0, column=0, columnspan=3, sticky="w", pady=(0, 10))

        # Image
        self.tag_image_label = ctk.CTkLabel(self.tagging_frame, text="", height=200)
        self.tag_image_label.grid(row=1, column=0, columnspan=3, sticky="ew", pady=10)

        # File/Progress
        self.tag_filename_label = ctk.CTkLabel(self.tagging_frame, text="Person_0.jpg (1/10)", font=ctk.CTkFont(size=12, slant="italic"))
        self.tag_filename_label.grid(row=2, column=0, columnspan=3, sticky="w", pady=5)

        # Entry
        self.tag_name_label = ctk.CTkLabel(self.tagging_frame, text="Name:")
        self.tag_name_label.grid(row=3, column=0, sticky="w")
        
        self.tag_name_entry = ctk.CTkEntry(
            self.tagging_frame, font=ctk.CTkFont(size=12),
            fg_color=self.current_theme["ENTRY_COLOR"], text_color=self.current_theme["TEXT_COLOR"],
            border_color=self.current_theme["BORDER_COLOR"], border_width=1
        )
        self.tag_name_entry.grid(row=3, column=1, columnspan=2, sticky="ew", padx=(10, 0))
        self.tag_name_entry.bind("<Return>", self.on_tag_save_and_next)

        # Buttons
        self.tag_skip_btn = ctk.CTkButton(
            self.tagging_frame, text="Skip", command=self.on_tag_skip,
            fg_color=self.current_theme["ENTRY_COLOR"], text_color=self.current_theme["TEXT_COLOR"],
            hover_color=self.current_theme["MENU_COLOR"]
        )
        self.tag_skip_btn.grid(row=4, column=0, sticky="ew", pady=(15,0), padx=(0,5))
        
        self.tag_save_btn = ctk.CTkButton(
            self.tagging_frame, text="Save & Next", command=self.on_tag_save_and_next,
            fg_color=self.current_theme["BTN_COLOR"], text_color=self.current_theme["BTN_TEXT_COLOR"],
            hover_color=self.current_theme["BTN_HOVER_COLOR"]
        )
        self.tag_save_btn.grid(row=4, column=1, sticky="ew", pady=(15,0), padx=5)

        self.tag_finish_btn = ctk.CTkButton(
            self.tagging_frame, text="Finish Tagging", command=self.on_tag_finish,
            fg_color=self.current_theme["BTN_COLOR"], text_color=self.current_theme["BTN_TEXT_COLOR"],
            hover_color=self.current_theme["BTN_HOVER_COLOR"]
        )
        self.tag_finish_btn.grid(row=4, column=2, sticky="ew", pady=(15,0), padx=(5,0))
        # --- END TAGGING FRAME ---
        

        # --- Status Frame (at bottom) ---
        self.status_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.status_frame.grid(row=3, column=0, sticky="ew", padx=40, pady=(0, 20)) # <-- row=3
        self.status_frame.grid_columnconfigure(0, weight=1)

        self.start_btn = ctk.CTkButton(
            self.status_frame, 
            text="Start Sorting Photos",
            font=ctk.CTkFont(size=16, weight="bold"),
            command=self.start_processing_thread,
            fg_color=self.current_theme["BTN_COLOR"],
            text_color=self.current_theme["BTN_TEXT_COLOR"],
            hover_color=self.current_theme["BTN_HOVER_COLOR"],
            height=40
        )
        self.start_btn.grid(row=0, column=0, sticky="ew", padx=0, pady=(0, 15))


        self.status_label = ctk.CTkLabel(
            self.status_frame,
            text="Ready. Select inputs to begin.",
            font=ctk.CTkFont(size=12),
            text_color=self.current_theme["DISABLED_COLOR"]
        )
        self.status_label.grid(row=1, column=0, sticky="w", padx=0, pady=0)

        self.progress_bar = ctk.CTkProgressBar(
            self.status_frame,
            progress_color=self.current_theme["PROGRESS_COLOR"],
            fg_color=self.current_theme["ENTRY_COLOR"],
            border_width=1,
            border_color=self.current_theme["BORDER_COLOR"]
        )
        self.progress_bar.set(0)
        self.progress_bar.grid(row=2, column=0, sticky="ew", padx=0, pady=(5, 0))

        # --- Bindings ---
        self_check_theme_change_id = None
        def check_theme_change_debounced(event=None):
            nonlocal self_check_theme_change_id
            if self_check_theme_change_id:
                self.after_cancel(self_check_theme_change_id)
            self_check_theme_change_id = self.after(100, self.check_theme_change)
        self.bind("<Configure>", check_theme_change_debounced)
        self.after(250, lambda: self.on_mode_change(self.current_mode.get())) # Set initial state
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

    # ---
    # --- UI MODE LOGIC (Your requested layout) ---
    # ---
    def on_mode_change(self, mode):
        """Called by the segmented button to hide/show the reference row."""
        self.tagging_frame.grid_remove()
        
        if mode == "Reference Sort":
            for widget in self.reference_widgets:
                widget.grid()
            self.ref_label.configure(text="1. Select Reference Input:")
            self.event_label.configure(text="2. Select Event Input:")
            self.output_label.configure(text="3. Select Output Folder:")
            self.start_btn.configure(text="Start Sorting Photos")
        
        elif mode == "Auto-Discovery":
            for widget in self.reference_widgets:
                widget.grid_remove()
            self.ref_label.configure(text="") 
            self.event_label.configure(text="1. Select Event Input:")
            self.output_label.configure(text="2. Select Output Folder:")
            self.start_btn.configure(text="Start Auto-Discovery")
    
    # --- Button Command Functions (NO CHANGE) ---
    
    def _select_input_file(self, target_variable, title):
        options = {}
        if 'zip' in self.valid_extensions:
            options['filetypes'] = (("Image or Zip Files", "*.jpg *.jpeg *.png *.zip"), ("All files","*.*"))
        else:
            options['filetypes'] = (("Image Files", "*.jpg *.jpeg *.png"), ("All files", "*.*"))
        path = filedialog.askopenfilename(title=title, **options)
        if path:
            target_variable.set(path)

    def _select_input_folder(self, target_variable, title):
        folder_path = filedialog.askdirectory(title=title)
        if folder_path:
            target_variable.set(folder_path)

    def select_reference_file(self):
        self._select_input_file(self.reference_folder, "Select Reference File/ZIP")

    def select_reference_folder(self):
        self._select_input_folder(self.reference_folder, "Select Reference Folder")

    def select_event_file(self):
        self._select_input_file(self.event_folder, "Select Event File/ZIP")

    def select_event_folder(self):
        self._select_input_folder(self.event_folder, "Select Event Folder")
        
    def select_output_folder(self):
        self._select_input_folder(self.output_folder, "Select Output Folder")


    # ---
    # --- PROCESSING LOGIC (Updated to use themed popups) ---
    # ---
    def start_processing_thread(self):
        """
        Starts the photo processing in a separate thread.
        """
        if self.is_processing:
            return

        mode = self.current_mode.get()
        event_folder = self.event_folder.get()
        out_folder = self.output_folder.get()

        if not event_folder or not Path(event_folder).exists():
            self._show_themed_error("Error", "Please select a valid Event input (Folder/Image/ZIP).")
            return
        if not out_folder or not Path(out_folder).is_dir():
            self._show_themed_error("Error", "Please select a valid Output folder.")
            return
        
        if mode == "Reference Sort":
            ref_folder = self.reference_folder.get()
            if not ref_folder or not Path(ref_folder).exists():
                self._show_themed_error("Error", "Please select a valid Reference input (Folder/Image/ZIP).")
                return
            if ref_folder == event_folder or ref_folder == out_folder:
                self._show_themed_warning("Warning", "All three paths must be unique.")
                return
        
        if event_folder == out_folder:
            self._show_themed_warning("Warning", "Event and Output paths must be unique.")
            return

        self.set_ui_processing_state(True)
        
        if mode == "Reference Sort":
            process_thread = threading.Thread(
                target=self.run_reference_sort_process, 
                args=(self.reference_folder.get(), event_folder, out_folder),
                daemon=True
            )
        else: # Auto-Discovery
            self.tagging_event_folder = event_folder
            self.tagging_output_folder = out_folder
            process_thread = threading.Thread(
                target=self.run_auto_discovery_process, 
                args=(event_folder, out_folder),
                daemon=True
            )
            
        process_thread.start()

    def run_reference_sort_process(self, ref_folder, event_folder, out_folder):
        """The processing logic for Reference Sort mode."""
        print(f"Processing (Reference Sort) started: {ref_folder}, {event_folder} -> {out_folder}")
        
        try:
            run_reference_sort(
                ref_folder, event_folder, out_folder, self.update_status 
            )
            self.update_status("Processing complete!", 1.0)
            self.after(100, lambda: self._show_themed_info("Complete", "Photo sorting finished successfully!"))
            
        except Exception as e:
            print(f"Error during processing: {e}")
            self.update_status(f"Error: {e}", 0)
            self.after(100, lambda: self._show_themed_error("Error", f"An error occurred during processing:\n\n{e}"))
            
        finally:
            self.set_ui_processing_state(False)

    def run_auto_discovery_process(self, event_folder, out_folder):
        """Step 1 of Auto-Discovery. Finds faces, then starts the in-app tagger."""
        print(f"Processing (Auto-Discovery) started: {event_folder} -> {out_folder}")
        
        try:
            self.update_status("Step 1/2: Finding unique faces...", 0.1)
            
            self.portraits_to_tag = run_auto_discovery(
                event_folder, out_folder, self.update_status
            )
            
            # ---
            # --- POPUP FIX: This is the critical change ---
            # ---
            if not self.portraits_to_tag:
                # If no faces are found, show a themed popup instead
                # of just updating the status bar. This fixes the silent fail.
                self.update_status("No unique faces were detected in the photos.", 0)
                # We must use self.after() to show the popup from the main thread
                self.after(100, lambda: self._show_themed_warning("No Faces Found", "No unique faces were detected in any of the event photos."))
                self.set_ui_processing_state(False)
                return # Exit the thread
            # --- END FIX ---

            self.update_status("Step 1/2: Found unique faces. Awaiting tagging...", 0.6)
            
            # --- Start the in-app tagger on the main thread ---
            def start_tagger():
                self.set_ui_processing_state(False) # Re-enable UI
                self.tagging_frame.grid() # Show tagger
                self.current_portrait_index = 0
                self.load_next_portrait()

            self.after(100, start_tagger)

        except Exception as e:
            print(f"Error during auto-discovery: {e}")
            self.update_status(f"Error: {e}", 0)
            self.after(100, lambda: self._show_themed_error("Error", f"An error occurred during discovery:\n\n{e}"))
            self.set_ui_processing_state(False)

    # ---
    # --- IN-APP TAGGING FUNCTIONS ---
    # ---
    
    def load_next_portrait(self):
        """Loads the next portrait image into the tagging UI."""
        if self.current_portrait_index >= len(self.portraits_to_tag):
            self.on_tag_finish() # No more images, finish up.
            return
            
        image_path = self.portraits_to_tag[self.current_portrait_index]
        filename = os.path.basename(image_path)
        
        self.tag_filename_label.configure(
            text=f"{filename} ({self.current_portrait_index + 1}/{len(self.portraits_to_tag)})"
        )
        
        try:
            pil_image = Image.open(image_path)
            img_width, img_height = pil_image.size
            max_height = 200
            max_width = 300 # Let's also set a max width
            
            # Scale by height first
            if img_height > max_height:
                ratio = max_height / img_height
                img_width = int(img_width * ratio)
                img_height = max_height
            
            # Then scale by width if still too wide
            if img_width > max_width:
                ratio = max_width / img_width
                img_height = int(img_height * ratio)
                img_width = max_width

            # ---
            # --- FIX: Use CTkImage to stop the terminal warning ---
            # ---
            ctk_image = CTkImage(pil_image, size=(int(img_width), int(img_height)))
            
            self.tag_image_label.configure(image=ctk_image, text="")
            # self.tag_image_label.image = ctk_image # No longer needed
            # --- END FIX ---
            
        except Exception as e:
            print(f"Error loading portrait: {e}")
            self.tag_image_label.configure(image=None, text=f"Error loading image:\n{filename}")
            
        self.tag_name_entry.delete(0, "end")
        self.tag_name_entry.focus()

    def on_tag_save_and_next(self, event=None):
        """Saves the new name, then loads the next portrait."""
        new_name = self.tag_name_entry.get().strip()
        if not new_name:
            self.status_label.configure(text="Please enter a name or click Skip.")
            return
            
        try:
            old_path = self.portraits_to_tag[self.current_portrait_index]
            dir_name = os.path.dirname(old_path)
            new_name = "".join(c for c in new_name if c.isalnum() or c in (' ', '_', '-')).rstrip()
            new_path = os.path.join(dir_name, f"{new_name}.jpg")
            
            if os.path.exists(new_path):
                if new_path not in self.portraits_to_tag:
                    if not self._show_themed_askyesno("Warning", f"'{new_name}.jpg' already exists. Do you want to overwrite it?"):
                        return
            
            os.rename(old_path, new_path)
            self.portraits_to_tag[self.current_portrait_index] = new_path
            
        except Exception as e:
            print(f"Error renaming file: {e}")
            self._show_themed_error("Error", f"Could not rename file: {e}")
            return
            
        self.current_portrait_index += 1
        self.load_next_portrait()

    def on_tag_skip(self):
        """Skips the current portrait."""
        self.current_portrait_index += 1
        self.load_next_portrait()

    def on_tag_finish(self):
        """Called when user is done tagging, starts the final sort."""
        self.tagging_frame.grid_remove() # Hide tagger
        
        if not self.portraits_to_tag:
            self.set_ui_processing_state(False)
            return

        portraits_dir = os.path.dirname(self.portraits_to_tag[0])
        
        self.set_ui_processing_state(True)
        self.update_status("Step 2/2: Sorting photos based on tags...", 0.7)
        
        final_sort_thread = threading.Thread(
            target=self.run_final_sort_process,
            args=(portraits_dir, self.tagging_event_folder, self.tagging_output_folder),
            daemon=True
        )
        final_sort_thread.start()

    def run_final_sort_process(self, portraits_dir, event_folder, out_folder):
        """This is the final step, called after the user tags the files."""
        try:
            run_reference_sort(
                portraits_dir,
                event_folder,
                out_folder,
                lambda msg, prog: self.update_status(f"Step 2/2: {msg}", 0.7 + (prog * 0.3))
            )
            
            self.update_status("Auto-Discovery complete!", 1.0)
            self.after(100, lambda: self._show_themed_info("Complete", "Photo sorting finished successfully!"))

        except Exception as e:
            print(f"Error during final sort: {e}")
            self.update_status(f"Error: {e}", 0)
            self.after(100, lambda: self._show_themed_error("Error", f"An error occurred during the final sort:\n\n{e}"))
            
        finally:
            self.set_ui_processing_state(False)
    # --- END IN-APP TAGGING ---
    

    def update_status(self, message, progress):
        def _update():
            self.status_label.configure(text=message)
            if "Error" in message:
                self.status_label.configure(text_color="red")
            else:
                self.status_label.configure(text_color=self.current_theme["TEXT_COLOR"])
            
            self.progress_bar.set(progress)
        
        self.after(0, _update)

    def set_ui_processing_state(self, is_processing):
        self.is_processing = is_processing
        state = "disabled" if is_processing else "normal"
        
        def _update_ui():
            self.ref_btn_file.configure(state=state)
            self.ref_btn_folder.configure(state=state)
            self.event_btn_file.configure(state=state)
            self.event_btn_folder.configure(state=state)
            self.output_btn.configure(state=state)
            self.start_btn.configure(state=state)
            self.mode_switcher.configure(state=storage)
            
            self.progress_bar.set(0)

            if is_processing:
                current_text = self.start_btn.cget("text")
                if "Start " in current_text:
                    self.start_btn.configure(text=f"{current_text.replace('Start ', '')}ing...")
                self.ref_entry.configure(state="disabled")
                self.event_entry.configure(state="disabled")
                self.output_entry.configure(state="disabled")
                self.status_label.configure(text="Processing started...", text_color=self.current_theme["TEXT_COLOR"])
            else:
                self.on_mode_change(self.current_mode.get()) 
                self.ref_entry.configure(state="normal")
                self.event_entry.configure(state="normal")
                self.output_entry.configure(state="normal")
                self.status_label.configure(text="Ready. Select inputs to begin.", text_color=self.current_theme["DISABLED_COLOR"])
                
        self.after(0, _update_ui)

    def on_closing(self):
        if self.is_processing:
            if self._show_themed_askyesno("Confirm", "Processing is in progress. Are you sure you want to exit?"):
                self.destroy()
        else:
            self.destroy()

    def check_theme_change(self, event=None):
        try:
            new_theme_name = ctk.get_appearance_mode()
            if new_theme_name != self.current_theme_name:
                self.current_theme_name = new_theme_name
                self.current_theme = DARK_THEME if new_theme_name == "Dark" else LIGHT_THEME
                self.update_ui_theme()
        except Exception as e:
            pass

    def update_ui_theme(self):
        """Redraws all UI elements with the new theme colors."""
        self.configure(fg_color=self.current_theme["BG_COLOR"])
        self.title_label.configure(text_color=self.current_theme["TEXT_COLOR"])

        # Input Frame
        elements_to_update = [self.ref_label, self.event_label, self.output_label]
        for elem in elements_to_update:
            elem.configure(text_color=self.current_theme["TEXT_COLOR"])
        for entry in [self.ref_entry, self.event_entry, self.output_entry]:
            entry.configure(
                fg_color=self.current_theme["ENTRY_COLOR"],
                text_color=self.current_theme["TEXT_COLOR"],
                border_color=self.current_theme["BORDER_COLOR"]
            )
        for btn in [self.ref_btn_file, self.ref_btn_folder, self.event_btn_file, self.event_btn_folder, self.output_btn]:
            btn.configure(
                fg_color=self.current_theme["BTN_COLOR"],
                text_color=self.current_theme["BTN_TEXT_COLOR"],
                hover_color=self.current_theme["BTN_HOVER_COLOR"]
            )
        
        # Mode Switcher
        self.mode_switcher.configure(
            selected_color=self.current_theme["BTN_COLOR"],
            selected_hover_color=self.current_theme["BTN_HOVER_COLOR"],
            text_color=self.current_theme["BTN_TEXT_COLOR"],
            text_color_disabled=self.current_theme["DISABLED_COLOR"],
            unselected_color=self.current_theme["ENTRY_COLOR"],
            unselected_hover_color=self.current_theme["MENU_COLOR"],
            fg_color=self.current_theme["ENTRY_COLOR"]
        )

        # Tagging Frame
        self.tag_title.configure(text_color=self.current_theme["TEXT_COLOR"])
        self.tag_filename_label.configure(text_color=self.current_theme["DISABLED_COLOR"])
        self.tag_name_label.configure(text_color=self.current_theme["TEXT_COLOR"])
        self.tag_name_entry.configure(
            fg_color=self.current_theme["ENTRY_COLOR"],
            text_color=self.current_theme["TEXT_COLOR"],
            border_color=self.current_theme["BORDER_COLOR"]
        )
        self.tag_skip_btn.configure(
            fg_color=self.current_theme["ENTRY_COLOR"],
            text_color=self.current_theme["TEXT_COLOR"],
            hover_color=self.current_theme["MENU_COLOR"]
        )
        for btn in [self.tag_save_btn, self.tag_finish_btn]:
            btn.configure(
                fg_color=self.current_theme["BTN_COLOR"],
                text_color=self.current_theme["BTN_TEXT_COLOR"],
                hover_color=self.current_theme["BTN_HOVER_COLOR"]
            )

        # Status Frame
        self.start_btn.configure(
            fg_color=self.current_theme["BTN_COLOR"],
            text_color=self.current_theme["BTN_TEXT_COLOR"],
            hover_color=self.current_theme["BTN_HOVER_COLOR"]
        )
        self.status_label.configure(text_color=self.current_theme["DISABLED_COLOR"])
        self.progress_bar.configure(
            progress_color=self.current_theme["PROGRESS_COLOR"],
            fg_color=self.current_theme["ENTRY_COLOR"],
            border_color=self.current_theme["BORDER_COLOR"]
        )

    # ---
    # --- THEMED POPUP DIALOGS ---
    # ---
    # These functions replace the ugly white 'messagebox' popups
    # with themed CTkToplevel windows.
    
    def _show_themed_dialog(self, title, message, dialog_type, options=None):
        """Helper function to create a themed modal dialog."""
        dialog = ctk.CTkToplevel(self)
        dialog.title(title)
        dialog.transient(self) # Keep on top
        dialog.grab_set() # Modal
        dialog.geometry("400x150")
        dialog.resizable(False, False)
        dialog.configure(fg_color=self.current_theme["MENU_COLOR"])
        
        dialog.grid_columnconfigure(0, weight=1)
        dialog.grid_rowconfigure(0, weight=1)
        
        label = ctk.CTkLabel(
            dialog,
            text=message,
            font=ctk.CTkFont(size=13),
            text_color=self.current_theme["TEXT_COLOR"],
            wraplength=380
        )
        label.grid(row=0, column=0, columnspan=2, sticky="nsew", padx=20, pady=20)
        
        button_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        button_frame.grid(row=1, column=0, columnspan=2, sticky="ew", padx=20, pady=(0, 20))
        
        result = [None] # Use a list to pass by reference

        def on_ok():
            result[0] = True
            dialog.destroy()
            
        def on_yes():
            result[0] = True
            dialog.destroy()
            
        def on_no():
            result[0] = False
            dialog.destroy()

        if dialog_type == "info" or dialog_type == "error" or dialog_type == "warning":
            button_frame.grid_columnconfigure(0, weight=1) # Center the button
            button_frame.grid_columnconfigure(1, weight=0)
            button_frame.grid_columnconfigure(2, weight=1)
            ok_btn = ctk.CTkButton(
                button_frame, text="OK", command=on_ok,
                fg_color=self.current_theme["BTN_COLOR"],
                text_color=self.current_theme["BTN_TEXT_COLOR"],
                hover_color=self.current_theme["BTN_HOVER_COLOR"]
            )
            ok_btn.grid(row=0, column=1, padx=5) # Place in middle column
            dialog.bind("<Return>", lambda e: on_ok())
            
        elif dialog_type == "askyesno":
            button_frame.grid_columnconfigure(0, weight=1)
            button_frame.grid_columnconfigure(1, weight=1)
            
            yes_btn = ctk.CTkButton(
                button_frame, text="Yes", command=on_yes,
                fg_color=self.current_theme["BTN_COLOR"],
                text_color=self.current_theme["BTN_TEXT_COLOR"],
                hover_color=self.current_theme["BTN_HOVER_COLOR"]
            )
            yes_btn.grid(row=0, column=0, sticky="ew", padx=5)
            
            no_btn = ctk.CTkButton(
                button_frame, text="No", command=on_no,
                fg_color=self.current_theme["ENTRY_COLOR"],
                text_color=self.current_theme["TEXT_COLOR"],
                hover_color=self.current_theme["MENU_COLOR"]
            )
            no_btn.grid(row=0, column=1, sticky="ew", padx=5)
            dialog.bind("<Return>", lambda e: on_yes())

        # Center the dialog
        dialog.update_idletasks()
        x = self.winfo_x() + (self.winfo_width() - dialog.winfo_width()) // 2
        y = self.winfo_y() + (self.winfo_height() - dialog.winfo_height()) // 2
        dialog.geometry(f"+{x}+{y}")
        
        dialog.wait_window() # Wait until dialog is closed
        return result[0]

    def _show_themed_info(self, title, message):
        self._show_themed_dialog(title, message, "info")

    def _show_themed_warning(self, title, message):
        self._show_themed_dialog(title, message, "warning")

    def _show_themed_error(self, title, message):
        self._show_themed_dialog(title, message, "error")

    def _show_themed_askyesno(self, title, message):
        # This was the one line I forgot, which caused the crash.
        # It needs to call the main function, not a non-existent one.
        return self._show_themed_dialog(title, message, "askyesno")
    # --- END THEMED DIALOGS ---


if __name__ == "__main__":
    print("Running main_window.py directly for testing...")
    
    def test_resource_path(relative_path):
        base_path = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        return os.path.join(base_path, relative_path)

    app = App(resource_path_func=test_resource_path)
    
    try:
        icon_path = test_resource_path(os.path.join("assets", "app_logo.ico"))
        if os.path.exists(icon_path):
            app.iconbitmap(icon_path)
        else:
            print(f"Test icon not found at: {icon_path}")
    except Exception as e:
        print(f"Error loading test icon: {e}")
        
    app.mainloop()