import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
import requests
import json
from tkcalendar import DateEntry
from supabase import create_client, Client
from config import SUPABASE_URL, SUPABASE_KEY

# Initialize Supabase client
supabase_client: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

class NewOrderApp:
    def __init__(self, root, offer_data, on_save=None):
        self.root = root
        self.offer_data = offer_data
        self.client_id = offer_data.get("client_id", "")
        self.client_name = offer_data.get("client_name", "Client Necunoscut")
        self.vehicle_data = offer_data.get("vehicle_data", {
            "marca": "N/A",
            "model": "N/A",
            "numar_inmatriculare": "N/A"
        })
        self.all_products = {}  # Initially empty, will be populated from backend
        self.order_number = offer_data.get("order_number", "CMD-???")
        self.on_save = on_save

        # Fetch offer details from backend using the /offers/<offer_number> route
        offer_number = offer_data.get("offer_number")
        if offer_number:
            try:
                response = requests.get(f"http://127.0.0.1:5000/offers/{offer_number}")
                if response.status_code == 200:
                    self.offer_data = response.json()
                    self.offer_data["selected_category"] = offer_data.get("selected_category", "")  # ✅ RETAIN CATEGORY
                    self.all_products = {
                        category: data["products"]
                        for category, data in self.offer_data.get("categories", {}).items()
                    }
                else:
                    print(f"[ERROR] Failed to fetch offer details for {offer_number}: {response.text}")
            except Exception as e:
                print(f"[ERROR] Exception fetching offer details: {e}")

        # Check if categories are defined
        if not self.all_products:
            messagebox.showerror("Eroare", "Nu există categorii definite în ofertă.")
            self.root.destroy()
            return

        # Fetch vehicle data if missing or incomplete
        if self.vehicle_data.get("marca") == "N/A" or self.vehicle_data.get("model") == "N/A":
            vehicle_id = offer_data.get("vehicle_id")
            if vehicle_id:
                try:
                    response = requests.get(f"http://127.0.0.1:5000/vehicle/{vehicle_id}")
                    self.vehicle_data = response.json()
                    self.vehicle_data["id"] = vehicle_id  # Ensure it carries the ID too
                except Exception as e:
                    print("[ERROR] Couldn't fetch vehicle:", e)

        # Auto-generate order number if missing
        if not self.order_number or "???" in self.order_number:
            response = requests.get("http://127.0.0.1:5000/highest_order_number")
            highest = response.json().get("highest_order_number", "CMD0")
            next_number = int(highest[3:]) + 1
            self.order_number = f"CMD{next_number}"

        print("[DEBUG] Initializing NewOrderApp with offer_data:", json.dumps(self.offer_data, indent=2))  # Debug print
        self.setup_ui()

    def setup_ui(self):
        # Update window properties
        self.root.title(f"Comandă Nouă - {self.client_name}")  # ✅ Ensure title updates dynamically
        self.root.geometry("1200x800")
        self.root.configure(bg="#d9d9d9")
        self.root.resizable(True, True)
        self.root.transient(self.root.master)
        self.root.grab_set()

        # Center the window on the screen
        self.root.update_idletasks()
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = (screen_width - 1200) // 2
        y = (screen_height - 800) // 2
        self.root.geometry(f"1200x800+{x}+{y}")

        # Scrollable canvas and content frame
        canvas = tk.Canvas(self.root, highlightthickness=0, bg="#d9d9d9")
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scrollbar = ttk.Scrollbar(self.root, orient="vertical", command=canvas.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        canvas.configure(yscrollcommand=scrollbar.set)

        content_frame = ttk.Frame(canvas, padding=20)  # Add padding
        canvas.create_window((0, 0), window=content_frame, anchor="nw")

        def on_configure(event):
            canvas.configure(scrollregion=canvas.bbox("all"))

        content_frame.bind("<Configure>", on_configure)

        # Make content_frame stretchable
        content_frame.columnconfigure(1, weight=1)
        content_frame.rowconfigure(6, weight=1)

        # Disable scroll when mouse over form fields
        canvas.bind("<Enter>", lambda e: canvas.bind_all("<MouseWheel>", lambda e: canvas.yview_scroll(-1 * (e.delta // 120), "units")))
        canvas.bind("<Leave>", lambda e: canvas.unbind_all("<MouseWheel>"))

        # --- Section: Header Info ---
        self.client_name_var = tk.StringVar(value=self.client_name)  # ✅ Use StringVar for dynamic updates
        ttk.Label(content_frame, text="Nume Client:", font=("Segoe UI", 10, "bold")).grid(row=0, column=0, sticky="e", padx=10, pady=5)
        ttk.Label(content_frame, textvariable=self.client_name_var, font=("Segoe UI", 10)).grid(row=0, column=1, sticky="w", padx=10, pady=5)

        # --- Section: Order Number Display ---
        ttk.Label(content_frame, text="Număr Comandă:", font=("Segoe UI", 10, "bold")).grid(row=0, column=2, sticky="e", padx=10, pady=5)
        ttk.Label(content_frame, text=self.order_number, font=("Segoe UI", 10)).grid(row=0, column=3, sticky="w", padx=10, pady=5)

        # Adjust grid configuration for better layout
        content_frame.columnconfigure(1, weight=1)
        content_frame.columnconfigure(3, weight=1)

        # --- Section: Vehicle Display ---
        ttk.Label(content_frame, text="Vehicul:", font=("Segoe UI", 10, "bold")).grid(row=1, column=0, sticky="e", padx=10, pady=5)
        vehicle_text = f"{self.vehicle_data.get('marca', 'N/A')} {self.vehicle_data.get('model', 'N/A')} ({self.vehicle_data.get('numar_inmatriculare', 'N/A')})"
        extra = f"An: {self.vehicle_data.get('an', '')}, VIN: {self.vehicle_data.get('vin', '')}"
        ttk.Label(content_frame, text=vehicle_text, font=("Segoe UI", 10)).grid(row=1, column=1, sticky="w", padx=10, pady=5)
        ttk.Label(content_frame, text=extra, font=("Segoe UI", 9, "italic"), foreground="#666").grid(row=2, column=1, sticky="w", padx=10, pady=0)

        # --- Section: Order Status ---
        self.status_var = tk.StringVar()
        status_values = [
            "Comandată și neplătită",
            "Comandată și plătită",
            "Comandată și plătită parțial",
            "Ridicată și neplătită",
            "Ridicată și plătită parțial",
            "Ridicată și plătită"
        ]
        ttk.Label(content_frame, text="Status:", font=("Segoe UI", 10, "bold")).grid(row=3, column=0, sticky="e", padx=10, pady=5)
        self.status_dropdown = ttk.Combobox(content_frame, textvariable=self.status_var, values=status_values, state="readonly")
        self.status_dropdown.grid(row=3, column=1, sticky="w", padx=10, pady=5)
        self.status_dropdown.set(status_values[0])  # Default selection
        self.status_dropdown.configure(state="readonly")  # Make sure it starts enabled

        # --- Section: Date Entry ---
        ttk.Label(content_frame, text="Data Comandă:", font=("Segoe UI", 10, "bold")).grid(row=4, column=0, sticky="e", padx=10, pady=5)
        self.date_entry = DateEntry(content_frame, date_pattern='yyyy-mm-dd', width=12)
        self.date_entry.set_date(datetime.now())
        self.date_entry.grid(row=4, column=1, sticky="w", padx=10, pady=5)

        # --- Section: Observations ---
        ttk.Label(content_frame, text="Observații:", font=("Segoe UI", 10, "bold")).grid(row=5, column=0, sticky="ne", padx=10, pady=5)
        self.observatii_text = tk.Text(content_frame, height=3, width=60)
        self.observatii_text.grid(row=5, column=1, pady=5, sticky="w", padx=10)

        # --- Section: Plătit Acum ---
        ttk.Label(content_frame, text="Plătit acum (RON):", font=("Segoe UI", 10, "bold")).grid(row=5, column=2, sticky="e", padx=10, pady=5)
        self.platit_acum_var = tk.DoubleVar(value=0.0)
        self.platit_acum_var.trace_add("write", self.update_status_based_on_payment)
        ttk.Entry(content_frame, textvariable=self.platit_acum_var, width=12).grid(row=5, column=3, sticky="w", padx=10, pady=5)

        # --- Section: Checkbutton for full payment discount ---
        self.discount_checked = tk.BooleanVar(value=False)
        discount_checkbox = ttk.Checkbutton(
            content_frame,
            text="Plată integrală în avans (5% discount)",
            variable=self.discount_checked,
            command=self.toggle_discount
        )
        discount_checkbox.grid(row=5, column=4, sticky="w", padx=10, pady=5)

        # --- Total Label ---
        self.total_comanda_var = tk.StringVar(value="0.00 RON")
        ttk.Label(content_frame, text="Total Comandă:", font=("Segoe UI", 10, "bold")).grid(row=7, column=0, sticky="e", padx=10, pady=5)
        ttk.Label(content_frame, textvariable=self.total_comanda_var, font=("Segoe UI", 10)).grid(row=7, column=1, sticky="w", padx=10, pady=5)

        # --- Section: Products Table ---
        ttk.Label(content_frame, text="Produse:", font=("Segoe UI", 10, "bold")).grid(row=6, column=0, sticky="ne", padx=10, pady=5)

        # Wrap table in Frame + Scrollbar
        table_frame = ttk.Frame(content_frame)
        table_frame.grid(row=6, column=1, columnspan=2, sticky="nsew", pady=10)

        self.products_table = ttk.Treeview(
            table_frame,
            columns=("produs", "brand", "cod", "cantitate", "preț unitar", "total", "discount", "final"),
            show="headings", height=8
        )
        self.products_table.pack(side="left", fill="both", expand=True)

        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.products_table.yview)
        scrollbar.pack(side="right", fill="y")
        self.products_table.configure(yscrollcommand=scrollbar.set)

        # Update headers and widths
        headers = ["Produs", "Brand", "Cod", "Cant.", "PU", "Total", "Disc.", "Final"]
        widths = [50, 35, 30, 15, 20, 20, 15, 25]

        # Update table headings and column widths
        for i, h in enumerate(headers):
            self.products_table.heading(i, text=h)
            self.products_table.column(i, width=widths[i], anchor="center")

        # Populate the products table
        self.populate_products_table()  # ✅ Moved here

        # --- Section: Generate PDF Button ---
        generate_btn = ttk.Button(content_frame, text="📄 Generează PDF", command=self.generate_pdf)
        generate_btn.grid(row=8, column=1, sticky="e", pady=(10, 0), padx=10)

        # --- Section: Save Button ---
        save_btn = ttk.Button(content_frame, text="💾 Salvează Comanda", command=self.save_order)
        save_btn.grid(row=9, column=1, pady=30, sticky="e", padx=10)

    def toggle_discount(self):
        """Toggle the 5% discount for full payment in advance and update status accordingly."""
        selected_category = self.offer_data.get("selected_category", "")
        products = self.all_products.get(selected_category, [])

        if not products:
            return

        for p in products:
            base_final = p[7] / 0.95 if self.discount_checked.get() else p[7]  # Restore base price if needed
            if self.discount_checked.get():
                p[7] = round(base_final * 0.95, 2)
            else:
                p[7] = round(base_final, 2)

        self.populate_products_table()

        total_due = sum(round(p[7], 2) for p in products)

        if self.discount_checked.get():
            paid_now = round(total_due * 0.95, 2)  # Use 95% of the total
            self.platit_acum_var.set(paid_now)

            # Disable status selection manually
            self.status_dropdown.configure(state="disabled")

            if paid_now >= total_due * 0.95:
                self.status_dropdown.set("Comandată și plătită")
            else:
                self.status_dropdown.set("Comandată și plătită parțial")
        else:
            self.platit_acum_var.set(0.0)
            self.status_dropdown.set("Comandată și neplătită")
            self.status_dropdown.configure(state="readonly")

    def update_status_based_on_payment(self, *args):
        selected_category = self.offer_data.get("selected_category", "")
        products = self.all_products.get(selected_category, [])

        if not products:
            return

        total_due = sum(round(p[7], 2) for p in products)
        amount_paid = self.platit_acum_var.get()

        if amount_paid >= total_due * 0.95:
            self.status_dropdown.set("Comandată și plătită")
        elif amount_paid > 0:
            self.status_dropdown.set("Comandată și plătită parțial")
        else:
            self.status_dropdown.set("Comandată și neplătită")

        # Dynamically update the Observații field
        obs_text = self.observatii_text.get("1.0", "end").strip()
        amount_paid_str = self.safe_format_float(amount_paid)

        # Remove any previous auto-notes
        lines = [line for line in obs_text.splitlines() if not line.startswith("[Auto-Note:")]
        updated_obs = "\n".join(lines).strip()

        # Compose a friendly message based on amount
        if amount_paid >= total_due * 0.95:
            auto_note = f"[Auto-Note: Clientul a achitat integral in avans {amount_paid_str} RON. Discount de 5% aplicat cu succes pentru plata in avans. ]"
        elif amount_paid > 0:
            auto_note = f"[Auto-Note: Clientul a plătit parțial {amount_paid_str} RON. Se așteaptă diferența ]"
        else: 
            auto_note = ""

        # Merge and update
        final_obs = (updated_obs + ("\n" + auto_note if auto_note else "")).strip()
        self.observatii_text.delete("1.0", "end")
        self.observatii_text.insert("1.0", final_obs)

    def populate_products_table(self):
        """Populate the products table based on the selected category and update totals."""
        selected_category = self.offer_data.get("selected_category", "")
        products = self.all_products.get(selected_category, [])

        if not products:
            print(f"[DEBUG] No products found for category '{selected_category}'")
            return

        # Clear existing rows
        for item in self.products_table.get_children():
            self.products_table.delete(item)

        # Insert new rows
        for row in products:
            product_name, brand, cod, qty, pu, total, discount, final_price = row
            cells = [
                product_name, brand, cod, str(qty),
                self.safe_format_float(pu),
                self.safe_format_float(total),
                f"{discount}%",
                self.safe_format_float(final_price)
            ]
            self.products_table.insert("", "end", values=cells)

        # ✅ Update only the "Plătit acum" field if the checkbox is active
        if self.discount_checked.get():
            discounted_total = sum(round(p[7] * 0.95, 2) for p in products)  # Apply 5% discount
            self.platit_acum_var.set(discounted_total)

        total_final = sum(p[7] for p in products)
        self.total_comanda_var.set(f"{self.safe_format_float(total_final)} RON")

    def save_order(self):
        selected_category = self.offer_data.get("selected_category", "")
        products = self.all_products.get(selected_category, [])

        if not products:
            messagebox.showerror("Eroare", "Nu există produse pentru această comandă.")
            return

        # parse dd/mm/yyyy into ISO before sending
        try:
            # date is e.g. "12/05/2025"
            dt = datetime.strptime(self.date_entry.get(), '%d/%m/%Y')
            formatted_date = dt.strftime('%Y-%m-%d')
        except ValueError:
            # fallback if already ISO or another format
            formatted_date = self.date_entry.get()

        payload = {
            "offer_number": self.offer_data["offer_number"],
            "order_number": self.order_number,
            "selected_category": selected_category,
            "client_id": self.client_id,
            "vehicle_id": self.vehicle_data.get("id"),
            "status": self.status_dropdown.get(),
            "amount_paid": self.platit_acum_var.get(),
            "observations": self.observatii_text.get("1.0", "end").strip(),
            "date": formatted_date,  # ✅ Use formatted date
            "source_offer_info": f"Din oferta {self.offer_data['offer_number']} – categoria {selected_category}",  # ✅ Add source info
            "products": [
                {
                    "produs": p[0],
                    "brand": p[1],
                    "cod_produs": p[2],
                    "cantitate": int(float(str(p[3]).strip().replace("\\", "").replace("\n", "").replace("\r", ""))),  # ✅ Sanitize and clean
                    "pret_unitar": float(str(p[4]).strip().replace("\\", "").replace("\n", "").replace("\r", "")),     # ✅ Sanitize and clean
                    "pret_total": float(str(p[5]).strip().replace("\\", "").replace("\n", "").replace("\r", "")),      # ✅ Sanitize and clean
                    "discount": float(str(p[6]).strip().replace("\\", "").replace("\n", "").replace("\r", "")),        # ✅ Sanitize and clean
                    "pret_cu_discount": float(str(p[7]).strip().replace("\\", "").replace("\n", "").replace("\r", "")) # ✅ Sanitize and clean
                }
                for p in products
            ]
        }

        # Debugging: Log each cleaned product before sending
        for p in payload["products"]:
            print("[DEBUG] Clean product:", p)

        # Debugging: Log the full payload before sending
        print("[DEBUG] Payload to /add_order:\n", json.dumps(payload, indent=2))

        try:
            response = requests.post("http://127.0.0.1:5000/add_order", json=payload)
            if response.status_code == 200:
                messagebox.showinfo("Succes", "Comanda a fost salvată cu succes!")
                self.generate_pdf()
                self.root.destroy()
                if self.on_save:
                    self.on_save(self.offer_data["offer_number"], self.order_number, self.offer_data["selected_category"])  # ✅ Trigger callback
            else:
                messagebox.showerror("Eroare", f"Nu s-a putut salva comanda:\n{response.text}")
        except Exception as e:
            messagebox.showerror("Eroare", f"A apărut o eroare:\n{e}")

    def generate_pdf(self):
        from pdf import OrderPDFGenerator
        selected_category = self.offer_data.get("selected_category", "")
        products = self.all_products.get(selected_category, [])

        # Compute total and amount paid
        total_due = sum(p[7] for p in products)
        amount_paid = self.platit_acum_var.get()

        # Adjust logic if discount checkbox is active
        if self.discount_checked.get():
            discounted_total = round(total_due * 0.95, 2)
            if abs(amount_paid - discounted_total) < 0.01:
                computed_status = "Comandată și plătită"
            elif amount_paid > 0:
                computed_status = "Comandată și plătită parțial"
            else:
                computed_status = "Comandată și neplătită"
        else:
            if abs(amount_paid - total_due) < 0.01:
                computed_status = "Comandată și plătită"
            elif amount_paid > 0:
                computed_status = "Comandată și plătită parțial"
            else:
                computed_status = "Comandată și neplătită"

        # Pass everything to the PDF
        order_details = {
            "client_name": self.client_name,
            "vehicle_name": f"{self.vehicle_data['marca']} {self.vehicle_data['model']} ({self.vehicle_data['numar_inmatriculare']})",
            "order_number": self.order_number,
            "date": self.date_entry.get(),
            "status": computed_status,
            "amount_paid": amount_paid,
            "observations": self.observatii_text.get("1.0", "end").strip(),
            "products": [
                [p[0], p[1], p[3], p[4], p[5], p[6], p[7]] for p in products
            ]
        }
        generator = OrderPDFGenerator(order_details)
        generator.generate_pdf()

    def safe_format_float(self, value):
        """Safely format a float value to 2 decimal places."""
        try:
            return f"{float(value):.2f}"
        except ValueError:
            return "0.00"

def open_new_order_window(parent_root, offer_data, on_save=None):
    """Open the New Order window in a separate popup."""
    new_window = tk.Toplevel(parent_root)
    NewOrderApp(new_window, offer_data, on_save)