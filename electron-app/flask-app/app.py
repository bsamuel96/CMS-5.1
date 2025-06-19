# filepath: flask-app/app.py
from flask import Flask, jsonify, request, redirect
from flask_cors import CORS
from supabase import create_client, Client
from config import SUPABASE_URL, SUPABASE_KEY
import json
import os
import csv
import logging
from datetime import datetime
import sys
from google.oauth2 import service_account

# Determine the base path for data files
if getattr(sys, 'frozen', False):
    # Running in a PyInstaller bundle
    base_path = sys._MEIPASS
else:
    # Running in normal Python
    base_path = os.path.dirname(__file__)

# Point CONFIG_FILE, resources, and service account key to the correct folder
CONFIG_FILE = os.path.join(base_path, "config.json")
judete_localitati_path = os.path.join(base_path, 'resources', 'judete_localitati.json')
service_account_keyfile = os.path.join(base_path, 'driveuploader-456317-fdcff069c6d3.json')

# Load config.json
if os.path.exists(CONFIG_FILE):
    with open(CONFIG_FILE, "r") as config_file:
        config = json.load(config_file)
else:
    raise FileNotFoundError(f"Configuration file {CONFIG_FILE} not found.")

supabase_url = config.get("supabase_url")
supabase_key = config.get("supabase_key")

if not supabase_url or not supabase_key:
    raise ValueError("Supabase URL and key must be provided in the configuration file.")

# Load Google Service Account credentials
credentials = service_account.Credentials.from_service_account_file(
    service_account_keyfile,
    scopes=["https://www.googleapis.com/auth/drive"]
)

# Initialize Supabase client
supabase_client = create_client(supabase_url, supabase_key)

app = Flask(__name__)
CORS(app)

# Configure logging to save debug statements into a .txt file
LOG_FILE = os.path.join(os.path.dirname(__file__), 'debug_log.txt')

class RelevantFilter(logging.Filter):
    """Custom filter to include only relevant log messages."""
    def filter(self, record):
        # Include only messages with level WARNING or higher, or specific keywords
        return record.levelno >= logging.WARNING or "DEBUG" in record.msg or "ERROR" in record.msg

# Add a session separator
with open(LOG_FILE, "a") as log_file:
    log_file.write("\n" + "=" * 50 + f" SESSION START: {datetime.now()} " + "=" * 50 + "\n")

