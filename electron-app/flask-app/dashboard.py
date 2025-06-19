import tkinter as tk
from tkinter import ttk, messagebox, Menu, simpledialog, Toplevel, StringVar, Label, Button
import json
import os
import requests  # Import the requests module
from new_customer import open_add_client_window  # Import the function to open the client window
from new_car import open_add_vehicle_window  # Import the function to open the vehicle window
from new_offer import open_add_offer_window  # Import the function to open the offer window
from PIL import Image, ImageTk  # Ensure you have Pillow installed
from settings import open_settings_window  # Add this import statement
from config import SUPABASE_URL, SUPABASE_KEY  # Import Supabase configuration
from edit_offer import open_edit_offer_window, submit_offer  # Import the function to open the edit offer window and submit offer
import tksheet  # Ensure you have tksheet installed
from pdf import PDFGenerator  # Import the PDFGenerator class
from datorii import open_debts_report_window  # Import the function to open the debts report window
from top_clienti import open_top_clients_window  # Import the function to open the top clients window
from vanzari import open_sales_report_window  # Ensure this import is present
from edit_client import open_edit_client_window  # Import the function to open the edit client window
from vezi_oferte import open_view_offers_window  # Import the function to open the view offers window
from new_order import open_new_order_window  # Import the function to open the new order window
from edit_order import open_edit_order_window  # Import the function to open the edit order window
from vezi_comenzi import open_view_orders_window  # Ensure this import statement is present
from client_search import search_client_orders, search_client_offers  # Ensure this import statement is present
from client_search import open_client_search_window  # Ensure this import statement is present
from search_function import open_search_window, search_database, display_search_results

from supabase import create_client, Client  # Import Supabase client
import subprocess  # Add this import statement
from window_payments import open_payments_window  # Import the payments window function
from add_payment import AddPaymentWindow
from talon import open_talon_window  # Import the talon popup function
from return_window import ReturnWindow as ReturnProductsWindow  # Import the ReturnWindow class
import logging  # Add logging module

CONFIG_FILE = "config.json"

# Initialize Supabase client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

class DashboardApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Sistem de Gestionare a Comenzilor")
        self.root.geometry("1200x800")
        self.root.configure(bg="#d3d3d3")
        self.root.state('zoomed')  # Start the window maximized

        # Assign the DashboardApp instance to the root window's app attribute
        self.root.app = self

        self.style = ttk.Style()
        self.style.configure("TLabelFrame", background="#f0f0f0")  # Ensure TLabelFrame style is defined
        self.style.configure("Hover.TLabelFrame", background="#e0e0e0")  # Ensure Hover.TLabelFrame style is defined
        self.load_config()
        self.apply_theme()

        self.style.configure("TLabel", font=("Segoe UI", 10))
        self.style.configure("TButton", font=("Segoe UI", 10))
        self.style.configure("TEntry", font=("Segoe UI", 10))
        self.style.configure("Treeview.Heading", font=("Segoe UI", 10, "bold"))

        self.create_widgets()
        self.update_canvas_colors()  # Move this line here
        self.refresh_client_list()  # Fetch and display client data when the app is initialized

        # Setup undo stack and activity log
        self.undo_stack = []
        logging.basicConfig(
            filename=os.path.join(os.path.dirname(__file__), 'activity_log.txt'),
            level=logging.INFO,
            format='%(asctime)s - %(message)s'
        )

    def load_config(self):
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, "r") as config_file:
                self.config = json.load(config_file)
        else:
            self.config = {
                "supabase_url": SUPABASE_URL,
                "supabase_key": SUPABASE_KEY,
                "theme": "winnative"  # Ensure a default theme is set
            }

    def save_config(self):
        with open(CONFIG_FILE, "w") as config_file:
            json.dump(self.config, config_file)

    def apply_theme(self):
        theme = self.config.get("theme", "winnative")
        self.style.theme_use(theme)
        self.style.configure("TLabelFrame", background="#f0f0f0", relief="groove")
        self.style.configure("Hover.TLabelFrame", background="#e8e8e8", relief="ridge")

    def update_canvas_colors(self):
        """ Sets the background of Oferte and Comenzi sections to match button color. """
        button_color = self.style.lookup("TButton", "background")  # Get button color
        self.offers_canvas.config(bg=button_color)
        self.orders_canvas.config(bg=button_color)

    def toggle_dark_mode(self):
        self.config["dark_mode"] = not self.config.get("dark_mode")
        self.apply_theme()
        self.save_config()

    def create_widgets(self):
        self.style.configure("TLabel", font=("Segoe UI", 11), padding=5)
        self.style.configure("TButton", font=("Segoe UI", 11, "bold"), padding=5)
        self.style.configure("Treeview.Heading", font=("Segoe UI", 12, "bold"), padding=10)

        # Create the menu bar
        menubar = tk.Menu(self.root)

        # Create the "Nou" menu
        nou_menu = tk.Menu(menubar, tearoff=0)
        nou_menu.add_command(label="Adaugă Client", command=self.add_client)  # Correct method name
        nou_menu.add_command(label="Adaugă Vehicul", command=self.add_vehicle)  # Ensure the function works
        nou_menu.add_command(label="Ofertă Nouă", command=self.add_offer)  # Add new offer option
        menubar.add_cascade(label="Nou", menu=nou_menu)

        # Create the "Vezi" menu
        vezi_menu = tk.Menu(menubar, tearoff=0)
        vezi_menu.add_command(label="Vezi Oferte", command=self.view_offers)  # Update this line
        vezi_menu.add_command(label="Vezi Comenzi", command=self.view_orders)  # Update this line
        menubar.add_cascade(label="Vezi", menu=vezi_menu)

        # Create the "Rapoarte" menu
        rapoarte_menu = tk.Menu(menubar, tearoff=0)
        rapoarte_menu.add_command(label="Vânzări", command=lambda: self.open_sales_report())
        rapoarte_menu.add_command(label="Top Clienți", command=lambda: open_top_clients_window(self.root))  # Updated to call the function
        rapoarte_menu.add_command(label="Datorii", command=lambda: open_debts_report_window(self.root))
        menubar.add_cascade(label="Rapoarte", menu=rapoarte_menu)

        # Replace the "Exporta" menu with "Plăți"
        payments_menu = tk.Menu(menubar, tearoff=0)
        payments_menu.add_command(label="Plăți", command=lambda: open_payments_window(self.root))
        payments_menu.add_command(label="Plată Nouă", command=lambda: AddPaymentWindow(self.root))  # New menu item
        menubar.add_cascade(label="Plăți", menu=payments_menu)

        # Add "Return" menu
        return_menu = tk.Menu(menubar, tearoff=0)
        return_menu.add_command(label="Return", command=lambda: ReturnProductsWindow(self.root))
        menubar.add_cascade(label="Return", menu=return_menu)


        # Create the "User Profile" menu
        user_menu = tk.Menu(menubar, tearoff=0)
        user_menu.add_command(label="Setări", command=self.settings)
        user_menu.add_command(label="Logout", command=self.logout)
        menubar.add_cascade(label="👤 Utilizator", menu=user_menu)

        # Add "Undo" button to the menu bar
        menubar.add_command(label="↺ Undo", command=self.undo_last)

        # Configure the menu bar
        self.root.config(menu=menubar)

        # Create the main content area with a two-pane layout
        main_pane = tk.PanedWindow(self.root, orient="horizontal", sashwidth=2, bg="#d3d3d3")
        main_pane.pack(fill="both", expand=True)

        # Create the left panel for client management
        left_panel = ttk.Frame(main_pane, padding="10")
        main_pane.add(left_panel, width=500)

        left_panel_label = ttk.Label(left_panel, text="Gestionare Clienți", font=("Segoe UI", 10, "bold"), anchor="w")
        left_panel_label.pack(pady=(0, 10), anchor="w")

        self.client_list = ttk.Treeview(left_panel, columns=("Nume", "Telefon", "Localitate + Județ"), show="headings", height=20)
        self.client_list.heading("Nume", text="🧑‍💼 Nume")
        self.client_list.heading("Telefon", text="📞 Telefon")
        self.client_list.heading("Localitate + Județ", text="📍 Localitate + Județ")  # Updated header
        self.client_list.column("Nume", width=100, anchor="center")  # Adjusted width
        self.client_list.column("Telefon", width=100, anchor="center")  # Adjusted width
        self.client_list.column("Localitate + Județ", width=200, anchor="w")  # Adjusted width
        self.client_list.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.client_list.bind("<<TreeviewSelect>>", self.display_client_details)
        self.client_list.bind("<Button-3>", self.on_right_click)
        self.client_list.bind("<Double-1>", self.on_double_click)  # Add this line

        # Create the right panel for client details, orders, and offers
        right_panel = ttk.Frame(main_pane, padding="10")
        main_pane.add(right_panel)

        # Create the search bar
        search_frame = ttk.Frame(right_panel, padding=10)
        search_frame.pack(side="top", fill="x")

        self.search_entry = ttk.Entry(search_frame, width=50, font=("Segoe UI", 12))
        self.search_entry.pack(side="left", fill="x", expand=True, padx=10, ipady=6)
        self.search_entry.bind("<Return>", self.on_search)  # Bind Enter key to search

        search_button = ttk.Button(search_frame, text="🔍 Caută", width=10, command=self.on_search)
        search_button.pack(side="right", padx=10)

        # Filters below the search bar
        filters_frame = ttk.Frame(right_panel, padding=10)
        filters_frame.pack(side="top", fill="x", pady=5)

        select_all_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(filters_frame, text="Toate", variable=select_all_var, command=lambda: self.toggle_all_filters(select_all_var, self.categories)).pack(side="left", padx=5)

        self.categories = {
            "Clienți": tk.BooleanVar(value=True),
            "Vehicule": tk.BooleanVar(value=True),
            "Oferte": tk.BooleanVar(value=True),
            "Comenzi": tk.BooleanVar(value=True),
            "Produse din comanda": tk.BooleanVar(value=True),
            "Produse din oferta": tk.BooleanVar(value=True)
        }
        for category, var in self.categories.items():
            ttk.Checkbutton(filters_frame, text=category, variable=var).pack(side="left", padx=5)

        # Create the client details section
        client_details_frame = ttk.Frame(right_panel, padding=5)
        client_details_frame.pack(fill="x", padx=5, pady=5)

        client_details_label = ttk.Label(client_details_frame, text="Detalii Client", font=("Segoe UI", 10, "bold"), anchor="w")
        client_details_label.grid(row=0, column=0, pady=(0, 1), sticky="w")

        button_frame = ttk.Frame(client_details_frame)
        button_frame.grid(row=0, column=2, pady=(0, 1), sticky="e")

        edit_client_button = ttk.Button(button_frame, text="Editează detalii client", command=self.edit_selected_client)
        edit_client_button.pack(side="right", padx=(0, 1))

        view_dashboard_button = ttk.Button(button_frame, text="Vezi Dashboard", command=self.open_selected_client_dashboard, style="TButton")
        view_dashboard_button.pack(side="right", padx=(0, 10))  # Added 10px gap

        self.client_name_label = ttk.Label(client_details_frame, text="Nume: ", font=("Segoe UI", 10, "bold"))
        self.client_name_label.grid(row=1, column=0, sticky="w", padx=(0, 1))

        self.client_name_value = ttk.Label(client_details_frame, text="", font=("Segoe UI", 10))
        self.client_name_value.grid(row=2, column=0, sticky="w", padx=(0, 1))

        self.client_phone_label = ttk.Label(client_details_frame, text="Telefon: ", font=("Segoe UI", 10, "bold"))
        self.client_phone_label.grid(row=1, column=1, sticky="w", padx=(0, 1))

        self.client_phone_value = ttk.Label(client_details_frame, text="", font=("Segoe UI", 10))
        self.client_phone_value.grid(row=2, column=1, sticky="w", padx=(0, 1))

        self.client_address_label = ttk.Label(client_details_frame, text="Adresă: ", font=("Segoe UI", 10, "bold"))
        self.client_address_label.grid(row=1, column=2, sticky="w", padx=(0, 1))

        self.client_address_value = ttk.Label(client_details_frame, text="", font=("Segoe UI", 10))
        self.client_address_value.grid(row=2, column=2, sticky="w", padx=(0, 1))

        client_details_frame.grid_columnconfigure(0, weight=1)
        client_details_frame.grid_columnconfigure(1, weight=1)
        client_details_frame.grid_columnconfigure(2, weight=1)

        # Create the offers section
        offers_frame = ttk.Frame(right_panel, padding="10")
        offers_frame.pack(fill=tk.BOTH, expand=True)
        offers_frame.grid_columnconfigure(0, weight=1)  # Allow column to expand
        offers_frame.grid_rowconfigure(1, weight=1)  # Allow row to expand

        offers_label = ttk.Label(offers_frame, text="Oferte", font=("Segoe UI", 10, "bold"), anchor="w")
        offers_label.grid(row=0, column=0, pady=(5, 5), sticky="w")  # More spacing
        view_offers_button = ttk.Button(offers_frame, text="Vezi oferte", command=self.view_offers_from_section)
        view_offers_button.grid(row=0, column=1, pady=(5, 5), sticky="e")  # More spacing

        # Create a canvas inside offers_frame
        self.offers_canvas = tk.Canvas(offers_frame, highlightthickness=0, bg=self.style.lookup("TLabelFrame", "background"))
        self.offers_canvas.grid(row=1, column=0, columnspan=2, sticky="nsew")  # Stays in row=1

        # Create a frame inside the canvas
        self.offers_canvas_frame = ttk.Frame(self.offers_canvas)
        self.offers_canvas.create_window((0, 0), window=self.offers_canvas_frame, anchor="nw")

        # Scrollbars for the offers section
        offers_scrollbar_x = ttk.Scrollbar(offers_frame, orient="horizontal", command=self.offers_canvas.xview)
        offers_scrollbar_x.grid(row=2, column=0, columnspan=2, sticky="ew")
        self.offers_canvas.configure(xscrollcommand=offers_scrollbar_x.set)

        offers_scrollbar_y = ttk.Scrollbar(offers_frame, orient="vertical", command=self.offers_canvas.yview)
        offers_scrollbar_y.grid(row=1, column=2, sticky="ns")
        self.offers_canvas.configure(yscrollcommand=offers_scrollbar_y.set)

        # Bind resizing event
        offers_frame.bind("<Configure>", self.resize_offer_container)
        self.offers_canvas_frame.bind("<Configure>", lambda event: self.offers_canvas.configure(scrollregion=self.offers_canvas.bbox("all")))

        # Allow the offers canvas frame to expand
        self.offers_canvas_frame.grid_columnconfigure(0, weight=1)

        # Initialize the card row counter
        self.card_row = 0

        # Create the bottom panel for vehicles and orders
        bottom_pane = tk.PanedWindow(self.root, orient="horizontal", sashwidth=2, bg="#d3d3d3")
        bottom_pane.pack(fill="both", expand=True)

        # Left bottom panel for client's vehicles
        left_bottom_frame = ttk.Frame(bottom_pane, padding="10")
        bottom_pane.add(left_bottom_frame, width=600)

        left_bottom_label = ttk.Label(left_bottom_frame, text="Vehiculele Clientului", font=("Segoe UI", 10, "bold"), anchor="w")
        left_bottom_label.pack(pady=(0, 10), anchor="w")

        self.client_vehicles_list = ttk.Treeview(left_bottom_frame, columns=("Marcă", "Model", "An", "VIN", "Înmatriculare", "Talon"), show="headings", height=5)
        self.client_vehicles_list.heading("Marcă", text="Marcă")
        self.client_vehicles_list.heading("Model", text="Model")
        self.client_vehicles_list.heading("An", text="An")
        self.client_vehicles_list.heading("VIN", text="VIN")
        self.client_vehicles_list.heading("Înmatriculare", text="Înmatriculare")
        self.client_vehicles_list.heading("Talon", text="Talon")
        self.client_vehicles_list.column("Marcă", width=80, stretch=True)
        self.client_vehicles_list.column("Model", width=80, stretch=True)
        self.client_vehicles_list.column("An", width=50, stretch=True)
        self.client_vehicles_list.column("VIN", width=120, stretch=True)
        self.client_vehicles_list.column("Înmatriculare", width=120, stretch=True)
        self.client_vehicles_list.column("Talon", width=80, stretch=True)
        self.client_vehicles_list.pack(fill=tk.BOTH, expand=True)

        self.client_vehicles_list.bind("<Button-3>", self.on_vehicle_right_click)  # Ensure right-click is bound
        self.client_vehicles_list.bind("<Double-1>", self.open_vehicle_talon)  # Ensure binding for double-click

        # Right bottom panel for orders
        right_bottom_frame = ttk.Frame(bottom_pane, padding="10")
        bottom_pane.add(right_bottom_frame, width=600)
        right_bottom_frame.grid_columnconfigure(1, weight=1)  # Allow column to expand
        right_bottom_frame.grid_rowconfigure(1, weight=1)  # Allow row to expand

        orders_label = ttk.Label(right_bottom_frame, text="Comenzi", font=("Segoe UI", 10, "bold"), anchor="w")
        orders_label.grid(row=0, column=0, pady=(0, 10), sticky="w")

        payment_button = ttk.Button(
            right_bottom_frame,
            text="Plată",
            command=self.open_payment_for_selected_client
        )
        payment_button.grid(row=0, column=1, padx=(10, 10), pady=(0, 10), sticky="e")  # Added 10px gap on the right

        view_orders_button = ttk.Button(right_bottom_frame, text="Vezi Comenzi", command=self.view_orders_from_section)
        view_orders_button.grid(row=0, column=2, pady=(0, 10), sticky="e")

        self.orders_canvas = tk.Canvas(right_bottom_frame, highlightthickness=0, height=1, bg=self.style.lookup("TLabelFrame", "background"))  # Start with minimal height
        self.orders_canvas.grid(row=1, column=0, columnspan=3, sticky="nsew")  # Extended to span all columns

        # Create a frame inside the canvas
        self.orders_canvas_frame = ttk.Frame(self.orders_canvas)
        self.orders_canvas.create_window((0, 0), window=self.orders_canvas_frame, anchor="center")

        # Scrollbar for horizontal scrolling
        orders_scrollbar = ttk.Scrollbar(right_bottom_frame, orient="horizontal", command=self.orders_canvas.xview)
        orders_scrollbar.grid(row=2, column=0, columnspan=3, sticky="ew")  # Extended to span all columns
        self.orders_canvas.configure(xscrollcommand=orders_scrollbar.set)

        # Bind resizing event
        right_bottom_frame.bind("<Configure>", self.resize_order_container)
        self.orders_canvas_frame.bind("<Configure>", lambda event: self.orders_canvas.configure(scrollregion=self.orders_canvas.bbox("all")))

        # Allow the orders canvas frame to expand
        self.orders_canvas_frame.grid_columnconfigure(0, weight=1)

        # Create the right-click context menu for the client list
        self.client_list.bind("<Button-3>", self.on_right_click)

        # Create the right-click context menu for the vehicle list
        self.client_vehicles_list.bind("<Button-3>", self.on_right_click)

        self.refresh_client_balances()

        # Create the total amounts section
        total_frame = ttk.Frame(right_panel, padding=5)
        total_frame.pack(fill="x", padx=5, pady=5)

        total_label = ttk.Label(total_frame, text="Totaluri", font=("Segoe UI", 10, "bold"), anchor="w")
        total_label.grid(row=0, column=0, columnspan=4, sticky="w", pady=(0, 1))

        # Coloana 1: Total Cheltuit
        self.total_spent_label = ttk.Label(total_frame, text="Total Cheltuit:", font=("Segoe UI", 10, "bold"))
        self.total_spent_label.grid(row=1, column=0, sticky="w", padx=5)
        self.total_spent_value = ttk.Label(total_frame, text="", font=("Segoe UI", 10))
        self.total_spent_value.grid(row=2, column=0, sticky="w", padx=5)

        # Coloana 2: De Plătit (roșu)
        self.de_platit_label = ttk.Label(total_frame, text="De Plătit:", font=("Segoe UI", 10, "bold"))
        self.de_platit_label.grid(row=1, column=1, sticky="w", padx=5)
        self.de_platit_value = ttk.Label(total_frame, text="", font=("Segoe UI", 10), foreground="red")
        self.de_platit_value.grid(row=2, column=1, sticky="w", padx=5)

        # Coloana 3: Sold (verde)
        self.sold_label = ttk.Label(total_frame, text="Sold:", font=("Segoe UI", 10, "bold"))
        self.sold_label.grid(row=1, column=2, sticky="w", padx=5)
        self.sold_value = ttk.Label(total_frame, text="", font=("Segoe UI", 10), foreground="green")
        self.sold_value.grid(row=2, column=2, sticky="w", padx=5)

        # Coloana 4: Total Comenzi
        self.total_orders_label = ttk.Label(total_frame, text="Total Comenzi:", font=("Segoe UI", 10, "bold"))
        self.total_orders_label.grid(row=1, column=3, sticky="w", padx=5)
        self.total_orders_value = ttk.Label(total_frame, text="", font=("Segoe UI", 10))
        self.total_orders_value.grid(row=2, column=3, sticky="w", padx=5)

        # Ajustăm greutatea coloanelor
        total_frame.grid_columnconfigure(0, weight=1)
        total_frame.grid_columnconfigure(1, weight=1)
        total_frame.grid_columnconfigure(2, weight=1)
        total_frame.grid_columnconfigure(3, weight=1)

        # Call these functions to update colors and resize containers
        self.update_canvas_colors()
        self.resize_offer_container()
        self.resize_order_container()

        # Add Return button to the sidebar menu
        btn = tk.Button(left_panel, text="Return", command=lambda: ReturnProductsWindow(self.root))
        btn.pack(fill="x", pady=2)

    def toggle_all_filters(self, select_all_var, categories):
        """Toggle all category filters based on the 'Toate' checkbox."""
        for var in categories.values():
            var.set(select_all_var.get())

    def on_right_click(self, event):
        item = event.widget.identify_row(event.y)
        if item:
            event.widget.selection_set(item)
        selected_item = event.widget.selection()
        if selected_item:
            context_menu = Menu(self.root, tearoff=0)
            if event.widget == self.client_list:
                client = self.client_list.item(selected_item, "values")
                client_id = self.get_id_by_field('clients', 'name', client[0])
                if client_id:
                    context_menu.add_command(label="📝 Editează Client", command=lambda: open_edit_client_window(self.root, client_id))
                    context_menu.add_command(label="🚗 Adaugă Vehicul", command=lambda: open_add_vehicle_window(self.root, client_id, client[0]))
                    context_menu.add_command(label="📜 Vezi Oferte", command=lambda: open_view_offers_window(self.root, client_id=client_id))
                    context_menu.add_command(label="🛒 Vezi Comenzi", command=lambda: open_view_orders_window(self.root, client_id=client_id))
                    context_menu.add_command(label="📂 Deschide Dashboard", command=lambda: self.open_customer_dashboard(client_id))
                    context_menu.add_command(label="🛍️ Ofertă Nouă", command=self.open_new_offer_with_customer)
                    context_menu.add_separator()
                    context_menu.add_command(label="🗑️ Șterge Client", command=lambda: self.delete_client(client_id, client[0]))
            elif event.widget == self.client_vehicles_list:
                vehicle = self.client_vehicles_list.item(selected_item, "values")
                vehicle_id = self.client_vehicles_list.item(selected_item, "tags")[0]
                if vehicle_id:
                    context_menu.add_command(label="🛠️ Modifică Detalii Vehicul", command=lambda: subprocess.Popen(["python", "edit_vehicle.py", vehicle_id]))
                    context_menu.add_command(label="🗑️ Șterge Vehicul", command=lambda: self.delete_vehicle(vehicle_id, vehicle[3]))
                    context_menu.add_command(label="📜 Vezi Oferte", command=lambda: self.refresh_client_offers(self.client_list.item(self.client_list.selection(), "values")[0], vehicle_id))
            elif event.widget == self.orders_list:
                order = self.orders_list.item(selected_item, "values")
                order_number = order[0]
                if order_number:
                    context_menu.add_command(label="✏️ Editează Comandă", command=lambda: open_edit_order_window(self.root, order_number))
            context_menu.post(event.x_root, event.y_root)

    def open_customer_dashboard(self, client_id):
        script_path = os.path.join(os.path.dirname(__file__), "customer_dashboard.py")

        if not os.path.exists(script_path):
            print(f"Error: {script_path} not found.")  # Fixed f-string
            messagebox.showerror("Eroare", "Fișierul customer_dashboard.py nu a fost găsit!")
            return

        print(f"Launching customer dashboard for client {client_id}")  # Debugging
        subprocess.Popen(["python", script_path, str(client_id)], shell=True)

    def generate_pdf(self, offer_number):
        try:
            response = requests.get(f'http://127.0.0.1:5000/offers/{offer_number}')
            if (response.status_code == 200):
                offer_details = response.json()
                pdf_generator = PDFGenerator(offer_details)
                pdf_file = pdf_generator.generate_pdf()
                messagebox.showinfo("Succes", f"PDF generat cu succes: {pdf_file}")
            else:
                messagebox.showerror("Eroare", "Nu s-au putut încărca detaliile ofertei.")
        except Exception as e:
            messagebox.showerror("Eroare", f"A apărut o eroare: {e}")

    def get_client_id_by_name(self, client_name):
        """Retrieve the client_id for a given client name."""
        try:
            response = requests.get(f'http://127.0.0.1:5000/clients', params={'name': client_name})
            print(f"[DEBUG] API response for client name '{client_name}': {response.json()}")  # Debug: Log the API response

            if response.status_code == 200:
                client_data = response.json()
                if client_data:
                    return client_data[0]['id']  # Assuming the first result is the correct client
                else:
                    print(f"[DEBUG] No client found for name: {client_name}")  # Debug: Log if no client is found
            else:
                print(f"[ERROR] Failed to fetch client_id for '{client_name}'. Status code: {response.status_code}")  # Debug: Log API error
        except Exception as e:
            print(f"[ERROR] Exception in get_client_id_by_name: {e}")  # Debug: Log any exception
        return None

    def get_vehicle_id_by_vin(self, vin):
        try:
            response = requests.get(f'http://127.0.0.1:5000/vehicles?vin={vin}')
            vehicle_data = response.json()
            if response.status_code == 200 and vehicle_data:
                return vehicle_data[0]['id']
        except Exception as e:
            messagebox.showerror("Eroare", f"A apărut o eroare: {e}")
        return None

    def get_vehicle_id_by_id(self, vehicle_id):
        # Implement the logic to get the vehicle id by its unique id
        return vehicle_id

    def delete_client(self, client_id, client_name):
        if messagebox.askyesno("Confirmare", f"Sunteți sigur că doriți să ștergeți clientul {client_name}?", icon='warning', default='no'):
            try:
                # Log before deleting and push inverse onto undo stack
                resp_get = requests.get(f'http://127.0.0.1:5000/clients/{client_id}')
                old_client = resp_get.json() if resp_get.ok else None
                logging.info(f"Deleting client {client_id}")
                response = requests.delete(f'http://127.0.0.1:5000/delete_client', params={'client_id': client_id})
                if response.ok and old_client:
                    self.undo_stack.append({
                        'description': f"delete_client {client_id}",
                        'method': 'POST',
                        'endpoint': '/add_client',
                        'payload': old_client
                    })
                if response.status_code == 200:
                    messagebox.showinfo("Succes", "Clientul a fost șters cu succes!")
                    self.refresh_client_list()
                else:
                    messagebox.showerror("Eroare", "Ștergerea clientului a eșuat!")
            except Exception as e:
                messagebox.showerror("Eroare", f"A apărut o eroare: {e}")

    def delete_vehicle(self, vehicle_id, vin):
        if messagebox.askyesno("Confirmare", f"Sunteți sigur că doriți să ștergeți vehiculul cu ID {vehicle_id}?", icon='warning', default='no'):
            try:
                response = requests.delete(f'http://127.0.0.1:5000/delete_vehicle', params={'vehicle_id': vehicle_id})
                if response.status_code == 200:
                    messagebox.showinfo("Succes", "Vehiculul a fost șters cu succes!")
                    # Refresh the vehicle list after deletion
                    selected_client = self.client_list.selection()
                    if selected_client:
                        client_name = self.client_list.item(selected_client, "values")[0]
                        self.refresh_client_vehicles(client_name)
                else:
                    messagebox.showerror("Eroare", "Ștergerea vehiculului a eșuat!")
            except Exception as e:
                messagebox.showerror("Eroare", f"A apărut o eroare: {e}")

    def add_client(self):
        print("Add Client Button Pressed")  # Debug print
        open_add_client_window(self.root, self.refresh_client_list)  # Pass the refresh_client_list method

    def add_vehicle(self):
        open_add_vehicle_window(self.root)  # Call the function to open the vehicle window

    def add_offer(self):
        open_add_offer_window(self.root)  # Call the function to open the offer window

    def manage_orders(self):
        open_client_search_window(self.root, self.on_client_selected_for_orders)  # Use the client search window

    def view_offers(self):
        def on_client_selected(client_id, client_name):
            if not client_id:
                messagebox.showerror("Eroare", "ID-ul clientului nu este specificat.")
                return
            open_view_offers_window(self.root, client_id=client_id)

        open_client_search_window(self.root, on_client_selected)

    def view_offers_from_section(self):
        selected_item = self.client_list.selection()
        if not selected_item:
            messagebox.showerror("Eroare", "Selectați un client pentru a vedea ofertele.")
            return
        client_name = self.client_list.item(selected_item, "values")[0]
        client_id = self.get_client_id_by_name(client_name)
        if not client_id:
            messagebox.showerror("Eroare", "ID-ul clientului nu a fost găsit.")
            return
        open_view_offers_window(self.root, client_id=client_id)

    def view_orders(self):
        def on_client_selected(client_id, client_name):
            if not client_id:
                messagebox.showerror("Eroare", "ID-ul clientului nu este specificat.")
                return
            open_view_orders_window(self.root, client_id=client_id)

        open_client_search_window(self.root, on_client_selected)

    def view_orders_from_section(self):
        selected_item = self.client_list.selection()
        if not selected_item:
            messagebox.showerror("Eroare", "Selectați un client pentru a vedea comenzile.")
            return
        client_name = self.client_list.item(selected_item, "values")[0]
        client_id = self.get_client_id_by_name(client_name)
        if not client_id:
            messagebox.showerror("Eroare", "ID-ul clientului nu a fost găsit.")
            return
        open_view_orders_window(self.root, client_id=client_id)

    def on_client_selected_for_orders(self, client_id, client_name):
        search_client_orders(self.root, client_name)  # Pass the client name to filter orders

    def on_client_selected_for_offers(self, client_id, client_name):
        search_client_offers(self.root, client_name)  # Pass the client name to filter offers

    def completed_orders(self):
        messagebox.showinfo("Comenzi Finalizate", "Aici puteți vizualiza comenzile finalizate.")

    def sales_report(self):
        self.open_window("Raport Vânzări", self.sales_report_content)

    def sales_report_content(self, frame):
        label = ttk.Label(frame, text="Aici puteți vizualiza raportul de vânzări.")
        label.pack(pady=10)
        proceed_button = ttk.Button(frame, text="Continuă")
        proceed_button.pack(pady=10)

    def top_clients_report(self):
        self.open_window("Raport Top Clienți", self.top_clients_report_content)

    def top_clients_report_content(self, frame):
        label = ttk.Label(frame, text="Aici puteți vizualiza raportul top clienți.")
        label.pack(pady=10)
        proceed_button = ttk.Button(frame, text="Continuă")
        proceed_button.pack(pady=10)

    def debts_report(self):
        self.open_window("Raport Datorii", self.debts_report_content)

    def debts_report_content(self, frame):
        label = ttk.Label(frame, text="Aici puteți vizualiza raportul de datorii.")
        label.pack(pady=10)
        proceed_button = ttk.Button(frame, text="Continuă")
        proceed_button.pack(pady=10)

    def export_data(self):
        self.open_window("Exportă Date", self.export_data_content)

    def export_data_content(self, frame):
        label = ttk.Label(frame, text="Aici puteți exporta datele.")
        label.pack(pady=10)
        proceed_button = ttk.Button(frame, text="Continuă")
        proceed_button.pack(pady=10)

    def refresh_data(self):
        messagebox.showinfo("Reîmprospătare Date", "Funcționalitatea de reîmprospătare a datelor.")

    def settings(self):
        """Open the settings window."""
        user_id = self.get_user_id()
        current_name = self.config.get("username", "Unknown")
        user_email = self.config.get("email", "Unknown")
        open_settings_window(user_id, user_email, current_name)  

    def get_user_id(self):
        """Retrieve the user ID from the configuration file."""
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, "r") as config_file:
                config = json.load(config_file)
                return config.get("user_id")
        return None

    def logout(self):
        self.root.destroy()
        messagebox.showinfo("Logout", "Ați fost deconectat.")

    def search(self, query):
        try:
            print(f"Searching for offers with query: {query}")  # Debug print
            response = requests.get(f'http://127.0.0.1:5000/offers?offer_number={query}')
            if response.status_code == 200:
                offers = response.json()
                # Clear the existing offers list
                for item in self.offers_list.get_children():
                    self.offers_list.delete(item)
                # Insert the updated offers list
                for offer in offers:
                    self.offers_list.insert('', 'end', values=(offer['id'], offer['nr_optiuni'], offer['date'], offer['status']))
            else:
                messagebox.showerror("Eroare", "Nu s-au găsit oferte pentru această căutare.")
        except Exception as e:
            print(f"Error searching offers: {e}")  # Debug print
            messagebox.showerror("Eroare", f"A apărut o eroare: {e}")

    def refresh_list(self, api_url, treeview, column_keys):
        try:
            response = requests.get(api_url)
            data = response.json()
            if response.status_code == 200:
                treeview.delete(*treeview.get_children())
                for item in data:
                    values = [item[key] for key in column_keys]
                    treeview.insert('', 'end', values=values)
            else:
                messagebox.showerror("Eroare", "Nu s-au putut încărca datele.")
        except Exception as e:
            messagebox.showerror("Eroare", f"A apărut o eroare: {e}")

    def get_id_by_field(self, endpoint, field, value):
        try:
            response = requests.get(f'http://127.0.0.1:5000/{endpoint}?{field}={value}')
            data = response.json()
            return data[0]['id'] if response.status_code == 200 and data else None
        except Exception as e:
            messagebox.showerror("Eroare", f"A apărut o eroare: {e}")
            return None

    def refresh_client_list(self):
        try:
            response = requests.get('http://127.0.0.1:5000/clients')
            data = response.json()
            if response.status_code == 200:
                self.client_list.delete(*self.client_list.get_children())  # Clear existing rows
                # Sort clients alphabetically by name
                sorted_clients = sorted(data, key=lambda client: client['nume'].lower())
                for client in sorted_clients:
                    localitate_judet = f"{client.get('localitate', '')}, {client.get('judet', '')}"  # Combine Localitate and Județ
                    self.client_list.insert("", "end", values=(client['nume'], client['telefon'], localitate_judet))
            else:
                messagebox.showerror("Eroare", "Nu s-au putut încărca clienții.")
        except Exception as e:
            messagebox.showerror("Eroare", f"A apărut o eroare: {e}")

    def refresh_client_vehicles(self, client_name):
        """Refresh the vehicle list for the selected client."""
        client_id = self.get_id_by_field('clients', 'name', client_name)
        if client_id:
            try:
                response = requests.get(f'http://127.0.0.1:5000/vehicles?client_id={client_id}')
                vehicles = response.json() if response.status_code == 200 else []

                self.client_vehicles_list.delete(*self.client_vehicles_list.get_children())  # Clear existing rows

                for vehicle in vehicles:
                    self.client_vehicles_list.insert(
                        "", "end",
                        values=(vehicle['marca'], vehicle['model'], vehicle['an'], vehicle['vin'], vehicle['numar_inmatriculare'], vehicle['image_url']),
                        tags=(vehicle['id'],)  # Store the vehicle ID in the tags
                    )
            except Exception as e:
                messagebox.showerror("Eroare", f"A apărut o eroare: {e}")

    def refresh_client_offers(self, client_name, vehicle_id=None):
        client_id = self.get_id_by_field('clients', 'name', client_name)
        if client_id:
            try:
                if vehicle_id:
                    response = requests.get(f'http://127.0.0.1:5000/offers?client_id={client_id}&vehicle_id={vehicle_id}')
                else:
                    response = requests.get(f'http://127.0.0.1:5000/offers?client_id={client_id}')
                
                offers = response.json() if response.status_code == 200 else []
                print(f"[DEBUG] Offers fetched: {offers}")  # Debug: Log the offers

                # Clear the existing offers list
                for widget in self.offers_canvas_frame.winfo_children():
                    widget.destroy()

                if not offers:
                    print("[DEBUG] No offers to display.")  # Debug: Log if no offers
                    return  # Exit early if no offers

                # Inject client_id into each offer and display as cards
                for index, offer in enumerate(offers[:4]):
                    offer["client_id"] = client_id  # ✅ Inject client_id here
                    is_last_row = index == len(offers[:4]) - 1
                    self.create_offer_card(self.offers_canvas_frame, offer, index, is_last_row)

                # Add "View More" card if there are more than 4 offers
                if len(offers) > 4:
                    self.create_view_more_offer_card(self.offers_canvas_frame, 4)

                self.root.after(100, self.resize_offer_container)  # Adjust UI
            except Exception as e:
                print(f"[ERROR] Exception in refresh_client_offers: {e}")  # Debug: Log the exception

    def refresh_client_orders(self, client_name):
        client_id = self.get_id_by_field('clients', 'name', client_name)
        if not client_id:
            return

        try:
            # Fetch all orders (including "balance") in one shot:
            resp = requests.get(f'http://127.0.0.1:5000/orders?client_id={client_id}')
            orders = resp.json() if resp.status_code == 200 else []

            # Clear old cards
            for widget in self.orders_canvas_frame.winfo_children():
                widget.destroy()

            # Iterate over each "order" object returned by the backend:
            for idx, order in enumerate(orders):
                # Create each order card, passing the full order object:
                self.create_order_card(
                    self.orders_canvas_frame,
                    order,
                    idx,
                    is_last_row=(idx == len(orders) - 1)
                )

            self.root.after(100, self.resize_order_container)

        except Exception as e:
            print(f"[ERROR] Exception in refresh_client_orders: {e}")
            messagebox.showerror("Eroare", f"A apărut o eroare: {e}")

    def display_client_details(self, event):
        """Display details of the selected client."""
        try:
            selected_item = self.client_list.selection()
            if selected_item:
                client = self.client_list.item(selected_item, "values")
                print(f"[DEBUG] Selected client: {client}")  # Debug: Log the selected client

                client_name = client[0]  # Assuming the first column is the client's name
                client_id = self.get_client_id_by_name(client_name)
                print(f"[DEBUG] Retrieved client_id for '{client_name}': {client_id}")  # Debug: Log the retrieved client_id

                if client_id:
                    # Update the client details section
                    self.client_name_value.config(text=client[0])
                    self.client_phone_value.config(text=client[1])
                    # Combine Adresă, Localitate, and Județ
                    client_details = self.get_client_details(client_id)
                    if client_details:
                        full_address = f"{client_details.get('adresa', '')}, {client_details.get('localitate', '')}, {client_details.get('judet', '')}"
                        self.client_address_value.config(text=full_address)
                    self.refresh_client_vehicles(client_name)
                    self.refresh_client_orders(client_name)
                    self.refresh_client_offers(client_name)
                    self.refresh_client_balances(client_name)
                else:
                    messagebox.showerror("Eroare", "ID-ul clientului nu a fost găsit.")
            else:
                print("[DEBUG] No client selected.")  # Debug: Log if no client is selected
        except Exception as e:
            print(f"[ERROR] Exception in display_client_details: {e}")  # Debug: Log any exception
            messagebox.showerror("Eroare", f"A apărut o eroare: {e}")

    def get_client_details(self, client_id):
        """Fetch client details by client ID."""
        try:
            response = requests.get(f'http://127.0.0.1:5000/clients/{client_id}')
            if response.status_code == 200:
                return response.json()
            else:
                print(f"[ERROR] Failed to fetch client details for ID {client_id}.")
                return None
        except Exception as e:
            print(f"[ERROR] Exception in get_client_details: {e}")
            return None

    def load_client_details(self):
        try:
            response = requests.get(f'http://127.0.0.1:5000/clients/{self.client_id}')
            if response.status_code == 200:
                client_details = response.json()
                self.client_name_value.config(text=client_details['nume'])
                self.client_phone_value.config(text=client_details['telefon'])
                self.client_address_value.config(text=f"{client_details['adresa']}, {client_details['localitate']}, {client_details['judet']}")  # Full address
                self.load_client_vehicles()
                self.load_client_offers()
                self.load_client_orders()
            else:
                messagebox.showerror("Eroare", "Nu s-au putut încărca detaliile clientului.")
        except Exception as e:
            messagebox.showerror("Eroare", f"A apărut o eroare: {e}")

    def edit_selected_client(self):
        selected_item = self.client_list.selection()
        if selected_item:
            client_name = self.client_list.item(selected_item, "values")[0]  # Assuming the client name is the first value
            client_id = self.get_client_id_by_name(client_name)
            if client_id:
                open_edit_client_window(self.root, client_id)
            else:
                messagebox.showerror("Eroare", "ID-ul clientului nu a fost găsit.")
        else:
            messagebox.showerror("Eroare", "Selectați un client pentru a edita detaliile.")

    def on_double_click(self, event):
        selected_item = self.client_list.selection()
        
        if not selected_item:
            print("No item selected on double-click.")  # Debugging
            return

        client = self.client_list.item(selected_item, "values")
        client_id = self.get_client_id_by_name(client[0])

        if not client_id:
            print(f"Failed to retrieve client ID for: {client[0]}")  # Debugging
            messagebox.showerror("Eroare", "Nu s-a putut găsi ID-ul clientului.")
            return

        print(f"Opening dashboard for client ID: {client_id}")  # Debugging
        self.open_customer_dashboard(client_id)

    def bind_right_click(self):
        self.client_list.bind("<Button-3>", self.on_right_click)

    def refresh_client_balances(self, client_name=None):
        # Dacă nu avem încă etichetele de Totaluri inițializate, ieșim
        if not hasattr(self, 'total_spent_value'):
            return

        try:
            if client_name:
                # 1. Obținem client_id din client_name
                client_id = self.get_client_id_by_name(client_name)
                if not client_id:
                    # Dacă nu găsește ID, afișăm zero în toate câmpurile
                    self.total_spent_value .config(text="0.00 RON")
                    self.de_platit_value   .config(text="0.00 RON")
                    self.sold_value        .config(text="0.00 RON")
                    self.total_orders_value.config(text="0")
                    return

                # 2. Apelăm endpoint-ul /totals/<client_id>
                response = requests.get(f'http://127.0.0.1:5000/totals/{client_id}')
                if response.status_code == 200:
                    data = response.json()
                    total_cheltuit = data.get('total_cheltuit', 0.0)
                    de_platit      = data.get('de_platit', 0.0)
                    sold           = data.get('sold', 0.0)       # suma totală a returnărilor
                    total_comenzi  = data.get('total_comenzi', 0)

                    # 3. Aplicăm sold-ul (refund) pentru a acoperi întâi balanțele deschise
                    net_de_platit = max(de_platit - sold, 0.0)
                    net_sold      = max(sold - de_platit, 0.0)

                    # 4. Actualizăm label-urile
                    self.total_spent_value .config(text=f"{float(total_cheltuit):,.2f} RON")
                    self.de_platit_value   .config(text=f"{net_de_platit:,.2f} RON")
                    self.sold_value        .config(text=f"{net_sold:,.2f} RON")
                    self.total_orders_value.config(text=str(total_comenzi))
                else:
                    # Dacă nu răspunde OK, afișăm zero
                    self.total_spent_value .config(text="0.00 RON")
                    self.de_platit_value   .config(text="0.00 RON")
                    self.sold_value        .config(text="0.00 RON")
                    self.total_orders_value.config(text="0")
            else:
                # Fără client selectat, afișăm zero
                self.total_spent_value .config(text="0.00 RON")
                self.de_platit_value   .config(text="0.00 RON")
                self.sold_value        .config(text="0.00 RON")
                self.total_orders_value.config(text="0")
        except Exception as e:
            messagebox.showerror("Eroare", f"A apărut o eroare la încărcarea totalurilor: {e}")

    def on_search(self, event=None):
        """Handle search action and open the search window with the query."""
        query = self.search_entry.get().strip()
        if query:
            open_search_window(self.root, query)
        else:
            messagebox.showinfo("Căutare", "Introduceți un termen de căutare.")

    def create_offer_card(self, parent, offer, column, is_last_row=False):
        """Create a card for an offer."""
        card_frame = ttk.LabelFrame(parent, text=f"🛍️ Ofertă {offer['offer_number']}", padding=10)
        # Add bottom padding if it's the last row
        bottom_padding = 10 if is_last_row else 0
        card_frame.grid(row=0, column=column, padx=10, pady=(10, bottom_padding), sticky="nsew")

        ttk.Label(card_frame, text=f"📅 Data: {offer['date']}", font=("Segoe UI", 10)).pack(anchor="w")
        ttk.Label(card_frame, text=f"⚙️ Opțiuni: {offer.get('nr_optiuni', 'N/A')}", font=("Segoe UI", 10)).pack(anchor="w")
        ttk.Label(card_frame, text=f"📌 Status: {offer['status']}", font=("Segoe UI", 10)).pack(anchor="w")
        ttk.Label(card_frame, text=f"👤 Client: {offer.get('client_name', 'N/A')}", font=("Segoe UI", 10)).pack(anchor="w")

        # Ensure the client variable is passed to the function
        client = self.get_client_details(offer["client_id"])  # Fetch client details using client_id
        if not client:
            print(f"[ERROR] Client not found for offer: {offer}")
            return

        button_frame = ttk.Frame(card_frame)
        button_frame.pack(anchor="e", pady=5)

        # Restore "Vizualizează" button
        ttk.Button(
            button_frame,
            text="Vizualizează",
            command=lambda: open_edit_offer_window(self.root, offer['offer_number'])
        ).pack(side="left", padx=5)

        # Restore "Transformă în Comandă" button
        ttk.Button(
            button_frame,
            text="Transformă în Comandă",
            command=lambda o=offer: self.transform_to_order({**o, "client_id": client["id"]})
        ).pack(side="left", padx=5)

    def create_view_more_offer_card(self, parent, column):
        card_frame = ttk.LabelFrame(parent, text="🛍️ Vezi mai multe oferte", padding=10)
        card_frame.grid(row=0, column=column, padx=10, pady=10, sticky="nsew")

        ttk.Label(card_frame, text="📅 Data: --/--/----", font=("Segoe UI", 10)).pack(anchor="w")
        ttk.Label(card_frame, text="⚙️ Opțiuni: --", font=("Segoe UI", 10)).pack(anchor="w")
        ttk.Label(card_frame, text="📌 Status: --", font=("Segoe UI", 10)).pack(anchor="w")

        card_frame.bind("<Enter>", lambda event: card_frame.configure(style="Hover.TLabelFrame"))
        card_frame.bind("<Leave>", lambda event: card_frame.configure(style="TLabelFrame"))
        card_frame.bind("<Button-1>", lambda event: open_view_offers_window(self.root))

    def create_view_more_order_card(self, parent, column):
        card_frame = ttk.LabelFrame(parent, text="📦 Vezi mai multe comenzi", padding=10)
        card_frame.grid(row=0, column=column, padx=10, pady=10, sticky="nsew")

        ttk.Label(card_frame, text="📅 Data: --/--/----", font=("Segoe UI", 10)).pack(anchor="w")
        ttk.Label(card_frame, text="🛒 Produse: --", font=("Segoe UI", 10)).pack(anchor="w")
        ttk.Label(card_frame, text="📌 Status: --", font=("Segoe UI", 10)).pack(anchor="w")

        card_frame.bind("<Enter>", lambda event: card_frame.configure(style="Hover.TLabelFrame"))
        card_frame.bind("<Leave>", lambda event: card_frame.configure(style="TLabelFrame"))
        card_frame.bind("<Button-1>", lambda event: open_view_orders_window(self.root))

    def open_selected_client_dashboard(self):
        selected_item = self.client_list.selection()
        
        if not selected_item:
            messagebox.showerror("Eroare", "Selectați un client pentru a deschide dashboard-ul.")
            return

        client = self.client_list.item(selected_item, "values")
        client_id = self.get_id_by_field('clients', 'name', client[0])

        if not client_id:
            messagebox.showerror("Eroare", "Nu s-a putut găsi ID-ul clientului.")
            return

        self.open_customer_dashboard(client_id)

    def resize_offer_container(self, event=None):
        """ Adjusts the height of the offers container and centers cards vertically. """
        if self.offers_canvas_frame.winfo_children():
            self.root.update_idletasks()

            # Calculate max height
            max_card_height = max(widget.winfo_reqheight() for widget in self.offers_canvas_frame.winfo_children())
            new_height = min(max_card_height + 10, 140)  # Slight padding above & below

            # Apply new height to the canvas
            self.offers_canvas.configure(height=new_height)

            # Calculate vertical padding to center elements
            for widget in self.offers_canvas_frame.winfo_children():
                vertical_pad = max((new_height - widget.winfo_reqheight()) // 2, 0)  # Ensure padding is non-negative
                widget.grid_configure(pady=vertical_pad)
        else:
            self.offers_canvas.configure(height=1)  # Collapse if empty

    def resize_order_container(self, event=None):
        """ Adjusts the height of the orders container and centers cards vertically. """
        if self.orders_canvas_frame.winfo_children():
            self.root.update_idletasks()

            # Calculate max height
            max_card_height = max(widget.winfo_reqheight() for widget in self.orders_canvas_frame.winfo_children())
            new_height = min(max_card_height + 10, 140)  # Padding for better spacing

            # Apply new height to the canvas
            self.orders_canvas.configure(height=new_height)

            # Calculate vertical padding to center elements
            for widget in self.orders_canvas_frame.winfo_children():
                vertical_pad = max((new_height - widget.winfo_reqheight()) // 2, 0)  # Ensure padding is non-negative
                widget.grid_configure(pady=vertical_pad)
        else:
            self.orders_canvas.configure(height=1)  # Collapse if empty

    def create_order_card(self, parent, order, column, is_last_row=False):
        """Create a card for an order, now using server-computed 'balance'."""
        card_frame = ttk.LabelFrame(parent, text=f"📦 Comandă {order['order_number']}", padding=10)
        bottom_padding = 10 if is_last_row else 0
        card_frame.grid(row=0, column=column, padx=10, pady=(10, bottom_padding), sticky="nsew")

        # Extract client and vehicle details
        client_name = order.get('client', {}).get('nume', 'N/A')
        vehicle = order.get('vehicle', {})
        marca = vehicle.get('marca', 'N/A')
        model = vehicle.get('model', 'N/A')
        inmatriculare = vehicle.get('numar_inmatriculare', 'N/A')

        # Use `order["balance"]` directly:
        remaining = order.get('balance', 0.0)

        ttk.Label(card_frame, text=f"👤 Client: {client_name}", font=("Segoe UI", 10)).pack(anchor="w")
        ttk.Label(card_frame, text=f"🚗 Vehicul: {marca} {model} - {inmatriculare}", font=("Segoe UI", 10)).pack(anchor="w")
        ttk.Label(card_frame, text=f"📅 Data: {order['date']}", font=("Segoe UI", 10)).pack(anchor="w")
        ttk.Label(card_frame, text=f"📌 Status: {order.get('status', 'N/A')}", font=("Segoe UI", 10)).pack(anchor="w")

        # Show the server-computed balance:
        ttk.Label(
            card_frame,
            text=f"💰 De Plătit: {remaining:.2f} RON",
            font=("Segoe UI", 10, "bold"),
            foreground="red"
        ).pack(anchor="w")

        button_frame = ttk.Frame(card_frame)
        button_frame.pack(anchor="e", pady=5)

        ttk.Button(
            button_frame,
            text="Return",
            command=lambda o=order: ReturnProductsWindow(self.root, prefill_order=o['id'])
        ).pack(side="left", padx=5)

        ttk.Button(
            button_frame,
            text="Vizualizează",
            command=lambda: open_edit_order_window(self.root, order['order_number'])
        ).pack(side="left", padx=5)

        card_frame.bind("<Enter>", lambda event: card_frame.configure(style="Hover.TLabelFrame"))
        card_frame.bind("<Leave>", lambda event: card_frame.configure(style="TLabelFrame"))
        card_frame.bind("<Button-3>", lambda event, order=order: self.show_order_context_menu(event, order))
        card_frame.bind("<Double-1>", lambda event, order=order: open_edit_order_window(self.root, order['order_number']))

    def view_totals(self):
        # Placeholder method for viewing totals
        messagebox.showinfo("Totaluri", "Aici puteți vizualiza totalurile.")

    def resize_total_container(self, event=None):
        """
        Adjusts the height of the total container to match the height of the tallest total card,
        adding 10 pixels above and below, and limiting the height to 150 pixels.
        """
        if self.balance_list.get_children():
            self.root.update_idletasks()  # Force Tkinter to update before measuring
            
            # Get the maximum height among all total cards
            max_card_height = max((self.balance_list.bbox(item)[3] for item in self.balance_list.get_children() if self.balance_list.bbox(item)), default=0)

            # Calculate the new height (card height + 10px)
            new_height = min(max_card_height + 10, 150)  # Limit height to 150px

            # Apply the height to the treeview
            self.balance_list.configure(height=new_height)
        else:
            self.balance_list.configure(height=1)  # Collapse if empty

    def show_offer_context_menu(self, event, offer):
        context_menu = Menu(self.root, tearoff=0)
        context_menu.add_command(label="Generează PDF", command=lambda: self.generate_pdf(offer['offer_number']))
        context_menu.add_command(label="Transformă în comandă", command=lambda: self.transform_to_order(offer))
        context_menu.post(event.x_root, event.y_root)

    def show_order_context_menu(self, event, order):
        context_menu = Menu(self.root, tearoff=0)
        context_menu.add_command(label="Generează PDF", command=lambda: self.generate_pdf(order['order_number']))
        context_menu.add_command(label="Transformă în comandă", command=lambda: self.transform_to_order(order))
        context_menu.post(event.x_root, event.y_root)

    def select_category_popup(self, categories):
        """Popup window to select a category using a dropdown."""
        popup = Toplevel(self.root)
        popup.title("Selectează o Categorie")
        popup.geometry("300x150")
        popup.transient(self.root)
        popup.grab_set()

        selected_category = StringVar()
        selected_category.set(categories[0])  # Default selection

        Label(popup, text="Alege categoria pentru comandă:").pack(pady=10)
        dropdown = ttk.Combobox(popup, textvariable=selected_category, values=categories, state="readonly")
        dropdown.pack(pady=5)

        def confirm():
            popup.destroy()

        Button(popup, text="Continuă", command=confirm).pack(pady=10)
        popup.wait_window()  # Pause until window is closed

        return selected_category.get()

    def transform_to_order(self, offer_summary):
        try:
            offer_number = offer_summary["offer_number"]
            print("[DEBUG] Calling /offers/ with offer_number:", offer_number)

            response = requests.get(f"http://127.0.0.1:5000/offers/{offer_number}")
            print("[DEBUG] HTTP status:", response.status_code)
            print("[DEBUG] Raw text:", response.text)

            if response.status_code != 200 or not response.text.strip():
                messagebox.showerror("Eroare", "Nu s-au putut încărca detaliile ofertei.")
                return

            try:
                offer_data = response.json()
            except Exception as e:
                print("[ERROR] JSON decode error:", e)
                messagebox.showerror("Eroare", f"A apărut o eroare la preluarea ofertei:\n{e}")
                return

            print("[DEBUG] Full offer data received:", offer_data)

            if "categories" not in offer_data or not offer_data["categories"]:
                print("[DEBUG] Categories missing or empty.")
                messagebox.showerror("Eroare", "Ofertă invalidă: lipsesc categoriile.")
                return

            selected_category = self.select_category_popup(list(offer_data["categories"].keys()))
            if not selected_category:
                messagebox.showwarning("Anulare", "Conversia în comandă a fost anulată.")
                return

            # Fetch vehicle details
            vehicle_id = offer_data["vehicle_id"]
            vehicle_response = requests.get(f"http://127.0.0.1:5000/vehicle/{vehicle_id}")
            try:
                vehicle_data = vehicle_response.json()
            except Exception as e:
                print("[ERROR] JSON decode error for vehicle:", vehicle_response.text)
                messagebox.showerror("Eroare", f"A apărut o eroare la preluarea vehiculului: {vehicle_response.text}")
                return

            # Inject client_name into offer_data
            client_response = requests.get(f"http://127.0.0.1:5000/clients/{offer_data['client_id']}")
            if client_response.status_code == 200:
                client_info = client_response.json()
                offer_data["client_name"] = client_info.get("nume", "Client Necunoscut")
            else:
                offer_data["client_name"] = "Client Necunoscut"

            # Prepare order data
            order_data = {
                "offer_number": offer_data["offer_number"],
                "client_id": offer_data["client_id"],
                "client_name": offer_data.get("client_name", ""),
                "vehicle_id": vehicle_id,
                "vehicle_data": vehicle_data,
                "selected_category": selected_category,
                "order_number": offer_data["offer_number"].replace("O", "CMD")
            }

            from new_order import open_new_order_window
            open_new_order_window(self.root, order_data, on_save=self.handle_order_saved)  # ✅ Pass callback

        except Exception as e:
            print("[ERROR] Exception occurred in transform_to_order:", e)
            messagebox.showerror("Eroare", f"A apărut o eroare: {e}")

    def handle_order_saved(self, offer_number, order_number, selected_category):
        """Callback after an order is saved to update the offer status without losing existing fields."""
        try:
            # 1. Fetch existing offer
            response = requests.get(f"http://127.0.0.1:5000/offers/{offer_number}")
            if response.status_code != 200:
                messagebox.showerror("Eroare", "Nu s-au putut încărca detaliile ofertei.")
                return

            offer_data = response.json()

            # 2. Concatenează observațiile (nu le înlocui complet)
            previous_observations = offer_data.get("observations", "").strip()
            new_note = f"Transformată în comandă {order_number}, categoria aleasă: {selected_category}"
            merged_observations = f"{previous_observations}\n{new_note}".strip() if previous_observations else new_note

            # 3. Trimite PATCH cu toate câmpurile esențiale
            update_payload = {
                "status": "Acceptată",
                "observations": merged_observations,
                "vehicle_id": offer_data.get("vehicle_id"),
                "date": offer_data.get("date"),
                "client_id": offer_data.get("client_id"),  # ✅ Include client_id for redundancy
                "offer_number": offer_data.get("offer_number")  # ✅ Include offer_number for redundancy
            }

            headers = {"Content-Type": "application/json"}
            patch_resp = requests.patch(
                f"http://127.0.0.1:5000/offers/{offer_number}",
                data=json.dumps(update_payload),
                headers=headers
            )

            if patch_resp.status_code == 200:
                messagebox.showinfo("Actualizare", f"Ofertă {offer_number} marcată ca Acceptată.")
                self.refresh_client_offers(self.client_name_value.cget("text"))
            else:
                messagebox.showerror("Eroare", f"Actualizarea ofertei a eșuat:\n{patch_resp.text}")

        except Exception as e:
            messagebox.showerror("Eroare", f"A apărut o eroare la actualizarea ofertei:\n{e}")

    def open_new_offer_with_customer(self):
        try:
            selected_item = self.client_list.selection()[0]
            customer_data = self.client_list.item(selected_item, "values")
            if not customer_data:
                messagebox.showerror("Eroare", "Nu a fost selectat niciun client.")
                return

            customer_id = self.get_client_id_by_name(customer_data[0])  # Assuming the first column contains the customer name
            customer_name = customer_data[0]  # Assuming the first column contains the customer name

            # Fetch the customer's vehicles
            response = requests.get(f'http://127.0.0.1:5000/vehicles?client_id={customer_id}')
            vehicles = response.json() if response.status_code == 200 else []

            # Fetch next offer number from backen
            try:
                response = requests.get("http://127.0.0.1:5000/highest_offer_number")
                if response.status_code == 200:
                    last_offer = response.json().get("highest_offer_number", "O0")
                    next_offer_number = f"O{int(last_offer[1:]) + 1}"
                else:
                    next_offer_number = "O1"
            except:
                next_offer_number = "O1"

            from datetime import datetime

            # Prepare offer details
            offer_details = {
                "client_id": customer_id,
                "client_name": customer_name,
                "offer_number": next_offer_number,
                "categories": {},
                "status": "Ofertă (în așteptare)",
                "observations": "",
                "date": datetime.now().strftime("%Y-%m-%d"),  # Set current date in ISO format
                "vehicles": vehicles
            }

            # Open the new offer window with prefilled customer details
            open_add_offer_window(self.root, offer_details)
        except Exception as e:
            messagebox.showerror("Eroare", f"A apărut o eroare: {e}")

    def on_vehicle_right_click(self, event):
        """Show context menu for vehicles when right-clicking."""
        try:
            selected_item = self.client_vehicles_list.identify_row(event.y)
            if selected_item:
                self.client_vehicles_list.selection_set(selected_item)
                vehicle_data = self.client_vehicles_list.item(selected_item, "values")
                vehicle_id = self.client_vehicles_list.item(selected_item, "tags")[0]  # Retrieve vehicle ID from tags
                if vehicle_data and vehicle_id:
                    context_menu = Menu(self.root, tearoff=0)
                    context_menu.add_command(label="🛠️ Editează Vehicul", command=lambda: self.edit_vehicle(vehicle_id))
                    context_menu.add_command(label="🗑️ Șterge Vehicul", command=lambda: self.delete_vehicle(vehicle_id, vehicle_data[3]))
                    context_menu.post(event.x_root, event.y_root)
        except Exception as e:
            messagebox.showerror("Eroare", f"A apărut o eroare: {e}")

    def edit_vehicle(self, vehicle_id):
        """Open the edit vehicle window."""
        try:
            subprocess.Popen(["python", "edit_vehicle.py", str(vehicle_id)], shell=True)
        except Exception as e:
            messagebox.showerror("Eroare", f"A apărut o eroare la deschiderea ferestrei de editare: {e}")

    def open_sales_report(self):
        """Open the sales report window."""
        sales_report_window = tk.Toplevel(self.root)
        sales_report_window.title("Raport Vânzări")
        sales_report_window.geometry("1000x700")
        sales_report_window.transient(self.root)
        sales_report_window.grab_set()
        open_sales_report_window(sales_report_window)  # Pass the new window to the sales report function

    def open_vehicle_talon(self, event):
        """Open the talon (vehicle document) for the selected vehicle."""
        try:
            selected_item = self.client_vehicles_list.selection()
            if not selected_item:
                messagebox.showerror("Eroare", "Selectați un vehicul pentru a deschide talonul.")
                return

            vehicle = self.client_vehicles_list.item(selected_item, "values")
            talon_url = vehicle[5]  # Assuming the talon URL is in the 6th column (index 5)

            if talon_url and talon_url != "None":
                open_talon_window(self.root, talon_url)  # Open the talon image in a popup window
            else:
                messagebox.showinfo("Informație", "Vehiculul selectat nu are un talon asociat.")
        except Exception as e:
            messagebox.showerror("Eroare", f"A apărut o eroare: {e}")

    def undo_last(self):
        """Undo the very last action, if any."""
        if not self.undo_stack:
            return messagebox.showinfo("Undo", "Nothing to undo.")

        action = self.undo_stack.pop()
        logging.info(f"Undoing: {action['description']}")

        try:
            # Decide how to call the inverse
            method = action['method'].upper()
            url = f"http://127.0.0.1:5000{action['endpoint']}"
            if method == 'GET':
                requests.get(url, params=action.get('params'))
            else:
                requests.request(method, url, json=action.get('payload'), params=action.get('params'))
            messagebox.showinfo("Undo", "Last action undone.")
        except Exception as e:
            logging.error(f"Undo failed: {e}")
            messagebox.showerror("Undo Error", f"Failed to undo last action:\n{e}")

    def open_payment_for_selected_client(self):
        selected = self.client_list.selection()
        if not selected:
            messagebox.showerror("Eroare", "Selectați un client înainte de a adăuga o plată.")
            return

        client_name = self.client_list.item(selected, "values")[0]
        client_id = self.get_client_id_by_name(client_name)
        if not client_id:
            messagebox.showerror("Eroare", "Nu s-a putut găsi ID-ul clientului.")
            return

        AddPaymentWindow(self.root, client_id=client_id, client_name=client_name)

def open_add_payment_window():
    payment_window = tk.Toplevel(root)
    AddPaymentWindow(payment_window)

if __name__ == "__main__":
    root = tk.Tk()
    app = DashboardApp(root)
    app.bind_right_click()
    root.mainloop()
