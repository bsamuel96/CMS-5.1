import tkinter as tk
from tkinter import ttk, messagebox
import requests
import json
import os
from ttkwidgets.autocomplete import AutocompleteCombobox
import sys  # Add this import at the top of the file

TEMP_FILE = "temp_client_data.json"

# Cache for judete and localitati to avoid repetitive API calls
judete_cache = []
localitati_cache = {}

def open_add_client_window(root, refresh_client_list):
    """Open the Add Client window."""
    window = tk.Toplevel(root)
    window.title("Adaugă Client")

    # Let the user resize, but enforce sensible min/max
    window.resizable(True, True)
    window.minsize(500, 450)

    # Center & size at 60% of screen (clamped 500×450 to 1000×800)
    window.update_idletasks()
    sw = window.winfo_screenwidth()
    sh = window.winfo_screenheight()
    w = int(sw * 0.6)
    h = int(sh * 0.6)
    w = max(500, min(w, 1000))
    h = max(450, min(h, 800))
    x = (sw - w) // 2
    y = (sh - h) // 2
    window.geometry(f"{w}x{h}+{x}+{y}")

    window.transient(root)
    window.grab_set()

    content_frame = ttk.Frame(window, padding=20)
    content_frame.pack(fill=tk.BOTH, expand=True)

    add_client_content(content_frame, window, refresh_client_list)

    # Load temporary data if available
    load_temp_data(content_frame)

    # Save temporary data on window close
    def on_close():
        save_temp_data(content_frame, window)
        window.destroy()

    # Ensure the "X" button closes the window
    # Uncomment one of the following lines based on desired behavior:

    # To save+close:
    window.protocol("WM_DELETE_WINDOW", on_close)

    # — or — to just close and drop temp data:
    # window.protocol("WM_DELETE_WINDOW", window.destroy)

def add_client_content(frame, window, refresh_client_list):
    """Add content to the Add Client form."""
    # Add a title label
    title_label = ttk.Label(frame, text="Adaugă Client", font=("Segoe UI", 14, "bold"))
    title_label.grid(row=0, column=0, columnspan=3, pady=(0, 20), sticky="N")

    # Input fields
    ttk.Label(frame, text="Nume:", font=("Segoe UI", 10, "bold")).grid(row=1, column=0, padx=10, pady=5, sticky="E")
    nume_entry = ttk.Entry(frame, font=("Segoe UI", 10))
    nume_entry.grid(row=1, column=1, padx=10, pady=5, sticky="W")

    ttk.Label(frame, text="Telefon:", font=("Segoe UI", 10, "bold")).grid(row=2, column=0, padx=10, pady=5, sticky="E")
    telefon_entry = ttk.Entry(frame, font=("Segoe UI", 10))
    telefon_entry.grid(row=2, column=1, padx=10, pady=5, sticky="W")

    ttk.Label(frame, text="Adresă:", font=("Segoe UI", 10, "bold")).grid(row=3, column=0, padx=10, pady=5, sticky="E")
    adresa_entry = ttk.Entry(frame, font=("Segoe UI", 10))
    adresa_entry.grid(row=3, column=1, padx=10, pady=5, sticky="W")

    ttk.Label(frame, text="CNP:", font=("Segoe UI", 10, "bold")).grid(row=4, column=0, padx=10, pady=5, sticky="E")
    cnp_entry = ttk.Entry(frame, font=("Segoe UI", 10))
    cnp_entry.grid(row=4, column=1, padx=10, pady=5, sticky="W")

    ttk.Label(frame, text="Județ:", font=("Segoe UI", 10, "bold")).grid(row=5, column=0, padx=10, pady=5, sticky="E")
    judet_combobox = AutocompleteCombobox(frame, font=("Segoe UI", 10), completevalues=[], width=30)
    judet_combobox.grid(row=5, column=1, padx=10, pady=5, sticky="W")

    ttk.Label(frame, text="Localitate:", font=("Segoe UI", 10, "bold")).grid(row=6, column=0, padx=10, pady=5, sticky="E")
    localitate_combobox = AutocompleteCombobox(frame, font=("Segoe UI", 10), width=30)
    localitate_combobox.grid(row=6, column=1, padx=10, pady=5, sticky="W")

    # Buttons for clearing fields
    clear_judet_button = ttk.Button(frame, text="Șterge Județ", command=lambda: clear_combobox(judet_combobox, load_judete, localitate_combobox))
    clear_judet_button.grid(row=5, column=2, padx=5, pady=5, sticky="W")

    clear_localitate_button = ttk.Button(frame, text="Șterge Localitate", command=lambda: clear_combobox(localitate_combobox, update_localitati, judet_combobox))
    clear_localitate_button.grid(row=6, column=2, padx=5, pady=5, sticky="W")

    # Action buttons
    button_frame = ttk.Frame(frame)
    button_frame.grid(row=7, column=0, columnspan=3, pady=(20, 0))

    submit_button = ttk.Button(button_frame, text="Adaugă Client")
    submit_button.pack(side="left", padx=10)

    # Replace its command with a wrapper
    def handle_submit():
        # Disable the button during the network call
        submit_button.config(state="disabled")
        try:
            submit_client(
                nume_entry.get(),
                telefon_entry.get(),
                adresa_entry.get(),
                cnp_entry.get(),
                judet_combobox.get(),
                localitate_combobox.get(),
                window,
                refresh_client_list
            )
        finally:
            # Re-enable the button even if the call errors
            submit_button.config(state="normal")

    submit_button.config(command=handle_submit)

    cancel_button = ttk.Button(button_frame, text="Anulează", command=window.destroy)
    cancel_button.pack(side="left", padx=10)

    # Configure column weights for better alignment
    frame.grid_columnconfigure(0, weight=1)
    frame.grid_columnconfigure(1, weight=2)
    frame.grid_columnconfigure(2, weight=1)

    # Load judete and localitati
    load_judete(judet_combobox, localitate_combobox)

    # Highlight fields on focus
    for widget in frame.winfo_children():
        if isinstance(widget, ttk.Entry) or isinstance(widget, AutocompleteCombobox):
            widget.bind("<FocusIn>", lambda event, w=widget: w.configure(style="Focus.TEntry"))
            widget.bind("<FocusOut>", lambda event, w=widget: w.configure(style="TEntry"))

