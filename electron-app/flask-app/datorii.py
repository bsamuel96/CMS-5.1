import tkinter as tk
from tkinter import ttk, messagebox
import requests  # Add missing import for requests

class DebtsReportApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Raport Datorii")
        self.root.geometry("1000x600")
        self.root.configure(bg="#d3d3d3")

        # Center the window on the screen
        self.center_window()

        self.create_widgets()
        self.current_page = 1
        self.page_size = 10
        self.total_pages = 1
        self.fetch_debts()

    def center_window(self):
        """Center the window horizontally and vertically."""
        self.root.update_idletasks()
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        window_width = 1000
        window_height = 600
        x = (screen_width // 2) - (window_width // 2)
        y = (screen_height // 2) - (window_height // 2)
        self.root.geometry(f"{window_width}x{window_height}+{x}+{y}")

    def create_widgets(self):
        self.style = ttk.Style()
        self.style.configure("TLabel", font=("Segoe UI", 10))
        self.style.configure("TButton", font=("Segoe UI", 10))
        self.style.configure("TEntry", font=("Segoe UI", 10))
        self.style.configure("Treeview.Heading", font=("Segoe UI", 10, "bold"))

        self.main_frame = ttk.Frame(self.root, padding="10")
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        self.debts_label = ttk.Label(self.main_frame, text="Clienți cu Datorii", font=("Segoe UI", 14, "bold"))
        self.debts_label.pack(pady=(0, 10))

        self.debts_tree = ttk.Treeview(self.main_frame, columns=("Nume", "Telefon", "Adresă", "Suma Datorată", "Vehicul"), show="headings", height=15)
        self.debts_tree.heading("Nume", text="Nume")
        self.debts_tree.heading("Telefon", text="Telefon")
        self.debts_tree.heading("Adresă", text="Adresă")
        self.debts_tree.heading("Suma Datorată", text="Suma Datorată")
        self.debts_tree.heading("Vehicul", text="Vehicul")
        self.debts_tree.column("Nume", width=200)
        self.debts_tree.column("Telefon", width=100)
        self.debts_tree.column("Adresă", width=300)
        self.debts_tree.column("Suma Datorată", width=100)
        self.debts_tree.column("Vehicul", width=200)
        self.debts_tree.pack(fill=tk.BOTH, expand=True)

        self.pagination_frame = ttk.Frame(self.main_frame)
        self.pagination_frame.pack(pady=10)

        self.prev_button = ttk.Button(self.pagination_frame, text="<<", command=self.prev_page)
        self.prev_button.pack(side=tk.LEFT, padx=5)

        self.page_label = ttk.Label(self.pagination_frame, text=f"Pagina {self.current_page} din {self.total_pages}")
        self.page_label.pack(side=tk.LEFT, padx=5)

        self.next_button = ttk.Button(self.pagination_frame, text=">>", command=self.next_page)
        self.next_button.pack(side=tk.LEFT, padx=5)  # Corrected "padx5" to "padx=5"

    def fetch_debts(self):
        try:
            response = requests.get('http://127.0.0.1:5000/debts')
            if response.status_code == 200:
                data = response.json()
                self.total_pages = 1  # no pagination
                self.current_page = 1
                self.update_debts_table(data)
                self.pagination_frame.pack_forget()  # hide the frame
            else:
                messagebox.showerror("Eroare", "Nu s-au putut încărca datoriile.")
        except Exception as e:
            messagebox.showerror("Eroare", f"A apărut o eroare: {e}")

    def update_debts_table(self, debts):
        for item in self.debts_tree.get_children():
            self.debts_tree.delete(item)
        for debt in debts:
            self.debts_tree.insert('', 'end', values=(debt['nume'], debt['telefon'], debt['adresa'], debt['suma_datorata'], debt['vehicul']))
        self.page_label.config(text=f"Pagina {self.current_page} din {self.total_pages}")

    def prev_page(self):
        if self.current_page > 1:
            self.current_page -= 1
            self.fetch_debts()

    def next_page(self):
        if self.current_page < self.total_pages:
            self.current_page += 1
            self.fetch_debts()

def open_debts_report_window(root):
    window = tk.Toplevel(root)
    app = DebtsReportApp(window)
    window.mainloop()