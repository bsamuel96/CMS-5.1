import sys
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import requests
from drive_upload import upload_file_to_drive  # Ensure this module is available

class EditVehicleApp:
    def __init__(self, root, vehicle_id):
        print(f"[DEBUG] Initializing EditVehicleApp with vehicle_id: {vehicle_id}")  # Debug statement
        self.root = root
        self.vehicle_id = vehicle_id
        self.image_url = ""  # Hidden image URL storage
        self.root.title("Editează Vehicul")
        self.root.geometry("500x400")
        self.root.configure(bg="#d3d3d3")

        # Center the window on the screen
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() - self.root.winfo_reqwidth()) // 2
        y = (self.root.winfo_screenheight() - self.root.winfo_reqheight()) // 2
        self.root.geometry(f"+{x}+{y}")

        self.style = ttk.Style()
        self.style.configure("TLabel", font=("Segoe UI", 11), background="#d3d3d3")
        self.style.configure("TButton", font=("Segoe UI", 11, "bold"))
        self.style.configure("TEntry", font=("Segoe UI", 11))
        self.style.configure("TFrame", background="#d3d3d3")

        self.create_widgets()
        self.fetch_vehicle_details()

    def create_widgets(self):
        print("[DEBUG] Creating widgets for EditVehicleApp")  # Debug statement
        self.main_frame = ttk.Frame(self.root, padding="20", style="TFrame")
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(self.main_frame, text="Marcă:", style="TLabel").grid(row=0, column=0, padx=10, pady=10, sticky="E")
        self.brand_entry = ttk.Entry(self.main_frame, style="TEntry")
        self.brand_entry.grid(row=0, column=1, padx=10, pady=10, sticky="W")

        ttk.Label(self.main_frame, text="Model:", style="TLabel").grid(row=1, column=0, padx=10, pady=10, sticky="E")
        self.model_entry = ttk.Entry(self.main_frame, style="TEntry")
        self.model_entry.grid(row=1, column=1, padx=10, pady=10, sticky="W")

        ttk.Label(self.main_frame, text="An:", style="TLabel").grid(row=2, column=0, padx=10, pady=10, sticky="E")
        self.year_entry = ttk.Entry(self.main_frame, style="TEntry")
        self.year_entry.grid(row=2, column=1, padx=10, pady=10, sticky="W")

        ttk.Label(self.main_frame, text="VIN:", style="TLabel").grid(row=3, column=0, padx=10, pady=10, sticky="E")
        self.vin_entry = ttk.Entry(self.main_frame, style="TEntry")
        self.vin_entry.grid(row=3, column=1, padx=10, pady=10, sticky="W")

        ttk.Label(self.main_frame, text="Număr Înmatriculare:", style="TLabel").grid(row=4, column=0, padx=10, pady=10, sticky="E")
        self.registration_entry = ttk.Entry(self.main_frame, style="TEntry")
        self.registration_entry.grid(row=4, column=1, padx=10, pady=10, sticky="W")

        # Add the "Încarcă Imagine" button
        ttk.Button(self.main_frame, text="Încarcă Imagine", command=self.handle_image_upload, style="TButton").grid(
            row=5, column=1, padx=10, pady=(0, 10), sticky="W"
        )

        button_frame = ttk.Frame(self.main_frame, style="TFrame")
        button_frame.grid(row=6, column=0, columnspan=2, pady=20)

        self.save_button = ttk.Button(button_frame, text="💾 Salvează", command=self.save_vehicle_details, style="TButton")
        self.save_button.pack(side="left", padx=10)

        self.cancel_button = ttk.Button(button_frame, text="❌ Anulează", command=self.root.destroy, style="TButton")
        self.cancel_button.pack(side="left", padx=10)

    def handle_image_upload(self):
        """Handle image upload to the drive."""
        file_path = filedialog.askopenfilename(filetypes=[("Imagini", "*.jpg *.jpeg *.png")])
        if not file_path:
            return

        # Show a loading popup while uploading
        loading = tk.Toplevel(self.root)
        loading.title("Se încarcă imaginea...")
        loading.geometry("300x120")
        loading.transient(self.root)
        loading.grab_set()

        ttk.Label(loading, text="Se încarcă imaginea...\nVă rugăm să așteptați.", font=("Segoe UI", 11)).pack(pady=20)
        loading.update()

        try:
            uploaded_link = upload_file_to_drive(file_path)
            self.image_url = uploaded_link  # Store the link
            loading.destroy()
            messagebox.showinfo("Succes", "Imaginea a fost încărcată cu succes!")
        except Exception as e:
            loading.destroy()
            messagebox.showerror("Eroare", f"Nu s-a putut încărca imaginea:\n{e}")

    def fetch_vehicle_details(self):
        """Fetch vehicle details from the server and populate the fields."""
        print(f"[DEBUG] Fetching vehicle details for vehicle_id: {self.vehicle_id}")  # Debug statement
        try:
            response = requests.get(f'http://127.0.0.1:5000/vehicles/{self.vehicle_id}')
            print(f"[DEBUG] Response status code: {response.status_code}")  # Debug statement
            if response.status_code == 200:
                vehicle_data = response.json()
                print(f"[DEBUG] Vehicle data fetched: {vehicle_data}")  # Debug statement
                self.populate_vehicle_fields(vehicle_data)
            elif response.status_code == 404:
                print("[ERROR] Vehicle not found. Fetching vehicles for client_id.")  # Debug statement
                self.fetch_vehicles_for_client()
            else:
                print(f"[ERROR] Failed to fetch vehicle details. Status code: {response.status_code}")  # Debug statement
                messagebox.showerror("Eroare", "Nu s-au putut încărca detaliile vehiculului.")
        except Exception as e:
            print(f"[ERROR] Exception occurred while fetching vehicle details: {e}")  # Debug statement
            messagebox.showerror("Eroare", f"A apărut o eroare: {e}")

    def fetch_vehicles_for_client(self):
        """Fetch all vehicles for the client and allow the user to select one."""
        try:
            client_id = self.vehicle_id  # Assuming vehicle_id is used as client_id in this case
            response = requests.get(f'http://127.0.0.1:5000/vehicles', params={'client_id': client_id})
            print(f"[DEBUG] Response status code: {response.status_code}")  # Debug statement
            if response.status_code == 200:
                vehicles = response.json()
                print(f"[DEBUG] Retrieved vehicles: {vehicles}")  # Debug statement
                if vehicles:
                    self.show_vehicle_selection_dialog(vehicles)
                else:
                    messagebox.showerror("Eroare", "Nu există vehicule asociate acestui client.")
                    self.root.destroy()
            else:
                print(f"[ERROR] Failed to fetch vehicles. Status code: {response.status_code}")  # Debug statement
                messagebox.showerror("Eroare", "Nu s-au putut încărca vehiculele clientului.")
        except Exception as e:
            print(f"[ERROR] Exception occurred while fetching vehicles: {e}")  # Debug statement
            messagebox.showerror("Eroare", f"A apărut o eroare: {e}")

    def show_vehicle_selection_dialog(self, vehicles):
        """Show a dialog to select a vehicle from the list."""
        selection_window = tk.Toplevel(self.root)
        selection_window.title("Vehiculele Clientului")
        selection_window.geometry("500x500")
        selection_window.configure(bg="#d3d3d3")

        ttk.Label(selection_window, text="Selectați un vehicul:", style="TLabel").pack(pady=10)

        vehicle_listbox = tk.Listbox(selection_window, font=("Segoe UI", 11), height=10)
        vehicle_listbox.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        vehicle_map = {}
        for vehicle in vehicles:
            display_text = f"{vehicle['marca']} {vehicle['model']} ({vehicle['numar_inmatriculare']})"
            vehicle_listbox.insert(tk.END, display_text)
            vehicle_map[display_text] = vehicle

        def on_select():
            selected_index = vehicle_listbox.curselection()
            if selected_index:
                selected_vehicle = vehicle_listbox.get(selected_index)
                vehicle_data = vehicle_map[selected_vehicle]
                self.vehicle_id = vehicle_data['id']  # Update the vehicle_id
                print(f"[DEBUG] Updated vehicle_id: {self.vehicle_id}")  # Debug statement
                selection_window.destroy()
                self.populate_vehicle_fields(vehicle_data)
            else:
                messagebox.showerror("Eroare", "Selectați un vehicul din listă.")

        ttk.Button(selection_window, text="Selectează", command=on_select, style="TButton").pack(pady=10)

    def populate_vehicle_fields(self, vehicle_data):
        """Populate the fields with vehicle data."""
        self.brand_entry.delete(0, tk.END)
        self.brand_entry.insert(0, vehicle_data.get("marca", ""))
        self.model_entry.delete(0, tk.END)
        self.model_entry.insert(0, vehicle_data.get("model", ""))
        self.year_entry.delete(0, tk.END)
        self.year_entry.insert(0, vehicle_data.get("an", ""))
        self.vin_entry.delete(0, tk.END)
        self.vin_entry.insert(0, vehicle_data.get("vin", ""))
        self.registration_entry.delete(0, tk.END)
        self.registration_entry.insert(0, vehicle_data.get("numar_inmatriculare", ""))
        print(f"[DEBUG] Populated fields with vehicle data: {vehicle_data}")  # Debug statement

    def save_vehicle_details(self):
        """Save the updated vehicle details to the server."""
        print("[DEBUG] Saving vehicle details")  # Debug statement
        try:
            updated_data = {
                "marca": self.brand_entry.get(),
                "model": self.model_entry.get(),
                "an": self.year_entry.get(),
                "vin": self.vin_entry.get(),
                "numar_inmatriculare": self.registration_entry.get()
            }
            # Only add image_url if it was updated
            if self.image_url:
                updated_data["image_url"] = self.image_url

            print(f"[DEBUG] Updated data to save: {updated_data}")  # Debug statement

            # Send the PATCH request to update the vehicle details
            response = requests.patch(f'http://127.0.0.1:5000/vehicles/{self.vehicle_id}', json=updated_data)
            print(f"[DEBUG] Response status code: {response.status_code}")  # Debug statement

            if response.status_code == 200:
                print("[DEBUG] Vehicle details updated successfully")  # Debug statement
                messagebox.showinfo("Succes", "Detaliile vehiculului au fost actualizate cu succes!")

                # Refresh the parent window if it has a `refresh_client_vehicles` method
                if hasattr(self.root.master, 'refresh_client_vehicles'):
                    print("[DEBUG] Refreshing vehicle list in parent window")  # Debug statement
                    client_name = self.root.master.client_list.item(self.root.master.client_list.selection(), "values")[0]
                    self.root.master.refresh_client_vehicles(client_name)

                self.root.destroy()
            else:
                print(f"[ERROR] Failed to update vehicle details. Status code: {response.status_code}")  # Debug statement
                messagebox.showerror("Eroare", "Actualizarea detaliilor vehiculului a eșuat.")
        except Exception as e:
            print(f"[ERROR] Exception occurred while saving vehicle details: {e}")  # Debug statement
            messagebox.showerror("Eroare", f"A apărut o eroare: {e}")

def open_edit_vehicle_window(root, vehicle_id):
    """Open the Edit Vehicle window."""
    print(f"[DEBUG] Opening Edit Vehicle window for vehicle_id: {vehicle_id}")  # Debug statement
    try:
        window = tk.Toplevel(root)
        EditVehicleApp(window, vehicle_id)
        window.mainloop()
    except Exception as e:
        print(f"[ERROR] Exception occurred while opening Edit Vehicle window: {e}")  # Debug statement
        messagebox.showerror("Eroare", f"A apărut o eroare: {e}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        vehicle_id = sys.argv[1]
        print(f"[DEBUG] Received vehicle_id: {vehicle_id}")  # Debug statement
        root = tk.Tk()
        app = EditVehicleApp(root, vehicle_id)
        root.mainloop()
    else:
        print("[ERROR] No vehicle_id passed to edit_vehicle.py")  # Debug statement
        messagebox.showerror("Eroare", "Nu a fost furnizat un ID de vehicul!")