logging.basicConfig(
    filename=LOG_FILE,
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Add the custom filter to the root logger
logging.getLogger().addFilter(RelevantFilter())

# Temporary storage for tokens
tokens = {}

with open(judete_localitati_path, 'r', encoding='utf-8') as json_file:
    judete_localitati = json.load(json_file)

# Define constants for table names
TABLE_CLIENTS = "clients"
TABLE_VEHICLES = "vehicles"
TABLE_OFFERS = "offers"
TABLE_OFFER_PRODUCTS = "offer_products"
TABLE_ORDERS = "orders"
TABLE_ORDER_PRODUCTS = "order_products"
TABLE_PROFILES = "profiles"

def handle_api_error(func):
    """Decorator to handle errors in API endpoints."""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            app.logger.error(f"Error in {func.__name__}: {e}")
            return jsonify({"error": str(e)}), 500
    return wrapper

def paginate_results(queryset, page, per_page):
    """Utility function to paginate results."""
    offset = (page - 1) * per_page
    paginated_data = queryset[offset:offset + per_page]
    total_results = len(queryset)
    return paginated_data, total_results

def fetch_from_supabase(table, filters=None):
    """Fetch data from a Supabase table with optional filters."""
    query = supabase_client.table(table).select('*')
    if filters:
        for key, value in filters.items():
            query = query.eq(key, value)
    response = query.execute()
    return response

def insert_into_supabase(table, data):
    """Insert data into a Supabase table."""
    return supabase_client.table(table).insert(data).execute()

def update_supabase(table, data, filters):
    """Update data in a Supabase table with filters."""
    query = supabase_client.table(table).update(data)
    for key, value in filters.items():
        query = query.eq(key, value)
    return query.execute()

def delete_from_supabase(table, filters):
    """Delete data from a Supabase table with filters."""
    query = supabase_client.table(table).delete()
    for key, value in filters.items():
        query = query.eq(key, value)
    return query.execute()

@app.route('/get_judete', methods=['GET'], endpoint='get_judete')
@handle_api_error
def get_judete():
    """Return all counties (keys from the JSON)."""
    return jsonify(sorted(judete_localitati.keys()))

@app.route('/get_localitati/<judet>', methods=['GET'], endpoint='get_localitati')
@handle_api_error
def get_localitati(judet):
    """Return the list of localities for the given county."""
    localitati = judete_localitati.get(judet, [])
    return jsonify(sorted(localitati))

@app.route('/search_localitati', methods=['GET'], endpoint='search_localitati')
@handle_api_error
def search_localitati():
    query = request.args.get('query', '')
    results = []
    for judet, localitati in judete_localitati.items():
        for localitate in localitati:
            if query.lower() in localitate.lower():
                results.append({'judet': judet, 'localitate': localitate})
    return jsonify(results)

@app.route('/search_judete', methods=['GET'], endpoint='search_judete')
@handle_api_error
def search_judete():
    query = request.args.get('query', '')
    results = [judet for judet in judete_localitati.keys() if query.lower() in judet.lower()]
    return jsonify(results)

@app.route('/', endpoint='home')
def home():
    return "Welcome to the Flask App!"

@app.route('/login', methods=['POST'], endpoint='login')
@handle_api_error
def login():
    data = request.json
    username = data.get('username')
    password = data.get('password')

    print(f"Received login request for username: {username}")

    # Authenticate with Supabase
    response = supabase_client.auth.sign_in_with_password({
        'email': username,
        'password': password
    })
    print(f"Supabase response: {response}")
    if response.user is None:
        print("Login failed!")
        return jsonify({"message": "Autentificare eșuată!"}), 401
    print("Login successful!")
    user_id = response.user.id  # Get the user ID from the response
    return jsonify({"message": "Autentificare reușită!", "user_id": user_id})

@app.route('/add_client', methods=['POST'], endpoint='add_client')
@handle_api_error
def add_client():
    data = request.json
    response = insert_into_supabase(TABLE_CLIENTS, data)
    return jsonify(response.data)

@app.route('/clients', methods=['GET'], endpoint='get_clients')
@handle_api_error
def get_clients():
    name = request.args.get('name')
    filters = None
    if name:
        filters = {'nume': name}  # Use exact match for now
    print(f"[DEBUG] Filters for /clients endpoint: {filters}")  # Debug: Log the filters

    query = supabase_client.table(TABLE_CLIENTS).select('*')
    if filters:
        for key, value in filters.items():
            query = query.ilike(key, f"%{value}%")  # Use ilike for case-insensitive partial matching
    response = query.execute()

    print(f"[DEBUG] Response from Supabase for /clients: {response.data}")  # Debug: Log the response
    return jsonify(response.data)

@app.route('/clients/<client_id>', methods=['GET', 'PATCH'], endpoint='client_details')
@handle_api_error
def client_details(client_id):
    if request.method == 'GET':
        response = fetch_from_supabase(TABLE_CLIENTS, {'id': client_id})
        client = response.data[0] if response.data else None
        if client:
            print(f"[DEBUG] Selected client: {client}, Retrieved client_id: {client_id}")
            return jsonify(client), 200
        else:
            return jsonify({"message": "Clientul nu a fost găsit!"}), 404
    elif request.method == 'PATCH':
        data = request.json
        response = update_supabase(TABLE_CLIENTS, data, {'id': client_id})
        return jsonify(response.data)

@app.route('/delete_client', methods=['DELETE'], endpoint='delete_client')
@handle_api_error
def delete_client():
    client_id = request.args.get('client_id')
    response = delete_from_supabase(TABLE_CLIENTS, {'id': client_id})
    return jsonify(response.data)

@app.route('/vehicles', methods=['GET'], endpoint='get_vehicles')
@handle_api_error
def get_vehicles():
    client_id = request.args.get('client_id')
    if client_id is None:
        return jsonify({"message": "ID-ul clientului nu este valid."}), 400
    print(f"[DEBUG] Fetching vehicles for client_id: {client_id}")  # Debug statement
    response = fetch_from_supabase(TABLE_VEHICLES, {'client_id': client_id})
    print(f"[DEBUG] Retrieved vehicles: {response.data}")  # Debug statement
    return jsonify(response.data)

@app.route("/vehicle/<vehicle_id>", methods=["GET"], endpoint="get_vehicle_by_id")
def get_vehicle_by_id(vehicle_id):
    print(f"[DEBUG] Called /vehicle/{vehicle_id}")  # 👈 Added debug print
    try:
        response = supabase_client.table("vehicles").select("*").eq("id", vehicle_id).execute()
        print(f"[DEBUG] Vehicle response: {response.data}")  # 👈 Added debug print
        if response.data:
            return jsonify(response.data[0]), 200  # Ensure JSON response
        else:
            return jsonify({"error": "Vehicle not found"}), 404  # Return JSON error
    except Exception as e:
        app.logger.error(f"Error fetching vehicle details: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/vehicles/<vehicle_id>', methods=['PATCH'])
def update_vehicle(vehicle_id):
    """Update details of a specific vehicle by its ID."""
    try:
        # Log the incoming request data
        print(f"[DEBUG] Received update request for vehicle_id: {vehicle_id}")
        updated_data = request.json
        print(f"[DEBUG] Data received: {updated_data}")

        if not updated_data:
            return jsonify({"error": "No data provided"}), 400

        # Validate required fields
        required_fields = ["marca", "model", "an", "vin", "numar_inmatriculare"]
        for field in required_fields:
            if field not in updated_data:
                print(f"[ERROR] Missing required field: {field}")
                return jsonify({"error": f"Missing required field: {field}"}), 400

        # Check if the vehicle exists
        existing_vehicle = supabase_client.table('vehicles').select("*").eq('id', vehicle_id).execute()
        if not existing_vehicle.data:
            print(f"[ERROR] Vehicle with ID {vehicle_id} not found.")
            return jsonify({"error": "Vehicle not found"}), 404

        # Update the vehicle in the database
        response = supabase_client.table('vehicles').update(updated_data).eq('id', vehicle_id).execute()
        print(f"[DEBUG] Supabase response: {response}")

        # Check if the update was successful
        if response.data and len(response.data) > 0:
            print(f"[DEBUG] Vehicle updated successfully: {response.data}")
            return jsonify({"message": "Vehicle details updated successfully"}), 200
        else:
            print(f"[ERROR] Update failed. Supabase response: {response}")
            return jsonify({"error": "Failed to update vehicle details"}), 400
    except Exception as e:
        print(f"[ERROR] Exception occurred while updating vehicle details: {str(e)}")
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500

@app.route('/add_vehicle', methods=['POST'], endpoint='add_vehicle')
@handle_api_error
def add_vehicle():
    data = request.json
    response = insert_into_supabase(TABLE_VEHICLES, data)
    return jsonify(response.data)
    
@app.route('/search_vehicles', methods=['GET'])
def search_vehicles():
    """Search vehicles based on a query with pagination."""
    try:
        query = request.args.get('query', '')
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 10))

        # Call the Supabase RPC function
        response = supabase_client.rpc('search_vehicles', {
            'query': query,
            'page': page,
            'per_page': per_page
        }).execute()

        if response.data:
            return jsonify(response.data), 200
        else:
            return jsonify({"error": "No vehicles found"}), 404
    except Exception as e:
        print(f"[ERROR] Exception occurred while searching vehicles: {str(e)}")  # Debugging
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500

