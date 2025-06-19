import tkinter as tk
from tkinter import ttk, messagebox
import requests

class EditOrderApp:
    def __init__(self, root, order_number):
        self.root = root
        self.order_number = order_number
        self.root.title("Editează Comandă")
        self.root.geometry("1000x600")
        self.root.configure(bg="#d3d3d3")

        # Center the window on the screen
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() - self.root.winfo_reqwidth()) // 2
        y = (self.root.winfo_screenheight() - self.root.winfo_reqheight()) // 2
        self.root.geometry(f"+{x}+{y}")

        self.create_widgets()
        self.fetch_order_details()

    def create_widgets(self):
        self.style = ttk.Style()
        self.style.configure("TLabel", font=("Segoe UI", 10))
        self.style.configure("TButton", font=("Segoe UI", 10))
        self.style.configure("TEntry", font=("Segoe UI", 10))

        self.main_frame = ttk.Frame(self.root, padding="10")
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(self.main_frame, text="Client:", font=("Segoe UI", 10)).grid(row=0, column=0, padx=10, pady=5, sticky="E")
        self.client_label = ttk.Label(self.main_frame, font=("Segoe UI", 10))
        self.client_label.grid(row=0, column=1, padx=10, pady=5, sticky="W")

        ttk.Label(self.main_frame, text="Vehicul:", font=("Segoe UI", 10)).grid(row=1, column=0, padx=10, pady=5, sticky="E")
        self.vehicle_label = ttk.Label(self.main_frame, font=("Segoe UI", 10))
        self.vehicle_label.grid(row=1, column=1, padx=10, pady=5, sticky="W")

        ttk.Label(self.main_frame, text="Nr. Comandă:", font=("Segoe UI", 10)).grid(row=2, column=0, padx=10, pady=5, sticky="E")
        self.order_number_label = ttk.Label(self.main_frame, font=("Segoe UI", 10))
        self.order_number_label.grid(row=2, column=1, padx=10, pady=5, sticky="W")

        ttk.Label(self.main_frame, text="Data Comandă:", font=("Segoe UI", 10)).grid(row=3, column=0, padx=10, pady=5, sticky="E")
        self.order_date_label = ttk.Label(self.main_frame, font=("Segoe UI", 10))
        self.order_date_label.grid(row=3, column=1, padx=10, pady=5, sticky="W")

        ttk.Label(self.main_frame, text="Observații:", font=("Segoe UI", 10)).grid(row=4, column=0, padx=10, pady=5, sticky="NE")
        self.observations_text = tk.Text(self.main_frame, height=3, wrap=tk.WORD)
        self.observations_text.grid(row=4, column=1, columnspan=3, padx=10, pady=5, sticky="W")

        ttk.Label(self.main_frame, text="Status:", font=("Segoe UI", 10)).grid(row=5, column=0, padx=10, pady=5, sticky="E")
        self.status_var = tk.StringVar()
        self.status_dropdown = ttk.Combobox(self.main_frame, textvariable=self.status_var, values=[
            "Comandată și neplătită", "Comandată și plătită parțial", "Comandată și plătită",
            "Ridicată și neplătită", "Ridicată și plătită parțial", "Ridicată și plătită"
        ], state="readonly")
        self.status_dropdown.grid(row=5, column=1, padx=10, pady=5, sticky="W")

        self.products_frame = ttk.Frame(self.main_frame, padding="10")
        self.products_frame.grid(row=6, column=0, columnspan=4, pady=10, sticky="nsew")

        ttk.Label(self.main_frame, text="Suma Plătită:", font=("Segoe UI", 10)).grid(row=7, column=0, padx=10, pady=5, sticky="E")
        self.amount_paid_entry = ttk.Entry(self.main_frame, font=("Segoe UI", 10))
        self.amount_paid_entry.grid(row=7, column=1, padx=10, pady=5, sticky="W")

        ttk.Label(self.main_frame, text="Total de Plătit:", font=("Segoe UI", 10)).grid(row=8, column=0, padx=10, pady=5, sticky="E")
        self.total_amount_label = ttk.Label(self.main_frame, font=("Segoe UI", 10))
        self.total_amount_label.grid(row=8, column=1, padx=10, pady=5, sticky="W")

        self.save_button = ttk.Button(self.main_frame, text="Salvează", command=self.save_order)
        self.save_button.grid(row=9, column=0, pady=10)

        self.generate_pdf_button = ttk.Button(self.main_frame, text="Generează PDF", command=self.generate_pdf)
        self.generate_pdf_button.grid(row=9, column=1, pady=10)

    def fetch_order_details(self):
        try:
            response = requests.get(f'http://127.0.0.1:5000/orders/{self.order_number}')
            if response.status_code == 200:
                order = response.json()
                self.client_label.config(text=order['client_name'])
                self.vehicle_label.config(text=order['vehicle'])
                self.order_number_label.config(text=order['order_number'])
                self.order_date_label.config(text=order['order_date'])
                self.observations_text.insert("1.0", order['observations'])
                self.status_var.set(order['status'])
                self.amount_paid_entry.insert(0, order['amount_paid'])
                self.total_amount_label.config(text=order['total_amount'])

                self.display_products(order['products'])
            else:
                messagebox.showerror("Eroare", "Nu s-au putut încărca detaliile comenzii.")
        except Exception as e:
            messagebox.showerror("Eroare", f"A apărut o eroare: {e}")

    def display_products(self, products):
        columns = ["Nume produs", "Brand", "Cantitate", "Preț Unitar", "Preț Total", "Discount", "Preț cu Discount"]
        self.products_tree = ttk.Treeview(self.products_frame, columns=columns, show="headings", height=10)
        for col in columns:
            self.products_tree.heading(col, text=col)
            self.products_tree.column(col, width=100)
        self.products_tree.pack(fill=tk.BOTH, expand=True)

        for product in products:
            self.products_tree.insert('', 'end', values=product)

    def save_order(self):
        observations = self.observations_text.get("1.0", tk.END).strip()
        status = self.status_var.get()
        amount_paid = self.amount_paid_entry.get()

        if not all([observations, status, amount_paid]):
            messagebox.showerror("Eroare", "Toate câmpurile sunt obligatorii!")
            return

        try:
            response = requests.put(f'http://127.0.0.1:5000/orders/{self.order_number}', json={
                'observations': observations,
                'status': status,
                'amount_paid': amount_paid
            })
            if response.status_code == 200:
                messagebox.showinfo("Succes", "Detaliile comenzii au fost actualizate cu succes.")
                self.root.destroy()
            else:
                messagebox.showerror("Eroare", "Nu s-au putut actualiza detaliile comenzii.")
        except Exception as e:
            messagebox.showerror("Eroare", f"A apărut o eroare: {e}")

    def generate_pdf(self):
        # Implement the logic to generate the PDF
        # ...
        pass

def open_edit_order_window(root, order_number):
    window = tk.Toplevel(root)
    app = EditOrderApp(window, order_number)
    window.mainloop()