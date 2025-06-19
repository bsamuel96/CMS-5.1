import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import requests
import pandas as pd

class SalesReportApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Raport Vânzări")
        self.root.geometry("800x600")  # Window size
        self.center_window()  # Center the window
        self.root.configure(bg="#d3d3d3")
        self.style = ttk.Style()
        self.apply_styling()
        self.create_widgets()

    def center_window(self):
        """Center the window horizontally and vertically."""
        self.root.update_idletasks()
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        window_width = self.root.winfo_width()
        window_height = self.root.winfo_height()
        x = (screen_width // 2) - (800 // 2)  # Center horizontally
        y = (screen_height // 2) - (600 // 2)  # Center vertically
        self.root.geometry(f"800x600+{x}+{y}")

    def apply_styling(self):
        """Apply consistent styling."""
        self.style.configure("TLabel", font=("Segoe UI", 11), padding=5)
        self.style.configure("TButton", font=("Segoe UI", 11, "bold"), padding=5)
        self.style.configure("Treeview.Heading", font=("Segoe UI", 12, "bold"), padding=10)
        self.style.configure("TLabelFrame", background="#f0f0f0")
        self.style.configure("Hover.TLabelFrame", background="#e0e0e0")

    def create_widgets(self):
        # Title
        title_label = ttk.Label(self.root, text="Raport Vânzări", font=("Segoe UI", 14, "bold"), background="#d3d3d3")
        title_label.pack(pady=10)

        # Export button frame
        button_frame = tk.Frame(self.root, bg="#d3d3d3")
        button_frame.pack(fill=tk.X, padx=20)
        ttk.Button(button_frame, text="Exportă CSV", command=self.export_to_csv).pack(side=tk.LEFT, pady=10)

        # Table frame with consistent background
        table_frame = tk.Frame(self.root, bg="#d3d3d3")
        table_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=(10, 20))

        # Configure Treeview style for better background
        self.style.configure("Custom.Treeview",
                             background="#f9f9f9",
                             fieldbackground="#f9f9f9",
                             rowheight=25,
                             font=("Segoe UI", 10))
        self.style.configure("Custom.Treeview.Heading",
                             font=("Segoe UI", 11, "bold"),
                             background="#e0e0e0")

        self.sales_table = ttk.Treeview(table_frame, style="Custom.Treeview",
                                        columns=("Localitate", "Județ", "Nr. Comenzi", "Total Vânzări"),
                                        show="headings", height=10)

        self.sales_table.heading("Localitate", text="Localitate")
        self.sales_table.heading("Județ", text="Județ")
        self.sales_table.heading("Nr. Comenzi", text="Nr. Comenzi")
        self.sales_table.heading("Total Vânzări", text="Total Vânzări")

        self.sales_table.column("Localitate", width=150, anchor="center")
        self.sales_table.column("Județ", width=150, anchor="center")
        self.sales_table.column("Nr. Comenzi", width=100, anchor="center")
        self.sales_table.column("Total Vânzări", width=150, anchor="center")

        self.sales_table.pack(fill=tk.BOTH, expand=True)

        # Fetch data
        self.fetch_sales_report()

    def fetch_sales_report(self):
        try:
            # Fetch data from the API
            response = requests.get("http://127.0.0.1:5000/sales_report")
            if response.status_code == 200:
                sales_data = response.json()
                self.update_sales_table(sales_data)
            else:
                error_message = response.json().get("error", "Unknown error occurred.")
                messagebox.showerror("Eroare", f"Nu s-au putut încărca datele de vânzări: {error_message}")
        except Exception as e:
            messagebox.showerror("Eroare", f"A apărut o eroare: {e}")

    def update_sales_table(self, sales_data):
        # Clear existing data
        for row in self.sales_table.get_children():
            self.sales_table.delete(row)

        # Insert new data
        for sale in sales_data:
            self.sales_table.insert("", "end", values=(sale["localitate"], sale["judet"], sale["nr_comenzi"], sale["total_vanzari"]))

    def export_to_csv(self):
        file_path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV files", "*.csv")])
        if not file_path:
            return

        try:
            # Collect data from the table
            data = [self.sales_table.item(row)["values"] for row in self.sales_table.get_children()]
            df = pd.DataFrame(data, columns=["Localitate", "Județ", "Nr. Comenzi", "Total Vânzări"])
            df.to_csv(file_path, index=False)
            messagebox.showinfo("Succes", "Raportul a fost exportat cu succes!")
        except Exception as e:
            messagebox.showerror("Eroare", f"A apărut o eroare la export: {e}")

def open_sales_report_window(root):
    """Open the Sales Report window."""
    app = SalesReportApp(root)
    root.mainloop()

if __name__ == "__main__":
    root = tk.Tk()
    app = SalesReportApp(root)
    root.mainloop()
