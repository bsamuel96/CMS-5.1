import sys  # Add this import to handle command-line arguments
import re
import tkinter as tk
from tkinter import ttk, messagebox
import requests
from ttkwidgets.autocomplete import AutocompleteCombobox

class EditClientApp:
    def __init__(self, root, client_id):
        print(f"[DEBUG] Initializing EditClientApp with client_id: {client_id}")  # Debug statement
        self.root = root
        self.client_id = client_id
        self.root.title("Editează Client")
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

        # Set up our close-confirmation first
        self.setup_close_protocol()
        # Now we can safely build all widgets that refer to self._on_close
        self.create_widgets()
        self.fetch_client_details()

    def setup_close_protocol(self):
        """Confirm on window 'X' or Cancel button."""
        def on_close():
            if messagebox.askyesno("Confirmare", "Renunți la modificări?"):
                self.root.destroy()
        self.root.protocol("WM_DELETE_WINDOW", on_close)
        self._on_close = on_close

    def create_widgets(self):
        print("[DEBUG] Creating widgets for EditClientApp")  # Debug statement
        self.main_frame = ttk.Frame(self.root, padding="20", style="TFrame")
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(self.main_frame, text="Nume:", style="TLabel").grid(row=0, column=0, padx=10, pady=10, sticky="E")
        self.name_entry = ttk.Entry(self.main_frame, style="TEntry")
        self.name_entry.grid(row=0, column=1, padx=10, pady=10, sticky="W")

        # Telefon
        ttk.Label(self.main_frame, text="Telefon:", style="TLabel")\
            .grid(row=1, column=0, padx=10, pady=10, sticky="E")
        self.phone_entry = ttk.Entry(self.main_frame, style="TEntry")
        self.phone_entry.grid(row=1, column=1, padx=10, pady=10, sticky="W")

        ttk.Label(self.main_frame, text="Adresă:", style="TLabel").grid(row=2, column=0, padx=10, pady=10, sticky="E")
        self.address_entry = ttk.Entry(self.main_frame, style="TEntry")
        self.address_entry.grid(row=2, column=1, padx=10, pady=10, sticky="W")

        ttk.Label(self.main_frame, text="CNP:", style="TLabel").grid(row=3, column=0, padx=10, pady=10, sticky="E")
        self.cnp_entry = ttk.Entry(self.main_frame, style="TEntry")
        self.cnp_entry.grid(row=3, column=1, padx=10, pady=10, sticky="W")

        # Județ
        ttk.Label(self.main_frame, text="Județ:", style="TLabel")\
            .grid(row=4, column=0, padx=10, pady=10, sticky="E")
        self.judet_cb = AutocompleteCombobox(self.main_frame, width=30, style="TEntry")
        self.judet_cb.grid(row=4, column=1, padx=10, pady=10, sticky="W")

        # Localitate
        ttk.Label(self.main_frame, text="Localitate:", style="TLabel")\
            .grid(row=5, column=0, padx=10, pady=10, sticky="E")
        self.localitate_cb = AutocompleteCombobox(self.main_frame, width=30, style="TEntry")
        self.localitate_cb.grid(row=5, column=1, padx=10, pady=10, sticky="W")

        button_frame = ttk.Frame(self.main_frame, style="TFrame")
        button_frame.grid(row=6, column=0, columnspan=2, pady=20)

        self.save_button = ttk.Button(
            button_frame, text="💾 Salvează",
            command=self.save_client_details, style="TButton")
        self.save_button.pack(side="left", padx=10)

        self.cancel_button = ttk.Button(
            button_frame, text="❌ Anulează",
            command=self._on_close, style="TButton")
        self.cancel_button.pack(side="left", padx=10)

    def fetch_client_details(self):
        """Fetch client details from the server and populate the fields."""
        print(f"[DEBUG] Fetching client details for client_id: {self.client_id}")  # Debug statement
        try:
            response = requests.get(f'http://127.0.0.1:5000/clients/{self.client_id}')
            print(f"[DEBUG] Response status code: {response.status_code}")  # Debug statement
            if response.status_code == 200:
                client_data = response.json()
                print(f"[DEBUG] Client data fetched: {client_data}")  # Debug statement

                # Name
                self.name_entry.insert(0, client_data.get("nume", ""))

                # Telefon: strip out anything except digits
                raw_tel = client_data.get("telefon", "")
                clean_tel = re.sub(r"\D+", "", raw_tel)
                self.phone_entry.insert(0, clean_tel)

                self.address_entry.insert(0, client_data.get("adresa", ""))
                self.cnp_entry.insert(0, client_data.get("cnp", ""))

                # Load counties → populate Județ combobox
                judete = requests.get('http://127.0.0.1:5000/get_judete').json()
                self.judet_cb.set_completion_list(judete)

                # When Județ changes, fetch Localități
                def on_judet_change(evt=None):
                    sel = self.judet_cb.get()
                    locs = requests.get(f'http://127.0.0.1:5000/get_localitati/{sel}').json()
                    self.localitate_cb.set_completion_list(locs)
                for seq in ("<<ComboboxSelected>>", "<FocusOut>", "<Return>"):
                    self.judet_cb.bind(seq, on_judet_change)

                # Preselect the stored Județ & trigger Localități load
                stored_j = client_data.get("judet") or ""
                self.judet_cb.set(stored_j)
                on_judet_change()

                # Preselect the stored Localitate
                self.localitate_cb.set(client_data.get("localitate", ""))
            else:
                print(f"[ERROR] Failed to fetch client details. Status code: {response.status_code}")  # Debug statement
                messagebox.showerror("Eroare", "Nu s-au putut încărca detaliile clientului.")
        except Exception as e:
            print(f"[ERROR] Exception occurred while fetching client details: {e}")  # Debug statement
            messagebox.showerror("Eroare", f"A apărut o eroare: {e}")

    def save_client_details(self):
        """Save the updated client details to the server."""
        print("[DEBUG] Saving client details")  # Debug statement
        try:
            updated_data = {
                "nume": self.name_entry.get(),
                "telefon": self.phone_entry.get(),
                "adresa": self.address_entry.get(),
                "cnp": self.cnp_entry.get(),
                "localitate": self.localitate_cb.get(),
                "judet": self.judet_cb.get()
            }
            print(f"[DEBUG] Updated data to save: {updated_data}")  # Debug statement
            response = requests.patch(f'http://127.0.0.1:5000/clients/{self.client_id}', json=updated_data)
            print(f"[DEBUG] Response status code: {response.status_code}")  # Debug statement
            if response.status_code == 200:
                print("[DEBUG] Client details updated successfully")  # Debug statement
                messagebox.showinfo("Succes", "Detaliile clientului au fost actualizate cu succes!")
                
                # Refresh the parent window if it has a `refresh_client_list` method
                if hasattr(self.root.master, 'refresh_client_list'):
                    print("[DEBUG] Refreshing client list in parent window")  # Debug statement
                    self.root.master.refresh_client_list()
                
                self.root.destroy()
            else:
                print(f"[ERROR] Failed to update client details. Status code: {response.status_code}")  # Debug statement
                messagebox.showerror("Eroare", "Actualizarea detaliilor clientului a eșuat.")
        except Exception as e:
            print(f"[ERROR] Exception occurred while saving client details: {e}")  # Debug statement
            messagebox.showerror("Eroare", f"A apărut o eroare: {e}")

def open_edit_client_window(root, client_id):
    """Open the Edit Client window."""
    print(f"[DEBUG] Opening Edit Client window for client_id: {client_id}")  # Debug statement
    try:
        window = tk.Toplevel(root)
        EditClientApp(window, client_id)
        window.mainloop()
    except Exception as e:
        print(f"[ERROR] Exception occurred while opening Edit Client window: {e}")  # Debug statement
        messagebox.showerror("Eroare", f"A apărut o eroare: {e}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        client_id = sys.argv[1]
        print(f"[DEBUG] Received client_id: {client_id}")  # Debug statement
        root = tk.Tk()
        app = EditClientApp(root, client_id)
        root.mainloop()
    else:
        print("[ERROR] No client_id passed to edit_client.py")  # Debug statement
        messagebox.showerror("Eroare", "Nu a fost furnizat un ID de client!")