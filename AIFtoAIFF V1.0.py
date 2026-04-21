import os
import threading
import tkinter as tk
from tkinter import filedialog, ttk

# ----------------
# Version History
# ----------------
#
# v1.0 - Initial Release
# Does what it says on the tin: converts file extensions from .aif to .aiff
#
# Planned:
# - Bidirectional conversion
# - Display list of converted files within success popup
# - Custom app and title icons

try:
    from tkinterdnd2 import DND_FILES, TkinterDnD
    DND_AVAILABLE = True
except ImportError:
    DND_AVAILABLE = False
    DND_FILES = None
    TkinterDnD = None


APP_THEME = {
    "bg": "#1b1026",
    "panel": "#261537",
    "panel_alt": "#2f1b45",
    "entry": "#341f4f",
    "text": "#f3eefe",
    "muted": "#cbb9e8",
    "accent": "#8b5cf6",
    "accent_hover": "#9d73ff",
    "border": "#50306f",
    "success": "#c4b5fd",
    "listbox_bg": "#221331",
    "listbox_select": "#6d48c9",
    "drag_glow": "#7c4dff",
    "tile_selected": "#241238",
    "tile_unselected": "#2f1b45",
    "tile_border_selected": "#a78bfa",
    "tile_border_unselected": "#50306f",
}