def load_judete(judet_combobox, localitate_combobox):
    """Load counties from the /get_judete API route."""
    global judete_cache
    if not judete_cache:
        try:
            response = requests.get('http://127.0.0.1:5000/get_judete')
            if response.status_code == 200:
                judete_cache = response.json()
            else:
                messagebox.showerror("Eroare", "Nu s-au putut încărca județele.")
        except Exception as e:
            messagebox.showerror("Eroare", f"A apărut o eroare: {e}")
    judet_combobox.set_completion_list(judete_cache)
    judet_combobox.bind("<KeyRelease>", lambda event: filter_combobox(judet_combobox, judete_cache))

    def on_judet_changed(event):
        # Clear cached localități for the selected județ
        selected = judet_combobox.get()
        localitati_cache.pop(selected, None)
        update_localitati(judet_combobox, localitate_combobox)

    judet_combobox.bind("<<ComboboxSelected>>", on_judet_changed)
    judet_combobox.bind("<FocusOut>", on_judet_changed)
    judet_combobox.bind("<Return>", on_judet_changed)

def update_localitati(judet_combobox, localitate_combobox):
    """Update localities based on the selected county using /get_localitati/<judet>."""
    global localitati_cache
    judet_selected = judet_combobox.get()
    if judet_selected in localitati_cache:
        localitati = localitati_cache[judet_selected]
    else:
        try:
            response = requests.get(f'http://127.0.0.1:5000/get_localitati/{judet_selected}')
            if response.status_code == 200:
                localitati = response.json()
                localitati_cache[judet_selected] = localitati
            else:
                messagebox.showerror("Eroare", "Nu s-au putut încărca localitățile.")
                return
        except Exception as e:
            messagebox.showerror("Eroare", f"A apărut o eroare: {e}")
            return
    localitate_combobox.set_completion_list(localitati)
    localitate_combobox.bind("<KeyRelease>", lambda event: filter_combobox(localitate_combobox, localitati))
    if len(localitati) == 1:
        localitate_combobox.set(localitati[0])
        messagebox.showinfo("Info", "Localitatea a fost completată automat.")

