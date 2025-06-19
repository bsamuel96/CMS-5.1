import sys
import os
import threading
import time
import traceback
import logging
import tkinter as tk
from tkinter import messagebox

# Setup logging to a file next to the EXE
if getattr(sys, 'frozen', False):
    base_path = sys._MEIPASS
else:
    base_path = os.path.dirname(__file__)
logfile = os.path.join(base_path, "startup_errors.log")
logging.basicConfig(filename=logfile, level=logging.ERROR,
                    format="%(asctime)s %(levelname)s %(message)s")

# 1) Preflight: make sure required data files got bundled
required = [
    "config.json",
    os.path.join("resources", "judete_localitati.json"),
    "driveuploader-456317-fdcff069c6d3.json",  # your service account key
]
missing = []
for rel in required:
    if not os.path.exists(os.path.join(base_path, rel)):
        missing.append(rel)

if missing:
    err = f"Missing required files: {', '.join(missing)}"
    logging.error(err)
    # Show a message box if GUI is available
    try:
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror("Startup Error", err + f"\n\nSee {logfile}")
    except:
        pass
    sys.exit(1)

# 2) Import your Flask app & login UI under try/except
try:
    from app import app as flask_app
    from login import LoginApp
except Exception:
    tb = traceback.format_exc()
    logging.error("Import failure:\n" + tb)
    # Let the user know if possible
    try:
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror("Startup Error", "Failed to import modules:\n" + tb)
    except:
        pass
    sys.exit(1)

def start_flask():
    try:
        flask_app.run(host="127.0.0.1", port=5000, use_reloader=False)
    except Exception:
        tb = traceback.format_exc()
        logging.error("Flask startup failed:\n" + tb)
        # we could popup here, but thread might be headless

if __name__ == "__main__":
    # Catch *any* uncaught exceptions on the main thread
    def excepthook(exc_type, exc_value, exc_tb):
        tb = ''.join(traceback.format_exception(exc_type, exc_value, exc_tb))
        logging.error("Uncaught exception:\n" + tb)
        messagebox.showerror("Fatal Error", tb)
        sys.exit(1)
    sys.excepthook = excepthook

    # 3) Start Flask
    t = threading.Thread(target=start_flask, daemon=True)
    t.start()

    # 4) Give Flask a moment
    time.sleep(1.5)

    # 5) Launch your login UI
    root = tk.Tk()
    LoginApp(root)
    root.mainloop()
