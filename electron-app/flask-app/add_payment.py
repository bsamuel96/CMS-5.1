import tkinter as tk
from tkinter import ttk
from ttkwidgets.autocomplete import AutocompleteCombobox
from tkcalendar import DateEntry
import requests
from tkinter import messagebox

class AddPaymentWindow:
    def __init__(self, parent, client_id=None, client_name=None):
        self.parent = parent
        self.window = tk.Toplevel(parent)
        self.window.title("Adaugă Plată")
        self.window.geometry("1200x700")
        self.window.configure(bg="#d3d3d3")
        self.window.resizable(True, False)
        self.window.protocol("WM_DELETE_WINDOW", self.window.destroy)

        self.client_id = client_id
        self.client_name_var = tk.StringVar()
        if client_name:
            self.client_name_var.set(client_name)

        self.center_window()
        self.style = ttk.Style()
        self.style.configure("TLabel", font=("Segoe UI", 11), background="#d3d3d3")
        self.style.configure("TButton", font=("Segoe UI", 11, "bold"))
        self.style.configure("TFrame", background="#d3d3d3")

        self.create_widgets()

        if self.client_id:
            self.load_orders_for_client(self.client_id)

    def center_window(self):
        self.window.update_idletasks()
        screen_width = self.window.winfo_screenwidth()
        screen_height = self.window.winfo_screenheight()
        window_width = 1200
        window_height = 700
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        self.window.geometry(f"{window_width}x{window_height}+{x}+{y}")

    def create_widgets(self):
        header_frame = ttk.Frame(self.window, padding="10")
        header_frame.pack(fill=tk.X)
        ttk.Label(header_frame, text="Adaugă Plată", font=("Segoe UI", 16, "bold"), anchor="center").pack()

        self.main_frame = ttk.Frame(self.window, padding="10")
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(self.main_frame, text="Selectează Client:", font=("Segoe UI", 12)).grid(row=0, column=0, sticky="w", pady=10)
        
        client_name_entry = ttk.Entry(self.main_frame, textvariable=self.client_name_var, font=("Segoe UI", 12), state="readonly", cursor="hand2")
        client_name_entry.grid(row=0, column=1, sticky="ew", pady=10, padx=10)
        client_name_entry.bind("<Button-1>", lambda e: self.open_client_search_popup())
        search_client_button = ttk.Button(self.main_frame, text="Caută Client", command=self.open_client_search_popup)
        search_client_button.grid(row=0, column=2, padx=10)

        ttk.Label(self.main_frame, text="Comenzile Clientului:", font=("Segoe UI", 12, "bold")).grid(row=1, column=0, columnspan=2, sticky="w", pady=10)

        self.orders_canvas = tk.Canvas(self.main_frame, bg="#d3d3d3", highlightthickness=0)
        self.orders_scrollbar = ttk.Scrollbar(self.main_frame, orient="vertical", command=self.orders_canvas.yview)
        self.orders_frame = ttk.Frame(self.orders_canvas, padding="10")

        self.orders_frame.bind(
            "<Configure>",
            lambda e: self.orders_canvas.configure(
                scrollregion=self.orders_canvas.bbox("all")
            )
        )

        self.orders_canvas.create_window((0, 0), window=self.orders_frame, anchor="nw")
        self.orders_canvas.configure(yscrollcommand=self.orders_scrollbar.set)

        self.orders_canvas.grid(row=2, column=0, columnspan=2, sticky="nsew", pady=10)
        self.orders_scrollbar.grid(row=2, column=2, sticky="ns", pady=10)

        button_frame = ttk.Frame(self.main_frame)
        button_frame.grid(row=4, column=0, columnspan=2, pady=20)

        save_button = ttk.Button(button_frame, text="Salvează", width=15, command=self.save_payment)
        save_button.pack(side=tk.LEFT, padx=10)

        close_button = ttk.Button(button_frame, text="Închide", width=15, command=self.window.destroy)
        close_button.pack(side=tk.LEFT, padx=10)

        self.main_frame.columnconfigure(1, weight=1)
        self.main_frame.rowconfigure(2, weight=1)

        # Fields below the canvas
        fields_frame = ttk.Frame(self.main_frame, padding="10")
        fields_frame.grid(row=3, column=0, columnspan=2, sticky="ew", pady=10)

        ttk.Label(fields_frame, text="Număr Comandă:", font=("Segoe UI", 12)).grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.order_number_var = tk.StringVar()
        order_number_entry = ttk.Entry(fields_frame, textvariable=self.order_number_var, font=("Segoe UI", 12), state="readonly")
        order_number_entry.grid(row=0, column=1, sticky="ew", padx=5, pady=5)

        ttk.Label(fields_frame, text="Data Plății:", font=("Segoe UI", 12)).grid(row=1, column=0, sticky="w", padx=5, pady=5)
        self.payment_date_var = tk.StringVar()
        date_entry = DateEntry(fields_frame, textvariable=self.payment_date_var, font=("Segoe UI", 12), date_pattern='yyyy-MM-dd')
        date_entry.grid(row=1, column=1, sticky="ew", padx=5, pady=5)

        ttk.Label(fields_frame, text="Sumă de Plată:", font=("Segoe UI", 12)).grid(row=2, column=0, sticky="w", padx=5, pady=5)
        self.payment_amount_var = tk.StringVar()
        payment_amount_entry = ttk.Entry(fields_frame, textvariable=self.payment_amount_var, font=("Segoe UI", 12))
        payment_amount_entry.grid(row=2, column=1, sticky="ew", padx=5, pady=5)

        ttk.Label(fields_frame, text="Observații:", font=("Segoe UI", 12)).grid(row=3, column=0, sticky="w", padx=5, pady=5)
        self.observations_var = tk.StringVar()
        observations_entry = ttk.Entry(fields_frame, textvariable=self.observations_var, font=("Segoe UI", 12))
        observations_entry.grid(row=3, column=1, sticky="ew", padx=5, pady=5)

        fields_frame.columnconfigure(1, weight=1)

    def open_client_search_popup(self):
        from client_search import open_client_search_window

        def on_client_selected(client_id, client_name):
            self.client_id = client_id  # Save for later use
            self.client_name_var.set(client_name)
            self.load_orders_for_client(client_id)

        open_client_search_window(self.window, on_client_selected)

    def load_orders_for_client(self, client_id):
        """Fetch and display only orders with balance > 0."""
        try:
            response = requests.get(f'http://127.0.0.1:5000/orders?client_id={client_id}')
            if response.status_code == 200:
                all_orders = response.json()
                self.orders = [o for o in all_orders if o.get('balance', 0) > 0]
                for widget in self.orders_frame.winfo_children():
                    widget.destroy()
                for idx, order in enumerate(self.orders):
                    self.create_order_card(order, idx)
            else:
                messagebox.showerror("Adaugă Plată – Eroare", "Nu s-au putut încărca comenzile clientului.")
        except Exception as e:
            messagebox.showerror("Adaugă Plată – Eroare", f"A apărut o eroare: {e}")

    def create_order_card(self, order, index):
        """Display a card for orders with remaining balance."""
        columns = 4
        row = index // columns
        column = index % columns

        card = ttk.Frame(self.orders_frame, relief="raised", borderwidth=2, padding="10", style="TFrame")
        card.grid(row=row, column=column, padx=10, pady=10, sticky="nsew")

        remaining = order.get('balance', 0.0)

        ttk.Label(card, text=f"📦 Comandă {order.get('order_number', order.get('id'))}", font=("Segoe UI", 12, "bold")).pack(anchor="w")
        ttk.Label(card, text=f"📅 Data: {order.get('date')}", font=("Segoe UI", 10)).pack(anchor="w")
        ttk.Label(card, text=f"📌 Rest de Plată: {remaining:.2f} RON", font=("Segoe UI", 10, "italic"), foreground="red").pack(anchor="w")

        select_button = ttk.Button(card, text="Selectează", command=lambda: self.select_order(order))
        select_button.pack(pady=5)

        self.orders_frame.grid_columnconfigure(column, weight=1)

    def select_order(self, order):
        """Populate fields below the canvas when an order is selected."""
        valoare = order.get('order_number') or str(order.get('id'))  # Fallback to 'id' if 'order_number' is missing
        self.order_number_var.set(valoare)
        self.payment_amount_var.set("")
        self.observations_var.set("")

    def save_payment(self):
        if not hasattr(self, 'client_id') or not self.client_id:
            messagebox.showerror("Adaugă Plată", "Selectați un client.")
            return

        order_number = self.order_number_var.get()
        if not order_number:
            messagebox.showerror("Adaugă Plată", "Selectați o comandă.")
            return

        try:
            amount = float(self.payment_amount_var.get())
        except ValueError:
            messagebox.showerror("Adaugă Plată – Eroare", "Introduceți o sumă validă.")
            return

        observations = self.observations_var.get()

        selected_order = next((o for o in self.orders if (o.get('order_number') or str(o.get('id'))) == order_number), None)
        if not selected_order:
            messagebox.showerror("Adaugă Plată", "Comanda selectată nu a fost găsită.")
            return

        payload = {
            "client_id": self.client_id,
            "order_id": selected_order['id'],
            "amount": amount,
            "date": self.payment_date_var.get(),  # Include selected payment date
            "recorded_by": "admin",  # Or the logged-in user
            "observations": observations
        }

        try:
            response = requests.post("http://127.0.0.1:5000/add_payment", json=payload)
            if response.status_code == 200:
                messagebox.showinfo("Succes", "Plata a fost salvată.")

                # Refresh the main Dashboard's orders and balances
                dashboard = self.parent.app
                client_name = self.client_name_var.get()
                dashboard.refresh_client_orders(client_name)
                dashboard.refresh_client_balances(client_name)

                # Close this payment window
                self.window.destroy()
            else:
                messagebox.showerror("Adaugă Plată", f"Nu s-a putut salva plata: {response.text}")
        except Exception as e:
            messagebox.showerror("Adaugă Plată", f"Eroare la trimiterea plății: {e}")
