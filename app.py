import sqlite3
import datetime
import uuid
import random
import string
from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash
from werkzeug.security import generate_password_hash, check_password_hash
import google.generativeai as genai

import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'gamerz_secret_key_2025'

# --- CONFIGURATION ---
GEMINI_API_KEY = "PASTE YOUR API HERE"  # (Using a placeholder key)
UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

try:
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-2.0-flash') 
except Exception as e:
    print(f"Error configuring AI: {e}")
    model = None

# --- DATABASE CONNECTION & DATA FETCHERS ---
def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

# --- GLOBAL GAME EXTRAS DATA ---
GAME_EXTRAS = {
    'Cyberpunk 2077': {
        'dlcs': [{'id': 11, 'title': 'Phantom Liberty', 'price': 29.99, 'desc': 'Spy-thriller expansion.', 'image': '/static/assets/cyberpunk/phantom_liberty.png'}],
        'editions': [{'id': 12, 'title': 'Ultimate Edition', 'price': 89.99, 'desc': 'Base Game + Phantom Liberty.', 'image': '/static/assets/cyberpunk/ultimate_edition.png'}],
        'specs': {
            'min': {'os': 'Windows 10', 'cpu': 'Core i7-6700 / Ryzen 5 1600', 'ram': '12GB', 'gpu': 'GTX 1060 6GB / RX 580', 'storage': '70GB SSD'},
            'rec': {'os': 'Windows 10', 'cpu': 'Core i7-12700 / Ryzen 7 7800X3D', 'ram': '16GB', 'gpu': 'RTX 2060 SUPER / RX 5700 XT', 'storage': '70GB SSD'}
        }
    },
    'Red Dead Redemption 2': {
        'dlcs': [{'id': 21, 'title': 'Story Mode Content', 'price': 9.99, 'desc': 'Bank Robbery Mission & Gang Hideout.'}],
        'editions': [{'id': 22, 'title': 'Ultimate Edition', 'price': 99.99, 'desc': 'Exclusive Story & Online content.'}],
        'specs': {
            'min': {'os': 'Windows 10', 'cpu': 'i5-2500K / FX-6300', 'ram': '8GB', 'gpu': 'GTX 770 / R9 280', 'storage': '150GB'},
            'rec': {'os': 'Windows 10', 'cpu': 'i7-4770K / Ryzen 5 1500X', 'ram': '12GB', 'gpu': 'GTX 1060 / RX 480', 'storage': '150GB'}
        }
    },
    'Resident Evil 4': {
        'dlcs': [{'id': 31, 'title': 'Separate Ways', 'price': 9.99, 'desc': 'Play as Ada Wong in this story expansion.'}],
        'editions': [{'id': 32, 'title': 'Deluxe Edition', 'price': 59.99, 'desc': 'Includes Extra DLC Pack.'}],
        'specs': {
            'min': {'os': 'Windows 10', 'cpu': 'Ryzen 3 1200 / i5-7500', 'ram': '8GB', 'gpu': 'RX 560 / GTX 1050 Ti', 'storage': '60GB'},
            'rec': {'os': 'Windows 10', 'cpu': 'Ryzen 5 3600 / i7-8700', 'ram': '16GB', 'gpu': 'RX 5700 / GTX 1070', 'storage': '60GB'}
        }
    },
    'God of War Ragnarok': {
        'dlcs': [{'id': 51, 'title': 'Valhalla', 'price': 'Free', 'desc': 'Roguelite mode epilogue.'}],
        'editions': [{'id': 52, 'title': 'Digital Deluxe', 'price': 79.99, 'desc': 'Darkdale Armor & Digital Artbook.'}],
        'specs': {
            'min': {'os': 'Windows 10', 'cpu': 'i5-4670K / Ryzen 3 1200', 'ram': '8GB', 'gpu': 'GTX 1060 / RX 580', 'storage': '190GB SSD'},
            'rec': {'os': 'Windows 10', 'cpu': 'i5-8600 / Ryzen 5 3600', 'ram': '16GB', 'gpu': 'RTX 2060 Super / RX 5700', 'storage': '190GB SSD'}
        }
    },
    'Elden Ring': {
        'dlcs': [{'id': 61, 'title': 'Shadow of the Erdtree', 'price': 39.99, 'desc': 'Massive expansion set in the Land of Shadow.'}],
        'editions': [{'id': 62, 'title': 'Shadow of the Erdtree Edition', 'price': 79.99, 'desc': 'Base Game + Expansion.'}],
        'specs': {
            'min': {'os': 'Windows 10', 'cpu': 'i5-8400 / Ryzen 3 3300X', 'ram': '12GB', 'gpu': 'GTX 1060 / RX 580', 'storage': '60GB'},
            'rec': {'os': 'Windows 10', 'cpu': 'i7-8700K / Ryzen 5 3600X', 'ram': '16GB', 'gpu': 'GTX 1070 / RX VEGA 56', 'storage': '60GB'}
        }
    },
    'Grand Theft Auto V': {
        'dlcs': [{'id': 71, 'title': 'Criminal Enterprise', 'price': 9.99, 'desc': 'Starter pack for GTA Online.'}],
        'editions': [{'id': 72, 'title': 'Premium Edition', 'price': 29.99, 'desc': 'Includes GTA V & Criminal Enterprise Pack.'}],
        'specs': {
            'min': {'os': 'Windows 10', 'cpu': 'Core 2 Quad Q6600', 'ram': '4GB', 'gpu': '9800 GT 1GB', 'storage': '72GB'},
            'rec': {'os': 'Windows 10', 'cpu': 'i5 3470 / FX-8350', 'ram': '8GB', 'gpu': 'GTX 660 / HD 7870', 'storage': '72GB'}
        }
    },
    'EA Sports FC 25': {
        'dlcs': [{'id': 81, 'title': 'FC Points', 'price': 19.99, 'desc': 'In-game currency for Ultimate Team.'}],
        'editions': [{'id': 82, 'title': 'Ultimate Edition', 'price': 99.99, 'desc': '4600 FC Points & Early Access.'}],
        'specs': {
            'min': {'os': 'Windows 10', 'cpu': 'i5-6600K / Ryzen 5 1600', 'ram': '8GB', 'gpu': 'GTX 1050 Ti / RX 570', 'storage': '100GB'},
            'rec': {'os': 'Windows 10', 'cpu': 'i7-6700 / Ryzen 7 2700X', 'ram': '12GB', 'gpu': 'GTX 1660 / RX 5600 XT', 'storage': '100GB'}
        }
    },
    'Dispatch': {
        'dlcs': [],
        'editions': [],
        'specs': {
            'min': {'os': 'Windows 10', 'cpu': 'i5-4590', 'ram': '8GB', 'gpu': 'GTX 970', 'storage': '20GB'},
            'rec': {'os': 'Windows 10', 'cpu': 'i7-6700', 'ram': '16GB', 'gpu': 'GTX 1070', 'storage': '20GB'}
        }
    }
}

