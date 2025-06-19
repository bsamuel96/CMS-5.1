import tkinter as tk
from tkinter import ttk, messagebox
import requests
from vezi_comenzi import open_view_orders_window_with_orders  # Import the function to open the view orders window with orders
from vezi_oferte import open_view_offers_window_with_offers  # Import the function to open the view offers window with offers

def open_client_search_window(root, on_client_selected_callback):
    search_window = tk.Toplevel(root)
    search_window.title("Caută Client")
    search_window.geometry("400x300")
    search_window.transient(root)
    search_window.grab_set()
    search_window.resizable(False, False)

    # Center the window on the screen
    search_window.update_idletasks()
    x = (search_window.winfo_screenwidth() - search_window.winfo_reqwidth()) // 2
    y = (search_window.winfo_screenheight() - search_window.winfo_reqheight()) // 2
    search_window.geometry(f"+{x}+{y}")

    content_frame = ttk.Frame(search_window, padding=10)
    content_frame.pack(fill=tk.BOTH, expand=True)

    add_client_search_content(content_frame, search_window, on_client_selected_callback)

def add_client_search_content(frame, search_window, on_client_selected_callback):
    ttk.Label(frame, text="Caută Client:").grid(row=0, column=0, padx=10, pady=5, sticky="E")
    search_entry = ttk.Entry(frame)
    search_entry.grid(row=0, column=1, padx=10, pady=5, sticky="W")

    # Search button (and Enter key)
    search_btn = ttk.Button(frame, text="🔍 Caută",
                            command=lambda: search_clients(search_entry.get(), client_list))
    search_btn.grid(row=0, column=2, padx=5)
    # Bind Enter key to trigger the search
    search_entry.bind("<Return>", lambda e: search_btn.invoke())

    client_list = ttk.Treeview(frame, columns=("UUID", "Nume"), show="headings", height=10)
    client_list.heading("Nume", text="Nume")
    client_list.column("UUID", width=0, stretch=tk.NO)  # Hide the UUID column
    client_list.column("Nume", width=300)
    client_list.grid(row=1, column=0, columnspan=3, padx=10, pady=5, sticky="nsew")

    select_button = ttk.Button(frame, text="Selectează",
                                command=lambda: select_client(client_list, search_window, on_client_selected_callback))
    select_button.grid(row=2, column=0, columnspan=3, pady=10)

    frame.grid_rowconfigure(1, weight=1)
    frame.grid_columnconfigure(1, weight=1)

def search_clients(query, client_list):
    print(f"Searching for clients with query: {query}")  # Debugging statement
    try:
        response = requests.get(f'http://127.0.0.1:5000/clients?name={query}')
        print(f"Response status code: {response.status_code}")  # Debugging statement
        print(f"Response content: {response.content}")  # Debugging statement
        clients = response.json()

        # 1) Clear out any old rows
        for iid in client_list.get_children():
            client_list.delete(iid)

        # 2) Insert new ones (or a "no results" placeholder)
        if not clients:
            client_list.insert('', 'end', values=("", "Nu s-au găsit rezultate."))
        else:
            for client in clients:
                client_list.insert('', 'end', values=(client['id'], client['nume']))
    except Exception as e:
        messagebox.showerror("Eroare", f"A apărut o eroare: {e}")

def select_client(client_list, search_window, on_client_selected_callback):
    selected_item = client_list.selection()
    if selected_item:
        client = client_list.item(selected_item, "values")
        client_id = client[0]  # UUID
        client_name = client[1]  # Name
        search_window.destroy()  # Close the search window
        on_client_selected_callback(client_id, client_name)
    else:
        messagebox.showerror("Eroare", "Selectați un client din listă.")

def on_client_selected(client_id, client_name, search_window, on_client_selected_callback):
    """Handle client selection and close the search window."""
    if client_id and client_name:
        search_window.destroy()  # Close the search window
        on_client_selected_callback(client_id, client_name)

def get_client_id_by_name(client_name):
    try:
        response = requests.get(f'http://127.0.0.1:5000/clients?name={client_name}')
        client_data = response.json()
        if response.status_code == 200 and client_data:
            return client_data[0]['id']
    except Exception as e:
        messagebox.showerror("Eroare", f"A apărut o eroare: {e}")
    return None

def search_client_orders(root, client_name):
    def search():
        if client_name:
            try:
                response = requests.get(f'http://127.0.0.1:5000/orders?client_name={client_name}')
                if response.status_code == 200:
                    orders = response.json()
                    open_view_orders_window_with_orders(root, orders)
                else:
                    messagebox.showerror("Eroare", "Nu s-au putut găsi comenzile pentru clientul specificat.")
            except Exception as e:
                messagebox.showerror("Eroare", f"A apărut o eroare: {e}")
        else:
            messagebox.showerror("Eroare", "Introduceți numele clientului.")

    search()

def search_client_offers(root, client_name):
    def search():
        if client_name:
            try:
                response = requests.get(f'http://127.0.0.1:5000/offers?client_name={client_name}')
                if response.status_code == 200:
                    offers = response.json()
                    open_view_offers_window_with_offers(root, offers)
                else:
                    messagebox.showerror("Eroare", "Nu s-au putut găsi ofertele pentru clientul specificat.")
            except Exception as e:
                messagebox.showerror("Eroare", f"A apărut o eroare: {e}")
        else:
            messagebox.showerror("Eroare", "Introduceți numele clientului.")

    search()
