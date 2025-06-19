import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import requests
import tksheet
from tkcalendar import DateEntry
from pdf import PDFGenerator  # Import the PDFGenerator class

def open_edit_offer_window(root, offer_number):
    """Open the Edit Offer window."""
    print(f"[DEBUG] Opening Edit Offer window for offer_number: {offer_number}")
    try:
        # Call the updated Supabase RPC function to get offer details
        response = requests.get(
            f"http://127.0.0.1:5000/rpc/get_offer_details",
            params={"p_offer_number": offer_number}
        )
        print(f"[DEBUG] Response status code: {response.status_code}")

        if response.status_code == 404:
            messagebox.showerror("Eroare", f"Oferta cu numărul {offer_number} nu a fost găsită.")
            return

        if response.status_code == 200:
            offer_details = response.json()
            print(f"[DEBUG] Offer details fetched: {offer_details}")

            if not offer_details:
                print(f"[ERROR] No details found for offer_number: {offer_number}")
                messagebox.showerror("Eroare", f"Nu s-au găsit detalii pentru oferta cu numărul {offer_number}.")
                return

            # Create the Toplevel window
            if root is None:
                print("[ERROR] Root is None. Cannot create Toplevel window.")
                return

            window = tk.Toplevel(root)
            print(f"[DEBUG] Toplevel window created: {window}")
            window.title(f"Editează Ofertă {offer_number}")
            window.geometry("1000x600")
            window.transient(root)
            window.grab_set()
            window.resizable(True, True)

            # Center the window on the screen
            window.update_idletasks()
            x = (window.winfo_screenwidth() - window.winfo_reqwidth()) // 2
            y = (window.winfo_screenheight() - window.winfo_reqheight()) // 2
            window.geometry(f"+{x}+{y}")
            print(f"[DEBUG] Window geometry set to: {window.geometry()}")

            # Add content to the window
            content_frame = ttk.Frame(window, padding=10)
            content_frame.pack(fill=tk.BOTH, expand=True)
            add_edit_offer_content(content_frame, window, offer_details)
        else:
            print(f"[ERROR] Failed to fetch offer details. Status code: {response.status_code}")
            messagebox.showerror("Eroare", f"Nu s-au găsit detalii pentru oferta cu numărul {offer_number}.")
    except Exception as e:
        print(f"[ERROR] Exception occurred while opening Edit Offer window: {e}")
        messagebox.showerror("Eroare", f"A apărut o eroare: {e}")

def add_edit_offer_content(frame, window, offer_details):
    try:
        print(f"Adding offer content with details: {offer_details}")  # Debug print
        vehicle_dropdown = ttk.Combobox(frame, state="readonly")
        vehicle_dropdown.vehicle_ids = {}

        def fetch_vehicle_details(vehicle_id):
            try:
                response = requests.get(f'http://127.0.0.1:5000/vehicles?id=eq.{vehicle_id}')
                vehicle_data = response.json()
                if response.status_code == 200 and vehicle_data:
                    vehicle = vehicle_data[0]
                    return f"{vehicle['marca']} {vehicle['model']} ({vehicle['numar_inmatriculare']})"
                else:
                    return "Unknown Vehicle"
            except Exception as e:
                messagebox.showerror("Eroare", f"A apărut o eroare: {e}")
                return "Unknown Vehicle"

        def refresh_vehicle_dropdown(client_id):
            try:
                response = requests.get(f'http://127.0.0.1:5000/vehicles?client_id={client_id}')
                vehicles = response.json()
                if vehicles is not None:
                    vehicle_dropdown['values'] = [f"{v['marca']} {v['model']} ({v['numar_inmatriculare']})" for v in vehicles]
                    vehicle_dropdown.vehicle_ids = {f"{v['marca']} {v['model']} ({v['numar_inmatriculare']})": v['id'] for v in vehicles}
                else:
                    vehicle_dropdown['values'] = []
                    vehicle_dropdown.vehicle_ids = {}
            except Exception as e:
                messagebox.showerror("Eroare", f"A apărut o eroare: {e}")

        def open_category_window(category, prefilled_data=None):
            try:
                category_window = tk.Toplevel(window)
                category_window.title(f"Produse - {category}")
                category_window.geometry("1000x600")
                # Add additional logic for the category window here
            except Exception as e:
                print(f"[ERROR] Exception occurred while opening category window: {e}")
                messagebox.showerror("Eroare", f"A apărut o eroare: {e}")
    except Exception as e:
        print(f"[ERROR] Exception occurred while adding offer content: {e}")
        messagebox.showerror("Eroare", f"A apărut o eroare: {e}")

def submit_offer(offer_details):
    """Submit the offer details to the server."""
    try:
        response = requests.post("http://127.0.0.1:5000/add_offer", json=offer_details)
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Failed to submit offer: {response.status_code}")
    except Exception as e:
        print(f"[ERROR] {e}")
        raise