def get_all_game_specs():
    conn = get_db_connection()
    specs = conn.execute('SELECT title, description, price, genre, rating FROM games').fetchall()
    conn.close()
    
    spec_list = []
    for game in specs:
        info = f"Title: {game['title']} | Genre: {game['genre']} | Price: ${game['price']} | Rating: {game['rating']}"
        
        # Append Extras if available
        if game['title'] in GAME_EXTRAS:
            extras = GAME_EXTRAS[game['title']]
            if 'dlcs' in extras:
                dlcs = ", ".join([f"{d['title']} (${d['price']})" for d in extras['dlcs']])
                info += f" | DLCs: {dlcs}"
            if 'editions' in extras:
                editions = ", ".join([f"{e['title']} (${e['price']})" for e in extras['editions']])
                info += f" | Editions: {editions}"
            if 'specs' in extras:
                min_specs = extras['specs']['min']
                rec_specs = extras['specs']['rec']
                info += f" | Min Specs: {min_specs['cpu']}, {min_specs['gpu']}, {min_specs['ram']}"
                info += f" | Rec Specs: {rec_specs['cpu']}, {rec_specs['gpu']}, {rec_specs['ram']}"
        
        spec_list.append(info)
    return "\n".join(spec_list)

# --- ADMIN CHECK (We assume user_id 1 is the admin) ---
def is_admin():
    return session.get('user_id') == 1

# --- CORE ROUTES (STOREFRONT) ---

