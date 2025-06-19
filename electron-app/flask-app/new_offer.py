import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import requests
import tksheet  # Ensure you have tksheet installed
import uuid
from tkcalendar import DateEntry
from pdf import PDFGenerator  # Import the PDFGenerator class
from datetime import datetime
import json  # Add this import at the top of the file

def open_add_offer_window(root, offer_details=None):
    try:
        print(f"Opening offer window with details: {offer_details}")  # Debug print
        window = tk.Toplevel(root)
        window.title("Ofertă Nouă" if offer_details is None else "Editează Ofertă")
        window.geometry("1200x800")  # Adjusted window size to fit full category
        
        # Center the window dynamically
        window.update_idletasks()
        screen_width = window.winfo_screenwidth()
        screen_height = window.winfo_screenheight()
        
        window_width = 1200  # Match the width in .geometry()
        window_height = 800  # Match the height in .geometry()
        
        position_x = (screen_width - window_width) // 2
        position_y = (screen_height - window_height) // 2
        
        window.geometry(f"{window_width}x{window_height}+{position_x}+{position_y}")

        window.transient(root)  # Attach it to the main window
        window.grab_set()  # Make it modal

        canvas = tk.Canvas(window, highlightthickness=0, bg="#d9d9d9")
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scrollbar = ttk.Scrollbar(window, orient="vertical", command=canvas.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        canvas.configure(yscrollcommand=scrollbar.set)

        content_frame = ttk.Frame(canvas)
        canvas.create_window((0, 0), window=content_frame, anchor="nw")

        def on_configure(event):
            canvas.configure(scrollregion=canvas.bbox("all"))

        content_frame.bind("<Configure>", on_configure)
        canvas.bind_all("<MouseWheel>", lambda e: canvas.yview_scroll(-1 * (e.delta // 120), "units"))

        add_offer_content(content_frame, window, offer_details)
    except Exception as e:
        print(f"Exception occurred while opening offer window: {e}")  # Debug print
        messagebox.showerror("Eroare", f"A apărut o eroare: {e}")

def add_offer_content(content_frame, window, offer_details=None):
    try:
        print(f"Adding offer content with details: {offer_details}")  # Debug print
        vehicle_dropdown = ttk.Combobox(content_frame, state="readonly")  # Define vehicle_dropdown here
        vehicle_dropdown.vehicle_ids = {}  # Initialize vehicle_ids attribute

        # Extract vehicles from offer_details
        vehicles = offer_details.get("vehicles") if offer_details else []
        if isinstance(vehicles, list) and all(isinstance(v, dict) for v in vehicles):
            vehicle_dropdown['values'] = [f"{v['marca']} {v['model']} ({v['numar_inmatriculare']})" for v in vehicles]
            vehicle_dropdown.vehicle_ids = {f"{v['marca']} {v['model']} ({v['numar_inmatriculare']})": v['id'] for v in vehicles}  # Corrected to use vehicle ID
        else:
            print("[ERROR] Invalid structure for 'vehicles' in offer_details.")  # Debug statement
            raise ValueError("Invalid structure for 'vehicles' in offer_details.")

        # Create the search window for selecting a client
        def open_client_search():
            from client_search import open_client_search_window
            open_client_search_window(window, on_client_selected)

        def on_client_selected(client_id, client_name):
            client_id_entry.delete(0, tk.END)
            client_id_entry.insert(0, client_id)
            client_name_label.config(text=client_name)
            refresh_vehicle_dropdown(client_id)

        def refresh_vehicle_dropdown(client_id):
            try:
                response = requests.get(f'http://127.0.0.1:5000/vehicles?client_id={client_id}')
                vehicles = response.json()
                if vehicles is not None:
                    vehicle_dropdown['values'] = [f"{v['marca']} {v['model']} ({v['numar_inmatriculare']})" for v in vehicles]
                    vehicle_dropdown.vehicle_ids = {f"{v['marca']} {v['model']} ({v['numar_inmatriculare']})": v['id'] for v in vehicles}  # Store vehicle IDs in the dropdown
                else:
                    vehicle_dropdown['values'] = []
                    vehicle_dropdown.vehicle_ids = {}
            except Exception as e:
                messagebox.showerror("Eroare", f"A apărut o eroare: {e}")

        def open_category_window(category, prefilled_data=None):
            category_window = tk.Toplevel(window)
            category_window.title(f"Produse - {category}")
            category_window.geometry("1200x700")  # Increased window size
            category_window.transient(window)
            category_window.grab_set()
            category_window.resizable(True, True)

            # Center the window dynamically
            category_window.update_idletasks()
            screen_width = category_window.winfo_screenwidth()
            screen_height = category_window.winfo_screenheight()
            
            window_width = 1200  # Match the width in .geometry()
            window_height = 700  # Match the height in .geometry()
            
            position_x = (screen_width - window_width) // 2
            position_y = (screen_height - window_height) // 2
            
            category_window.geometry(f"{window_width}x{window_height}+{position_x}+{position_y}")

            category_frame = ttk.Frame(category_window, padding=10)
            category_frame.pack(fill=tk.BOTH, expand=True)

            add_category_content(category_frame, category_window, category, prefilled_data)

        def add_category_content(frame, window, category, prefilled_data=None):
            sheet_frame = ttk.Frame(frame)
            sheet_frame.pack(fill=tk.BOTH, expand=True)

            # Add a scrollbar
            scrollbar = ttk.Scrollbar(sheet_frame, orient=tk.VERTICAL)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

            sheet = tksheet.Sheet(sheet_frame, headers=["Nume produs", "Brand", "Cod Produs", "Cantitate", "Preț Unitar", "Preț Total", "Discount", "Preț cu Discount"], height=300, yscrollcommand=scrollbar.set)
            sheet.pack(fill=tk.BOTH, expand=True)

            scrollbar.config(command=sheet.yview)  # Link scrollbar to the sheet

            # Set Romanian labels for right-click menu and accelerators
            sheet.set_options(
                # Cell & header editing
                edit_cell_label="Editează celulă",
                edit_header_label="Editează antet",
                edit_index_label="Editează index",
                # Clipboard
                cut_label="Taie",
                cut_contents_label="Taie conținut",
                copy_label="Copiază",
                copy_contents_label="Copiază conținut",
                paste_label="Lipește",
                # Deletion
                delete_label="Șterge",
                clear_contents_label="Șterge conținut",
                delete_rows_label="Șterge rânduri",
                delete_columns_label="Șterge coloane",
                # Insertion
                insert_row_label="Inserează rând",
                insert_rows_above_label="Inserează rânduri deasupra",
                insert_rows_below_label="Inserează rânduri dedesubt",
                insert_column_label="Inserează coloană",
                insert_columns_left_label="Inserează coloane la stânga",
                insert_columns_right_label="Inserează coloane la dreapta",
                # Selection
                select_all_label="Selectează tot",
                # Undo/Redo
                undo_label="Anulează",
                redo_label="Refă",
            )

            # Enable bindings
            sheet.enable_bindings((
                "single_select", "row_select", "column_select", "arrowkeys",
                "row_height_resize", "double_click_column_resize", "right_click_popup_menu",
                "rc_select", "rc_insert_row", "rc_delete_row",
                "copy", "cut", "paste", "delete", "undo", "edit_cell"
            ))

            # Adjust column widths to ensure all columns are visible at once
            sheet.set_column_widths([120, 80, 80, 80, 80, 80, 70, 120])

            # Enable cell editing
            sheet.enable_bindings(("single_select", "row_select", "column_select", "arrowkeys", "row_height_resize", "double_click_column_resize", "right_click_popup_menu", "rc_select", "rc_insert_row", "rc_delete_row", "copy", "cut", "paste", "delete", "undo", "edit_cell"))

            if prefilled_data:
                for row_data in prefilled_data:
                    sheet.insert_row(row_data)
            else:
                sheet.insert_row()  # Start with an empty row

            def update_totals():
                for row in range(sheet.get_total_rows()):
                    try:
                        cantitate = float(sheet.get_cell_data(row, 3))
                        pret_unitar = float(sheet.get_cell_data(row, 4))
                        discount = sheet.get_cell_data(row, 6)
                        if not discount:
                            discount = 0.0
                        else:
                            discount = float(discount)
                        if discount > 20:
                            discount = 20
                            sheet.set_cell_data(row, 6, "20.00")
                        pret_total = cantitate * pret_unitar
                        pret_cu_discount = pret_total - (pret_total * discount / 100)
                        sheet.set_cell_data(row, 5, f"{pret_total:.2f}")
                        sheet.set_cell_data(row, 7, f"{pret_cu_discount:.2f}")
                    except ValueError:
                        continue
                update_saved_categories_text()  # Ensure totals are updated
                update_total()  # Update the total for the selected category

            def apply_bulk_discount():
                discount = simpledialog.askfloat("Discount", "Introduceți discountul pentru produsele fără discount:", minvalue=0, maxvalue=20)
                if discount is not None:
                    for row in range(sheet.get_total_rows()):
                        if not sheet.get_cell_data(row, 6):
                            sheet.set_cell_data(row, 6, f"{discount:.2f}")
                    update_totals()

            def add_product():
                sheet.insert_row()
                update_totals()  # Ensure totals are updated

            def delete_product():
                selected_rows = sheet.get_selected_rows()
                if selected_rows:
                    for row in selected_rows:
                        sheet.delete_row(row)
                update_totals()  # Ensure totals are updated

            def save_category():
                products = sheet.get_sheet_data()
                total_price = sum(float(row[7]) for row in products if row[7])  # Use price after discount
                saved_categories[category] = {"products": products, "total_price": total_price}
                update_saved_categories_text()
                window.destroy()

            sheet.bind("<FocusOut>", lambda event: update_totals())
            sheet.bind("<KeyRelease>", lambda event: update_totals())

            add_product_button = ttk.Button(frame, text="Adaugă Produs", command=add_product)
            add_product_button.pack(side=tk.LEFT, padx=5, pady=5)

            delete_product_button = ttk.Button(frame, text="Șterge Produs", command=delete_product)
            delete_product_button.pack(side=tk.LEFT, padx=5, pady=5)

            apply_discount_button = ttk.Button(frame, text="Aplică Discount", command=apply_bulk_discount)
            apply_discount_button.pack(side=tk.LEFT, padx=5, pady=5)

            total_label = ttk.Label(frame, text="Total: 0.00 RON", font=("Arial", 12))
            total_label.pack(side=tk.LEFT, padx=5, pady=5)

            save_category_button = ttk.Button(frame, text="Salvează Categorie", command=save_category)
            save_category_button.pack(side=tk.RIGHT, padx=5, pady=5)

            def update_total():
                """Calculate and update the total for the selected category."""
                total = 0
                for row in sheet.get_sheet_data():
                    try:
                        total += float(row[7])  # Assuming the price after discount is in the 8th column (index 7)
                    except ValueError:
                        continue
                total_label.config(text=f"Total: {total:.2f} RON")

        def update_saved_categories_text():
            """Update the UI to display saved categories with products and edit buttons."""
            for widget in saved_categories_frame.winfo_children():
                widget.destroy()

            for category, data in saved_categories.items():
                # Outer frame with consistent background color
                category_outer_frame = tk.Frame(saved_categories_frame, padx=25, pady=5, bg="#d9d9d9")
                category_outer_frame.pack(fill=tk.X, pady=5)

                # Inner frame with consistent background color
                category_frame = tk.Frame(category_outer_frame, bd=2, relief="solid", padx=5, pady=5, bg="#d9d9d9")
                category_frame.pack(fill=tk.X)

                # Header row with consistent background color
                header_row = tk.Frame(category_frame, bg="#d9d9d9")
                header_row.pack(fill=tk.X, pady=5)

                category_label = ttk.Label(header_row, text=f"{category}: Total {data['total_price']:.2f} RON", font=("Arial", 12), background="#d9d9d9")
                category_label.pack(side=tk.LEFT, padx=5)

                edit_button = ttk.Button(header_row, text="Editează", command=lambda c=category: open_category_window(c, saved_categories[c]["products"]))
                edit_button.pack(side=tk.RIGHT, padx=5)

                # Products frame with consistent background color
                products_frame = ttk.Frame(category_frame, style="Custom.TFrame")  # Use ttk.Frame for styling
                products_frame.pack(fill=tk.X, padx=10, pady=5)

                headers = ["Nume produs", "Brand", "Cod Produs", "Cantitate", "Preț Unitar", "Preț Total", "Discount", "Preț cu Discount"]
                header_row = tk.Frame(products_frame, bg="#d9d9d9")
                header_row.pack(fill=tk.X)

                for header in headers:
                    ttk.Label(header_row, text=header, font=("Arial", 10, "bold"), width=15, anchor="w", background="#d9d9d9").pack(side=tk.LEFT, padx=2)

                for product in data["products"]:
                    product_row = tk.Frame(products_frame, bg="#d9d9d9")
                    product_row.pack(fill=tk.X)

                    for value in product:
                        ttk.Label(product_row, text=value, font=("Arial", 10), width=15, anchor="w", background="#d9d9d9").pack(side=tk.LEFT, padx=2)

        ttk.Label(content_frame, text="Client:").grid(row=0, column=0, padx=10, pady=5, sticky="E")
        client_name_label = ttk.Label(content_frame, text=offer_details.get("client_name", "") if offer_details else "")
        client_name_label.grid(row=0, column=1, padx=10, pady=5, sticky="W")
        client_search_button = ttk.Button(content_frame, text="Caută Client", command=open_client_search)
        client_search_button.grid(row=0, column=2, padx=10, pady=5, sticky="W")

        client_id_entry = ttk.Entry(content_frame)  # Define the client_id_entry variable
        client_id_entry.grid(row=0, column=3, padx=10, pady=5, sticky="W")
        client_id_entry.grid_remove()  # Hide the client_id_entry

        ttk.Label(content_frame, text="Vehicul:").grid(row=1, column=0, padx=10, pady=5, sticky="E")
        vehicle_dropdown.grid(row=1, column=1, padx=10, pady=5, sticky="W")

        def fetch_next_offer_number():
            try:
                response = requests.get('http://127.0.0.1:5000/highest_offer_number')
                if response.status_code == 200:
                    highest_offer_number = response.json().get('highest_offer_number', 'O0')
                    next_number = int(highest_offer_number[1:]) + 1
                    return f"O{next_number}"
                else:
                    return f"O1"
            except Exception as e:
                messagebox.showerror("Eroare", f"A apărut o eroare: {e}")
                return f"O1"

        if offer_details and offer_details.get("offer_number"):
            order_number = offer_details["offer_number"]
        else:
            order_number = fetch_next_offer_number()

        ttk.Label(content_frame, text="Nr. Comandă:").grid(row=2, column=0, padx=10, pady=5, sticky="E")
        order_number_label = ttk.Label(content_frame, text=order_number)
        order_number_label.grid(row=2, column=1, padx=10, pady=5, sticky="W")

        ttk.Label(content_frame, text="Data Ofertă:").grid(row=2, column=2, padx=10, pady=5, sticky="E")
        date_entry = DateEntry(content_frame, date_pattern='dd/mm/yyyy', width=12, background='darkblue', foreground='white', borderwidth=2)
        date_entry.grid(row=2, column=3, padx=10, pady=5, sticky="W")

        ttk.Label(content_frame, text="Categorie:").grid(row=3, column=0, padx=10, pady=5, sticky="E")
        category_var = tk.StringVar()
        category_dropdown = ttk.Combobox(content_frame, textvariable=category_var, values=["Premium", "Standard", "Economic"], state="readonly")
        category_dropdown.grid(row=3, column=1, padx=10, pady=5, sticky="W")

        ttk.Label(content_frame, text="Observații:").grid(row=4, column=0, padx=10, pady=5, sticky="NE")
        observations_text = tk.Text(content_frame, height=3, wrap=tk.WORD)
        observations_text.grid(row=4, column=1, columnspan=3, padx=10, pady=5, sticky="W")

        ttk.Label(content_frame, text="Status:").grid(row=5, column=0, padx=10, pady=5, sticky="E")
        status_var = tk.StringVar()
        status_dropdown = ttk.Combobox(content_frame, textvariable=status_var, values=["Ofertă (în așteptare)", "Acceptată", "Respinsă"], state="readonly")
        status_dropdown.grid(row=5, column=1, padx=10, pady=5, sticky="W")

        def on_category_selected(event):
            category = category_var.get()
            if (category in saved_categories):
                messagebox.showerror("Eroare", "Această categorie a fost deja utilizată!")
            else:
                open_category_window(category)

        category_dropdown.bind("<<ComboboxSelected>>", on_category_selected)

        saved_categories = {}
        saved_categories_frame = ttk.Frame(content_frame)
        saved_categories_frame.grid(row=6, column=0, columnspan=4, pady=10, sticky="nsew")

        save_button = ttk.Button(content_frame, text="Salvează", command=lambda: submit_offer(client_id_entry.get(), vehicle_dropdown, order_number, saved_categories, status_var.get(), observations_text.get("1.0", tk.END).strip(), date_entry.get(), window))
        save_button.grid(row=7, column=0, pady=10)

        generate_pdf_button = ttk.Button(
            content_frame,
            text="Genereaza PDF",
            command=lambda: generate_pdf(
                None,
                {
                    "client_name": client_name_label.cget("text"),
                    "vehicle_name": vehicle_dropdown.get(),
                    "offer_number": order_number_label.cget("text"),
                    "categories": saved_categories,
                    "status": status_var.get(),
                    "observations": observations_text.get("1.0", tk.END).strip(),
                    "date": date_entry.get(),
                }
            )
        )
        generate_pdf_button.grid(row=7, column=1, pady=10)

        if offer_details:
            client_id_entry.insert(0, offer_details['client_id'])
            client_name_label.config(text=offer_details.get('client_name', ''))  # Ensure client_name is used
            if isinstance(vehicles, list) and vehicles:
                vehicle_dropdown.set(f"{vehicles[0]['marca']} {vehicles[0]['model']} ({vehicles[0]['numar_inmatriculare']})")  # Preselect the first vehicle
            default_date = datetime.now().strftime('%Y-%m-%d')  # Default to today's date
            raw_date = offer_details.get('date', default_date)
            try:
                valid_date = datetime.strptime(raw_date, '%Y-%m-%d').date() if isinstance(raw_date, str) else raw_date
                date_entry.set_date(valid_date)
            except ValueError:
                date_entry.set_date(default_date)  # Fallback to default date if invalid
            status_var.set(offer_details['status'])
            observations_text.insert(tk.END, offer_details['observations'])
            for category, data in offer_details['categories'].items():
                saved_categories[category] = {"products": data['products'], "total_price": data['total_price']}
            update_saved_categories_text()
    except Exception as e:
        print(f"Exception occurred while adding offer content: {e}")  # Debug print
        messagebox.showerror("Eroare", f"A apărut o eroare: {e}")

def generate_pdf(offer_number=None, offer_details=None, client_name=None, vehicle_name=None):
    try:
        if offer_details:
            # Ensure client and vehicle details are included
            if "client_name" not in offer_details and client_name:
                offer_details["client_name"] = client_name
            if "vehicle_name" not in offer_details and vehicle_name:
                offer_details["vehicle_name"] = vehicle_name

            # Generate PDF directly from provided offer details
            pdf_generator = PDFGenerator(offer_details)
            pdf_file = pdf_generator.generate_pdf()
            messagebox.showinfo("Succes", f"PDF generat cu succes: {pdf_file}")
        elif offer_number:
            # Fetch offer details from the server if offer_number is provided
            response = requests.get(f'http://127.0.0.1:5000/offers/{offer_number}')
            if response.status_code == 200:
                offer_details = response.json()
                pdf_generator = PDFGenerator(offer_details)
                pdf_file = pdf_generator.generate_pdf()
                messagebox.showinfo("Succes", f"PDF generat cu succes: {pdf_file}")
            else:
                messagebox.showerror("Eroare", "Nu s-au putut încărca detaliile ofertei.")
        else:
            messagebox.showerror("Eroare", "Nu există detalii pentru generarea PDF-ului.")
    except Exception as e:
        messagebox.showerror("Eroare", f"A apărut o eroare: {e}")

def submit_offer(client_id, vehicle_dropdown, offer_number, categories, status, observations, date, window):
    if not all([client_id, vehicle_dropdown, offer_number, categories, status, date]):
        messagebox.showerror("Eroare", "Toate câmpurile sunt obligatorii!")
        return

    # Ensure categories are not empty
    if not categories:
        messagebox.showerror("Eroare", "Trebuie să adăugați cel puțin o categorie de produse!")
        return

    # Ensure status is valid
    valid_statuses = ["Ofertă (în așteptare)", "Acceptată", "Respinsă"]
    if status not in valid_statuses:
        messagebox.showerror("Eroare", "Statusul selectat nu este valid!")
        return

    # Get the vehicle ID from the dropdown
    vehicle = vehicle_dropdown.get()
    vehicle_id = vehicle_dropdown.vehicle_ids.get(vehicle)

    try:
        formatted_date = date if isinstance(date, str) else date.strftime('%Y-%m-%d')

        # Prepare payload for saving the offer
        payload = {
            "client_id": client_id,
            "vehicle_id": vehicle_id,
            "offer_number": offer_number,
            "categories": categories,
            "status": status,
            "observations": observations,
            "date": formatted_date
        }

        # Debug print for categories payload
        print("[DEBUG] Categories payload:", json.dumps(categories, indent=2))

        try:
            response = requests.post("http://127.0.0.1:5000/add_offer", json=payload)
            if response.status_code == 200:
                messagebox.showinfo("Succes", "Ofertă salvată cu succes!")
                window.destroy()
                
                # Trigger refresh in dashboard
                if hasattr(window.master, "app"):
                    selected_client_name = window.master.app.client_name_value.cget("text")
                    window.master.app.refresh_client_offers(selected_client_name)
            else:
                messagebox.showerror("Eroare", f"Nu s-a putut salva oferta:\n{response.text}")
        except Exception as e:
            messagebox.showerror("Eroare", f"A apărut o eroare:\n{e}")

    except Exception as e:
        messagebox.showerror("Eroare", f"A apărut o eroare: {e}")