@app.route('/add_offer', methods=['POST'], endpoint='add_offer')
@handle_api_error
def add_offer():
    data = request.json
    print("[DEBUG] Full /add_offer payload:", json.dumps(data, indent=2))  # Debug log for the full payload

    client_id = data.get('client_id')
    vehicle_id = data.get('vehicle_id')
    offer_number = data.get('offer_number')  # Change variable name to offer_number
    categories = data.get('categories')
    status = data.get('status')
    observations = data.get('observations')
    raw_date = data.get('date')

    # Parse client-sent "dd/mm/yyyy" into ISO
    try:
        date_obj = datetime.strptime(raw_date, '%d/%m/%Y').date()
    except ValueError:
        # Assume it's already "YYYY-MM-DD"
        date_obj = datetime.fromisoformat(raw_date).date()

    # Ensure all required fields are provided
    if not all([client_id, vehicle_id, offer_number, categories, status, raw_date]):
        return jsonify({"message": "Toate câmpurile sunt obligatorii!"}), 400

    # Insert the new offer into the database
    response = insert_into_supabase(TABLE_OFFERS, {
        'client_id': client_id,
        'vehicle_id': vehicle_id,
        'offer_number': offer_number,  # Use offer_number instead of offer_id
        'status': status,
        'observations': observations,
        'date': date_obj.isoformat()  # Date should be in ISO format
    })

    # Nicio reasignare, doar verificare
    print(f"[DEBUG] Offer successfully inserted with number: {offer_number}")

    # Insert the products for each category
    for category, data in categories.items():
        print(f"[DEBUG] Adding category '{category}' with products: {data['products']}")  # Debug print
        for product in data['products']:
            result = insert_into_supabase(TABLE_OFFER_PRODUCTS, {
                'offer_number': offer_number,
                'categorie': category,
                'produs': product[0],
                'brand': product[1],
                'cod_produs': product[2],
                'cantitate': int(product[3]),  # Ensure cantitate is an integer
                'pret_unitar': float(product[4]),  # Ensure pret_unitar is a float
                'pret_total': float(product[5]),  # Ensure pret_total is a float
                'discount': float(product[6]) if product[6] else 0.0,  # Ensure discount is a float
                'pret_cu_discount': float(product[7])  # Ensure pret_cu_discount is a float
            })
            print(f"[DEBUG] Insert result for product: {result}")

    return jsonify({"message": "Ofertă adăugată cu succes!"}, 200)

@app.route('/offers', methods=['GET'], endpoint='get_offers')
@handle_api_error
def get_offers():
    client_id = request.args.get('client_id')
    if not client_id:
        app.logger.error("Client ID is missing in the request.")
        return jsonify({"error": "Client ID is required"}), 400

    app.logger.debug(f"Fetching offers for client_id: {client_id}")
    try:
        # Call the Supabase function
        response = supabase_client.rpc('get_offers_with_options', {'p_client_id': client_id}).execute()
        
        # Debug print for response data
        print("[DEBUG] /offers response data:", response.data)

        if response.data:
            # Fetch client name
            client_resp = fetch_from_supabase(TABLE_CLIENTS, {'id': client_id})
            client_name = client_resp.data[0]['nume'] if client_resp.data else "N/A"

            # Attach client name to each offer
            for offer in response.data:
                offer["client_name"] = client_name

            app.logger.debug(f"Offers fetched successfully: {response.data}")
            return jsonify(response.data), 200
        else:
            app.logger.error(f"No offers found for client_id: {client_id}")
            return jsonify({"error": "No offers found"}), 404
    except Exception as e:
        app.logger.error(f"Error fetching offers for client_id {client_id}: {e}")
        return jsonify({"error": f"Failed to fetch offers: {str(e)}"}), 500

