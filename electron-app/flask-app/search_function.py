import requests
from tkinter import Tk, Toplevel, Label, Entry, Button, Listbox, END, messagebox, ttk, Frame
import unicodedata
import tkinter as tk
from tkinter import ttk, messagebox, Menu
import subprocess  # Add this import for running external scripts
from supabase import create_client, Client  # Import Supabase client
from config import SUPABASE_URL, SUPABASE_KEY  # Import Supabase configuration
import os  # Add this import for handling paths
import json  # Add this import for handling JSON
from customer_dashboard import CustomerDashboardApp  # Import the CustomerDashboardApp class
import logging  # Add this import for logging
from vezi_comenzi import ViewOrdersApp  # Import the ViewOrdersApp class
from vezi_oferte import ViewOffersApp  # Import the ViewOffersApp class
import tkinter.font as tkFont  # Import for measuring text width
from vezi_comenzi import open_view_orders_window  # Import the function to open the view orders window
from vezi_oferte import open_view_offers_window  # Import the function to open the view offers window
import sys  # Add this import to resolve the undefined variable error
from new_offer import open_add_offer_window  # Import the function to open the add offer window
from edit_offer import open_edit_offer_window  # Import the function to open the edit offer window

# Initialize Supabase client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Configure logging to save debug statements into a .txt file
LOG_FILE = os.path.join(os.path.dirname(__file__), 'debug_log.txt')
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def normalize_text(text):
    """Normalize text by removing diacritics, converting to lowercase, and stripping whitespace."""
    if not text:
        return ""
    sanitized_text = unicodedata.normalize('NFKC', text.strip())  # Normalize Unicode to NFKC form
    sanitized_text = ''.join(
        c for c in unicodedata.normalize('NFD', sanitized_text)
        if unicodedata.category(c) != 'Mn'
    )  # Remove diacritics
    return sanitized_text.lower()

def normalize_text_once(data):
    """Normalize text for a list of dictionaries or a single string."""
    if isinstance(data, list):
        return [{key: normalize_text(value) if isinstance(value, str) else value for key, value in item.items()} for item in data]
    elif isinstance(data, str):
        return normalize_text(data)
    return data

def search_customer(customers, query):
    """Perform flexible search for customers by name (or 'nume'), ignoring diacritics."""
    normalized_query = normalize_text(query)
    normalized_customers = normalize_text_once(customers)
    return [customer for customer in normalized_customers if normalized_query in customer.get('nume', '')]

def search_database(query, category):
    try:
        response = requests.get(f'http://127.0.0.1:5000/search', params={'query': query, 'category': category})
        if response.status_code == 200:
            return response.json()
        else:
            messagebox.showerror("Eroare", "Căutarea a eșuat!")
            return []
    except Exception as e:
        messagebox.showerror("Eroare", f"A apărut o eroare: {e}")
        return []

def create_scrollable_frame(parent_frame):
    """Create a scrollable frame inside the given parent frame."""
    canvas = tk.Canvas(parent_frame, bg="#d3d3d3", highlightthickness=0)
    scrollbar = ttk.Scrollbar(parent_frame, orient="vertical", command=canvas.yview)
    scrollable_frame = ttk.Frame(canvas, padding=10)

    # Configure the canvas and the scrollbar
    canvas.configure(yscrollcommand=scrollbar.set)
    scrollbar.grid(row=0, column=1, sticky="ns")  # Changed to grid
    canvas.grid(row=0, column=0, sticky="nsew")  # Changed to grid
    canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
    scrollable_frame.bind(
        "<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
    )

    parent_frame.grid_rowconfigure(0, weight=1)
    parent_frame.grid_columnconfigure(0, weight=1)

    return scrollable_frame, canvas

def display_search_results(results, category):
    search_window = Toplevel()
    search_window.title("Rezultatele Căutării")
    search_window.geometry("1200x800")
    search_window.configure(bg="#d3d3d3")
    search_window.resizable(False, False)  # Prevent resizing

    # Configure grid for the search window
    search_window.grid_rowconfigure(0, weight=1)
    search_window.grid_columnconfigure(0, weight=1)

    # Create main frame
    main_frame = ttk.Frame(search_window, padding=10)
    main_frame.grid(row=0, column=0, sticky="nsew")

    # Configure grid for the main frame
    main_frame.rowconfigure(0, weight=1)
    main_frame.columnconfigure(0, weight=1)

    # Create and configure the Treeview table
    results_table = ttk.Treeview(main_frame, columns=("Nume", "Telefon", "Localitate", "Județ"), show="headings", height=20)
    results_table.heading("Nume", text="🧑‍💼 Nume")
    results_table.heading("Telefon", text="📞 Telefon")
    results_table.heading("Localitate", text="📍 Localitate")
    results_table.heading("Județ", text="🌍 Județ")
    results_table.column("Nume", width=300, anchor="center")  # Adjusted width for full window
    results_table.column("Telefon", width=200, anchor="center")
    results_table.column("Localitate", width=300, anchor="center")
    results_table.column("Județ", width=200, anchor="center")
    results_table.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

    # Add a vertical scrollbar for the Treeview
    scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=results_table.yview)
    results_table.configure(yscrollcommand=scrollbar.set)
    scrollbar.grid(row=0, column=1, sticky="ns")

    # Populate the table with search results
    for result in results:
        results_table.insert("", "end", values=(
            result.get("nume", "N/A"),
            result.get("telefon", "N/A"),
            result.get("localitate", "N/A"),
            result.get("judet", "N/A")
        ))

    # Add double-click event to open the customer dashboard
    def on_double_click(event):
        selected_item = results_table.selection()
        if selected_item:
            customer = results_table.item(selected_item, "values")
            customer_id = result.get("id")  # Assuming `id` is part of the result data
            open_customer_dashboard(customer_id)

    results_table.bind("<Double-1>", on_double_click)

