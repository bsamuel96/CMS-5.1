import tkinter as tk
from tkinter import ttk, messagebox, Menu, simpledialog
import requests
from PIL import Image, ImageTk
import os
import json
import sys
from supabase import create_client, Client
from config import SUPABASE_URL, SUPABASE_KEY
from edit_offer import open_edit_offer_window
from edit_order import open_edit_order_window
from vezi_oferte import open_view_offers_window  # Import the function to open the view offers window
from vezi_comenzi import open_view_orders_window  # Import the function to open the view orders window
from add_payment import AddPaymentWindow
import subprocess

CONFIG_FILE = "config.json"

# Initialize Supabase client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

class CustomerDashboardApp:
    def __init__(self, root, client_id):
        self.root = root
        self.client_id = client_id
        self.root.title("Detalii Client")
        self.root.geometry("1200x800")
        self.root.configure(bg="#d3d3d3")
        self.root.resizable(True, True)  # Allow the window to be resizable

        self.style = ttk.Style()
        self.load_config()
        self.apply_theme()

        # Match DashboardApp styling
        self.style.configure("TLabel", font=("Segoe UI", 11), padding=5)
        self.style.configure("TButton", font=("Segoe UI", 11, "bold"), padding=5)
        self.style.configure("TEntry", font=("Segoe UI", 11))
        self.style.configure("Treeview.Heading", font=("Segoe UI", 12, "bold"), padding=10)

        self.create_widgets()
        self.update_canvas_colors()  # Move this line here
        self.load_client_details()

    def load_config(self):
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, "r") as config_file:
                self.config = json.load(config_file)
        else:
            self.config = {
                "supabase_url": SUPABASE_URL,
                "supabase_key": SUPABASE_KEY,
                "theme": "winnative"
            }

    def save_config(self):
        with open(CONFIG_FILE, "w") as config_file:
            json.dump(self.config, config_file)

    def apply_theme(self):
        theme = self.config.get("theme", "winnative")
        self.style.theme_use(theme)
        self.style.configure("TLabelFrame", background="#f0f0f0", relief="groove")
        self.style.configure("Hover.TLabelFrame", background="#e0e0e0", relief="ridge")

    def update_canvas_colors(self):
        """ Sets the background of Oferte and Comenzi sections to match button color. """
        button_color = self.style.lookup("TButton", "background")  # Get button color
        self.offers_canvas.config(bg=button_color)
        self.orders_canvas.config(bg=button_color)

    def create_widgets(self):
        # --- Entire Window Scrolls Vertically ---
        container = ttk.Frame(self.root)
        container.pack(fill="both", expand=True)

        vsb = ttk.Scrollbar(container, orient="vertical")
        vsb.pack(side="right", fill="y")

        canvas = tk.Canvas(
            container,
            bd=0,
            highlightthickness=0,
            yscrollcommand=vsb.set,
            bg=self.root["bg"]
        )
        canvas.pack(side="left", fill="both", expand=True)
        vsb.config(command=canvas.yview)

        # This is now your "main_frame"
        main_frame = ttk.Frame(canvas, padding=10)
        # Store the window ID so we can resize it later
        self._main_window = canvas.create_window((0, 0), window=main_frame, anchor="nw")

        # Whenever the outer canvas width changes, stretch the inner frame to match
        canvas.bind("<Configure>", lambda e: canvas.itemconfig(self._main_window, width=e.width))

        main_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        # --- Client Details Section ---
        client_details_frame = ttk.Frame(main_frame, padding=10)
        client_details_frame.pack(fill=tk.X, expand=True)
        client_details_frame.grid_columnconfigure(0, weight=1)
        client_details_frame.grid_columnconfigure(1, weight=1)
        client_details_frame.grid_columnconfigure(2, weight=1)

        ttk.Label(client_details_frame, text="Detalii Client", font=("Segoe UI", 10, "bold"), anchor="w").grid(row=0, column=0, sticky="w")
        ttk.Button(client_details_frame, text="Editează detalii client",
                   command=self.edit_selected_client).grid(row=0, column=2,
                                                            padx=(0, 10),
                                                            sticky="e")

        ttk.Label(client_details_frame, text="Nume:", font=("Segoe UI", 10, "bold"), anchor="w").grid(row=1, column=0, sticky="w")
        self.client_name_value = ttk.Label(client_details_frame, text="", font=("Segoe UI", 10), anchor="w")
        self.client_name_value.grid(row=2, column=0, sticky="w", padx=(0, 5))

        ttk.Label(client_details_frame, text="Telefon:", font=("Segoe UI", 10, "bold"), anchor="w").grid(row=1, column=1, sticky="w")
        self.client_phone_value = ttk.Label(client_details_frame, text="", font=("Segoe UI", 10), anchor="w")
        self.client_phone_value.grid(row=2, column=1, sticky="w", padx=(0, 5))

        ttk.Label(client_details_frame, text="Adresă:", font=("Segoe UI", 10, "bold"), anchor="w").grid(row=1, column=2, sticky="w")
        self.client_address_value = ttk.Label(client_details_frame, text="", font=("Segoe UI", 10), anchor="w")
        self.client_address_value.grid(row=2, column=2, sticky="w", padx=(0, 5))

        # --- Vehicles Section ---
        vehicles_frame = ttk.Frame(main_frame, padding=10)
        vehicles_frame.pack(fill=tk.X, expand=True)
        vehicles_frame.grid_columnconfigure(0, weight=1)

        ttk.Label(vehicles_frame, text="Vehiculele Clientului", font=("Segoe UI", 10, "bold"), anchor="w").grid(row=0, column=0, sticky="w")

        self.client_vehicles_list = ttk.Treeview(vehicles_frame, columns=("Marcă", "Model", "An", "VIN", "Înmatriculare", "Talon"), show="headings", height=3)
        self.client_vehicles_list.heading("Marcă", text="Marcă")
        self.client_vehicles_list.heading("Model", text="Model")
        self.client_vehicles_list.heading("An", text="An")
        self.client_vehicles_list.heading("VIN", text="VIN")
        self.client_vehicles_list.heading("Înmatriculare", text="Înmatriculare")
        self.client_vehicles_list.heading("Talon", text="Talon")
        self.client_vehicles_list.grid(row=1, column=0,
                                       padx=10, pady=5,
                                       sticky="nsew")

        self.client_vehicles_list.bind("<Button-3>", self.on_right_click)
        self.client_vehicles_list.bind("<Double-1>", self.on_double_click)

        # --- Offers Section ---
        offers_frame = ttk.Frame(main_frame, padding=10)
        offers_frame.pack(fill=tk.X, expand=True)
        offers_frame.grid_columnconfigure(0, weight=1)
        offers_frame.grid_rowconfigure(1, weight=1)

        offers_label = ttk.Label(offers_frame, text="Oferte", font=("Segoe UI", 10, "bold"), anchor="w")
        offers_label.grid(row=0, column=0, pady=(5, 5), sticky="w")
        view_offers_button = ttk.Button(offers_frame, text="Vezi oferte", command=lambda: open_view_offers_window(self.root))
        view_offers_button.grid(row=0, column=1, pady=(5, 5), sticky="e")

        self.offers_canvas = tk.Canvas(
            offers_frame,
            highlightthickness=0,
            bg=self.style.lookup("TLabelFrame", "background")
        )
        self.offers_canvas.grid(row=1, column=0, columnspan=2, padx=10, pady=5, sticky="nsew")

        self.offers_canvas_frame = ttk.Frame(self.offers_canvas)
        self.offers_canvas.create_window((0, 0), window=self.offers_canvas_frame, anchor="nw")

        offers_scrollbar = ttk.Scrollbar(offers_frame, orient="horizontal", command=self.offers_canvas.xview)
        offers_scrollbar.grid(row=2, column=0, columnspan=2, sticky="ew")
        self.offers_canvas.configure(xscrollcommand=offers_scrollbar.set)

        offers_frame.bind("<Configure>", self.resize_offer_container)
        self.offers_canvas_frame.bind(
            "<Configure>",
            lambda e: self.offers_canvas.configure(scrollregion=self.offers_canvas.bbox("all"))
        )

        self.offers_canvas_frame.grid_columnconfigure(0, weight=1)

        # --- Orders Section ---
        orders_frame = ttk.Frame(main_frame, padding=10)
        orders_frame.pack(fill=tk.X, expand=True)
        orders_frame.grid_columnconfigure(0, weight=1)
        orders_frame.grid_rowconfigure(1, weight=1)

        orders_label = ttk.Label(orders_frame, text="Comenzi", font=("Segoe UI", 10, "bold"), anchor="w")
        orders_label.grid(row=0, column=0, pady=(5, 5), sticky="w")

        payment_button = ttk.Button(orders_frame, text="Plată", command=lambda: AddPaymentWindow(tk.Toplevel(self.root), customer_id=self.client_id))
        payment_button.grid(row=0, column=1, padx=(10, 0), pady=(5, 5), sticky="e")

        view_orders_button = ttk.Button(orders_frame, text="Vezi Comenzi", command=lambda: open_view_orders_window(self.root))
        view_orders_button.grid(row=0, column=2, pady=(5, 5), sticky="e")

        self.orders_canvas = tk.Canvas(
            orders_frame,
            highlightthickness=0,
            bg=self.style.lookup("TLabelFrame", "background")
        )
        self.orders_canvas.grid(row=1, column=0, columnspan=2, padx=10, pady=5, sticky="nsew")

        self.orders_canvas_frame = ttk.Frame(self.orders_canvas)
        self.orders_canvas.create_window((0, 0), window=self.orders_canvas_frame, anchor="nw")

        orders_scrollbar = ttk.Scrollbar(orders_frame, orient="horizontal", command=self.orders_canvas.xview)
        orders_scrollbar.grid(row=2, column=0, columnspan=2, sticky="ew")
        self.orders_canvas.configure(xscrollcommand=orders_scrollbar.set)

        orders_frame.bind("<Configure>", self.resize_order_container)
        self.orders_canvas_frame.bind(
            "<Configure>",
            lambda e: self.orders_canvas.configure(scrollregion=self.orders_canvas.bbox("all"))
        )

        self.orders_canvas_frame.grid_columnconfigure(0, weight=1)

        # Finalize
        self.update_canvas_colors()
        self.resize_offer_container()
        self.resize_order_container()

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

    def load_client_vehicles(self):
        try:
            response = requests.get(f'http://127.0.0.1:5000/vehicles?client_id={self.client_id}')
            if response.status_code == 200:
                vehicles = response.json()
                for vehicle in vehicles:
                    self.client_vehicles_list.insert('', 'end', values=(vehicle['marca'], vehicle['model'], vehicle['an'], vehicle['vin'], vehicle['numar_inmatriculare'], vehicle['image_url']))
            else:
                messagebox.showerror("Eroare", "Nu s-au putut încărca vehiculele clientului.")
        except Exception as e:
            messagebox.showerror("Eroare", f"A apărut o eroare: {e}")

    def load_client_offers(self):
        try:
            response = requests.get(f'http://127.0.0.1:5000/offers?client_id={self.client_id}')
            if response.status_code == 200:
                offers = response.json()
                print(f"Offers loaded: {offers}")  # Debug print

                # Clear previous cards
                for widget in self.offers_canvas_frame.winfo_children():
                    widget.destroy()

                # Display up to 4 offers only
                for index, offer in enumerate(offers[:4]):
                    self.create_offer_card(self.offers_canvas_frame, offer, index)

                self.root.after(100, self.resize_offer_container)  # Adjust UI
            else:
                messagebox.showerror("Eroare", "Nu s-au putut încărca ofertele clientului.")
        except Exception as e:
            messagebox.showerror("Eroare", f"A apărut o eroare: {e}")

    def load_client_orders(self):
        try:
            response = requests.get(f'http://127.0.0.1:5000/orders?client_id={self.client_id}')
            if response.status_code == 200:
                orders = response.json()
                print(f"Orders loaded: {orders}")  # Debug print

                # Clear previous cards
                for widget in self.orders_canvas_frame.winfo_children():
                    widget.destroy()

                # Display up to 4 orders only
                for index, order in enumerate(orders[:4]):
                    self.create_order_card(self.orders_canvas_frame, order, index)

                self.root.after(100, self.resize_order_container)  # Adjust UI
            else:
                messagebox.showerror("Eroare", "Nu s-au putut încărca comenzile clientului.")
        except Exception as e:
            messagebox.showerror("Eroare", f"A apărut o eroare: {e}")

    def edit_selected_client(self):
        # Implement the logic to edit the selected client
        pass

    def create_offer_card(self, parent, offer, column):
        # Copy DashboardApp's offer card exactly
        card_frame = ttk.LabelFrame(parent, text=f"🛍️ Ofertă {offer['offer_number']}", padding=10)
        card_frame.grid(row=0, column=column, padx=10, pady=10, sticky="nsew")

        ttk.Label(card_frame, text=f"📅 Data: {offer['date']}", font=("Segoe UI", 10)).pack(anchor="w")
        ttk.Label(card_frame, text=f"⚙️ Opțiuni: {offer.get('nr_optiuni', '—')}", font=("Segoe UI", 10)).pack(anchor="w")
        ttk.Label(card_frame, text=f"📌 Status: {offer['status']}", font=("Segoe UI", 10)).pack(anchor="w")

        # Buttons row
        btn_frame = ttk.Frame(card_frame)
        btn_frame.pack(anchor="e", pady=5)
        ttk.Button(btn_frame, text="Vizualizează",
                   command=lambda o=offer: open_edit_offer_window(self.root, o['offer_number'])
        ).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Transformă în Comandă",
                   command=lambda o=offer: self.transform_to_order(o)
        ).pack(side="left", padx=5)

        # Only hover to highlight; right-click for menu; double-click to open
        card_frame.bind("<Enter>", lambda e: card_frame.configure(style="Hover.TLabelFrame"))
        card_frame.bind("<Leave>", lambda e: card_frame.configure(style="TLabelFrame"))
        card_frame.bind("<Button-3>", lambda e, of=offer: self.show_offer_context_menu(e, of))
        card_frame.bind("<Double-1>", lambda e, of=offer: open_edit_offer_window(self.root, of['offer_number']))

    def create_order_card(self, parent, order, column):
        # Copy DashboardApp's order card exactly
        card_frame = ttk.LabelFrame(parent, text=f"📦 Comandă {order['order_number']}", padding=10)
        card_frame.grid(row=0, column=column, padx=10, pady=10, sticky="nsew")

        ttk.Label(card_frame, text=f"📅 Data: {order['date']}", font=("Segoe UI", 10)).pack(anchor="w")
        ttk.Label(card_frame, text=f"🛒 Produse: {order.get('nr_produse', '—')}", font=("Segoe UI", 10)).pack(anchor="w")
        ttk.Label(card_frame, text=f"📌 Status: {order['status']}", font=("Segoe UI", 10)).pack(anchor="w")

        # Buttons row
        btn_frame = ttk.Frame(card_frame)
        btn_frame.pack(anchor="e", pady=5)
        ttk.Button(btn_frame, text="Vizualizează",
                   command=lambda o=order: open_edit_order_window(self.root, o['order_number'])
        ).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Return",
                   command=lambda o=order: AddPaymentWindow(tk.Toplevel(self.root), customer_id=o['order_number'])
        ).pack(side="left", padx=5)

        # Only hover to highlight; right-click for menu; double-click to open
        card_frame.bind("<Enter>", lambda e: card_frame.configure(style="Hover.TLabelFrame"))
        card_frame.bind("<Leave>", lambda e: card_frame.configure(style="TLabelFrame"))
        card_frame.bind("<Button-3>", lambda e, od=order: self.show_order_context_menu(e, od))
        card_frame.bind("<Double-1>", lambda e, od=order: open_edit_order_window(self.root, od['order_number']))

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

    def transform_to_order(self, offer):
        try:
            offer_number = offer["offer_number"]
            response = requests.get(f"http://127.0.0.1:5000/offers/{offer_number}")
            if response.status_code != 200:
                raise Exception("Nu s-au putut încărca detaliile ofertei.")

            offer_data = response.json()
            if "categories" not in offer_data or not offer_data["categories"]:
                raise Exception("Ofertă invalidă: lipsesc categoriile.")

            categories = list(offer_data["categories"].keys())
            selected_category = simpledialog.askstring("Selectează Categorie", f"Alege una dintre: {', '.join(categories)}")
            if not selected_category or selected_category not in categories:
                messagebox.showwarning("Anulare", "Conversia în comandă a fost anulată.")
                return

            offer_data["selected_category"] = selected_category
            from new_order import open_new_order_window
            open_new_order_window(self.root, offer_data)
        except Exception as e:
            messagebox.showerror("Eroare", f"A apărut o eroare: {e}")

    def resize_offer_container(self, event=None):
        # Make offers_canvas exactly as tall as its tallest card + padding
        self.root.update_idletasks()
        cards = self.offers_canvas_frame.winfo_children()
        if not cards:
            return self.offers_canvas.configure(height=0)

        heights = [w.winfo_reqheight() for w in cards]
        new_h = max(heights) + 20
        self.offers_canvas.configure(height=new_h)

        # Vertically center each card
        for w in cards:
            pady = (new_h - w.winfo_reqheight()) // 2
            w.grid_configure(pady=pady)

    def resize_order_container(self, event=None):
        # Make orders_canvas exactly as tall as its tallest card + padding
        self.root.update_idletasks()
        cards = self.orders_canvas_frame.winfo_children()
        if not cards:
            return self.orders_canvas.configure(height=0)

        heights = [w.winfo_reqheight() for w in cards]
        new_h = max(heights) + 20
        self.orders_canvas.configure(height=new_h)

        # Vertically center each card
        for w in cards:
            pady = (new_h - w.winfo_reqheight()) // 2
            w.grid_configure(pady=pady)

    def on_right_click(self, event):
        item = event.widget.identify_row(event.y)
        if item:
            event.widget.selection_set(item)
        selected_item = event.widget.selection()
        if selected_item:
            context_menu = Menu(self.root, tearoff=0)
            if event.widget == self.client_vehicles_list:
                vehicle = self.client_vehicles_list.item(selected_item, "values")
                vehicle_id = self.client_vehicles_list.item(selected_item, "tags")[0]
                if vehicle_id:
                    context_menu.add_command(label="🗑️ Șterge Vehicul", command=lambda: self.delete_vehicle(vehicle_id, vehicle[3]))
                    context_menu.add_command(label="📜 Vezi Oferte", command=lambda: self.refresh_client_offers(self.client_list.item(self.client_list.selection(), "values")[0], vehicle_id))
            context_menu.post(event.x_root, event.y_root)

    def on_double_click(self, event):
        selected_item = self.client_vehicles_list.selection()
        if selected_item:
            vehicle = self.client_vehicles_list.item(selected_item, "values")
            vehicle_id = self.client_vehicles_list.item(selected_item, "tags")[0]
            if vehicle_id:
                self.refresh_client_offers(self.client_list.item(self.client_list.selection(), "values")[0], vehicle_id)

    def delete_vehicle(self, vehicle_id, vin):
        if messagebox.askyesno("Confirmare", f"Sunteți sigur că doriți să ștergeți vehiculul cu ID {vehicle_id}?", icon='warning', default='no'):
            try:
                response = requests.delete(f'http://127.0.0.1:5000/delete_vehicle', params={'vehicle_id': vehicle_id})
                if response.status_code == 200:
                    messagebox.showinfo("Succes", "Vehiculul a fost șters cu succes!")
                    self.load_client_vehicles()
                else:
                    messagebox.showerror("Eroare", "Ștergerea vehiculului a eșuat!")
            except Exception as e:
                messagebox.showerror("Eroare", f"A apărut o eroare: {e}")

    def refresh_client_offers(self, client_name, vehicle_id=None):
        try:
            client_response = requests.get(f'http://127.0.0.1:5000/clients?name={client_name}')
            client_data = client_response.json()
            if client_response.status_code == 200 and client_data:
                client_id = client_data[0]['id']
                if vehicle_id:
                    response = requests.get(f'http://127.0.0.1:5000/offers?client_id={client_id}&vehicle_id={vehicle_id}')
                else:
                    response = requests.get(f'http://127.0.0.1:5000/offers?client_id={client_id}')
                offers = response.json()

                # Clear the existing offers list
                for widget in self.offers_canvas_frame.winfo_children():
                    widget.destroy()

                # Ensure the parent frame has 3 equal columns
                self.offers_canvas_frame.grid_columnconfigure(0, weight=1)
                self.offers_canvas_frame.grid_columnconfigure(1, weight=1)
                self.offers_canvas_frame.grid_columnconfigure(2, weight=1)

                # Insert the updated offers list
                total_offers = len(offers)
                if (total_offers == 1):
                    self.create_offer_card(self.offers_canvas_frame, offers[0], 0)  # Left
                elif (total_offers == 2):
                    self.create_offer_card(self.offers_canvas_frame, offers[0], 0)  # Left
                    self.create_offer_card(self.offers_canvas_frame, offers[1], 1)  # Center
                elif (total_offers == 3):
                    self.create_offer_card(self.offers_canvas_frame, offers[0], 0)  # Left
                    self.create_offer_card(self.offers_canvas_frame, offers[1], 1)  # Center
                    self.create_offer_card(self.offers_canvas_frame, offers[2], 2)  # Right
                else:
                    for index, offer in enumerate(offers[:4]):  # Show max 4 cards
                        self.create_offer_card(self.offers_canvas_frame, offer, index)

                # Add the "View More" card at the end
                self.create_view_more_offer_card(self.offers_canvas_frame, 4)
                self.root.after(100, self.resize_offer_container)  # Small delay to ensure UI update
            else:
                messagebox.showerror("Eroare", "Clientul nu a fost găsit.")
        except Exception as e:
            messagebox.showerror("Eroare", f"A apărut o eroare: {e}")

def open_add_payment_window_with_customer(client_id):
    payment_window = tk.Toplevel(root)
    AddPaymentWindow(payment_window, customer_id=client_id)

def open_customer_dashboard(client_id):
    """Open the customer dashboard for a specific client."""
    script_path = os.path.join(os.path.dirname(__file__), "customer_dashboard.py")
    if not os.path.exists(script_path):
        raise FileNotFoundError(f"Customer dashboard script not found at {script_path}")
    subprocess.Popen(["python", script_path, str(client_id)], shell=True)

if __name__ == "__main__":
    if len(sys.argv) > 1:
        client_id = sys.argv[1]
    else:
        client_id = None

    root = tk.Tk()
    app = CustomerDashboardApp(root, client_id)
    root.mainloop()
