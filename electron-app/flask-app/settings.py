import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk  # For eye icon
import requests
import os
from config import SUPABASE_URL, SUPABASE_KEY  # Import Supabase configuration
import json

CONFIG_FILE = "config.json"

def load_config():
    """Load configuration from the config file."""
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as config_file:
            return json.load(config_file)
    else:
        return {
            "supabase_url": SUPABASE_URL,
            "supabase_key": SUPABASE_KEY,
            "theme": "winnative"  # Ensure a default theme is set
        }

def save_config(config):
    """Save configuration to the config file."""
    with open(CONFIG_FILE, "w") as config_file:
        json.dump(config, config_file)

def fetch_users():
    """Fetch users from Supabase."""
    try:
        response = requests.get(f"{SUPABASE_URL}/rest/v1/profiles", headers={
            "apikey": SUPABASE_KEY,
            "Authorization": f"Bearer {SUPABASE_KEY}",
            "Content-Type": "application/json"
        })
        print(f"Response status code: {response.status_code}")  # Debugging statement
        print(f"Response content: {response.content}")  # Debugging statement
        if response.status_code == 200:
            users = response.json()
            if isinstance(users, list):
                return users
            else:
                messagebox.showerror("Eroare", "Formatul răspunsului nu este corect!")
                return []
        else:
            messagebox.showerror("Eroare", "Nu s-au putut încărca utilizatorii!")
            return []
    except Exception as e:
        messagebox.showerror("Eroare", f"Nu s-au putut încărca utilizatorii: {e}")
        return []



def open_settings_window(user_id, user_email, current_name):
    """Open the settings window."""
    settings_window = tk.Toplevel()
    settings_window.title("Setări Utilizator")
    settings_window.geometry("600x400")  # Adjusted window size

    frame = ttk.Frame(settings_window, padding=20)
    frame.pack(fill="both", expand=True)

    # Title
    ttk.Label(frame, text="Setări", font=("Segoe UI", 16, "bold")).grid(row=0, column=0, columnspan=3, pady=10, sticky="w")

    # Theme Selection
    def change_theme(theme_name):
        style.theme_use(theme_name)
        config["theme"] = theme_name
        save_config(config)

    config = load_config()
    style = ttk.Style()
    theme_var = tk.StringVar(value=config.get("theme", style.theme_use()))  # Get current theme
    ttk.Label(frame, text="Temă:", font=("Segoe UI", 12, "bold")).grid(row=1, column=0, sticky="w", padx=5, pady=5)
    theme_dropdown = ttk.Combobox(frame, textvariable=theme_var, values=style.theme_names(), state="readonly")
    theme_dropdown.grid(row=1, column=1, padx=5, pady=5)
    theme_dropdown.bind("<<ComboboxSelected>>", lambda e: change_theme(theme_var.get()))

    # User List Table
    ttk.Label(frame, text="Lista Utilizatori", font=("Segoe UI", 14, "bold")).grid(row=2, column=0, columnspan=3, pady=10)

    user_table = ttk.Treeview(frame, columns=("Nume", "Email", "Rol"), show="headings", height=10)
    user_table.heading("Nume", text="Nume")
    user_table.heading("Email", text="Email")
    user_table.heading("Rol", text="Rol")
    user_table.column("Nume", width=150)
    user_table.column("Email", width=200)
    user_table.column("Rol", width=100)
    user_table.grid(row=3, column=0, columnspan=3, pady=5, sticky="nsew")

    # Fetch users and populate table
    users = fetch_users()
    for user in users:
        user_table.insert("", "end", values=(user["name"], user["email"], user["role"]))

    # Make the table columns resizable
    frame.grid_rowconfigure(3, weight=1)
    frame.grid_columnconfigure(1, weight=1)

    settings_window.mainloop()