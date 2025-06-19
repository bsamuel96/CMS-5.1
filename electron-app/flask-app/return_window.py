import tkinter as tk
from tkinter import ttk, messagebox
import requests
import re

API = "http://127.0.0.1:5000"  # adjust if needed

# Module-level UUID regex
_UUID_RE = re.compile(
    r'^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[1-5][0-9a-fA-F]{3}-'
    r'[89ABab][0-9a-fA-F]{3}-[0-9a-fA-F]{12}$'
)

class ReturnDetailDialog(tk.Toplevel):
    def __init__(self, master, item):
        super().__init__(master)
        self.transient(master)      # Keep on top
        self.grab_set()             # Make modal
        self.title("Detalii Returnare")
        self.resizable(False, False)

        # Keep a reference to the item
        self.item = item
        unit_price = item['pret_unitar']
        discount = item['discount'] / 100.0
        max_qty = item['eligible_qty']

        # Layout fields
        frm = ttk.Frame(self, padding=10)
        frm.grid()

        # Product info (read-only)
        labels = [
            ("Client:",       item["client_name"]),
            ("Vehicul:",      item["vehicle_desc"]),
            ("Produs:",       item['produs']),
            ("Brand:",        item['brand']),
            ("Cod Produs:",   item['cod_produs']),
            ("Preț Unitar:",  f"{unit_price:.2f} RON"),
            ("Discount:",     f"{item['discount']}%"),
            ("Eligibil:",     f"{max_qty} buc.")
        ]
        for i, (text, value) in enumerate(labels):
            ttk.Label(frm, text=text).grid(row=i, column=0, sticky="e", pady=2)
            ttk.Label(frm, text=value).grid(row=i, column=1, sticky="w", pady=2)

        # Return qty
        ttk.Label(frm, text="Cantitate Returnat:").grid(row=8, column=0, sticky="e", pady=10)
        self.qty_var = tk.IntVar(value=1)
        self.qty_spin = ttk.Spinbox(frm, from_=1, to=max_qty, textvariable=self.qty_var, width=5)
        self.qty_spin.grid(row=8, column=1, sticky="w")
        # Whenever qty changes, recalculate refund
        self.qty_var.trace_add("write", self._update_refund)

        # Refund preview
        ttk.Label(frm, text="Total Refund:").grid(row=9, column=0, sticky="e")
        self.refund_var = tk.StringVar()
        ttk.Label(frm, textvariable=self.refund_var).grid(row=9, column=1, sticky="w")
        # Initialize refund calculation
        self._update_refund()

        # Notes
        ttk.Label(frm, text="Observații:").grid(row=10, column=0, sticky="ne", pady=5)
        self.notes = tk.Text(frm, width=30, height=4)
        self.notes.grid(row=10, column=1, pady=5)

        # Buttons
        btn_frame = ttk.Frame(frm)
        btn_frame.grid(row=11, column=0, columnspan=2, pady=(10, 0))
        ttk.Button(btn_frame, text="Confirmă", command=self.on_confirm).grid(row=0, column=0, padx=5)
        ttk.Button(btn_frame, text="Anulează", command=self.destroy).grid(row=0, column=1, padx=5)

    def _update_refund(self, *_):
        """Recalculate refund = qty * unit_price * (1-discount)."""
        qty = self.qty_var.get()
        unit_price = self.item['pret_unitar']
        discount = self.item['discount'] / 100.0
        total = qty * unit_price * (1 - discount)
        self.refund_var.set(f"{total:.2f} RON")

    def on_confirm(self):
        qty = self.qty_var.get()
        notes = self.notes.get("1.0", "end").strip()
        payload = {
            "order_product_id": self.item['id'],
            "return_qty": qty,
            "notes": notes
        }
        try:
            resp = requests.post(f"{API}/add_return", json=payload)
            data = resp.json()
            if resp.ok:
                messagebox.showinfo(
                    "Succes",
                    f"Return înregistrat pentru {self.item['client_name']}.\n"
                    f"Refund: {data['refund']:.2f} RON"
                )
                self.destroy()
                # Tell the parent to reload
                self.master.load_all_items()
            else:
                messagebox.showerror("Eroare", data.get("error", ""))
        except Exception as e:
            messagebox.showerror("Eroare", str(e))