def filter_combobox(combobox, values):
    """Filter dropdown options based on user input."""
    input_text = combobox.get().lower()
    filtered_values = [value for value in values if input_text in value.lower()]
    combobox.set_completion_list(filtered_values)
    if len(filtered_values) == 1:
        combobox.set(filtered_values[0])

def clear_combobox(combobox, reload_function, related_combobox=None):
    """Clear the combobox and reload its values."""
    combobox.set("")
    if related_combobox:
        related_combobox.set("")
    reload_function(combobox, related_combobox)

def submit_client(nume, telefon, adresa, cnp, judet, localitate, window, refresh_client_list):
    print("Submitting Client")  # Debug print
    # Minimal validation: only Nume, Telefon, Județ & Localitate are required.
    if not nume or not telefon or not judet or not localitate:
        messagebox.showerror("Eroare", "Te rog completează Nume, Telefon, Județ și Localitate.")
        return

    # Telefon still numeric
    if not telefon.isdigit():
        messagebox.showerror("Eroare", "Telefonul trebuie să conțină doar cifre!")
        return

    # No more checks on 'cnp' or 'adresa'—anything goes

    # Send data to the Flask API
    try:
        payload = {
            'nume': nume,
            'telefon': telefon,
            'adresa': adresa,
            'localitate': localitate,
            'judet': judet
        }
        if cnp:  # Include CNP only if provided
            payload['cnp'] = cnp

        response = requests.post('http://127.0.0.1:5000/add_client', json=payload)

        # Log HTTP status and raw response payload
        print("⮕ HTTP status:", response.status_code)
        print("⮕ raw payload:", response.text)

        result = response.json()

        if response.status_code == 200:
            messagebox.showinfo("Succes!", "Clientul a fost adăugat cu succes.")
            refresh_client_list()  # Refresh the client list
            window.destroy()  # Close the window upon success
            clear_temp_data()  # Clear temporary data
        else:
            # Look for either 'message' or 'error', or fall back to raw text
            err = result.get('message') or result.get('error') or response.text
            messagebox.showerror("Eroare", err)
    except Exception as e:
        # Log the full exception to the console
        print("❌ submit_client error:", repr(e), file=sys.stderr)
        # Show a friendly error message to the user
        messagebox.showerror("Eroare", f"A apărut o eroare: {e}")

def save_temp_data(frame, window):
    """Save temporary data from the form to a JSON file."""
    # Map each field name to its (row, column) in the grid
    coords = {
        "nume": (1, 1),
        "telefon": (2, 1),
        "adresa": (3, 1),
        "cnp": (4, 1),
        "judet": (5, 1),
        "localitate": (6, 1),
    }
    temp_data = {}
    for key, (r, c) in coords.items():
        widget = frame.grid_slaves(row=r, column=c)[0]
        # Comboboxes and Entries both use get()
        temp_data[key] = widget.get()

    with open(TEMP_FILE, "w") as f:
        json.dump(temp_data, f)
    window.destroy()

def load_temp_data(frame):
    """Load temporary data from a JSON file into the form."""
    if not os.path.exists(TEMP_FILE):
        return

    with open(TEMP_FILE, "r") as f:
        temp_data = json.load(f)

    coords = {
        "nume": (1, 1),
        "telefon": (2, 1),
        "adresa": (3, 1),
        "cnp": (4, 1),
        "judet": (5, 1),
        "localitate": (6, 1),
    }

    # Fill each widget
    for key, (r, c) in coords.items():
        widget = frame.grid_slaves(row=r, column=c)[0]
        # Clear existing text for Entry
        try:
            widget.delete(0, tk.END)
        except Exception:
            pass
        widget.insert(0, temp_data.get(key, ""))

    # Once judet and localitate are set, refresh localități
    judet_w = frame.grid_slaves(row=5, column=1)[0]
    local_w = frame.grid_slaves(row=6, column=1)[0]
    update_localitati(judet_w, local_w)
    # And then set localitate explicitly (in case auto-fill kicked in)
    local_w.set(temp_data.get("localitate", ""))

def clear_temp_data():
    if os.path.exists(TEMP_FILE):
        os.remove(TEMP_FILE)