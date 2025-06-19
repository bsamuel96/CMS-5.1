import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import requests
import pandas as pd

class PaymentsWindow:
    def __init__(self, root):
        self.root = root
        self.root.title("Plăți")
        self.root.geometry("1000x600")
        self.root.configure(bg="#d3d3d3")

        # Center the window on the screen
        self.center_window()

        self.create_widgets()
        self.fetch_payments()

    def center_window(self):
        """Center the window horizontally and vertically."""
        self.root.update_idletasks()
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        window_width = 1000
        window_height = 600
        x = (screen_width // 2) - (window_width // 2)
        y = (screen_height // 2) - (window_height // 2)
        self.root.geometry(f"{window_width}x{window_height}+{x}+{y}")

    def create_widgets(self):
        """Create the UI components for the payments window."""
        # Title
        ttk.Label(self.root, text="Plăți", font=("Segoe UI", 14, "bold")).pack(pady=10)

        # Search frame
        search_frame = ttk.Frame(self.root)
        search_frame.pack(fill=tk.X, padx=20, pady=10)

        ttk.Label(search_frame, text="Client:").pack(side=tk.LEFT, padx=5)
        self.client_search = ttk.Entry(search_frame, width=20)
        self.client_search.pack(side=tk.LEFT, padx=5)

        ttk.Label(search_frame, text="Comandă:").pack(side=tk.LEFT, padx=5)
        self.order_search = ttk.Entry(search_frame, width=20)
        self.order_search.pack(side=tk.LEFT, padx=5)

        ttk.Label(search_frame, text="Data:").pack(side=tk.LEFT, padx=5)
        self.date_search = ttk.Entry(search_frame, width=20)
        self.date_search.pack(side=tk.LEFT, padx=5)

        search_button = ttk.Button(search_frame, text="Caută", command=self.filter_payments)
        search_button.pack(side=tk.LEFT, padx=5)

        # Table frame
        table_frame = ttk.Frame(self.root)
        table_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        self.payments_table = ttk.Treeview(table_frame, columns=("Data", "Client", "Comandă", "Sumă", "Înregistrat de"), show="headings", height=15)
        self.payments_table.heading("Data", text="Data")
        self.payments_table.heading("Client", text="Client")
        self.payments_table.heading("Comandă", text="Comandă")
        self.payments_table.heading("Sumă", text="Sumă")
        self.payments_table.heading("Înregistrat de", text="Înregistrat de")
        self.payments_table.column("Data", width=150, anchor="center")
        self.payments_table.column("Client", width=200, anchor="center")
        self.payments_table.column("Comandă", width=150, anchor="center")
        self.payments_table.column("Sumă", width=100, anchor="center")
        self.payments_table.column("Înregistrat de", width=200, anchor="center")
        self.payments_table.pack(fill=tk.BOTH, expand=True)

        # Buttons frame
        buttons_frame = ttk.Frame(self.root)
        buttons_frame.pack(fill=tk.X, padx=20, pady=10)

        export_button = ttk.Button(buttons_frame, text="Exportă CSV", command=self.export_to_csv)
        export_button.pack(side=tk.LEFT, padx=5)

        close_button = ttk.Button(buttons_frame, text="Închide", command=self.root.destroy)
        close_button.pack(side=tk.RIGHT, padx=5)

    def fetch_payments(self):
        """Fetch all payments from the backend."""
        try:
            response = requests.get("http://127.0.0.1:5000/payments")
            if response.status_code == 200:
                payments = response.json()
                self.update_payments_table(payments)
            else:
                messagebox.showerror("Eroare", "Nu s-au putut încărca plățile.")
        except Exception as e:
            messagebox.showerror("Eroare", f"A apărut o eroare: {e}")

    def update_payments_table(self, payments):
        """Update the payments table with fetched data."""
        # Clear existing data
        for row in self.payments_table.get_children():
            self.payments_table.delete(row)

        # Insert new data
        for payment in payments:
            self.payments_table.insert("", "end", values=(payment["data"], payment["client"], payment["comanda"], payment["suma"], payment["inregistrat_de"]))

    def filter_payments(self):
        """Filter payments based on search fields."""
        client = self.client_search.get()
        order = self.order_search.get()
        date = self.date_search.get()

        try:
            params = {}
            if client:
                params["client"] = client
            if order:
                params["order"] = order
            if date:
                params["date"] = date

            response = requests.get("http://127.0.0.1:5000/payments", params=params)
            if response.status_code == 200:
                payments = response.json()
                self.update_payments_table(payments)
            else:
                messagebox.showerror("Eroare", "Nu s-au putut filtra plățile.")
        except Exception as e:
            messagebox.showerror("Eroare", f"A apărut o eroare: {e}")

    def export_to_csv(self):
        """Export the payments table to a CSV file."""
        file_path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV files", "*.csv")])
        if not file_path:
            return

        try:
            # Collect data from the table
            data = [self.payments_table.item(row)["values"] for row in self.payments_table.get_children()]
            df = pd.DataFrame(data, columns=["Data", "Client", "Comandă", "Sumă", "Înregistrat de"])
            df.to_csv(file_path, index=False)
            messagebox.showinfo("Succes", "Plățile au fost exportate cu succes!")
        except Exception as e:
            messagebox.showerror("Eroare", f"A apărut o eroare la export: {e}")

def open_payments_window(root):
    """Open the Payments window."""
    payments_window = tk.Toplevel(root)
    PaymentsWindow(payments_window)
    payments_window.mainloop()