class ReturnWindow(tk.Toplevel):
    def __init__(self, master, prefill_order=None):
        super().__init__(master)
        self.title("Returnare Produse")

        # Set initial dimensions and center the window
        self.geometry("600x400")
        self.update_idletasks()
        w = self.winfo_width()
        h = self.winfo_height()
        ws = self.winfo_screenwidth()
        hs = self.winfo_screenheight()
        x = (ws // 2) - (w // 2)
        y = (hs // 2) - (h // 2)
        self.geometry(f'{w}x{h}+{x}+{y}')

        self.prefill_order = prefill_order

        # Main container (make it grow)
        container = ttk.Frame(self, padding=10)
        container.pack(fill="both", expand=True)
        # Make the single column stretch
        container.columnconfigure(0, weight=1)
        # Make row 2 (the tree) stretch
        container.rowconfigure(2, weight=1)

        # Row 0: Order ID and Load Button
        order_frame = ttk.Frame(container)
        order_frame.grid(row=0, column=0, sticky="ew", pady=(0, 5))
        order_frame.columnconfigure(1, weight=1)

        ttk.Label(order_frame, text="ID Comandă:", font=("Segoe UI", 10)).grid(row=0, column=0, sticky="w")
        self.order_entry = ttk.Entry(order_frame)
        self.order_entry.grid(row=0, column=1, sticky="ew", padx=(5, 5))
        if self.prefill_order:
            self.order_entry.insert(0, str(self.prefill_order))
        # Load Items (ignore Product Code field)
        ttk.Button(order_frame, text="Încarcă Produse", command=self.load_all_items).grid(row=0, column=2)

        # Row 1: Product Code and Find Button
        code_frame = ttk.Frame(container)
        code_frame.grid(row=1, column=0, sticky="ew", pady=(0, 10))
        code_frame.columnconfigure(1, weight=1)

        ttk.Label(code_frame, text="Cod Produs:", font=("Segoe UI", 10)).grid(row=0, column=0, sticky="w")
        self.code_entry = ttk.Entry(code_frame)
        self.code_entry.grid(row=0, column=1, sticky="ew", padx=(5, 5))
        # Find Item (use Product Code + Order ID)
        ttk.Button(code_frame, text="Caută Produs", command=self.search_by_code).grid(row=0, column=2)

        # Row 2: Treeview with Scrollbars (now stretchable and with full columns)
        tree_frame = ttk.Frame(container)
        tree_frame.grid(row=2, column=0, sticky="nsew")
        tree_frame.rowconfigure(0, weight=1)
        tree_frame.columnconfigure(0, weight=1)

        cols = (
            "Product", "Brand", "Product Code",
            "Sold Qty", "Elig. to Return",
            "Order No", "Order Date", "Customer", "Car"
        )
        self.tree = ttk.Treeview(
            tree_frame,
            columns=cols, show="headings", selectmode="browse"
        )
        for c in cols:
            self.tree.heading(c, text=c)
            # Make every column stretch when the window resizes
            self.tree.column(c, anchor="w", stretch=True)
        # Give reasonable minimum widths
        self.tree.column("Product", minwidth=120)
        self.tree.column("Brand", minwidth=100)
        self.tree.column("Product Code", minwidth=100, anchor="center")
        self.tree.column("Sold Qty", minwidth=60, anchor="e")
        self.tree.column("Elig. to Return", minwidth=60, anchor="e")
        self.tree.column("Order No", minwidth=80, anchor="center")
        self.tree.column("Order Date", minwidth=80, anchor="center")
        self.tree.column("Customer", minwidth=120, anchor="w")
        self.tree.column("Car", minwidth=140, anchor="w")
        self.tree.grid(row=0, column=0, sticky="nsew")

        vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        vsb.grid(row=0, column=1, sticky="ns")
        hsb = ttk.Scrollbar(tree_frame, orient="horizontal", command=self.tree.xview)
        hsb.grid(row=1, column=0, sticky="ew")

        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        # Row 3: Qty Spinbox and Confirm Button
        bottom_frame = ttk.Frame(container)
        bottom_frame.grid(row=3, column=0, sticky="ew", pady=(10, 0))
        bottom_frame.columnconfigure(1, weight=1)

        ttk.Label(bottom_frame, text="Cantitate de Returnat:", font=("Segoe UI", 10))\
            .grid(row=0, column=0, sticky="w")
        self.qty_spin = tk.Spinbox(bottom_frame, from_=1, to=1, width=5)
        self.qty_spin.grid(row=0, column=1, sticky="w", padx=(5, 5))
        # Open the detail dialog instead of self.submit()
        ttk.Button(
            bottom_frame,
            text="Confirmă Returnarea",
            command=self.open_detail_dialog
        ).grid(row=0, column=2, padx=(10, 0))

        # Cache for additional data
        self.price_cache = {}
        self.discount_cache = {}

        # Bind double-click to open detail dialog
        self.tree.bind("<Double-1>", self.open_detail_dialog)

    def _resolve_order_id(self, entered):
        """
        Resolve `entered` as either an order_number (e.g., CMD78) or an order_id (UUID/integer).
        If it's already a UUID/integer, return it directly. Otherwise, fetch the order_id via GET /orders/<order_number>.
        """
        entered = entered.strip()
        if entered.isdigit() or _UUID_RE.match(entered):
            return entered

        # Otherwise treat it as an order_number – normalize to uppercase
        entered_norm = entered.upper()
        try:
            resp = requests.get(f"{API}/orders/{entered_norm}")
            if resp.status_code == 200:
                return str(resp.json().get("id", ""))
        except Exception:
            pass
        return None

    def load_all_items(self):
        """
        Load all returnable items for the entered order (can be order_number or order_id).
        """
        entered = self.order_entry.get().strip()
        if not entered:
            return messagebox.showerror("Eroare", "Vă rugăm să introduceți un ID sau Număr de Comandă.")

        resolved = self._resolve_order_id(entered)
        print(f"[DEBUG] Resolved order_id: {resolved!r}")  # Debug statement
        if not resolved:
            return messagebox.showerror("Eroare", f"Comanda '{entered}' nu a fost găsită.")

        try:
            resp = requests.get(f"{API}/returnable_items", params={"order_id": resolved})
            items = resp.json() if resp.status_code == 200 else []
            for itm in items:
                itm.setdefault("order_date", "")
                itm.setdefault("client_name", "")
                itm.setdefault("vehicle_desc", "")
            # Ensure additional fields are included
        except Exception as e:
            return messagebox.showerror("Eroare", f"A apărut o eroare la încărcarea produselor:\n{e}")

        # Populate the Treeview with all items
        self._populate_tree(items)

    def search_by_code(self):
        """
        Search for items by Product Code. If an Order ID/Order Number is provided, filter results for that order.
        If no Order ID is provided, perform a global product search.
        """
        entered = self.order_entry.get().strip()
        code = self.code_entry.get().strip()

        if not code:
            return messagebox.showerror("Eroare", "Vă rugăm să introduceți un Cod Produs.")

        # Strip hyphens to match how our RPC works
        cleaned = code.replace('-', '')

        if entered:
            resolved = self._resolve_order_id(entered)
            if not resolved:
                return messagebox.showerror("Eroare", f"Comanda '{entered}' nu a fost găsită.")

            try:
                resp = requests.get(
                    f"{API}/order_products/search_any",
                    params={"order_id": resolved, "term": cleaned}
                )
                items = resp.json() if resp.status_code == 200 else []
            except Exception as e:
                return messagebox.showerror("Eroare", f"A apărut o eroare la căutarea produsului după ID Comandă:\n{e}")
        else:
            try:
                resp = requests.get(f"{API}/order_products/search_global", params={"term": cleaned})
                raw = resp.json() if resp.status_code == 200 else []
                items = [{
                    "id": row["id"],
                    "produs": row["produs"],
                    "brand": row["brand"],
                    "cod_produs": row["cod_produs"],
                    "cantitate": row["cantitate"],
                    "eligible_qty": row["cantitate"],
                    "order_number": row["order_number"],
                    "order_date": row.get("order_date", ""),
                    "client_name": row.get("client_name", ""),
                    "vehicle_desc": row.get("vehicle_desc", "")
                } for row in raw]
            except Exception as e:
                return messagebox.showerror("Eroare", f"A apărut o eroare la căutarea produsului global:\n{e}")
        # Populate the Treeview with the retrieved items
        self._populate_tree(items)

    def _populate_tree(self, items):
        """
        Clear the Treeview and populate it with the given items. Adjust the Spinbox based on 'eligible_qty'.
        """
        self.tree.delete(*self.tree.get_children())
        max_eligible = 1
        for row in items:
            self.tree.insert("", "end", iid=row['id'],
                values=(
                    row['produs'],
                    row['brand'],
                    row['cod_produs'],
                    row['cantitate'],
                    row['cantitate'],  # eligible_qty
                    row.get('order_number', row.get('order_id', '')),  # Use order_number if available, fallback to order_id
                    row.get('order_date', ''),
                    row.get('client_name', ''),
                    row.get('vehicle_desc', '')
                )
            )
            # Cache additional data
            self.price_cache[row['id']] = row.get('pret_unitar', 0)
            self.discount_cache[row['id']] = row.get('discount', 0)

            if row.get('cantitate', 0) > max_eligible:
                max_eligible = row['cantitate']

        # Adjust the upper limit of the Spinbox
        self.qty_spin.config(to=max_eligible)

    def open_detail_dialog(self, event=None):
        """
        Open the detail dialog for the selected item.
        """
        sel = self.tree.selection()
        if not sel:
            return messagebox.showwarning("Eroare", "Selectați un produs mai întâi.")
        iid = sel[0]
        vals = self.tree.item(iid, "values")
        item = {
            "id":            iid,
            "produs":        vals[0],
            "brand":         vals[1],
            "cod_produs":    vals[2],
            "cantitate":     int(vals[3]),
            "eligible_qty":  int(vals[4]),
            "order_number":  vals[5],
            "order_date":    vals[6],
            "client_name":   vals[7],
            "vehicle_desc":  vals[8],
            "pret_unitar":   self.price_cache.get(iid, 0),
            "discount":      self.discount_cache.get(iid, 0),
        }
        ReturnDetailDialog(self, item)
        
        ReturnDetailDialog(self, item)