@app.route('/')
def home():
    try:
        conn = get_db_connection()
        games = conn.execute("SELECT * FROM games WHERE genre NOT IN ('DLC', 'Edition')").fetchall()
        dlcs = conn.execute("SELECT * FROM games WHERE genre = 'DLC'").fetchall()
        editions = conn.execute("SELECT * FROM games WHERE genre = 'Edition'").fetchall()
        
        # Refresh user session data if logged in
        if 'user_id' in session:
            user = conn.execute('SELECT * FROM users WHERE id = ?', (session['user_id'],)).fetchone()
            if user:
                session['profile_photo'] = user['profile_photo']
        
        conn.close()

        featured_slides = [
            { 'id': 1, 'title': "Monster Hunter Wilds", 'subtitle': "Pre-Order Available: February 28, 2025", 'tagline': "The next generation of the hunt.", 'image': "/static/assets/featured/featured_mh.jpg", 'link': "/game/101" },
            { 'id': 2, 'title': "GTA VI: Postponed!", 'subtitle': "Pre-order now for Nov 2026 delivery.", 'tagline': "The ultimate open-world delay is confirmed.", 'image': "/static/assets/featured/featured_gta.jpg", 'link': "/preorder-gta6" },
            { 'id': 3, 'title': "RTX 5090 Launch", 'subtitle': "The Blackwall Beast is Here.", 'tagline': "Experience 8K gaming and run local AI models on 32GB GDDR7 VRAM.", 'image': "/static/assets/featured/featured_rtx.jpg", 'link': "/hardware/5090" }
        ]

        return render_template('index.html', games=games, dlcs=dlcs, editions=editions, featured_slides=featured_slides)
    except sqlite3.OperationalError:
        return "Database Error: Table 'games' not found. Run 'python3 init_db.py'."

@app.route('/profile', methods=['GET', 'POST'])
def profile():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    
    if request.method == 'POST':
        print("DEBUG: POST request received at /profile")
        if 'profile_photo' not in request.files:
            print("DEBUG: No file part")
            flash('No file part')
            return redirect(request.url)
            
        file = request.files['profile_photo']
        print(f"DEBUG: File received: {file.filename}")
        
        if file.filename == '':
            print("DEBUG: No selected file")
            flash('No selected file')
            return redirect(request.url)
            
        if file and allowed_file(file.filename):
            print("DEBUG: File allowed, processing...")
            # Use timestamp to force unique filename (avoids browser caching)
            import time
            ext = file.filename.rsplit('.', 1)[1].lower()
            timestamp = int(time.time())
            filename = secure_filename(f"user_{session['user_id']}_{timestamp}.{ext}")
            
            save_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            print(f"DEBUG: Saving to {save_path}")
            file.save(save_path)
            
            # Update DB
            conn.execute('UPDATE users SET profile_photo = ? WHERE id = ?', (filename, session['user_id']))
            conn.commit()
            session['profile_photo'] = filename # Update session
            flash('Profile photo updated!')
        else:
            print("DEBUG: File type not allowed")
            flash('Invalid file type. Allowed: png, jpg, jpeg, gif')
    
    user = conn.execute('SELECT * FROM users WHERE id = ?', (session['user_id'],)).fetchone()
    
    # Get User's Library (Join Orders + Games)
    library = conn.execute('''
        SELECT games.title, games.image, orders.key, orders.purchase_date, users.email
        FROM orders 
        JOIN games ON orders.game_id = games.id 
        JOIN users ON orders.user_id = users.id
        WHERE orders.user_id = ?
        ORDER BY orders.purchase_date DESC
    ''', (session['user_id'],)).fetchall()
    
    conn.close()
    return render_template('profile.html', user=user, library=library)


# ... (Existing /game/<id>, /signup, /login, /logout, /cart routes here) ...

@app.route('/game/<int:game_id>')
def game_details(game_id):
    conn = get_db_connection()
    game = conn.execute('SELECT * FROM games WHERE id = ?', (game_id,)).fetchone()
    # conn.close()  <-- REMOVED: Keep connection open for ownership check
    
    if game is None:
        conn.close()
        return "Game not found", 404

    # --- EXTRAS FROM GLOBAL DATA ---
    extras = GAME_EXTRAS.get(game['title'], {})

    # --- CHECK OWNERSHIP ---
    owned_game_ids = []
    if 'user_id' in session:
        orders = conn.execute('SELECT game_id FROM orders WHERE user_id = ?', (session['user_id'],)).fetchall()
        owned_game_ids = [order['game_id'] for order in orders]
    
    conn.close() # Close connection here
    return render_template('game_details.html', game=game, extras=extras, owned_game_ids=owned_game_ids)

