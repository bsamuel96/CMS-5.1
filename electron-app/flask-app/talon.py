import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import requests
from io import BytesIO

def open_talon_window(parent, image_url):
    """Open a popup window to display and zoom a vehicle image."""
    window = tk.Toplevel(parent)
    window.title("Talon Vehicul")
    window.geometry("800x600")
    window.transient(parent)
    window.grab_set()
    window.configure(bg="#f0f0f0")  # Match the background color with dashboard.py

    ttk.Label(window, text="Talon Vehicul", font=("Segoe UI", 14, "bold")).pack(pady=10)

    # Create a scrollable canvas for the image
    canvas_frame = ttk.Frame(window)
    canvas_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    canvas = tk.Canvas(canvas_frame, bg="white", highlightthickness=0)
    h_scrollbar = ttk.Scrollbar(canvas_frame, orient="horizontal", command=canvas.xview)
    v_scrollbar = ttk.Scrollbar(canvas_frame, orient="vertical", command=canvas.yview)
    canvas.configure(xscrollcommand=h_scrollbar.set, yscrollcommand=v_scrollbar.set)

    h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
    v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    zoom_scale = 1.0
    pil_image = None
    tk_image = None

    def load_image():
        nonlocal pil_image, tk_image
        try:
            response = requests.get(image_url)
            img_data = BytesIO(response.content)
            pil_image = Image.open(img_data)
            update_image()
        except Exception as e:
            ttk.Label(window, text=f"Nu s-a putut încărca imaginea:\n{e}", foreground="red").pack(pady=20)

    def update_image():
        nonlocal tk_image
        if pil_image:
            new_size = (int(pil_image.width * zoom_scale), int(pil_image.height * zoom_scale))
            resized = pil_image.resize(new_size, Image.LANCZOS)
            tk_image = ImageTk.PhotoImage(resized)
            canvas.delete("all")
            canvas.create_image(0, 0, anchor="nw", image=tk_image)
            canvas.config(scrollregion=canvas.bbox("all"))

    def zoom_in():
        nonlocal zoom_scale
        zoom_scale *= 1.1
        update_image()

    def zoom_out():
        nonlocal zoom_scale
        zoom_scale /= 1.1
        update_image()

    def reset_zoom():
        nonlocal zoom_scale
        zoom_scale = 1.0
        update_image()

    def move_image(event):
        """Allow the user to drag the image."""
        canvas.scan_dragto(event.x, event.y, gain=1)

    def start_move(event):
        """Start the drag operation."""
        canvas.scan_mark(event.x, event.y)

    # Bind mouse events for dragging
    canvas.bind("<ButtonPress-1>", start_move)
    canvas.bind("<B1-Motion>", move_image)

    # Add buttons for zoom and reset
    btn_frame = ttk.Frame(window)
    btn_frame.pack(pady=10)

    ttk.Button(btn_frame, text="🔍 Zoom +", command=zoom_in).pack(side="left", padx=5)
    ttk.Button(btn_frame, text="🔎 Zoom -", command=zoom_out).pack(side="left", padx=5)
    ttk.Button(btn_frame, text="🔄 Resetare Zoom", command=reset_zoom).pack(side="left", padx=5)
    ttk.Button(btn_frame, text="Închide", command=window.destroy).pack(side="left", padx=5)

    load_image()
