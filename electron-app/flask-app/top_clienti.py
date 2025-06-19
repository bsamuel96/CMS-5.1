import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import requests
import pandas as pd

class TopClientsApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Top Clienți")
        self.root.geometry("1000x600")
        self.root.configure(bg="#d3d3d3")

        # Center the window on the screen
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() - self.root.winfo_width()) // 2
        y = (self.root.winfo_screenheight() - self.root.winfo_height()) // 2
        self.root.geometry(f"+{x}+{y}")

        self.create_widgets()
        self.fetch_top_clients()

    def create_widgets(self):
        self.style = ttk.Style()
        self.style.configure("TLabel", font=("Segoe UI", 10))
        self.style.configure("TButton", font=("Segoe UI", 10))
        self.style.configure("TEntry", font=("Segoe UI", 10))
        self.style.configure("Treeview.Heading", font=("Segoe UI", 10, "bold"))
        self.style.configure("Gold.Treeview", background="#ffd700")     # Gold
        self.style.configure("Silver.Treeview", background="#c0c0c0")   # Silver
        self.style.configure("Bronze.Treeview", background="#cd7f32")   # Bronze

        self.main_frame = ttk.Frame(self.root, padding="10")
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)  # Added padding to left, right, and bottom

        self.title_label = ttk.Label(self.main_frame, text="Top Clienți", font=("Segoe UI", 14, "bold"))
        self.title_label.pack(pady=(0, 10))

        self.filters_frame = ttk.Frame(self.main_frame)
        self.filters_frame.pack(pady=10)

        ttk.Label(self.filters_frame, text="Sortare după:").pack(side=tk.LEFT, padx=5)
        self.sort_by_var = tk.StringVar()
        self.sort_by_dropdown = ttk.Combobox(self.filters_frame, textvariable=self.sort_by_var, values=["Nr. Comenzi", "Total Cheltuit"], state="readonly")
        self.sort_by_dropdown.pack(side=tk.LEFT, padx=5)
        self.sort_by_dropdown.current(0)

        self.fetch_button = ttk.Button(self.filters_frame, text="Afișează", command=self.fetch_top_clients)
        self.fetch_button.pack(side=tk.LEFT, padx=5)

        self.clients_tree = ttk.Treeview(self.main_frame, columns=("Nume", "Număr Comenzi", "Total Cheltuit"), show="headings", height=15)
        self.clients_tree.heading("Nume", text="Nume")
        self.clients_tree.heading("Număr Comenzi", text="Număr Comenzi")
        self.clients_tree.heading("Total Cheltuit", text="Total Cheltuit (RON)")
        self.clients_tree.column("Nume", width=300)
        self.clients_tree.column("Număr Comenzi", width=150)
        self.clients_tree.column("Total Cheltuit", width=150)
        self.clients_tree.pack(fill=tk.BOTH, expand=True)

        # Footer label showing total number of existing customers
        self.footer_label = ttk.Label(self.main_frame, text="Total clienți existenți: N/A", font=("Segoe UI", 10, "italic"))
        self.footer_label.pack(pady=(5, 0))

        # Export CSV button
        self.export_button = ttk.Button(self.main_frame, text="Exportă CSV", command=self.export_to_csv)
        self.export_button.pack(pady=10)

        # Fetch initial data when the application starts
        self.fetch_top_clients()

    def fetch_top_clients(self):
        """Fetch and display top clients based on selected filters."""
        sort_by = self.sort_by_var.get()

        try:
            # Prepare parameters for the API request
            params = {'sort_by': sort_by}

            # Fetch data from the backend API
            response = requests.get(f'http://127.0.0.1:5000/top_clients', params=params)
            if response.status_code == 200:
                data = response.json()
                self.update_clients_table(data)

                # Fetch total number of existing customers
                total_clients_response = requests.get(f'http://127.0.0.1:5000/clients')
                if total_clients_response.status_code == 200:
                    total_clients = len(total_clients_response.json())
                    self.footer_label.config(text=f"Total clienți existenți: {total_clients}")
                else:
                    self.footer_label.config(text="Total clienți existenți: N/A")
            else:
                error_message = response.json().get("error", "Unknown error occurred.")
                messagebox.showerror("Eroare", f"Nu s-au putut încărca datele: {error_message}")
        except Exception as e:
            messagebox.showerror("Eroare", f"A apărut o eroare: {e}")

    def update_clients_table(self, clients):
        """Update the table with the fetched top clients data."""
        # Clear existing data
        for item in self.clients_tree.get_children():
            self.clients_tree.delete(item)

        # Insert new data with custom styles for top three rows
        for index, client in enumerate(clients):
            style_tag = ""
            if index == 0:
                style_tag = "gold"
            elif index == 1:
                style_tag = "silver"
            elif index == 2:
                style_tag = "bronze"

            # Format total_cheltuit as currency
            total = f"{client['total_cheltuit']:.2f} RON"

            self.clients_tree.insert(
                '', 'end',
                values=(client['nume'], client['nr_comenzi'], total),
                tags=(style_tag,)
            )

        # Apply tag-to-style mapping
        self.clients_tree.tag_configure("gold", background="#ffd700")
        self.clients_tree.tag_configure("silver", background="#e0e0e0")
        self.clients_tree.tag_configure("bronze", background="#f4a460")

    def export_to_csv(self):
        file_path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV files", "*.csv")])
        if not file_path:
            return

        try:
            # Collect data from the Treeview
            data = [self.clients_tree.item(item)["values"] for item in self.clients_tree.get_children()]
            df = pd.DataFrame(data, columns=["Nume", "Număr Comenzi", "Total Cheltuit (RON)"])
            df.to_csv(file_path, index=False)
            messagebox.showinfo("Succes", "Datele au fost exportate cu succes!")
        except Exception as e:
            messagebox.showerror("Eroare", f"A apărut o eroare la export: {e}")

def open_top_clients_window(root):
    """Open the Top Clients window."""
    top_clients_window = tk.Toplevel(root)
    app = TopClientsApp(top_clients_window)
    top_clients_window.mainloop()