def open_search_window(root, query=""):
    """Open the advanced search window."""
    try:
        print("[DEBUG] Opening search window...")
        search_window = tk.Toplevel(root)
        search_window.title("Căutare Avansată")
        search_window.geometry("1200x800")
        search_window.configure(bg="#d3d3d3")
        search_window.state('zoomed')  # Start maximized for consistency with dashboard

        # Configure the grid system for the search_window
        search_window.grid_rowconfigure(0, weight=0)  # Search bar
        search_window.grid_rowconfigure(1, weight=0)  # Filters
        search_window.grid_rowconfigure(2, weight=1)  # Results area
        search_window.grid_columnconfigure(0, weight=1)

        # Search Bar
        search_frame = ttk.Frame(search_window, padding=10)
        search_frame.grid(row=0, column=0, sticky="ew")

        search_entry = ttk.Entry(search_frame, font=("Segoe UI", 14))
        search_entry.insert(0, query)  # Initialize with the searched term
        search_entry.pack(side="left", fill="x", expand=True, padx=10, ipady=6)

        # Instead of reopening the window, pressing Enter now reruns perform_search()
        search_entry.bind(
            "<Return>",
            lambda event, se=search_entry: perform_search(
                se.get().strip(), categories, results_notebook
            )
        )

        def perform_refresh():
            current_query = search_entry.get().strip()
            if current_query:
                perform_search(current_query, categories, results_notebook)
            else:
                messagebox.showinfo("Reîmprospătare", "Introduceți un termen de căutare pentru a reîmprospăta.")

        search_button = ttk.Button(search_frame, text="🔍 Caută", command=lambda: perform_search(search_entry.get(), categories, results_notebook))
        search_button.pack(side="left", padx=10)

        # Add the refresh button
        refresh_button = ttk.Button(search_frame, text="🔄 Reîmprospătare", command=perform_refresh)
        refresh_button.pack(side="left", padx=10)

        # Filters
        filters_frame = ttk.Frame(search_window, padding=10)
        filters_frame.grid(row=1, column=0, sticky="ew")

        select_all_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(filters_frame, text="Toate", variable=select_all_var, command=lambda: toggle_all_filters(select_all_var, categories)).pack(side="left", padx=5)

        categories = {
            "Clienți": tk.BooleanVar(value=True),
            "Vehicule": tk.BooleanVar(value=True),
            "Oferte": tk.BooleanVar(value=True),
            "Comenzi": tk.BooleanVar(value=True),
            "Produse din comanda": tk.BooleanVar(value=True),
            "Produse din oferta": tk.BooleanVar(value=True)
        }
        for category, var in categories.items():
            ttk.Checkbutton(filters_frame, text=category, variable=var).pack(side="left", padx=5)

        # Results Notebook
        results_notebook = ttk.Notebook(search_window)
        results_notebook.grid(row=2, column=0, sticky="nsew", padx=10, pady=10)

        # Automatically trigger the search with the initial query
        if query:
            perform_search(query, categories, results_notebook)  # Trigger search immediately

    except Exception as e:
        print(f"[ERROR] Exception in open_search_window: {e}")

def toggle_all_filters(select_all_var, categories):
    """Toggle all category filters based on the 'Toate' checkbox."""
    for var in categories.values():
        var.set(select_all_var.get())

def perform_search(query, categories, results_notebook):
    """Perform search and populate results in the notebook."""
    # 1) Clear out old tabs
    for tab in results_notebook.tabs():
        results_notebook.forget(tab)

    # 2) Always build the “Clienti” tab first, if enabled
    client_results = []
    if categories["Clienți"].get():
        clients_tab = ttk.Frame(results_notebook)
        client_results = fetch_results(query, "clients", clients_tab, results_notebook, {}, "Clienti") or []
        results_notebook.add(clients_tab, text=f"Clienti ({len(client_results)})")

    # 3) Now for each of Vehicule, Comenzi, Oferte
    for label, (backend_cat, tab_name) in {
        "Vehicule": ("vehicles", "Vehicule"),
        "Comenzi":  ("orders",   "Comenzi"),
        "Oferte":   ("offers",   "Oferte"),
    }.items():
        if not categories[label].get():
            continue

        tab = ttk.Frame(results_notebook)

        # 3a) If we have client_results, fetch by client_id via your REST endpoints
        if client_results:
            combined = []
            for client in client_results:
                cid = client.get("id")
                if not cid:
                    continue
                resp = requests.get(
                    f"http://127.0.0.1:5000/{backend_cat}",
                    params={"client_id": cid}
                )
                if resp.status_code == 200:
                    combined.extend(resp.json())

            # Render or show “no results”
            if backend_cat == "vehicles":
                if combined:
                    render_vehicle_items(tab, combined)
                else:
                    ttk.Label(tab,
                        text="⚠️ Nu s-au găsit vehicule pentru acest client.",
                        font=("Segoe UI", 12)
                    ).pack(padx=20, pady=20)
            elif backend_cat == "orders":
                if combined:
                    render_orders_notebook(tab, combined)
                else:
                    ttk.Label(tab,
                        text="⚠️ Nu s-au găsit comenzi pentru acest client.",
                        font=("Segoe UI", 12)
                    ).pack(padx=20, pady=20)
            else:  # offers
                if combined:
                    render_offers_notebook(tab, combined)
                else:
                    ttk.Label(tab,
                        text="⚠️ Nu s-au găsit oferte pentru acest client.",
                        font=("Segoe UI", 12)
                    ).pack(padx=20, pady=20)

            count = len(combined)

        # 3b) Otherwise fallback to your full-text RPC
        else:
            results = fetch_results(query, backend_cat, tab, results_notebook, {}, tab_name) or []
            count = len(results)

        # 4) Always add the tab (even if count = 0)
        results_notebook.add(tab, text=f"{tab_name} ({count})")

