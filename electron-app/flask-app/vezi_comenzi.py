import tkinter as tk
from tkinter import ttk, messagebox, Toplevel
import requests
from edit_order import open_edit_order_window  # Import the function to open the edit order window

class ViewOrdersApp:
    def __init__(self, root, client_id=None):
        if not isinstance(root, Toplevel):
            raise ValueError("Expected a Toplevel window for 'root'.")
        self.root = root
        self.client_id = client_id  # Store client_id as an instance attribute
        self.root.title("Vezi Comenzi")
        self.root.geometry("1200x700")  # Standardized window size
        self.root.configure(bg="#d3d3d3")  # Match the application's background color

        # Enable the close (X) button
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

        # Center the window on the screen
        self.center_window()

        self.create_widgets()
        self.fetch_orders()  # Fetch orders for the selected client

    def on_close(self):
        """Handle the close (X) button action."""
        self.root.destroy()

    def center_window(self):
        """Centers the window both vertically and horizontally."""
        self.root.update_idletasks()
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        window_width = 1200
        window_height = 700
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        self.root.geometry(f"{window_width}x{window_height}+{x}+{y}")

    def create_widgets(self):
        self.style = ttk.Style()
        self.style.configure("TLabel", font=("Segoe UI", 11), background="#d3d3d3")
        self.style.configure("TButton", font=("Segoe UI", 11, "bold"))
        self.style.configure("TFrame", background="#d3d3d3")

        # Header section
        header_frame = ttk.Frame(self.root, padding="10")
        header_frame.pack(fill=tk.X)
        ttk.Label(header_frame, text="Comenzi Disponibile", font=("Segoe UI", 16, "bold"), anchor="center").pack()

        # Main content area
        self.main_frame = ttk.Frame(self.root, padding="10")
        self.main_frame.pack(fill=tk.BOTH, expand=True)

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

        self.orders_canvas.pack(side="left", fill="both", expand=True)
        self.orders_scrollbar.pack(side="right", fill="y")

    def fetch_orders(self):
        """Fetch orders for the given client_id and display them."""
        try:
            if not self.client_id:
                messagebox.showerror("Eroare", "ID-ul clientului nu este specificat.")
                return

            # Fetch orders for the client
            response = requests.get('http://127.0.0.1:5000/orders', params={'client_id': self.client_id})
            if response.status_code == 200:
                orders = response.json()
                if not orders:
                    messagebox.showinfo("Informație", "Nu există comenzi pentru acest client.")
                    return

                # Display the fetched orders
                self.display_orders(orders)
            else:
                messagebox.showerror("Eroare", f"Nu s-au putut încărca comenzile. Cod eroare: {response.status_code}")
        except Exception as e:
            messagebox.showerror("Eroare", f"A apărut o eroare: {e}")

    def display_orders(self, orders):
        """Display the fetched orders in the UI."""
        for widget in self.orders_frame.winfo_children():
            widget.destroy()

        # Ensure the parent frame has 3 equal columns
        self.orders_frame.grid_columnconfigure(0, weight=1)
        self.orders_frame.grid_columnconfigure(1, weight=1)
        self.orders_frame.grid_columnconfigure(2, weight=1)

        # Insert the updated orders list
        for index, order in enumerate(orders):
            self.create_order_card(self.orders_frame, order, index % 3, index // 3)

    def create_order_card(self, parent, order, column, row):
        """Create a card for an order."""
        card_frame = ttk.Frame(parent, relief="raised", borderwidth=2, padding="10", style="TFrame")
        card_frame.grid(row=row, column=column, padx=10, pady=10, sticky="nsew")

        ttk.Label(card_frame, text=f"📦 Comandă {order['order_number']}", font=("Segoe UI", 12, "bold")).pack(anchor="w")
        ttk.Label(card_frame, text=f"📅 Data: {order.get('date', 'N/A')}", font=("Segoe UI", 10)).pack(anchor="w")
        ttk.Label(card_frame, text=f"📌 Status: {order['status']}", font=("Segoe UI", 10)).pack(anchor="w")
        ttk.Label(card_frame, text=f"🛒 Produse: {order.get('nr_produse', 'N/A')}", font=("Segoe UI", 10)).pack(anchor="w")

        button_frame = ttk.Frame(card_frame, style="TFrame")
        button_frame.pack(anchor="e", pady=5)

        ttk.Button(button_frame, text="Vizualizează", command=lambda: self.view_order(order)).pack(side="left", padx=5)
        ttk.Button(button_frame, text="Editează", command=lambda: self.edit_order(order)).pack(side="left", padx=5)

    def view_order(self, order):
        """View the details of the selected order."""
        messagebox.showinfo("Vizualizare Comandă", f"Detalii pentru comanda {order['order_number']}:\n{order}")

    def edit_order(self, order):
        """Open the edit order window for the selected order."""
        open_edit_order_window(self.root, order['order_number'])

def open_view_orders_window(root, client_id=None):
    """Open the 'Vezi Comenzi' window for a specific client."""
    if not client_id:
        messagebox.showerror("Eroare", "ID-ul clientului nu este specificat.")
        return

    try:
        # Create the Toplevel window
        window = tk.Toplevel(root)
        window.resizable(True, False)  # Allow vertical resizing only
        app = ViewOrdersApp(window, client_id=client_id)  # Pass client_id to ViewOrdersApp
        window.mainloop()
    except Exception as e:
        messagebox.showerror("Eroare", f"A apărut o eroare: {e}")

def open_view_orders_window_with_orders(root, orders):
    """Open the 'Vezi Comenzi' window with a predefined list of orders."""
    try:
        # Create the Toplevel window
        window = Toplevel(root)
        window.title("Vezi Comenzi")
        window.geometry("1200x700")
        window.configure(bg="#d3d3d3")
        window.resizable(True, False)  # Allow vertical resizing only

        # Create the ViewOrdersApp instance and pass the orders
        app = ViewOrdersApp(window, orders=orders)
        window.mainloop()
    except Exception as e:
        messagebox.showerror("Eroare", f"A apărut o eroare: {e}")