import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
import requests
import sys
import json
import os
from dashboard import DashboardApp
from config import SUPABASE_URL, SUPABASE_KEY  # Import Supabase configuration
from loader import show_loader  # Import the loader

CONFIG_FILE = "config.json"

class LoginApp:
    def __init__(self, root, reset_link=None):
        self.root = root
        self.root.title("Log In")
        self.root.geometry("400x300")
        self.root.configure(bg="#d3d3d3")

        # Center the window on the screen
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() - self.root.winfo_reqwidth()) // 2
        y = (self.root.winfo_screenheight() - self.root.winfo_reqheight()) // 2
        self.root.geometry(f"+{x}+{y}")

        self.create_widgets()

        # Check if "Remember Me" is enabled and autofill the fields if credentials are saved
        self.check_remember_me()

    def create_widgets(self):
        container = ttk.Frame(self.root, padding="20 20 20 20", relief="raised")
        container.place(relx=0.5, rely=0.5, anchor="center")

        title_label = ttk.Label(container, text="Log In", font=("Arial", 16, "bold"))
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 10))

        username_label = ttk.Label(container, text="Utilizator:")
        username_label.grid(row=1, column=0, sticky="e", pady=(0, 5))
        self.username_entry = ttk.Entry(container)
        self.username_entry.grid(row=1, column=1, pady=(0, 5))

        password_label = ttk.Label(container, text="Parolă:")
        password_label.grid(row=2, column=0, sticky="e", pady=(0, 5))
        self.password_entry = ttk.Entry(container, show="●")
        self.password_entry.grid(row=2, column=1, pady=(0, 5))

        self.show_password_var = tk.BooleanVar()
        show_password_check = ttk.Checkbutton(container, text="Afișează parola", variable=self.show_password_var, command=self.toggle_password)
        show_password_check.grid(row=3, column=0, columnspan=2, pady=(0, 5))

        self.remember_me_var = tk.BooleanVar()
        remember_me_check = ttk.Checkbutton(container, text="Ține-mă minte", variable=self.remember_me_var)
        remember_me_check.grid(row=4, column=0, columnspan=2, pady=(0, 5))

        login_button = ttk.Button(container, text="Log In", command=self.login)
        login_button.grid(row=5, column=0, columnspan=2, pady=(10, 0))

        self.root.bind("<Return>", self.login)

    def toggle_password(self):
        if self.show_password_var.get():
            self.password_entry.config(show="")
        else:
            self.password_entry.config(show="●")

    def login(self, event=None):
        username = self.username_entry.get()
        password = self.password_entry.get()
        remember_me = self.remember_me_var.get()

        print(f"Încercare de autentificare cu utilizatorul: {username} și parola: {password}")

        # Comment out or remove the code that makes the request to the Supabase API
        # try:
        #     response = requests.post(f'{SUPABASE_URL}/auth/v1/token?grant_type=password', json={'email': username, 'password': password}, headers={"apikey": SUPABASE_KEY})
        #     print(f"Raw response content: {response.content}")  # Debugging statement
        #     try:
        #         result = response.json()
        #     except ValueError:
        #         raise ValueError("Invalid JSON response")
        #     print(f"Stare răspuns: {response.status_code}, Date răspuns: {result}")
        #     if response.status_code == 200:
        #         user = result.get('user')
        #         if user is None:
        #             raise ValueError("User data is missing in the response.")
        #         print(f"User dictionary: {user}")  # Debugging statement
        #         if remember_me:
        #             self.save_credentials(username, password)
        self.root.destroy()
        show_loader(self.open_dashboard)

    def open_dashboard(self):
        dashboard_root = tk.Tk()
        DashboardApp(dashboard_root)
        dashboard_root.mainloop()

    def save_credentials(self, username, password):
        config = {
            "username": username,
            "password": password,
            "remember_me": True
        }
        with open("config.json", "w") as config_file:
            json.dump(config, config_file)

    def check_remember_me(self):
        if os.path.exists("config.json"):
            with open("config.json", "r") as config_file:
                config = json.load(config_file)
                if config.get("remember_me"):
                    self.username_entry.insert(0, config.get("username"))
                    self.password_entry.insert(0, config.get("password"))
                    self.remember_me_var.set(True)

if __name__ == "__main__":
    root = tk.Tk()
    app = LoginApp(root)
    root.mainloop()