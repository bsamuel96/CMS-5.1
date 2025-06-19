import tkinter as tk
from tkinter import ttk, messagebox, Toplevel, simpledialog
import requests
import json  # NEW
from edit_offer import open_edit_offer_window  # Import the function to open the edit offer window
from new_order import open_new_order_window  # Import the function to open the new order window

class ViewOffersApp:
    def __init__(self, root, client_id=None):
        if not isinstance(root, Toplevel):
            raise ValueError("Expected a Toplevel window for 'root'.")
        self.root = root
        self.client_id = client_id  # Store client_id as an instance attribute
        self.root.title("Vezi Oferte")
        self.root.geometry("1200x700")  # Standardized window size
        self.root.configure(bg="#d3d3d3")  # Match the application's background color

        # Enable the close (X) button
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

        # Center the window on the screen
        self.center_window()

        self.create_widgets()
        self.fetch_offers()  # Fetch offers for the selected client

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
        ttk.Label(header_frame, text="Oferte Disponibile", font=("Segoe UI", 16, "bold"), anchor="center").pack()

        # Main content area
        self.main_frame = ttk.Frame(self.root, padding="10")
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        self.offers_canvas = tk.Canvas(self.main_frame, bg="#d3d3d3", highlightthickness=0)
        self.offers_scrollbar = ttk.Scrollbar(self.main_frame, orient="vertical", command=self.offers_canvas.yview)
        self.offers_frame = ttk.Frame(self.offers_canvas, padding="10")

        self.offers_frame.bind(
            "<Configure>",
            lambda e: self.offers_canvas.configure(
                scrollregion=self.offers_canvas.bbox("all")
            )
        )

        self.offers_canvas.create_window((0, 0), window=self.offers_frame, anchor="nw")
        self.offers_canvas.configure(yscrollcommand=self.offers_scrollbar.set)

        self.offers_canvas.pack(side="left", fill="both", expand=True)
        self.offers_scrollbar.pack(side="right", fill="y")

    def fetch_offers(self):
        """Fetch offers for the given client_id and display them."""
        try:
            if not self.client_id:
                messagebox.showerror("Eroare", "ID-ul clientului nu este specificat.")
                return

            # Fetch offers for the client
            response = requests.get('http://127.0.0.1:5000/offers', params={'client_id': self.client_id})
            if response.status_code == 200:
                offers = response.json()
                if not offers:
                    messagebox.showinfo("Informație", "Nu există oferte pentru acest client.")
                    return

                # Display the fetched offers
                self.display_offers(offers)
            else:
                messagebox.showerror("Eroare", f"Nu s-au putut încărca ofertele. Cod eroare: {response.status_code}")
        except Exception as e:
            messagebox.showerror("Eroare", f"A apărut o eroare: {e}")

    def display_offers(self, offers):
        """Display the fetched offers in the UI."""
        for widget in self.offers_frame.winfo_children():
            widget.destroy()

        # Ensure the parent frame has 3 equal columns
        self.offers_frame.grid_columnconfigure(0, weight=1)
        self.offers_frame.grid_columnconfigure(1, weight=1)
        self.offers_frame.grid_columnconfigure(2, weight=1)

        # Insert the updated offers list
        for index, offer in enumerate(offers):
            self.create_offer_card(self.offers_frame, offer, index % 3, index // 3)

    def create_offer_card(self, parent, offer, column, row):
        """Create a card for an offer."""
        card_frame = ttk.Frame(parent, relief="raised", borderwidth=2, padding="10", style="TFrame")
        card_frame.grid(row=row, column=column, padx=10, pady=10, sticky="nsew")

        ttk.Label(card_frame, text=f"🛍️ Ofertă {offer['offer_number']}", font=("Segoe UI", 12, "bold")).pack(anchor="w")
        ttk.Label(card_frame, text=f"📅 Data: {offer['date']}", font=("Segoe UI", 10)).pack(anchor="w")
        ttk.Label(card_frame, text=f"📌 Status: {offer['status']}", font=("Segoe UI", 10)).pack(anchor="w")

        button_frame = ttk.Frame(card_frame, style="TFrame")
        button_frame.pack(anchor="e", pady=5)

        ttk.Button(button_frame, text="Vizualizează", command=lambda: self.view_offer(offer)).pack(side="left", padx=5)
        ttk.Button(button_frame, text="Transformă în Comandă", command=lambda: self.transform_to_order(offer)).pack(side="left", padx=5)

    def view_offer(self, offer):
        """Open the edit offer window for the selected offer."""
        open_edit_offer_window(self.root, offer['offer_number'])

    def transform_to_order(self, offer):
        try:
            offer_number = offer["offer_number"]
            print("[DEBUG] Calling /offers/ with offer_number:", offer_number)

            response = requests.get(f"http://127.0.0.1:5000/offers/{offer_number}")
            if response.status_code != 200:
                raise Exception("Nu s-au putut încărca detaliile ofertei.")

            offer_data = response.json()
            print("[DEBUG] Full offer data received:", offer_data)

            if "categories" not in offer_data or not offer_data["categories"]:
                raise Exception("Ofertă invalidă: lipsesc categoriile.")

            # Ask user to select category
            category_choices = list(offer_data["categories"].keys())
            selected_category = simpledialog.askstring("Categorie", f"Alege categoria ({', '.join(category_choices)}):")
            if not selected_category or selected_category not in category_choices:
                messagebox.showwarning("Anulare", "Conversia în comandă a fost anulată.")
                return

            # Inject category choice into offer_data and open order window
            offer_data["selected_category"] = selected_category
            open_new_order_window(self.root, offer_data)

        except Exception as e:
            messagebox.showerror("Eroare", f"A apărut o eroare: {e}")

def open_view_offers_window(root, client_id=None):
    """Open the 'Vezi Oferte' window for a specific client."""
    if not client_id:
        messagebox.showerror("Eroare", "ID-ul clientului nu este specificat.")
        return

    try:
        # Create the Toplevel window
        window = tk.Toplevel(root)
        window.resizable(True, False)  # Allow vertical resizing only
        app = ViewOffersApp(window, client_id=client_id)  # Pass client_id to ViewOffersApp
        window.mainloop()
    except Exception as e:
        messagebox.showerror("Eroare", f"A apărut o eroare: {e}")

def open_view_offers_window_with_offers(root, offers):
    """Open the 'Vezi Oferte' window with a predefined list of offers."""
    try:
        # Create the Toplevel window
        window = tk.Toplevel(root)
        window.title("Vezi Oferte")
        window.geometry("1200x700")
        window.configure(bg="#d3d3d3")
        window.resizable(True, False)  # Allow vertical resizing only

        # Create the ViewOffersApp instance and pass the offers
        app = ViewOffersApp(window)
        app.display_offers(offers)  # Use the existing method to display the offers
        window.mainloop()
    except Exception as e:
        messagebox.showerror("Eroare", f"A apărut o eroare: {e}")