def fetch_results(query, category, tab_frame, results_notebook, related_data, tab_name, page=1, per_page=20):
    try:
        # Ensure related_data is initialized for the category
        if category not in related_data:
            related_data[category] = set()

        # Clear previous results
        for widget in tab_frame.winfo_children():
            widget.destroy()

        # API call to fetch universal search results
        print(f"[DEBUG] Fetching results for query='{query}', category='{category}'")
        response = supabase.rpc("search_universal", {
            "query": query,
            "category": category,
            "page": page,
            "per_page": per_page
        }).execute()

        # Log the raw response from Supabase
        print(f"[DEBUG] Raw Supabase response: {response.data}")

        if response.data:
            results = response.data

            if category == "vehicles":
                for item in results:
                    vehicle = item.get("vehicle", {})
                    offers = item.get("offers", [])
                    orders = item.get("orders", [])

                    # Render the vehicle details
                    render_vehicle_details(tab_frame, vehicle)

                    # Create a parent frame for stacking
                    sections_frame = ttk.Frame(tab_frame)
                    sections_frame.pack(fill="both", expand=True)

                    # Render the offers section
                    if offers:
                        offers_frame = ttk.Frame(sections_frame)
                        offers_frame.pack(fill="x", pady=10)  # Add padding between sections
                        ttk.Label(offers_frame, text="Oferte", font=("Segoe UI", 12, "bold")).pack(anchor="w", pady=5)
                        render_offers_notebook(offers_frame, offers)

                    # Render the orders section
                    if orders:
                        orders_frame = ttk.Frame(sections_frame)
                        orders_frame.pack(fill="x", pady=10)  # Add padding between sections
                        ttk.Label(orders_frame, text="Comenzi", font=("Segoe UI", 12, "bold")).pack(anchor="w", pady=5)
                        render_orders_notebook(orders_frame, orders)

                return results  # Return results to determine if the tab should be added
            else:
                render_results(tab_frame, category, results)
                return results  # Return results to determine if the tab should be added
        else:
            ttk.Label(tab_frame, text=f"Nu s-au găsit rezultate pentru categoria '{category}'.", font=("Segoe UI", 12)).grid(row=0, column=0, pady=20)
            return []  # Return empty list if no results
    except Exception as e:
        print(f"[ERROR] Exception during fetch_results for category='{category}': {e}")
        # Clear any partial widgets
        for w in tab_frame.winfo_children():
            w.destroy()
        # Show error in-tab
        ttk.Label(
            tab_frame,
            text=f"Eroare la încărcarea «{tab_name}»: {e}",
            foreground="red",
            font=("Segoe UI", 12, "italic"),
            wraplength=600,
            justify="center"
        ).grid(row=0, column=0, padx=10, pady=20, sticky="nsew")
        # Return an empty list so we still signal “handled”
        return []

def render_vehicle_details(tab_frame, vehicle):
    """Render the details of a vehicle."""
    ttk.Label(tab_frame, text=f"Vehicul: {vehicle.get('marca')} {vehicle.get('model')} ({vehicle.get('numar_inmatriculare')})", font=("Segoe UI", 12, "bold")).pack(anchor="w", pady=5)
    ttk.Label(tab_frame, text=f"An: {vehicle.get('an')}, VIN: {vehicle.get('vin')}", font=("Segoe UI", 10)).pack(anchor="w", pady=5)
    ttk.Label(tab_frame, text=f"Client: {vehicle.get('nume')} ({vehicle.get('telefon')}), Localitate: {vehicle.get('localitate')}", font=("Segoe UI", 10)).pack(anchor="w", pady=5)