# --- AUTHENTICATION ROUTES ---
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    # ... (existing signup logic) ...
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        
        hashed_pw = generate_password_hash(password, method='pbkdf2:sha256')
        
        try:
            conn = get_db_connection()
            conn.execute('INSERT INTO users (username, email, password) VALUES (?, ?, ?)',
                         (username, email, hashed_pw))
            conn.commit()
            conn.close()
            return redirect(url_for('login'))
            
        except sqlite3.IntegrityError:
            flash("Username or Email already exists!")
            return render_template('signup.html')

    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    # ... (existing login logic) ...
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
        conn.close()
        
        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            return redirect(url_for('home'))
        else:
            flash('Invalid Codename or Password!')
            
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

# --- ADMIN DASHBOARD (CRUD) ROUTES ---

@app.route('/admin')
def admin_index():
    if not is_admin():
        flash("Access Denied: Admin Clearance Required.")
        return redirect(url_for('login'))
        
    conn = get_db_connection()
    games = conn.execute('SELECT * FROM games').fetchall()
    conn.close()
    return render_template('admin_index.html', games=games) # R (Read)

@app.route('/admin/add', methods=['GET', 'POST'])
def admin_add():
    if not is_admin():
        flash("Access Denied: Admin Clearance Required.")
        return redirect(url_for('login'))
        
    if request.method == 'POST':
        conn = get_db_connection()
        conn.execute('INSERT INTO games (title, price, image, trailer, description, genre, rating) VALUES (?, ?, ?, ?, ?, ?, ?)',
                     (request.form['title'], request.form['price'], request.form['image'], request.form['trailer'], request.form['description'], request.form['genre'], request.form['rating']))
        conn.commit()
        conn.close()
        flash(f"Game '{request.form['title']}' added successfully.")
        return redirect(url_for('admin_index'))
        
    return render_template('admin_form.html', game={}) # C (Create)

@app.route('/admin/edit/<int:game_id>', methods=['GET', 'POST'])
def admin_edit(game_id):
    if not is_admin():
        flash("Access Denied: Admin Clearance Required.")
        return redirect(url_for('login'))
        
    conn = get_db_connection()
    
    if request.method == 'POST':
        conn.execute('UPDATE games SET title=?, price=?, image=?, trailer=?, description=?, genre=?, rating=? WHERE id=?',
                     (request.form['title'], request.form['price'], request.form['image'], request.form['trailer'], request.form['description'], request.form['genre'], request.form['rating'], game_id))
        conn.commit()
        conn.close()
        flash(f"Game '{request.form['title']}' updated successfully.")
        return redirect(url_for('admin_index'))
        
    game = conn.execute('SELECT * FROM games WHERE id = ?', (game_id,)).fetchone()
    conn.close()
    if game is None:
        flash("Game not found.")
        return redirect(url_for('admin_index'))
        
    return render_template('admin_form.html', game=game) # U (Update)

@app.route('/admin/delete/<int:game_id>', methods=['POST'])
def admin_delete(game_id):
    if not is_admin():
        flash("Access Denied: Admin Clearance Required.")
        return redirect(url_for('login'))
        
    conn = get_db_connection()
    conn.execute('DELETE FROM games WHERE id = ?', (game_id,))
    conn.commit()
    conn.close()
    flash("Game deleted successfully.")
    return redirect(url_for('admin_index')) # D (Delete)



# --- SHOPPING CART LOGIC & AI CHATBOT ---
@app.route('/add_to_cart', methods=['POST'])
def add_to_cart():
    # ... (existing add_to_cart logic) ...
    data = request.json
    game_id = data.get('game_id')
    
    if 'cart' not in session:
        session['cart'] = []
    
    if game_id not in session['cart']:
        session['cart'].append(game_id)
        session.modified = True
        return jsonify({"status": "success", "cart_count": len(session['cart'])})
    else:
        return jsonify({"status": "exists", "cart_count": len(session['cart'])})

