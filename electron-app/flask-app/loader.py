import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import time
import os

class LoaderApp:
    def __init__(self, root, on_complete):
        self.root = root
        self.on_complete = on_complete
        self.root.title("Loading...")
        self.root.geometry("1200x800")  # Set the loader window size to match the dashboard window size
        self.root.configure(bg="#d3d3d3")
        self.root.resizable(False, False)

        self.center_window()
        self.create_widgets()
        self.start_loading()

    def create_widgets(self):
        # Load and display the branding image
        image_path = os.path.join(os.path.dirname(__file__), "resources", "Branding.jpg")
        image = Image.open(image_path)
        self.root.update_idletasks()  # Ensure correct geometry calculation
        image = image.resize((int(self.root.winfo_width() * 0.4), int(self.root.winfo_height() * 0.4)), Image.LANCZOS)  # Resize the image to fit 40% of the window
        photo = ImageTk.PhotoImage(image)
        self.image_label = tk.Label(self.root, image=photo)
        self.image_label.image = photo  # Keep a reference to avoid garbage collection
        self.image_label.pack(pady=20)

        # Create the loading bar
        self.progress = ttk.Progressbar(self.root, orient="horizontal", length=400, mode="determinate")
        self.progress.pack(pady=20)

    def center_window(self):
        self.root.update_idletasks()  # Ensure correct geometry calculation
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() - width) // 2
        y = (self.root.winfo_screenheight() - height) // 2
        self.root.geometry(f"+{x}+{y}")

    def start_loading(self):
        self.progress["maximum"] = 100
        self.progress["value"] = 0
        self.increment_progress()

    def increment_progress(self):
        if self.progress["value"] < 100:
            self.progress["value"] += 1
            self.root.after(40, self.increment_progress)  # Increment every 40ms for a total of 4 seconds
        else:
            self.root.after(500, self.finish_loading)  # Call a method to close the window

    def finish_loading(self):
        self.root.destroy()  # Close the loader window
        self.on_complete()  # Call the main application function

def show_loader(on_complete):
    root = tk.Tk()
    app = LoaderApp(root, on_complete)
    root.mainloop()