class ThemedPopup(tk.Toplevel):
    def __init__(self, parent: tk.Tk, title: str, message: str, button_text: str = "OK") -> None:
        super().__init__(parent)
        self.title(title)
        self.configure(bg=APP_THEME["bg"])
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        popup_width = 380
        popup_height = 180
        parent.update_idletasks()
        x_pos = parent.winfo_rootx() + (parent.winfo_width() // 2) - (popup_width // 2)
        y_pos = parent.winfo_rooty() + (parent.winfo_height() // 2) - (popup_height // 2)
        self.geometry(f"{popup_width}x{popup_height}+{x_pos}+{y_pos}")

        outer_frame = tk.Frame(self, bg=APP_THEME["bg"], padx=16, pady=16)
        outer_frame.pack(fill="both", expand=True)

        panel = tk.Frame(
            outer_frame,
            bg=APP_THEME["panel"],
            highlightthickness=1,
            highlightbackground=APP_THEME["border"]
        )
        panel.pack(fill="both", expand=True)

        title_label = tk.Label(
            panel,
            text=title,
            bg=APP_THEME["panel"],
            fg=APP_THEME["text"],
            font=("Segoe UI", 12, "bold")
        )
        title_label.pack(anchor="w", padx=16, pady=(16, 8))

        message_label = tk.Label(
            panel,
            text=message,
            bg=APP_THEME["panel"],
            fg=APP_THEME["muted"],
            font=("Segoe UI", 10),
            justify="left",
            wraplength=320
        )
        message_label.pack(anchor="w", padx=16, pady=(0, 16))

        button = tk.Button(
            panel,
            text=button_text,
            bg=APP_THEME["accent"],
            fg=APP_THEME["text"],
            activebackground=APP_THEME["accent_hover"],
            activeforeground=APP_THEME["text"],
            relief="flat",
            bd=0,
            padx=18,
            pady=8,
            font=("Segoe UI", 10, "bold"),
            command=self.destroy,
            cursor="hand2"
        )
        button.pack(anchor="e", padx=16, pady=(0, 16))
        button.focus_set()

        self.bind("<Return>", lambda event: self.destroy())
        self.bind("<Escape>", lambda event: self.destroy())


class ExtensionChangerApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("AIF to AIFF")
        self.root.geometry("560x400")
        self.root.resizable(False, False)
        self.root.configure(bg=APP_THEME["bg"])

        self.selected_folder = tk.StringVar()
        self.status_text = tk.StringVar(value="Select or drag a folder to begin.")
        self.processed_count_text = tk.StringVar(value="")
        self.recursive_mode = tk.BooleanVar(value=False)

        self._configure_styles()
        self._build_ui()

    def _configure_styles(self) -> None:
        style = ttk.Style()
        style.theme_use("clam")

        style.configure("App.TFrame", background=APP_THEME["bg"])
        style.configure("Panel.TFrame", background=APP_THEME["panel"])

        style.configure(
            "Title.TLabel",
            background=APP_THEME["panel"],
            foreground=APP_THEME["text"],
            font=("Segoe UI", 13, "bold")
        )

        style.configure(
            "Label.TLabel",
            background=APP_THEME["panel"],
            foreground=APP_THEME["text"],
            font=("Segoe UI", 10)
        )

        style.configure(
            "Muted.TLabel",
            background=APP_THEME["panel"],
            foreground=APP_THEME["muted"],
            font=("Segoe UI", 10)
        )

        style.configure(
            "App.TButton",
            background=APP_THEME["accent"],
            foreground=APP_THEME["text"],
            bordercolor=APP_THEME["accent"],
            lightcolor=APP_THEME["accent"],
            darkcolor=APP_THEME["accent"],
            padding=(12, 8),
            relief="flat",
            font=("Segoe UI", 10, "bold")
        )
        style.map(
            "App.TButton",
            background=[("active", APP_THEME["accent_hover"]), ("disabled", APP_THEME["panel_alt"])],
            foreground=[("disabled", APP_THEME["muted"])]
        )

        style.configure(
            "App.TEntry",
            fieldbackground=APP_THEME["entry"],
            background=APP_THEME["entry"],
            foreground=APP_THEME["text"],
            bordercolor=APP_THEME["border"],
            lightcolor=APP_THEME["border"],
            darkcolor=APP_THEME["border"],
            insertcolor=APP_THEME["text"],
            padding=8
        )
        style.map(
            "App.TEntry",
            fieldbackground=[("readonly", APP_THEME["entry"])],
            foreground=[("readonly", APP_THEME["text"])]
        )

        style.configure(
            "App.Horizontal.TProgressbar",
            troughcolor=APP_THEME["panel_alt"],
            background=APP_THEME["accent"],
            bordercolor=APP_THEME["border"],
            lightcolor=APP_THEME["accent"],
            darkcolor=APP_THEME["accent"],
            thickness=18
        )

        style.configure(
            "App.TCheckbutton",
            background=APP_THEME["panel"],
            foreground=APP_THEME["text"],
            font=("Segoe UI", 10)
        )
        style.map(
            "App.TCheckbutton",
            background=[("active", APP_THEME["panel"])],
            foreground=[("active", APP_THEME["text"])]
        )

    def _build_ui(self) -> None:
        main_frame = ttk.Frame(self.root, style="App.TFrame", padding=16)
        main_frame.pack(fill="both", expand=True)

        panel_frame = ttk.Frame(main_frame, style="Panel.TFrame", padding=16)
        panel_frame.pack(fill="both", expand=True)

        title_label = ttk.Label(panel_frame, text="AIF to AIFF Extension Changer", style="Title.TLabel")
        title_label.pack(anchor="w", pady=(0, 12))

        folder_frame = ttk.Frame(panel_frame, style="Panel.TFrame")
        folder_frame.pack(fill="x", pady=(0, 12))

        folder_label = ttk.Label(folder_frame, text="Folder:", style="Label.TLabel")
        folder_label.pack(anchor="w")

        folder_entry_frame = ttk.Frame(folder_frame, style="Panel.TFrame")
        folder_entry_frame.pack(fill="x", pady=(6, 0))

        options_frame = ttk.Frame(panel_frame, style="Panel.TFrame")
        options_frame.pack(fill="x", pady=(10, 10))

        folder_entry = ttk.Entry(
            folder_entry_frame,
            textvariable=self.selected_folder,
            style="App.TEntry",
            state="readonly"
        )
        folder_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))

        browse_button = ttk.Button(
            folder_entry_frame,
            text="Select Folder",
            style="App.TButton",
            command=self.select_folder
        )
        browse_button.pack(side="right")

        recursive_check = tk.Checkbutton(
            options_frame,
            text="Include subfolders.",
            variable=self.recursive_mode,
            bg=APP_THEME["panel"],
            fg=APP_THEME["text"],
            activebackground=APP_THEME["panel"],
            activeforeground=APP_THEME["text"],
            selectcolor=APP_THEME["entry"],
            font=("Segoe UI", 10),
            highlightthickness=0,
            bd=0
        )
        recursive_check.pack(anchor="w", pady=(0, 10))

        button_frame = ttk.Frame(panel_frame, style="Panel.TFrame")
        button_frame.pack(fill="x", pady=(0, 12))

        self.change_button = ttk.Button(
            button_frame,
            text="Change Extensions",
            style="App.TButton",
            command=self.start_change_extensions
        )
        self.change_button.pack()

        self.progress_bar = ttk.Progressbar(
            panel_frame,
            orient="horizontal",
            mode="determinate",
            length=480,
            style="App.Horizontal.TProgressbar"
        )
        self.progress_bar.pack(fill="x", pady=(0, 8))

        status_row = ttk.Frame(panel_frame, style="Panel.TFrame")
        status_row.pack(fill="x")

        status_label = ttk.Label(
            status_row,
            textvariable=self.status_text,
            style="Muted.TLabel"
        )
        status_label.pack(side="left", anchor="w")

        processed_label = ttk.Label(
            status_row,
            textvariable=self.processed_count_text,
            style="Muted.TLabel"
        )
        processed_label.pack(side="right", anchor="e")

        if DND_AVAILABLE:
            self.enable_drag_and_drop(self.root)
            self.enable_drag_and_drop(main_frame)
            self.enable_drag_and_drop(panel_frame)

    def enable_drag_and_drop(self, widget: tk.Widget) -> None:
        widget.drop_target_register(DND_FILES)
        widget.dnd_bind("<<Drop>>", self.on_drop)
        widget.dnd_bind("<<DragEnter>>", self.on_drag_enter)
        widget.dnd_bind("<<DragLeave>>", self.on_drag_leave)

    def on_drag_enter(self, event=None):
        self.status_text.set("Drop a folder anywhere in the app.")
        return event.action if event else None

    def on_drag_leave(self, event=None):
        self.status_text.set("Select or drag a folder to begin.")
        return event.action if event else None

    def on_drop(self, event) -> None:
        dropped_path = event.data.strip()

        if dropped_path.startswith("{") and dropped_path.endswith("}"):
            dropped_path = dropped_path[1:-1]

        if os.path.isdir(dropped_path):
            self.selected_folder.set(dropped_path)
            self.status_text.set("Folder dropped successfully. Ready to change extensions.")
        else:
            self.show_popup("Invalid Drop", "Please drop a folder, not a file.")

    def show_popup(self, title: str, message: str) -> None:
        popup = ThemedPopup(self.root, title, message)
        self.root.wait_window(popup)

    def select_folder(self) -> None:
        folder = filedialog.askdirectory()
        if folder:
            self.selected_folder.set(folder)
            self.status_text.set("Folder selected. Ready to change extensions.")

    def start_change_extensions(self) -> None:
        folder = self.selected_folder.get().strip()

        if not folder:
            self.show_popup("No Folder Selected", "Please select a folder first.")
            return

        if not os.path.isdir(folder):
            self.show_popup("Invalid Folder", "The selected folder does not exist.")
            return

        self.change_button.config(state="disabled")
        self.progress_bar["value"] = 0
        self.status_text.set("Scanning for .aif files...")

        worker = threading.Thread(target=self.change_extensions, args=(folder, self.recursive_mode.get()), daemon=True)
        worker.start()

    def get_aif_files(self, folder: str, recursive: bool) -> list[str]:
        if recursive:
            aif_files = []
            for root_dir, _, files in os.walk(folder):
                for file_name in files:
                    if file_name.lower().endswith(".aif"):
                        aif_files.append(os.path.join(root_dir, file_name))
            return aif_files

        return [
            os.path.join(folder, file_name)
            for file_name in os.listdir(folder)
            if os.path.isfile(os.path.join(folder, file_name)) and file_name.lower().endswith(".aif")
        ]

    def change_extensions(self, folder: str, recursive: bool) -> None:
        try:
            aif_files = self.get_aif_files(folder, recursive)
            total_files = len(aif_files)

            if total_files == 0:
                self.root.after(0, self.no_files_found)
                return

            self.root.after(0, lambda: self.prepare_progress(total_files))

            renamed_count = 0

            for index, old_path in enumerate(aif_files, start=1):
                new_path = old_path[:-4] + ".aiff"

                if os.path.exists(new_path):
                    self.root.after(0, lambda current=index, total=total_files: self.update_progress(current, total))
                    continue

                os.rename(old_path, new_path)
                renamed_count += 1
                self.root.after(0, lambda current=index, total=total_files: self.update_progress(current, total))

            self.root.after(0, lambda: self.complete_success(total_files, renamed_count))

        except Exception as error:
            self.root.after(0, lambda: self.handle_error(str(error)))

    def prepare_progress(self, total_files: int) -> None:
        self.progress_bar["maximum"] = total_files
        self.status_text.set(f"Changing extensions for {total_files} file(s)...")
        self.processed_count_text.set(f"0 / {total_files}")

    def update_progress(self, current: int, total: int) -> None:
        self.progress_bar["value"] = current
        self.status_text.set(f"Processing file {current} of {total}...")
        self.processed_count_text.set(f"{current} / {total}")

    def no_files_found(self) -> None:
        self.change_button.config(state="normal")
        self.progress_bar["value"] = 0
        self.status_text.set("No .aif files were found in the selected folder.")
        self.show_popup("No Files Found", "No .aif files were found in the selected folder.")
        self.processed_count_text.set("")

    def complete_success(self, total_files: int, renamed_count: int) -> None:
        self.change_button.config(state="normal")
        self.progress_bar["value"] = total_files
        self.status_text.set("Task completed successfully.")
        self.show_popup("Success", f"Done. {renamed_count} file extension(s) changed from .aif to .aiff.")
        self.processed_count_text.set(f"{total_files} / {total_files}")

    def handle_error(self, error_message: str) -> None:
        self.change_button.config(state="normal")
        self.status_text.set("An error occurred.")
        self.processed_count_text.set("")

        safe_message = f"An error occurred:\n\n{error_message}"
        self.show_popup("Error", safe_message)


if __name__ == "__main__":
    if DND_AVAILABLE:
        root = TkinterDnD.Tk()
    else:
        root = tk.Tk()

    app = ExtensionChangerApp(root)
    root.mainloop()
