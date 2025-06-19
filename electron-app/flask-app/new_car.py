import tkinter as tk
from tkinter import ttk, messagebox, filedialog, Toplevel  # Add filedialog and Toplevel imports
import requests
from drive_upload import upload_file_to_drive  # Ensure this is imported
import json
import datetime

# Load the list of makes and models
try:
    with open("resources/marci_modele_refined.json", "r", encoding="utf-8") as f:
        make_model_data = json.load(f)
except FileNotFoundError:
    print("Warning: 'resources/marci_modele_refined.json' not found. Using an empty dictionary as fallback.")
    make_model_data = {}

def open_add_vehicle_window(root, client_id=None, client_name=None):
    window = tk.Toplevel(root)
    window.title("Adaugă Vehicul")
    window.geometry("400x400")
    window.transient(root)
    window.grab_set()
    window.resizable(False, False)

    # Center the window on the screen
    window.update_idletasks()
    x = (window.winfo_screenwidth() - window.winfo_reqwidth()) // 2
    y = (window.winfo_screenheight() - window.winfo_reqheight()) // 2
    window.geometry(f"+{x}+{y}")

    content_frame = ttk.Frame(window, padding=10)
    content_frame.pack(fill=tk.BOTH, expand=True)

    add_vehicle_content(content_frame, window, client_id, client_name, root)

def add_vehicle_content(frame, window, client_id, client_name, root):
    if client_id is None:
        from client_search import open_client_search_window
        open_client_search_window(frame.master, lambda cid, cname: add_vehicle_content(frame, window, cid, cname, root))
        return

    ttk.Label(frame, text=f"Client: {client_name}").grid(row=0, column=0, columnspan=2, padx=10, pady=5, sticky="W")

    ttk.Label(frame, text="Marcă:").grid(row=1, column=0, padx=10, pady=5, sticky="E")
    marca_var = tk.StringVar()
    marca_combobox = ttk.Combobox(frame, textvariable=marca_var, values=sorted(make_model_data.keys()))
    marca_combobox.grid(row=1, column=1, padx=10, pady=5, sticky="W")

    ttk.Label(frame, text="Model:").grid(row=2, column=0, padx=10, pady=5, sticky="E")
    model_var = tk.StringVar()
    model_combobox = ttk.Combobox(frame, textvariable=model_var)
    model_combobox.grid(row=2, column=1, padx=10, pady=5, sticky="W")

    # Update model list when a make is selected
    def update_model_list(event=None):
        selected_make = marca_var.get()
        model_list = make_model_data.get(selected_make, [])
        model_combobox["values"] = model_list
        model_combobox.set("")  # Reset previous selection

    marca_combobox.bind("<<ComboboxSelected>>", update_model_list)

    ttk.Label(frame, text="An:").grid(row=3, column=0, padx=10, pady=5, sticky="E")
    years = [str(y) for y in range(1980, datetime.datetime.now().year + 1)][::-1]  # From 1980 to the current year, reversed
    an_var = tk.StringVar()
    an_combobox = ttk.Combobox(frame, textvariable=an_var, values=years)
    an_combobox.grid(row=3, column=1, padx=10, pady=5, sticky="W")

    ttk.Label(frame, text="VIN:").grid(row=4, column=0, padx=10, pady=5, sticky="E")
    vin_entry = ttk.Entry(frame)
    vin_entry.grid(row=4, column=1, padx=10, pady=5, sticky="W")

    ttk.Label(frame, text="Număr Înmatriculare:").grid(row=5, column=0, padx=10, pady=5, sticky="E")
    numar_inmatriculare_entry = ttk.Entry(frame)
    numar_inmatriculare_entry.grid(row=5, column=1, padx=10, pady=5, sticky="W")

    # Hidden field to store image link
    image_url_var = tk.StringVar()

    # Function to handle image upload with a loader
    def handle_image_upload():
        file_path = filedialog.askopenfilename(filetypes=[("Imagini", "*.jpg *.jpeg *.png")])
        if not file_path:
            return

        # Create the loader popup
        loading_popup = Toplevel(window)
        loading_popup.title("Se încarcă imaginea...")
        loading_popup.geometry(f"{window.winfo_width()}x{window.winfo_height()}+{window.winfo_x()}+{window.winfo_y()}")
        loading_popup.resizable(False, False)
        loading_popup.transient(window)
        loading_popup.grab_set()

        # Match the design of the main window
        loading_frame = ttk.Frame(loading_popup, padding=20)
        loading_frame.pack(fill="both", expand=True)

        ttk.Label(loading_frame, text="Imaginea se încarcă...", font=("Segoe UI", 14, "bold")).pack(expand=True, pady=50)

        loading_popup.update()

        try:
            uploaded_link = upload_file_to_drive(file_path)
            image_url_var.set(uploaded_link)
            loading_popup.destroy()
            messagebox.showinfo("Succes", "Imaginea a fost încărcată cu succes!")
        except Exception as e:
            loading_popup.destroy()
            messagebox.showerror("Eroare", f"Nu s-a putut încărca imaginea:\n{e}")

    # Add the "Încarcă Imagine" button
    upload_btn = ttk.Button(frame, text="Încarcă Imagine", command=handle_image_upload)
    upload_btn.grid(row=6, column=0, columnspan=2, padx=10, pady=(10, 0))

    submit_button = ttk.Button(frame, text="Adaugă", command=lambda: submit_vehicle(
        client_id, client_name, marca_var.get(), model_var.get(), an_var.get(),
        vin_entry.get(), numar_inmatriculare_entry.get(), image_url_var.get(), window, root))
    submit_button.grid(row=7, columnspan=2, pady=10)

def submit_vehicle(client_id, client_name, marca, model, an, vin, numar_inmatriculare, image_url, window, root):
    if not all([marca, model, an, vin, numar_inmatriculare]):
        messagebox.showerror("Eroare", "Toate câmpurile sunt obligatorii!")
        return

    try:
        response = requests.post('http://127.0.0.1:5000/add_vehicle', json={
            'client_id': client_id,
            'marca': marca,
            'model': model,
            'an': an,
            'vin': vin,
            'numar_inmatriculare': numar_inmatriculare,
            'image_url': image_url or "None"  # Default to "None" if no image URL is provided
        })
        print("Raw response:", response.text)
        if response.status_code == 200:
            result = response.json()
            messagebox.showinfo("Succes", "Vehiculul a fost adăugat cu succes!")
            window.destroy()
            dashboard_app = root.app
            dashboard_app.refresh_client_vehicles(client_name)
        elif response.status_code == 400 and "duplicate key value violates unique constraint" in response.text:
            messagebox.showerror("Eroare", "Vehiculul cu acest VIN există deja!")
        else:
            result = response.json()
            messagebox.showerror("Eroare", result.get('message', "A apărut o eroare necunoscută."))
    except Exception as e:
        messagebox.showerror("Eroare", f"A apărut o eroare: {e}")