@app.route('/cart')
def view_cart():
    # ... (existing view_cart logic) ...
    if 'cart' not in session or not session['cart']:
        return render_template('cart.html', games=[], total=0)
    
    conn = get_db_connection()
    placeholders = ','.join('?' for _ in session['cart'])
    query = f'SELECT * FROM games WHERE id IN ({placeholders})'
    cart_games = conn.execute(query, session['cart']).fetchall()
    conn.close()
    
    total_price = sum(game['price'] for game in cart_games)
    return render_template('cart.html', games=cart_games, total=round(total_price, 2))

@app.route('/remove_from_cart/<int:game_id>')
def remove_from_cart(game_id):
    if 'cart' in session:
        cart = session['cart']
        # Filter out the game with the given ID
        session['cart'] = [id for id in cart if id != game_id]
        session.modified = True
    return redirect(url_for('view_cart'))

@app.route('/clear_cart')
def clear_cart():
    session.pop('cart', None)
    return redirect(url_for('home'))

@app.route('/checkout')
def checkout():
    # ... (existing checkout logic) ...
    if 'cart' not in session or not session['cart']:
        return redirect(url_for('home'))
    
    conn = get_db_connection()
    placeholders = ','.join('?' for _ in session['cart'])
    query = f'SELECT * FROM games WHERE id IN ({placeholders})'
    cart_games = conn.execute(query, session['cart']).fetchall()
    
    purchased_items = []
    total_price = 0
    user_id = session.get('user_id')
    
    for game in cart_games:
        part1 = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
        part2 = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
        part3 = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
        part4 = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
        fake_key = f"{part1}-{part2}-{part3}-{part4}"
        
        purchased_items.append({
            'title': game['title'],
            'image': game['image'],
            'key': fake_key
        })
        total_price += game['price']
        
        if user_id:
            conn.execute('INSERT INTO orders (user_id, game_id, key) VALUES (?, ?, ?)',
                         (user_id, game['id'], fake_key))
    
    if user_id:
        conn.commit()
        
    conn.close()
    
    session.pop('cart', None)
    return render_template('order_success.html', items=purchased_items, total=total_price)

@app.route('/chat', methods=['POST'])
def chat():
    # ... (existing chat logic) ...
    if not model:
        return jsonify({"reply": "Error: AI Model failed to load."})

    data = request.json
    user_input = data.get('message')
    history = data.get('history', [])

    chat_session = model.start_chat(history=history)

    current_game_inventory = get_all_game_specs()
    today = datetime.date.today().strftime("%B %d, %Y")
    
    current_context = (
        f"IMPORTANT SYSTEM CONTEXT:\n"
        f"1. TODAY'S DATE: {today} (Late 2025).\n"
        f"2. HARDWARE STATUS (Released & In Stock): NVIDIA RTX 5090 (Released Jan 2025, $1999, 32GB VRAM).\n"
        f"3. GAME STATUS (Based on Store Data):\n"
        f"{current_game_inventory}\n"
        f"4. SPECIAL ALERTS:\n"
        f"   - GTA VI: DELAYED to Nov 2026. (Pre-order only).\n"
        f"5. ROLE: You are the Assistant for 'GamerZ'.\n"
        f"   - Use the inventory list above for all pricing and game facts.\n"
        f"   - When asked 'Can I run [Game]?', use your internal knowledge to compare hardware to the game's requirements.\n"
        f"6. FORMATTING RULES:\n"
        f"   - Use **bold** for key terms (Game Titles, Prices, Specs).\n"
        f"   - Use bullet points for lists (Editions, DLCs, Specs).\n"
        f"   - Keep answers concise and easy to read.\n"
        f"   - Use newlines to separate sections.\n"
    )
    
    full_message = f"{current_context}\nUser Query: {user_input}"

    try:
        response = chat_session.send_message(full_message)
        return jsonify({"reply": response.text})
    except Exception as e:
        print(f"\n\n!!! AI ERROR DETECTED !!!\n{e}\n!!!!!!!!!!!!!!!!!!!!!!!!!\n")
        return jsonify({"reply": f"Technical Error: {e}"})

if __name__ == '__main__':
    app.run(debug=True, port=5000)