def render_offers_notebook(tab_frame, offers):
    """Render offers as cards instead of a Treeview."""
    if not offers:
        ttk.Label(tab_frame, text="Nu există oferte disponibile.", font=("Segoe UI", 12)).pack(pady=10)
        return

    # Create a canvas for scrolling
    canvas = tk.Canvas(tab_frame, bg="#d3d3d3", highlightthickness=0)
    canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    # Add a vertical scrollbar
    scrollbar = ttk.Scrollbar(tab_frame, orient="vertical", command=canvas.yview)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    # Configure the canvas to work with the scrollbar
    canvas.configure(yscrollcommand=scrollbar.set)

    # Create a frame inside the canvas
    frame = ttk.Frame(canvas, padding=10)
    canvas.create_window((0, 0), window=frame, anchor="nw")

    # Bind the frame to adjust the scroll region
    frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))

    # Set the number of cards per row
    cards_per_row = 3  # Adjust this value to change the number of cards per row

    # Configure the grid columns dynamically
    for col in range(cards_per_row):
        frame.grid_columnconfigure(col, weight=1)

    # Insert the offers into the grid
    for index, offer in enumerate(offers):
        create_offer_card(frame, offer, index % cards_per_row, index // cards_per_row)

def create_offer_card(parent, offer, column, row):
    """Create a card for an offer."""
    card_frame = ttk.LabelFrame(parent, text=f"🛍️ Ofertă {offer['offer_number']}", padding=10)
    card_frame.grid(row=row, column=column, padx=10, pady=10, sticky="nsew")

    ttk.Label(card_frame, text=f"📅 Data: {offer['date']}", font=("Segoe UI", 10)).pack(anchor="w")
    ttk.Label(card_frame, text=f"📌 Status: {offer['status']}", font=("Segoe UI", 10)).pack(anchor="w")

    button_frame = ttk.Frame(card_frame)
    button_frame.pack(anchor="e", pady=5)

    ttk.Button(
        button_frame,
        text="Vizualizează",
        command=lambda: open_edit_offer_window(parent.winfo_toplevel(), offer['id'])
    ).pack(side="left", padx=5)

    ttk.Button(
        button_frame,
        text="Transformă în Comandă",
        command=lambda: turn_into_order(offer)
    ).pack(side="left", padx=5)

def render_orders_notebook(tab_frame, orders):
    """Render orders as cards instead of a Treeview."""
    if not orders:
        ttk.Label(tab_frame, text="Nu există comenzi disponibile.", font=("Segoe UI", 12)).pack(pady=10)
        return

    # Create a canvas for scrolling
    canvas = tk.Canvas(tab_frame, bg="#d3d3d3", highlightthickness=0)
    canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    # Add a vertical scrollbar
    scrollbar = ttk.Scrollbar(tab_frame, orient="vertical", command=canvas.yview)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    # Configure the canvas to work with the scrollbar
    canvas.configure(yscrollcommand=scrollbar.set)

    # Create a frame inside the canvas
    frame = ttk.Frame(canvas, padding=10)
    canvas.create_window((0, 0), window=frame, anchor="nw")

    # Bind the frame to adjust the scroll region
    frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))

    # Set the number of cards per row
    cards_per_row = 3  # Adjust this value to change the number of cards per row

    # Configure the grid columns dynamically
    for col in range(cards_per_row):
        frame.grid_columnconfigure(col, weight=1)

    # Insert the orders into the grid
    for index, order in enumerate(orders):
        create_order_card(frame, order, index % cards_per_row, index // cards_per_row)

def create_order_card(parent, order, column, row):
    """Create a card for an order."""
    card_frame = ttk.LabelFrame(parent, text=f"📦 Comandă {order['order_number']}", padding=10)
    card_frame.grid(row=row, column=column, padx=10, pady=10, sticky="nsew")

    ttk.Label(card_frame, text=f"📅 Data: {order['date']}", font=("Segoe UI", 10)).pack(anchor="w")
    ttk.Label(card_frame, text=f"🛒 Produse: {order.get('nr_produse', 'N/A')}", font=("Segoe UI", 10)).pack(anchor="w")
    ttk.Label(card_frame, text=f"📌 Status: {order['status']}", font=("Segoe UI", 10)).pack(anchor="w")

    button_frame = ttk.Frame(card_frame)
    button_frame.pack(anchor="e", pady=5)

    ttk.Button(
        button_frame,
        text="Vizualizează",
        command=lambda: open_edit_order_window(parent.winfo_toplevel(), order['id'])
    ).pack(side="left", padx=5)

def adjust_treeview_column_widths(tree):
    """Dynamically adjust Treeview column widths based on content."""
    font = tkFont.Font()
    for col in tree["columns"]:
        max_width = max(
            [font.measure(str(tree.set(child, col))) for child in tree.get_children()] +
            [font.measure(col)]
        )
        tree.column(col, width=max_width + 20)  # Add padding for margins

def render_results(tab_frame, category, results):
    """Render results for supported categories."""
    logging.debug(f"Rendering results for category='{category}' with {len(results)} items.")
    
    if category == "clients":
        # Handle Client rendering from nested structure
        client_data = [
            {
                "id": item["id"],
                "nume": item.get("nume", "N/A"),
                "telefon": item.get("telefon", "N/A"),
                "localitate": item.get("localitate", "N/A"),
                "judet": item.get("judet", "N/A"),
                "adresa": item.get("adresa", "N/A")
            }
            for item in results
        ]
        render_client_items(tab_frame, client_data)  # Ensure this function is called with the correct data

    elif category == "vehicles":
        # Handle Vehicle rendering
        vehicle_data = [
            {
                "client_id": item["client"]["id"],
                "nume": item["client"]["nume"],
                "marca": item["vehicle"]["marca"],
                "model": item["vehicle"]["model"],
                "an": item["vehicle"]["an"],
                "vin": item["vehicle"]["vin"],
                "numar_inmatriculare": item["vehicle"]["numar_inmatriculare"]
            }
            for item in results
        ]
        render_vehicle_items(tab_frame, vehicle_data)

    elif category == "offers":
        # Handle Offer rendering
        offer_data = [
            {
                "offer_number": item["offer"]["offer_number"],
                "client_name": item["client"]["nume"],
                "vehicle": f"{item['vehicle']['marca']} {item['vehicle']['model']} ({item['vehicle']['numar_inmatriculare']})",
                "status": item["offer"].get("status", "N/A"),
                "date": item["offer"].get("date", "N/A"),
                "id": item["offer"]["id"],
                "nr_optiuni": item["offer"].get("nr_optiuni", "N/A")
            }
            for item in results
        ]
        render_offer_items(tab_frame, offer_data)

    elif category == "orders":
        # Handle Order rendering
        render_order_items(tab_frame, results)

    elif category == "order_products":
        order_product_data = [
            {
                "order_number": item["order"]["order_number"],
                "nume_client": item["client"]["nume"],
                "vehicul": f"{item['vehicle']['marca']} {item['vehicle']['model']} ({item['vehicle']['numar_inmatriculare']})",
                "product": item["order_product"]["produs"],
                "cod_produs": item["order_product"]["cod_produs"],
                "brand": item["order_product"]["brand"],
                "cantitate": item["order_product"]["cantitate"],
                "pret_unitar": item["order_product"]["pret_unitar"],
                "pret_total": item["order_product"]["pret_total"],
                "discount": item["order_product"]["discount"],
                "pret_cu_discount": item["order_product"]["pret_cu_discount"]
            }
            for item in results
        ]
        render_order_product_items(tab_frame, order_product_data)

    elif category == "offer_products":
        offer_product_data = [
            {
                "offer_number": item["offer"]["offer_number"],
                "nume_client": item["client"]["nume"],
                "vehicul": f"{item['vehicle']['marca']} {item['vehicle']['model']} ({item['vehicle']['numar_inmatriculare']})",
                "product": item["offer_product"]["produs"],
                "cod_produs": item["offer_product"]["cod_produs"],
                "brand": item["offer_product"]["brand"],
                "cantitate": item["offer_product"]["cantitate"],
                "pret_unitar": item["offer_product"]["pret_unitar"],
                "pret_total": item["offer_product"]["pret_total"],
                "discount": item["offer_product"]["discount"],
                "pret_cu_discount": item["offer_product"]["pret_cu_discount"]
            }
            for item in results
        ]
        render_offer_product_items(tab_frame, offer_product_data)

def render_client_items(tab_frame, data):
    """Render Client items in a Treeview with additional functionalities."""
    if not data:
        ttk.Label(tab_frame, text="⚠️ Nu s-au găsit rezultate pentru clienți.", font=("Segoe UI", 12)).grid(row=0, column=0, pady=20)
        return

    columns = ["Nume", "Telefon", "Localitate", "Județ"]
    tree = ttk.Treeview(tab_frame, columns=columns, show="headings", height=20)

    # Define style
    style = ttk.Style()
    style.configure("Treeview", font=("Segoe UI", 11), rowheight=30)
    style.configure("Treeview.Heading", font=("Segoe UI", 11, "bold"))
    style.map("Treeview", background=[("selected", "#f0ad4e")])

    # Add striped rows using tags
    tree.tag_configure('evenrow', background='#f9f9f9')
    tree.tag_configure('oddrow', background='#ffffff')

    for col in columns:
        tree.heading(col, text=col)
        tree.column(col, width=300, anchor="center")  # Adjust column width for full window width

    tree.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

    # Scrollbars
    x_scrollbar = ttk.Scrollbar(tab_frame, orient="horizontal", command=tree.xview)
    y_scrollbar = ttk.Scrollbar(tab_frame, orient="vertical", command=tree.yview)
    tree.configure(xscrollcommand=x_scrollbar.set, yscrollcommand=y_scrollbar.set)
    x_scrollbar.grid(row=1, column=0, sticky="ew")
    y_scrollbar.grid(row=0, column=1, sticky="ns")

    # Insert rows with striped background
    for index, item in enumerate(data):
        tag = 'evenrow' if index % 2 == 0 else 'oddrow'
        tree.insert("", "end", values=(item["nume"], item["telefon"], item["localitate"], item["judet"]), tags=(tag,), iid=item["id"])

    # Double-click to open dashboard
    def on_double_click(event):
        selected_item = tree.selection()
        if selected_item:
            client_id = selected_item[0]  # Use the item's ID as the client_id
            print(f"[DEBUG] Double-clicked client ID: {client_id}")  # Debug statement
            open_customer_dashboard(client_id)

    tree.bind("<Double-1>", on_double_click)

    # Right-click context menu
    def show_context_menu(event):
        selected_item = tree.identify_row(event.y)
        if selected_item:
            tree.selection_set(selected_item)
            client_id = selected_item  # Use the item's ID as the client_id
            print(f"[DEBUG] Right-clicked client ID: {client_id}")  # Debug statement

            context_menu = tk.Menu(tree, tearoff=0)
            context_menu.add_command(label="✅ Deschide Dashboard", command=lambda: open_customer_dashboard(client_id))
            context_menu.add_command(
                label="📝 Editează Client",
                command=lambda: launch_edit_client_script(client_id)
            )
            context_menu.add_command(label="🛒 Vezi Comenzi", command=lambda: open_view_orders_window(tree.master, client_id=client_id))
            context_menu.add_command(label="🎯 Vezi Oferte", command=lambda: open_view_offers_window(tree.master, client_id=client_id))
            context_menu.post(event.x_root, event.y_root)

    tree.bind("<Button-3>", show_context_menu)

def launch_edit_client_script(client_id):
    """Launch the edit_client.py script with the given client_id."""
    script_path = os.path.join(os.path.dirname(__file__), "edit_client.py")  # Relative path
    if not os.path.exists(script_path):
        print(f"[ERROR] Script not found: {script_path}")  # Debug statement
        messagebox.showerror("Eroare", "Fișierul edit_client.py nu a fost găsit!")
        return

    try:
        print(f"[DEBUG] Launching script: {script_path} with client_id: {client_id}")  # Debug statement
        print(f"[DEBUG] Current working directory: {os.getcwd()}")  # Debug statement
        print(f"[DEBUG] Python executable: {sys.executable}")  # Debug statement
        subprocess.Popen([sys.executable, script_path, str(client_id)], shell=True)
    except Exception as e:
        print(f"[ERROR] Failed to launch script: {e}")  # Debug statement
        messagebox.showerror("Eroare", f"A apărut o eroare la deschiderea scriptului: {e}")

def open_new_order_with_serialized_data(parent, client_id, vehicle_data):
    """Open the new order window with properly serialized vehicle data."""
    try:
        print(f"[DEBUG] Raw vehicle_data before serialization: {vehicle_data}")  # Debug statement

        # Ensure vehicle_data is a dictionary
        if isinstance(vehicle_data, str):
            try:
                vehicle_data = json.loads(vehicle_data.replace("'", '"'))  # Fix single quotes
                print("[DEBUG] Fixed vehicle_data with double quotes.")  # Debug statement
            except json.JSONDecodeError as e:
                raise ValueError(f"Invalid JSON string for vehicle_data: {e}")

        if not isinstance(vehicle_data, dict):
            raise ValueError(f"Expected vehicle_data to be a dictionary, got {type(vehicle_data)}")

        serialized_vehicle_data = json.dumps(vehicle_data)  # Serialize to JSON string
        print(f"[DEBUG] Serialized vehicle_data: {serialized_vehicle_data}")  # Debug statement

        subprocess.Popen(["python", "new_order.py", str(client_id), serialized_vehicle_data])
    except Exception as e:
        print(f"[ERROR] Failed to open new order window: {e}")  # Debug statement
        messagebox.showerror("Eroare", f"A apărut o eroare la deschiderea ferestrei de comandă: {e}")

def render_vehicle_items(tab_frame, data):
    """Render Vehicle items in the Treeview for Vehiculele Clientului."""
    if not data:
        ttk.Label(tab_frame, text="⚠️ Nu s-au găsit rezultate pentru vehicule.", font=("Segoe UI", 12)).grid(row=0, column=0, pady=20)
        return

    columns = ["Nume", "Marca", "Model", "An", "VIN", "Număr Înmatriculare"]
    tree = ttk.Treeview(tab_frame, columns=columns, show="headings", height=15)

    # Define style
    style = ttk.Style()
    style.configure("Treeview", font=("Segoe UI", 11), rowheight=30)
    style.configure("Treeview.Heading", font=("Segoe UI", 11, "bold"))
    style.map("Treeview", background=[("selected", "#f0ad4e")])

    for col in columns:
        tree.heading(col, text=col)
        tree.column(col, width=150, anchor="center", stretch=False)
    tree.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

    # Scrollbars
    y_scrollbar = ttk.Scrollbar(tab_frame, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=y_scrollbar.set)
    y_scrollbar.grid(row=0, column=1, sticky="ns")

    # Insert rows
    for index, item in enumerate(data):
        tree.insert("", "end", values=(
            item["nume"], item["marca"], item["model"], item["an"], item["vin"], item["numar_inmatriculare"]
        ), iid=item["client_id"], tags=(item,))  # Store the full item in tags for context

    # Double-click to open dashboard
    def on_double_click(event):
        selected_item = tree.selection()
        if selected_item:
            client_id = selected_item[0]  # Use the item's ID as the client_id
            print(f"[DEBUG] Double-clicked client ID: {client_id}")  # Debug statement
            open_customer_dashboard(client_id)

    tree.bind("<Double-1>", on_double_click)

    # Right-click context menu
    def show_context_menu(event):
        selected_item = tree.identify_row(event.y)
        if selected_item:
            tree.selection_set(selected_item)
            client_id = selected_item  # Use the item's ID as the client_id
            vehicle_data = tree.item(selected_item, "tags")[0]  # Retrieve the full vehicle data
            print(f"[DEBUG] Right-clicked client ID: {client_id}, Vehicle Data: {vehicle_data}")  # Debug statement

            context_menu = tk.Menu(tree, tearoff=0)
            context_menu.add_command(label="✅ Deschide Dashboard Client", command=lambda: open_customer_dashboard(client_id))
            context_menu.add_command(label="🛍️ Adaugă Ofertă", command=lambda: open_new_offer_with_vehicle(tree.master, client_id, vehicle_data))
            context_menu.add_command(label="📝 Editează Vehicul", command=lambda: open_edit_vehicle_window(tree.master, client_id=client_id))
            context_menu.post(event.x_root, event.y_root)

    tree.bind("<Button-3>", show_context_menu)

def open_new_offer_with_vehicle(parent, client_id, vehicle_data):
    """Open the new offer window with the customer's name and their car(s)."""
    try:
        print(f"[DEBUG] Opening New Offer Window with client_id: {client_id}, vehicle_data: {vehicle_data}")  # Debug statement

        # 🛠️ Ensure vehicle_data is parsed from JSON string if necessary
        if isinstance(vehicle_data, str):
            try:
                vehicle_data = json.loads(vehicle_data.replace("'", '"'))  # Replace single quotes for safety
                print(f"[DEBUG] Parsed vehicle_data: {vehicle_data}")
            except Exception as e:
                raise ValueError(f"[ERROR] Invalid vehicle_data string: {e}")

        if not isinstance(vehicle_data, dict):
            raise ValueError(f"[ERROR] vehicle_data should be a dict, got {type(vehicle_data)}")

        # Wrap vehicle_data in the expected structure, excluding offer_number and date
        offer_details = {
            "client_id": client_id,
            "client_name": vehicle_data["nume"],
            "vehicles": [vehicle_data],  # Pass the vehicle data as a list
            "categories": {},
            "status": "Ofertă (în așteptare)",
            "observations": ""
        }

        open_add_offer_window(parent, offer_details=offer_details)
    except Exception as e:
        print(f"[ERROR] Failed to open new offer window: {e}")
        messagebox.showerror("Eroare", f"A apărut o eroare la deschiderea ferestrei de ofertă: {e}")

def render_offer_items(tab_frame, data):
    """Render Offer items as cards in the notebook tab with vertical scrolling."""
    if not data:
        ttk.Label(tab_frame, text="Nu există oferte disponibile.", font=("Segoe UI", 12)).pack(pady=10)
        return

    # Create a canvas for scrolling
    canvas = tk.Canvas(tab_frame, bg="#d3d3d3", highlightthickness=0)
    canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    # Add a vertical scrollbar
    scrollbar = ttk.Scrollbar(tab_frame, orient="vertical", command=canvas.yview)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    # Configure the canvas to work with the scrollbar
    canvas.configure(yscrollcommand=scrollbar.set)

    # Create a frame inside the canvas
    frame = ttk.Frame(canvas, padding=10)
    canvas.create_window((0, 0), window=frame, anchor="nw")

    # Bind the frame to adjust the scroll region
    frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))

    # Set the number of cards per row
    cards_per_row = 4  # Change this value to adjust the number of cards per row

    # Configure the grid columns dynamically
    for col in range(cards_per_row):
        frame.grid_columnconfigure(col, weight=1)

    # Insert the updated offers list
    for index, offer in enumerate(data):
        if "id" not in offer:
            print(f"[ERROR] Missing 'id' in offer: {offer}")
            continue  # Skip offers without an 'id'
        create_offer_card(frame, offer, index % cards_per_row, index // cards_per_row)

    # Add double-click event to open the offer
    def on_double_click(event):
        widget = event.widget
        if isinstance(widget, ttk.Frame):
            selected_offer = widget.offer_data  # Attach offer data to the widget
            if selected_offer and "id" in selected_offer:
                open_edit_offer_window(None, selected_offer["id"])

    frame.bind("<Double-1>", on_double_click)

def create_offer_card(parent, offer, column, row):
    """Create a card for an offer."""
    card_frame = ttk.Frame(parent, relief="raised", borderwidth=2, padding="10", style="TFrame")
    card_frame.grid(row=row, column=column, padx=10, pady=10, sticky="nsew")

    ttk.Label(card_frame, text=f"🛍️ Ofertă {offer['offer_number']}", font=("Segoe UI", 12, "bold")).pack(anchor="w")
    ttk.Label(card_frame, text=f"📅 Data: {offer['date']}", font=("Segoe UI", 10)).pack(anchor="w")
    ttk.Label(card_frame, text=f"📌 Status: {offer['status']}", font=("Segoe UI", 10)).pack(anchor="w")
    ttk.Label(card_frame, text=f"👤 Client: {offer.get('client_name', 'N/A')}", font=("Segoe UI", 10)).pack(anchor="w")

    button_frame = ttk.Frame(card_frame, style="TFrame")
    button_frame.pack(anchor="e", pady=5)

    ttk.Button(
        button_frame,
        text="Vizualizează",
        command=lambda: open_edit_offer_window(parent.winfo_toplevel(), offer['offer_number'])
    ).pack(side="left", padx=5)
    ttk.Button(button_frame, text="Transformă în Comandă", command=lambda: turn_into_order(offer)).pack(side="left", padx=5)

def render_order_items(tab_frame, data):
    """Render Order items as cards in the notebook tab with vertical scrolling."""
    if not data:
        ttk.Label(tab_frame, text="Nu există comenzi disponibile.", font=("Segoe UI", 12)).pack(pady=10)
        return

    # Create a canvas for scrolling
    canvas = tk.Canvas(tab_frame, bg="#d3d3d3", highlightthickness=0)
    canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    # Add a vertical scrollbar
    scrollbar = ttk.Scrollbar(tab_frame, orient="vertical", command=canvas.yview)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    # Configure the canvas to work with the scrollbar
    canvas.configure(yscrollcommand=scrollbar.set)

    # Create a frame inside the canvas
    frame = ttk.Frame(canvas, padding=10)
    canvas.create_window((0, 0), window=frame, anchor="nw")

    # Bind the frame to adjust the scroll region
    frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))

    # Set the number of cards per row
    cards_per_row = 5  # Adjust this value to change the number of cards per row

    # Configure the grid columns dynamically
    for col in range(cards_per_row):
        frame.grid_columnconfigure(col, weight=1)

    # Insert the orders into the grid
    for index, order in enumerate(data):
        create_order_card(frame, order, index % cards_per_row, index // cards_per_row)

    # Add double-click event to open the order
    def on_double_click(event):
        widget = event.widget
        if isinstance(widget, ttk.Frame):
            selected_order = widget.order_data  # Attach order data to the widget
            if selected_order and "id" in selected_order:
                open_edit_order_window(selected_order["id"])

    frame.bind("<Double-1>", on_double_click)

def create_order_card(parent, order_data, column, row):
    """Create a card for an order."""
    card_frame = ttk.Frame(parent, relief="raised", borderwidth=2, padding="10")
    card_frame.grid(row=row, column=column, padx=10, pady="5 10", sticky="nsew")

    # Debugging: Print the order dictionary to check its contents
    print(f"[DEBUG] Order data: {order_data}")

    # Access the nested 'order' dictionary
    order = order_data.get('order', {})
    client = order_data.get('client', {})
    vehicle = order_data.get('vehicle', {})

    ttk.Label(card_frame, text=f"📦 Comandă {order.get('order_number', 'N/A')}", font=("Segoe UI", 12, "bold")).pack(anchor="w")
    ttk.Label(card_frame, text=f"📅 Data: {order.get('date', 'N/A')}", font=("Segoe UI", 10)).pack(anchor="w")
    ttk.Label(card_frame, text=f"📌 Status: {order.get('status', 'N/A')}", font=("Segoe UI", 10)).pack(anchor="w")
    ttk.Label(card_frame, text=f"👤 Client: {client.get('nume', 'N/A')}", font=("Segoe UI", 10)).pack(anchor="w")
    ttk.Label(card_frame, text=f"🚗 Vehicul: {vehicle.get('marca', 'N/A')} {vehicle.get('model', 'N/A')} ({vehicle.get('numar_inmatriculare', 'N/A')})", font=("Segoe UI", 10)).pack(anchor="w")

    button_frame = ttk.Frame(card_frame)
    button_frame.pack(anchor="e", pady=5)

    ttk.Button(button_frame, text="Vizualizează", command=lambda: open_edit_order_window(order.get('id'))).pack(side="left", padx=5)

    # Attach order data to the card frame for double-click handling
    card_frame.order_data = order_data

def render_product_items(tab_frame, data, is_offer=False):
    """Generic renderer for both offer and order products."""
    print(f"[DEBUG] Rendering {'offer' if is_offer else 'order'} product items")

    if not data:
        ttk.Label(
            tab_frame, 
            text="Nu s-au găsit rezultate pentru produsele din ofertă." if is_offer else "Nu s-au găsit rezultate pentru produsele din comandă.", 
            font=("Segoe UI", 12)
        ).grid(row=0, column=0, pady=20)
        return

    # Dynamically build columns and headers
    columns = [
        "offer_number" if is_offer else "order_number", "nume_client", "vehicul",
        "product", "cod_produs", "brand", "cantitate",
        "pret_unitar", "pret_total", "discount", "pret_cu_discount"
    ]
    headers = [
        "Nr. Ofertă" if is_offer else "Nr. Comandă", "Nume Client", "Vehicul",
        "Produs", "Cod Produs", "Brand", "Cantitate", 
        "Preț Unitar", "Preț Total", "Discount", "Preț cu Discount"
    ]

    tree = ttk.Treeview(tab_frame, columns=columns, show="headings", height=15)
    for col, header in zip(columns, headers):
        tree.heading(col, text=header)
        tree.column(col, width=150, anchor="center", stretch=False)
    tree.column(columns[-1], stretch=True)  # Allow the last column to stretch
    tree.grid(row=0, column=0, sticky="nsew", padx=10, pady=(10, 20))  # Added bottom padding

    scrollbar = ttk.Scrollbar(tab_frame, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=scrollbar.set)
    scrollbar.grid(row=0, column=1, sticky="ns")

    for item in data:
        try:
            number = item.get("offer_number" if is_offer else "order_number", "N/A")
            client_name = item.get("nume_client", "N/A")
            vehicul_str = item.get("vehicul", "N/A")

            tree.insert("", "end", values=(
                number,
                client_name,
                vehicul_str,
                item.get("product", "N/A"),
                item.get("cod_produs", "N/A"),
                item.get("brand", "N/A"),
                item.get("cantitate", "N/A"),
                item.get("pret_unitar", "N/A"),
                item.get("pret_total", "N/A"),
                item.get("discount", "N/A"),
                item.get("pret_cu_discount", "N/A")
            ))
        except Exception as e:
            print(f"[ERROR] Failed to process item: {e} | {item}")

    # Adjust column widths dynamically
    adjust_treeview_column_widths(tree)

    # Ensure the table stretches to fill the available space
    tab_frame.grid_rowconfigure(0, weight=1)
    tab_frame.grid_columnconfigure(0, weight=1)

def render_offer_product_items(tab_frame, data):
    """Render offer product items with duplicate removal."""
    # Remove duplicates based on unique combination of keys
    seen = set()
    unique_data = []
    for item in data:
        key = (item['offer_number'], item['product'], item['vehicul'])
        if key not in seen:
            seen.add(key)
            unique_data.append(item)
    render_product_items(tab_frame, unique_data, is_offer=True)

def render_order_product_items(tab_frame, data):
    """Render order product items with duplicate removal."""
    # Remove duplicates based on unique combination of keys
    seen = set()
    unique_data = []
    for item in data:
        key = (item['order_number'], item['product'], item['vehicul'])
        if key not in seen:
            seen.add(key)
            unique_data.append(item)
    render_product_items(tab_frame, unique_data, is_offer=False)

def add_pagination_controls(tab_frame, query, category, results_notebook, page, per_page, total_results):
    """Add pagination controls to the tab frame."""
    # Clear previous pagination controls
    for widget in tab_frame.winfo_children():
        if isinstance(widget, ttk.Frame):
            widget.destroy()

    pagination_frame = ttk.Frame(tab_frame)
    pagination_frame.grid(row=1, column=0, sticky="ew", pady=10)

    total_pages = (total_results + per_page - 1) // per_page

    # Add "Anterior" button if there is a previous page
    if page > 1:
        prev_button = ttk.Button(pagination_frame, text="⬅️ Anterior", command=lambda: fetch_results(query, category, tab_frame, results_notebook, {}, category, page - 1, per_page))
        prev_button.grid(row=0, column=0, padx=5)

    # Display current page and total pages
    ttk.Label(pagination_frame, text=f"Pagina {page} din {total_pages}").grid(row=0, column=1, padx=5)

    # Add "Următor" button if there is a next page
    if page < total_pages:
        next_button = ttk.Button(pagination_frame, text="➡️ Următor", command=lambda: fetch_results(query, category, tab_frame, results_notebook, {}, category, page + 1, per_page))
        next_button.grid(row=0, column=2, padx=5)

def open_customer_dashboard(client_id):
    """Open the customer dashboard for the selected client."""
    dashboard_window = tk.Toplevel()  # Create a new Toplevel window
    dashboard_window.title("Customer Dashboard")
    dashboard_window.geometry("1200x800")
    dashboard_window.configure(bg="#d3d3d3")
    CustomerDashboardApp(dashboard_window, client_id)  # Initialize the dashboard app in the new window
    dashboard_window.transient()  # Make it modal
    dashboard_window.grab_set()  # Prevent interaction with the parent window
    dashboard_window.mainloop()

def open_edit_offer_window(parent, offer_id):
    """Open the edit offer window for the selected offer."""
    subprocess.Popen(["python", "edit_offer.py", str(offer_id)])

def open_edit_order_window(order_id):
    """Open the edit order window for the selected order."""
    subprocess.Popen(["python", "edit_order.py", str(order_id)])

def open_new_order_window(parent, client_id, vehicle_data=None):
    """Open the new order window for the selected client."""
    try:
        serialized_vehicle_data = json.dumps(vehicle_data)  # Ensure valid JSON format
        print(f"[DEBUG] Serialized vehicle_data: {serialized_vehicle_data}")  # Debug statement
        subprocess.Popen(["python", "new_order.py", str(client_id), serialized_vehicle_data])
    except Exception as e:
        print(f"[ERROR] Failed to open new order window: {e}")  # Debug statement
        messagebox.showerror("Eroare", f"A apărut o eroare la deschiderea ferestrei de comandă: {e}")

def open_edit_vehicle_window(parent, client_id):
    """Open the edit vehicle window for the selected client."""
    subprocess.Popen(["python", "edit_vehicle.py", str(client_id)])

def refresh_vehicle_tab(results_notebook, client_id):
    """Refresh the 'Vehicule' tab in the notebook using universal search."""
    try:
        # Perform a universal search for vehicles by client_id
        query = client_id
        category = "vehicles"
        response = requests.get(f'http://127.0.0.1:5000/search', params={'query': query, 'category': category})
        
        if response.status_code == 200:
            vehicles = response.json()
            print(f"[DEBUG] Refreshed vehicles: {vehicles}")  # Debug statement

            # Find the "Vehicule" tab and clear its content
            for tab_id in results_notebook.tabs():
                if results_notebook.tab(tab_id, "text") == "Vehicule":
                    tab_frame = results_notebook.nametowidget(tab_id)
                    for widget in tab_frame.winfo_children():
                        widget.destroy()

                    # Render the updated vehicle data
                    render_vehicle_items(tab_frame, vehicles)
                    break
        else:
            print(f"[ERROR] Failed to refresh vehicles. Status code: {response.status_code}")
            messagebox.showerror("Eroare", "Nu s-au putut actualiza vehiculele.")
    except Exception as e:
        print(f"[ERROR] Exception occurred while refreshing vehicles: {e}")
        messagebox.showerror("Eroare", f"A apărut o eroare: {e}")

def turn_into_order(offer):
    """Transform an offer into an order."""
    try:
        # Assuming `offer` contains the necessary details to create an order
        response = requests.post('http://127.0.0.1:5000/orders', json=offer)
        if response.status_code == 200:
            messagebox.showinfo("Succes", "Oferta a fost transformată cu succes în comandă!")
        else:
            messagebox.showerror("Eroare", f"Transformarea ofertei în comandă a eșuat. Cod eroare: {response.status_code}")
    except Exception as e:
        messagebox.showerror("Eroare", f"A apărut o eroare: {e}")

if __name__ == "__main__":
    root = Tk()
    root.withdraw()  # Hide the root window
    try:
        open_search_window(root)
        root.mainloop()
    except Exception as e:
        print(f"[CRITICAL ERROR] Could not open search window: {e}")