@app.route('/offers/<offer_number>', methods=['GET'], endpoint='get_offer_details')
@handle_api_error
def get_offer_details(offer_number):
    print(f"Fetching full offer data for offer_number: {offer_number}")
    try:
        # Fetch the offer using a safer and debuggable query
        response = supabase_client.table(TABLE_OFFERS).select("*").eq("offer_number", offer_number).execute()
        if not response.data:
            print(f"[DEBUG] No offer found with number: {offer_number}")
            return jsonify({"message": "Ofertă nu a fost găsită!"}), 404

        offer = response.data[0]
        print(f"[DEBUG] Found offer: {offer}")

        # Fetch related products and build categories
        products_response = supabase_client.table(TABLE_OFFER_PRODUCTS).select("*").eq("offer_number", offer['offer_number']).execute()
        products = products_response.data or []
        categories = {}
        for product in products:
            category = product['categorie']
            if category not in categories:
                categories[category] = {"products": [], "total_price": 0}
            categories[category]["products"].append([
                product['produs'], product['brand'], product['cod_produs'],
                product['cantitate'], product['pret_unitar'], product['pret_total'],
                product['discount'], product['pret_cu_discount']
            ])
            categories[category]["total_price"] += product['pret_cu_discount']
        offer['categories'] = categories
        print(f"[DEBUG] categories built: {json.dumps(categories, indent=2)}")

        return jsonify(offer), 200  # Ensure proper JSON response
    except Exception as e:
        app.logger.error(f"Error calling get_full_offer_data: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/offers/<offer_number>', methods=['PATCH'], endpoint='update_offer')
@handle_api_error
def update_offer(offer_number):
    data = request.json
    vehicle_id = data.get('vehicle_id')
    categories = data.get('categories', {})  # ✅ Default to empty dict if None
    status = data.get('status')
    observations = data.get('observations')
    date = data.get('date')

    # Update the offer details
    response = update_supabase(TABLE_OFFERS, {
        'vehicle_id': vehicle_id,
        'status': status,
        'observations': observations,
        'date': date
    }, {'offer_number': offer_number})

    # ✅ Guard clause: skip if no categories
    if not categories:
        return jsonify({"message": "Ofertă actualizată fără produse."}), 200

    # Delete existing products
    delete_from_supabase(TABLE_OFFER_PRODUCTS, {'offer_number': response.data[0]['offer_number']})

    # Insert updated products
    for category, cat_data in categories.items():
        for product in cat_data['products']:
            insert_into_supabase(TABLE_OFFER_PRODUCTS, {
                'offer_number': response.data[0]['offer_number'],
                'categorie': category,
                'produs': product[0],
                'brand': product[1],
                'cod_produs': product[2],
                'cantitate': int(product[3]),
                'pret_unitar': float(product[4]),
                'pret_total': float(product[5]),
                'discount': float(product[6]) if product[6] else 0.0,
                'pret_cu_discount': float(product[7])
            })

    return jsonify({"message": "Ofertă actualizată cu succes!"}, 200)

@app.route('/update_offer_status', methods=['POST'])
def update_offer_status():
    print(f"[DEBUG] Raw request data: {request.data}")  # ✅ Log raw request data
    print(f"[DEBUG] request.is_json: {request.is_json}")  # ✅ Log JSON status
    data = request.get_json()
    offer_number = data.get("offer_number")
    new_status = data.get("new_status")

    if not offer_number or not new_status:
        return jsonify({"error": "Missing data"}), 400

    try:
        supabase_client.table("offers").update({"status": new_status}).eq("offer_number", offer_number).execute()
        return jsonify({"message": "Offer updated successfully"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/orders', methods=['GET'], endpoint='get_orders')
@handle_api_error
def get_orders():
    client_id = request.args.get('client_id')
    if not client_id:
        return jsonify({"error": "client_id query param is required"}), 400

    # 1. Fetch all orders for this client
    resp = supabase_client.table(TABLE_ORDERS) \
                         .select('*') \
                         .eq('client_id', client_id) \
                         .execute()
    orders = resp.data or []

    if not orders:
        return jsonify([]), 200

    # 2. Gather all order IDs
    order_ids = [o['id'] for o in orders]

    # 3. Fetch line items and payments for all orders
    prods_resp = supabase_client.table(TABLE_ORDER_PRODUCTS) \
                                .select('order_id, produs, brand, cod_produs, cantitate, pret_unitar, pret_total, discount, pret_cu_discount') \
                                .in_('order_id', order_ids) \
                                .execute()
    prods = prods_resp.data or []

    payments_resp = supabase_client.table('payments') \
                                   .select('order_id, amount, date, recorded_by, observations') \
                                   .in_('order_id', order_ids) \
                                   .execute()
    payments = payments_resp.data or []

    # 4. Build maps for totals, products, and payments per order_id
    totals_map = {}
    products_map = {}
    for p in prods:
        oid = p['order_id']
        totals_map[oid] = totals_map.get(oid, 0) + float(p['pret_cu_discount'])
        products_map.setdefault(oid, []).append(p)

    paid_map = {}
    payments_map = {}
    for p in payments:
        oid = p['order_id']
        paid_map[oid] = paid_map.get(oid, 0) + float(p['amount'])
        payments_map.setdefault(oid, []).append(p)

    # 5. Attach total, paid, balance, and lists (products + payments) to each order
    enriched_orders = []
    for o in orders:
        oid = o['id']
        total = totals_map.get(oid, 0.0)
        paid = paid_map.get(oid, 0.0)
        balance = total - paid

        enriched_orders.append({
            **o,  # Include all fields from the order
            "products": products_map.get(oid, []),
            "payments": payments_map.get(oid, []),
            "total": total,
            "paid": paid,
            "balance": balance
        })

    return jsonify(enriched_orders), 200

@app.route('/order_products', methods=['GET'])
@handle_api_error
def get_order_products():
    order_id = request.args.get('order_id')
    if not order_id:
        return jsonify({"error": "order_id query param is required"}), 400

    resp = supabase_client.table('order_products') \
                         .select('*') \
                         .eq('order_id', order_id) \
                         .execute()

    return jsonify(resp.data or []), 200

@app.route('/order_products/search', methods=['GET'], endpoint='search_order_product_by_code')
@handle_api_error
def search_order_product_by_code():
    order_id = request.args.get('order_id')
    cod_produs = request.args.get('cod_produs', '').strip()

    if not order_id or not cod_produs:
        return jsonify({"error": "order_id and cod_produs are required"}), 400

    resp = supabase_client.table(TABLE_ORDER_PRODUCTS) \
        .select('id, produs, brand, cod_produs, cantitate, pret_unitar, discount') \
        .eq('order_id', order_id) \
        .eq('cod_produs', cod_produs) \
        .execute()

    return jsonify(resp.data or []), 200

@app.route('/order_products/search_any', methods=['GET'], endpoint='search_order_product_by_any')
@handle_api_error
def search_order_products_by_any():
    order_id = request.args.get('order_id')
    term     = request.args.get('term', '').strip()

    if not order_id or not term:
        return jsonify({"error": "order_id and term are required"}), 400

    # Exact match on produs OR brand OR cod_produs, within that order
    response = supabase_client.table(TABLE_ORDER_PRODUCTS) \
        .select('id, produs, brand, cod_produs, cantitate, order_id') \
        .eq('order_id', order_id) \
        .or_(f'produs.eq.{term},brand.eq.{term},cod_produs.eq.{term}') \
        .execute()

    return jsonify(response.data or []), 200

@app.route('/delete_vehicle', methods=['DELETE'], endpoint='delete_vehicle')
@handle_api_error
def delete_vehicle():
    vehicle_id = request.args.get('vehicle_id')
    if not vehicle_id:
        return jsonify({"error": "vehicle_id is required"}), 400

    response = delete_from_supabase(TABLE_VEHICLES, {'id': vehicle_id})
    print(f"Supabase response: {response}")  # Add detailed logging
    if response.data:
        return jsonify({"message": "Vehicle deleted successfully"}), 200
    else:
        return jsonify({"message": "Vehicle deleted successfully, but no rows were affected"}), 200

@app.route('/highest_offer_number', methods=['GET'], endpoint='highest_offer_number')
@handle_api_error
def highest_offer_number():
    response = fetch_from_supabase(TABLE_OFFERS)
    offer_numbers = [int(offer['offer_number'][1:]) for offer in response.data if offer['offer_number'].startswith('O')]
    highest_offer_number = f"O{max(offer_numbers)}" if offer_numbers else 'O0'
    return jsonify({"highest_offer_number": highest_offer_number}), 200

@app.route('/search_universal', methods=['GET'], endpoint='search_universal')
@handle_api_error
def search_universal():
    """Search across multiple categories."""
    query = request.args.get('query', '').strip()
    category = request.args.get('category', '').strip().lower()
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 1000000))  # Set a very high default limit

    logging.debug(f"Received search request: query='{query}', category='{category}', page={page}, per_page={per_page}")

    if not query or not category:
        logging.error("Query or category is missing.")
        return jsonify({"error": "Query and category are required"}), 400

    try:
        # Call the Supabase RPC function
        logging.debug("Calling Supabase RPC function 'search_universal'.")
        response = supabase_client.rpc("search_universal", {
            "query": query,
            "category": category,
            "page": page,
            "per_page": per_page
        }).execute()

        logging.debug(f"Supabase RPC raw response: {response.data}")

        # Check if it's a single JSON string in a list
        if isinstance(response.data, list) and len(response.data) == 1 and isinstance(response.data[0], str):
            try:
                results = json.loads(response.data[0])
            except json.JSONDecodeError:
                logging.error("Failed to decode JSON from search_universal RPC.")
                return jsonify({"error": "Invalid response from search_universal function"}), 500
        else:
            results = response.data

        logging.debug(f"Processed results for category '{category}': {results}")

        # Transform flat data into nested structure for specific categories
        if category == "order_products":
            for item in results:
                item["order"] = {
                    "id": item.get("order", {}).get("id"),
                    "order_number": item.get("order", {}).get("order_number"),
                }
                item["client"] = {
                    "id": item.get("client", {}).get("id"),
                    "nume": item.get("client", {}).get("nume"),
                    "telefon": item.get("client", {}).get("telefon"),
                }
                item["vehicle"] = {
                    "marca": item.get("vehicle", {}).get("marca"),
                    "model": item.get("vehicle", {}).get("model"),
                    "numar_inmatriculare": item.get("vehicle", {}).get("numar_inmatriculare"),
                    "vin": item.get("vehicle", {}).get("vin"),
                    "an": item.get("vehicle", {}).get("an"),
                }
                item["order_product"] = {
                    "produs": item.get("order_product", {}).get("produs"),
                    "brand": item.get("order_product", {}).get("brand"),
                    "cod_produs": item.get("order_product", {}).get("cod_produs"),
                    "cantitate": item.get("order_product", {}).get("cantitate"),
                    "pret_unitar": item.get("order_product", {}).get("pret_unitar"),
                    "pret_total": item.get("order_product", {}).get("pret_total"),
                    "discount": item.get("order_product", {}).get("discount"),
                    "pret_cu_discount": item.get("order_product", {}).get("pret_cu_discount"),
                }

        elif category == "offer_products":
            for item in results:
                item["offer"] = {
                    "id": item.get("offer", {}).get("id"),
                    "offer_number": item.get("offer", {}).get("offer_number"),
                }
                item["client"] = {
                    "id": item.get("client", {}).get("id"),
                    "nume": item.get("client", {}).get("nume"),
                    "telefon": item.get("client", {}).get("telefon"),
                }
                item["vehicle"] = {
                    "marca": item.get("vehicle", {}).get("marca"),
                    "model": item.get("vehicle", {}).get("model"),
                    "numar_inmatriculare": item.get("vehicle", {}).get("numar_inmatriculare"),
                    "vin": item.get("vehicle", {}).get("vin"),
                    "an": item.get("vehicle", {}).get("an"),
                }
                item["offer_product"] = {
                    "produs": item.get("offer_product", {}).get("produs"),
                    "brand": item.get("offer_product", {}).get("brand"),
                    "cod_produs": item.get("offer_product", {}).get("cod_produs"),
                    "cantitate": item.get("offer_product", {}).get("cantitate"),
                    "pret_unitar": item.get("offer_product", {}).get("pret_unitar"),
                    "pret_total": item.get("offer_product", {}).get("pret_total"),
                    "discount": item.get("offer_product", {}).get("discount"),
                    "pret_cu_discount": item.get("offer_product", {}).get("pret_cu_discount"),
                }

        logging.debug(f"Transformed results for category '{category}': {results}")
        return jsonify(results), 200
    except Exception as e:
        logging.error(f"Error during search_universal: {e}")
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500

@app.route('/totals/<client_id>', methods=['GET'], endpoint='get_totals')
@handle_api_error
def get_totals(client_id):
    """Calculate totals for a specific client:
       - total_cheltuit: sumă totală a tuturor pret_cu_discount din order_products
       - de_platit: soldul rămas (order_total – suma plăților), doar dacă este > 0
       - sold: suma refund-urilor înregistrate în return_products
       - total_comenzi: numărul total de comenzi pentru client
    """
    # 1. Fetch all orders for acest client
    orders_resp = supabase_client.table(TABLE_ORDERS) \
                                 .select('id') \
                                 .eq('client_id', client_id) \
                                 .execute()
    orders = orders_resp.data or []
    order_ids = [o['id'] for o in orders]

    # Dacă nu există comenzi, returnăm toate valorile 0
    if not order_ids:
        return jsonify({
            "total_cheltuit": 0.0,
            "de_platit":      0.0,
            "sold":           0.0,
            "total_comenzi":  0
        }), 200

    # 2. Fetch all order_products pentru aceste order_ids  
    prods_resp = supabase_client.table(TABLE_ORDER_PRODUCTS) \
                                .select('id, order_id, pret_cu_discount') \
                                .in_('order_id', order_ids) \
                                .execute()
    prods = prods_resp.data or []

    # 3. Construim două hărți:
    #    - totals_map: order_id -> suma pret_cu_discount (totalul comenzii)
    #    - op_ids: lista tuturor order_product.id pentru a căuta refund-uri
    totals_map = {}
    op_ids = []
    for p in prods:
        oid = p['order_id']
        op_ids.append(p['id'])
        totals_map[oid] = totals_map.get(oid, 0) + float(p.get('pret_cu_discount', 0))

    # 4. Fetch plățile (payments) pentru aceste order_ids
    payments_resp = supabase_client.table('payments') \
                                   .select('order_id, amount') \
                                   .in_('order_id', order_ids) \
                                   .execute()
    payments = payments_resp.data or []

    # 5. Construim un map payment_map: order_id -> suma plătită
    paid_map = {}
    for pay in payments:
        oid = pay['order_id']
        paid_map[oid] = paid_map.get(oid, 0) + float(pay.get('amount', 0))

    # 6. Calculăm:
    #    - total_cheltuit = suma tuturor pret_cu_discount (orice comandă, indiferent de plată)
    #    - de_platit = suma pentru fiecare order unde (order_total - paid) > 0
    total_cheltuit = sum(totals_map.values())
    de_platit = 0.0
    for oid, order_total in totals_map.items():
        paid = paid_map.get(oid, 0.0)
        balance = order_total - paid
        if balance > 0:
            de_platit += balance

    # 7. Calculăm refund-uri (suma din return_products) doar pentru order_product_ids op_ids
    refund_amount = 0.0
    if op_ids:
        returns_resp = supabase_client.table('return_products') \
                                      .select('total_refund') \
                                      .in_('order_product_id', op_ids) \
                                      .execute()
        returns = returns_resp.data or []
        for r in returns:
            refund_amount += float(r.get('total_refund', 0))

    # 8. Număr total comenzi
    total_comenzi = len(order_ids)

    return jsonify({
        "total_cheltuit": round(total_cheltuit, 2),
        "de_platit":      round(de_platit, 2),
        "sold":           round(refund_amount, 2),
        "total_comenzi":  total_comenzi
    }), 200

@app.route('/sales_report', methods=['GET'], endpoint='sales_report')
@handle_api_error
def sales_report():
    """Return a sales report grouped by localitate and judet with total sales and number of orders."""

    # Fetch all orders
    orders_response = fetch_from_supabase(TABLE_ORDERS)
    orders = orders_response.data if orders_response.data else []

    # Fetch all order_products
    order_products_response = fetch_from_supabase(TABLE_ORDER_PRODUCTS)
    order_products = order_products_response.data if order_products_response.data else []

    # Fetch clients (needed for localitate and judet)
    clients_response = fetch_from_supabase(TABLE_CLIENTS)
    clients = clients_response.data if clients_response.data else []

    # Map client ID -> localitate + judet
    client_map = {
        client["id"]: {
            "localitate": client.get("localitate", "N/A"),
            "judet": client.get("judet", "N/A")
        } for client in clients
    }

    # Map order_id → list of product prices (cu discount)
    order_product_totals = {}
    for prod in order_products:
        order_id = prod.get("order_id")
        total = float(prod.get("pret_cu_discount", 0))
        order_product_totals.setdefault(order_id, 0)
        order_product_totals[order_id] += total

    # Build final report
    report = {}
    for order in orders:
        client_id = order.get("client_id")
        order_id = order.get("id")
        total_vanzare = order_product_totals.get(order_id, 0)

        if client_id not in client_map:
            continue

        loc = client_map[client_id]["localitate"]
        jud = client_map[client_id]["judet"]
        key = (loc, jud)

        if key not in report:
            report[key] = {"nr_comenzi": 0, "total_vanzari": 0.0}

        report[key]["nr_comenzi"] += 1
        report[key]["total_vanzari"] += total_vanzare

    # Format final JSON response
    response_data = [
        {
            "localitate": loc,
            "judet": jud,
            "nr_comenzi": data["nr_comenzi"],
            "total_vanzari": round(data["total_vanzari"], 2)
        }
        for (loc, jud), data in sorted(report.items())
    ]

    return jsonify(response_data), 200

@app.route('/top_clients', methods=['GET'], endpoint='top_clients')
@handle_api_error
def top_clients():
    """Return top clients by total value or number of orders."""

    sort_by = request.args.get('sort_by', 'Total Cheltuit')

    # Fetch all clients, orders, and order products
    clients = fetch_from_supabase(TABLE_CLIENTS).data or []
    orders = fetch_from_supabase(TABLE_ORDERS).data or []
    order_products = fetch_from_supabase(TABLE_ORDER_PRODUCTS).data or []

    # Build a lookup for products by order_id
    order_totals = {}
    for prod in order_products:
        order_id = prod.get('order_id')
        total = float(prod.get('pret_cu_discount') or 0)
        order_totals[order_id] = order_totals.get(order_id, 0) + total

    # Aggregate totals per client
    client_stats = {}
    for order in orders:
        client_id = order.get('client_id')
        if not client_id:
            continue

        if client_id not in client_stats:
            client_stats[client_id] = {
                'nr_comenzi': 0,
                'total_cheltuit': 0.0
            }

        client_stats[client_id]['nr_comenzi'] += 1
        client_stats[client_id]['total_cheltuit'] += order_totals.get(order['id'], 0.0)

    # Build final response including only clients with at least one order
    results = []
    for client in clients:
        client_id = client.get('id')
        stats = client_stats.get(client_id)
        if not stats:
            continue  # Skip clients with no orders

        results.append({
            "nume": client.get("nume", "N/A"),
            "nr_comenzi": stats["nr_comenzi"],
            "total_cheltuit": round(stats["total_cheltuit"], 2)
        })

    # Sort results
    if sort_by == "Nr. Comenzi":
        results.sort(key=lambda x: x["nr_comenzi"], reverse=True)
    else:
        results.sort(key=lambda x: x["total_cheltuit"], reverse=True)

    return jsonify(results), 200

@app.route('/debts', methods=['GET'], endpoint='debts_report')
@handle_api_error
def debts_report():
    """Return a list of clients with outstanding debts (unpaid or partially paid orders)."""

    # Fetch relevant orders
    relevant_statuses = [
        "Comandată și neplătită",
        "Comandată și plătită parțial",
        "Ridicată și neplătită",
        "Ridicată și plătită parțial"
    ]
    orders_response = supabase_client.table("orders").select("*").in_("plata", relevant_statuses).execute()
    orders = orders_response.data or []

    if not orders:
        return jsonify([]), 200

    # Fetch products from these orders
    order_ids = [order["id"] for order in orders]
    order_products_response = supabase_client.table("order_products").select("*").in_("order_id", order_ids).execute()
    order_products = order_products_response.data or []

    # Fetch payments related to these orders
    payments_response = supabase_client.table("payments").select("*").in_("order_id", order_ids).execute()
    payments = payments_response.data or []

    # Fetch clients and vehicles
    clients_response = supabase_client.table("clients").select("*").execute()
    clients = {client["id"]: client for client in clients_response.data}

    vehicles_response = supabase_client.table("vehicles").select("*").execute()
    vehicle_map = {v["id"]: v for v in vehicles_response.data}

    # Compute debts per client
    client_debts = {}

    for order in orders:
        client_id = order["client_id"]
        vehicle = vehicle_map.get(order.get("vehicle_id"), {})
        order_id = order["id"]

        # Calculate total from order products
        order_total = sum(
            float(p["pret_cu_discount"]) for p in order_products if p["order_id"] == order_id
        )

        # Calculate payments for this order
        order_paid = sum(
            float(p["amount"]) for p in payments if p["order_id"] == order_id
        )

        # If still debt, record it
        debt_remaining = order_total - order_paid
        if debt_remaining > 0:
            if client_id not in client_debts:
                client = clients.get(client_id, {})
                client_debts[client_id] = {
                    "nume": client.get("nume", "N/A"),
                    "telefon": client.get("telefon", "N/A"),
                    "adresa": f"{client.get('adresa', '')}, {client.get('localitate', '')}, {client.get('judet', '')}",
                    "suma_datorata": 0.0,
                    "vehicul": f"{vehicle.get('marca', '')} {vehicle.get('model', '')} ({vehicle.get('numar_inmatriculare', '')})"
                }

            client_debts[client_id]["suma_datorata"] += debt_remaining

    # Convert to list
    result = list(client_debts.values())
    result.sort(key=lambda x: x["suma_datorata"], reverse=True)

    return jsonify(result), 200

@app.route('/add_payment', methods=['POST'], endpoint='add_payment')
@handle_api_error
def add_payment():
    data = request.json
    client_id = data.get('client_id')
    order_id = data.get('order_id')
    amount = float(data.get('amount', 0))
    observations = data.get('observations', "")
    recorded_by = data.get('recorded_by', "admin")
    now = datetime.utcnow().isoformat()

    # 1. Insert payment
    insert_resp = insert_into_supabase("payments", [{
        "client_id": client_id,
        "order_id": order_id,
        "amount": amount,
        "recorded_by": recorded_by,
        "observations": observations,
        "date": now
    }])

    # 2. Calculate total paid for this order
    payments_resp = supabase_client.table("payments").select("amount").eq("order_id", order_id).execute()
    total_paid = sum(float(p["amount"]) for p in payments_resp.data)

    # 3. Calculate total order amount
    products_resp = supabase_client.table("order_products").select("pret_cu_discount").eq("order_id", order_id).execute()
    total_order = sum(float(p["pret_cu_discount"]) for p in products_resp.data)

    # 4. Fetch current order status (can be None)
    order_resp = supabase_client.table("orders").select("plata").eq("id", order_id).execute()
    raw_status = order_resp.data[0].get("plata") if order_resp.data else None

    # Normalize to an empty string if None
    current_status = raw_status or ""

    # 5. Update status only if it doesn't start with "Ridicată"
    if not current_status.startswith("Ridicată"):
        if total_paid >= total_order:
            new_status = "Comandată și plătită"
        else:
            new_status = "Comandată și plătită parțial"

        # Update the `plata` field in the orders table
        update_supabase("orders", {"plata": new_status}, {"id": order_id})

    return jsonify({"message": "Plata înregistrată cu succes"}), 200

@app.route('/returnable_items', methods=['GET'], endpoint='get_returnable_items')
@handle_api_error
def get_returnable_items():
    """Given an order_id, list all its products with how many remain eligible for return."""
    order_id = request.args.get('order_id')
    if not order_id:
        return jsonify({"error": "order_id is required"}), 400

    # 1. Fetch all order_products for this order
    items = supabase_client.table('order_products') \
        .select('id, produs, brand, cod_produs, cantitate, pret_unitar, discount') \
        .eq('order_id', order_id) \
        .execute().data or []

    # 2. Fetch all returns for these items
    item_ids = [i['id'] for i in items]
    returned = supabase_client.table('return_products') \
        .select('order_product_id, return_qty') \
        .in_('order_product_id', item_ids) \
        .execute().data or []

    # 3. Build a map of how many have already been returned
    returned_map = {}
    for r in returned:
        returned_map[r['order_product_id']] = returned_map.get(r['order_product_id'], 0) + r['return_qty']

    # 4. Attach eligible_qty = sold_cantitate – already_returned
    for i in items:
        sold = int(i['cantitate'])
        ret  = returned_map.get(i['id'], 0)
        i['eligible_qty'] = max(sold - ret, 0)

    return jsonify(items), 200

@app.route('/add_return', methods=['POST'], endpoint='add_return')
@handle_api_error
def add_return():
    """Record returned items and compute refund same as original sale price."""
    data = request.json
    op_id        = data.get('order_product_id')
    ret_qty      = int(data.get('return_qty', 0))
    notes        = data.get('notes', '')

    if not op_id or ret_qty <= 0:
        return jsonify({"error": "order_product_id and positive return_qty required"}), 400

    # 1. Fetch the original order_product to get price + discount
    op = supabase_client.table('order_products') \
        .select('pret_unitar, discount') \
        .eq('id', op_id) \
        .single() \
        .execute().data

    unit_price   = float(op['pret_unitar'])
    discount_pct = float(op['discount'])
    refund_total = ret_qty * unit_price * (1 - discount_pct/100)

    # 2. Insert into return_products
    supabase_client.table('return_products').insert({
        'order_product_id': op_id,
        'return_qty':       ret_qty,
        'unit_price':       unit_price,
        'discount_pct':     discount_pct,
        'total_refund':     refund_total,
        'notes':            notes
    }).execute()

    return jsonify({"message": "Return recorded", "refund": round(refund_total,2)}), 200

@app.route("/add_order", methods=["POST"], endpoint="add_order")
@handle_api_error
def add_order():
    data = request.get_json()
    offer_number = data.get("offer_number")
    selected_category = data.get("selected_category")
    status = data.get("status", "Comandată și neplătită")
    amount_paid = float(data.get("amount_paid", 0))
    observations = data.get("observations", "")
    date = data.get("date", datetime.utcnow().strftime("%Y-%m-%d"))

    # 1. Get offer details
    offer_resp = supabase_client.table("offers").select("*").eq("offer_number", offer_number).single().execute()
    if not offer_resp.data:
        return jsonify({"error": "Oferta nu a fost găsită!"}), 404
    offer = offer_resp.data

    # 2. Insert new order
    order_resp = supabase_client.table("orders").insert({
        "client_id": offer["client_id"],
        "vehicle_id": offer["vehicle_id"],
        "date": date,
        "status": status,  # ✅ CORECT: folosește `status`
        "observations": observations,
        "order_number": data.get("order_number", f"CMD{int(datetime.now().timestamp())}"),
        "source_offer_number": offer["offer_number"],  # ✅ Add source_offer_number
        "source_category": selected_category           # ✅ Add source_category
    }).execute()

    if not order_resp.data:
        return jsonify({"error": "Eroare la inserarea comenzii!"}), 500
    new_order_id = order_resp.data[0]["id"]

    # 3. Get products from offer_products
    products_resp = supabase_client.table("offer_products") \
        .select("*") \
        .eq("offer_number", offer_number) \
        .eq("categorie", selected_category) \
        .execute()
    if not products_resp.data:
        return jsonify({"error": "Nu există produse pentru această categorie!"}), 400

    # 4. Insert products into order_products
    try:
        for product in products_resp.data:
            supabase_client.table("order_products").insert({
                "order_id": new_order_id,
                "produs": str(product["produs"]),
                "brand": str(product["brand"]),
                "cod_produs": str(product["cod_produs"]),
                "cantitate": int(float(product["cantitate"])),  # ✅ Safe integer conversion
                "pret_unitar": float(product["pret_unitar"]),   # ✅ Safe float conversion
                "pret_total": float(product["pret_total"]),     # ✅ Safe float conversion
                "discount": float(product["discount"]) if product["discount"] is not None else 0.0,  # ✅ Handle None
                "pret_cu_discount": float(product["pret_cu_discount"])  # ✅ Safe float conversion
            }).execute()
    except Exception as e:
        app.logger.error(f"Error inserting product: {product} — {e}")
        return jsonify({"error": f"Eroare la salvarea produselor: {e}"}), 500

    # 5. Insert payment if amount_paid > 0
    if amount_paid > 0:
        supabase_client.table("payments").insert({
            "client_id": offer["client_id"],
            "order_id": new_order_id,
            "amount": amount_paid,
            "recorded_by": "admin",
            "observations": observations,
            "date": datetime.utcnow().isoformat()
        }).execute()

    return jsonify({"message": "Comandă salvată!", "order_id": new_order_id}), 200

@app.route("/orders/<order_number>", methods=["GET"], endpoint="get_order_by_number")
def get_order_by_number(order_number):
    result = supabase_client.table("orders").select("*").eq("order_number", order_number).execute()
    if result.data:
        return jsonify(result.data[0])
    else:
        return jsonify({"error": "Order not found"}), 404

@app.route('/payments', methods=['GET'], endpoint='get_payments')
@handle_api_error
def get_payments():
    client_id = request.args.get('client_id')
    order_id  = request.args.get('order_id')

    # 1. Base query on payments table
    query = supabase_client.table('payments') \
                           .select('id, date, client_id, order_id, amount, recorded_by, observations')

    # 2. Apply filters if provided
    if client_id:
        query = query.eq('client_id', client_id)
    if order_id:
        query = query.eq('order_id', order_id)

    payments_resp = query.execute()
    payments = payments_resp.data or []

    # 3. Fetch clients to map IDs → names
    client_ids = list({p['client_id'] for p in payments})
    clients = supabase_client.table(TABLE_CLIENTS) \
                             .select('id, nume') \
                             .in_('id', client_ids) \
                             .execute().data or []
    client_map = {c['id']: c['nume'] for c in clients}

    # 4. Fetch orders to map IDs → order_number
    order_ids = [p['order_id'] for p in payments if p['order_id']]
    orders = supabase_client.table(TABLE_ORDERS) \
                            .select('id, order_number') \
                            .in_('id', order_ids) \
                            .execute().data or []
    order_map = {o['id']: o['order_number'] for o in orders}

    # 5. Build the final list with Romanian labels
    result = []
    for p in payments:
        result.append({
            'id':             p['id'],
            'data':           p['date'],
            'client':         client_map.get(p['client_id'], ''),
            'comanda':        order_map.get(p['order_id'], ''),
            'suma':           p['amount'],
            'inregistrat_de': p['recorded_by'],
            'observations':   p.get('observations', '')
        })

    return jsonify(result), 200

@app.route('/order_products/search_global', methods=['GET'], endpoint='search_order_products_global')
@handle_api_error
def search_order_products_global():
    """
    Global product search (no order filter). Exact, case-insensitive,
    hyphens in term are ignored. Returns the order each item belongs to.
    """
    term = request.args.get('term', '').strip()
    if not term:
        return jsonify({"error": "`term` query param is required"}), 400

    # Remove any hyphens in the user’s term
    cleaned = term.replace('-', '')

    # Call the RPC we just created
    resp = supabase_client.rpc('search_order_products_global', {
        'p_term': cleaned
    }).execute()

    # Ensure the response includes the required keys
    return jsonify(resp.data or []), 200

if __name__ == '__main__':
    print("Starting Flask app...")
    app.run(debug=True, host='127.0.0.1', port=5000)