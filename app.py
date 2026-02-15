import os
import csv
import io
from flask import Flask, render_template, request, redirect, session, jsonify, url_for
from flask_sqlalchemy import SQLAlchemy
from Cryptodome.Util.number import getPrime
from random import randint
from flask import send_from_directory
import json


app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///voting.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.secret_key = "your_secret_key"
app.static_folder = "static"
app.config['UPLOAD_FOLDER'] = 'uploads'

# Ensure the uploads directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

db = SQLAlchemy(app)    

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True)
    password = db.Column(db.String(50))
    role = db.Column(db.String(10))
    voted = db.Column(db.Integer)

class Candidate(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    age = db.Column(db.Integer)
    sex = db.Column(db.String(10))
    area = db.Column(db.String(100))
    party = db.Column(db.String(50))
    votes = db.Column(db.Integer)
    agenda = db.Column(db.Text)
    description = db.Column(db.Text)
    candidate_image = db.Column(db.String(255))  # Store image file name or path

count = 0

class Paillier:
    def __init__(self, bit_length=10, key_file="paillier_keys.json"):
        self.key_file = key_file

        # Load keys if they exist; otherwise, generate new ones
        if os.path.exists(self.key_file):
            with open(self.key_file, "r") as f:
                keys = json.load(f)
                self.n = keys["n"]
                self.lmbda = keys["lmbda"]
                self.mu = keys["mu"]
                self.n_square = self.n * self.n
                self.g = self.n + 1
        else:
            p = getPrime(bit_length)
            q = getPrime(bit_length)
            self.n = p * q
            self.n_square = self.n * self.n
            self.g = self.n + 1
            self.lmbda = (p - 1) * (q - 1)
            self.mu = self.mod_inverse(self.lmbda, self.n)

            # Save the keys for future use
            with open(self.key_file, "w") as f:
                json.dump({"n": self.n, "lmbda": self.lmbda, "mu": self.mu}, f)

    def mod_inverse(self, a, m):
        def egcd(a, b):
            if a == 0:
                return b, 0, 1
            else:
                g, x, y = egcd(b % a, a)
                return g, y - (b // a) * x, x

        g, x, _ = egcd(a, m)
        if g != 1:
            raise Exception("Modular inverse does not exist.")
        else:
            return x % m

    def encrypt(self, plaintext):
        r = randint(1, self.n - 1)
        c = (
            pow(self.g, plaintext, self.n_square) * pow(r, self.n, self.n_square)
        ) % self.n_square
        return c

    def decrypt(self, ciphertext):
        numerator = pow(ciphertext, self.lmbda, self.n_square) - 1
        plaintext = (numerator // self.n * self.mu) % self.n
        return plaintext

paillier = Paillier()

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    """Serve uploaded files."""
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route("/")
def home():
    return render_template("login.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        user = User.query.filter_by(username=username, password=password).first()
        if user:
            session["user_id"] = user.id
            if user.role == "Admin":
                return redirect("/admin_panel")
            else:
                return redirect("/user_panel")
        else:
            return render_template("login.html", error="Invalid username or password")
    return render_template("login.html")

@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        role = request.form["role"]
        new_user = User(username=username, password=password, role=role, voted=0)
        db.session.add(new_user)
        db.session.commit()
        return redirect("/login")
    return render_template("signup.html")

@app.route("/admin_panel", methods=["GET", "POST"])
def admin_dashboard():
    if "user_id" in session:
        user_id = session["user_id"]
        user = db.session.get(User, user_id)  # Corrected this line
        if user.role == "Admin":
            return render_template("admin_panel.html")
    return redirect("/login")

@app.route("/add_candidate", methods=["GET", "POST"])
def add_candidate():
    if request.method == "POST":
        name = request.form["candidate_name"]
        age = request.form["age"]
        sex = request.form["sex"]
        area = request.form["area"]
        party = request.form["party"]
        agenda = request.form["agenda"]
        description = request.form["description"]

        # Handle image upload
        image = request.files["candidate_image"]
        if image and image.filename:
            # Save the uploaded image to the "uploads" folder
            image_filename = image.filename
            image_path = os.path.join(app.config['UPLOAD_FOLDER'], image_filename)
            image.save(image_path)
        else:
            image_filename = None  # Default value if no image is uploaded

        # Create a new candidate
        new_candidate = Candidate(
            name=name, age=age, sex=sex, area=area, party=party,
            agenda=agenda, description=description, candidate_image=image_filename,
            votes=paillier.encrypt(0)
        )
        db.session.add(new_candidate)
        db.session.commit()
        return redirect("/admin_panel")
    return render_template("admin_panel.html")


@app.route("/result")
def result():
    candidates = Candidate.query.all()
    candidate_list = []
    total = User.query.filter_by(role="Voter").count()
    for candidate in candidates:
        setv = paillier.decrypt(candidate.votes)
        setv = (setv * 100) / total
        candidate_data = {
            'id': candidate.id,
            'name': candidate.name,
            'age': candidate.age,
            'sex': candidate.sex,
            'area': candidate.area,
            'party': candidate.party,
            'votes': setv
        }
        candidate_list.append(candidate_data)
    return jsonify(candidate_list)

@app.route("/display_list")
def display_list():
    candidates = Candidate.query.all()
    candidate_list = []
    for candidate in candidates:
        candidate_data = {
            'id': candidate.id,
            'name': candidate.name,
            'age': candidate.age,
            'sex': candidate.sex,
            'area': candidate.area,
            'party': candidate.party,
            'agenda': candidate.agenda,
            'description': candidate.description,
            'votes': candidate.votes,
            'candidate_image': candidate.candidate_image  # Include image path
        }
        candidate_list.append(candidate_data)
    return jsonify(candidate_list)

@app.route("/display_users")
def display_users():
    """Retrieve all users (Admin only)"""
    if "user_id" not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    user_id = session["user_id"]
    user = db.session.get(User, user_id)
    
    if not user or user.role != "Admin":
        return jsonify({'error': 'Admin access required'}), 403
    
    users = User.query.all()
    users_list = []
    for u in users:
        user_data = {
            'id': u.id,
            'username': u.username,
            'role': u.role,
            'voted': u.voted
        }
        users_list.append(user_data)
    return jsonify(users_list)

@app.route("/user_panel")
def user_dashboard():
    if "user_id" in session:
        user_id = session["user_id"]
        user = db.session.get(User, user_id)  # Corrected this line
        if user.role == "Voter":
            return render_template("user_panel.html")
    return redirect("/login")

@app.route('/handle_click', methods=['POST'])
def handle_click():
    button_data = request.get_json()
    button_id = int(button_data.get('buttonId'))
    vote = Candidate.query.filter_by(id=button_id).with_entities(Candidate.votes).first()
    vote_to_update = db.session.get(Candidate, button_id)
    pvote = paillier.decrypt(vote[0])
    final = pvote + 1
    vote_to_update.votes = paillier.encrypt(final)
    db.session.commit()
    
    if "user_id" in session:
        user_id = session["user_id"]
        user = db.session.get(User, user_id)  # Corrected this line
        user_to_update = db.session.get(User, user.id)
        user_to_update.voted = 1
        db.session.commit()
    
    return jsonify({"message": "Vote cast successfully!"})

@app.route("/send_data", methods=['POST'])
def send_data():
    if "user_id" in session:
        user_id = session["user_id"]
        user = db.session.get(User, user_id)  # Corrected this line
        if user.voted == 1:
            data = 1
        else:
            data = 0
    response_data = {'vote1': data}
    return jsonify(response_data)

@app.route('/total_voters')
def total_voters():
    total_voters = User.query.filter_by(role='Voter').count()
    return jsonify({'total_voters': total_voters})

@app.route('/total_candidates')
def total_candidates():
    total_candidates = Candidate.query.count()
    return jsonify({'total_candidates': total_candidates})

@app.route("/logout")
def logout():
    session.pop("user_id", None)
    return redirect("/")

@app.route('/delete_candidate/<int:candidate_id>', methods=['POST'])
def delete_candidate(candidate_id):
    """Delete a candidate (Admin only)"""
    # Check admin authorization
    if "user_id" not in session:
        return jsonify({'error': 'Unauthorized. Please log in.'}), 401
    
    user_id = session["user_id"]
    user = db.session.get(User, user_id)
    
    if not user or user.role != "Admin":
        return jsonify({'error': 'Unauthorized. Admin access required.'}), 403
    
    try:
        candidate = db.session.get(Candidate, candidate_id)
        if not candidate:
            return jsonify({'error': 'Candidate not found.'}), 404
        
        db.session.delete(candidate)
        db.session.commit()
        return jsonify({'message': 'Candidate deleted successfully.'}), 200
    
    except Exception as e:
        db.session.rollback()
        print(f"Error deleting candidate {candidate_id}: {str(e)}")
        return jsonify({'error': f'Database error: {str(e)}'}), 500

@app.route('/delete_user/<int:user_id>', methods=['POST'])
def delete_user(user_id):
    """Delete a user (Admin only)"""
    # Check admin authorization
    if "user_id" not in session:
        return jsonify({'error': 'Unauthorized. Please log in.'}), 401
    
    admin_id = session["user_id"]
    admin = db.session.get(User, admin_id)
    
    if not admin or admin.role != "Admin":
        return jsonify({'error': 'Unauthorized. Admin access required.'}), 403
    
    # Prevent self-deletion
    if admin_id == user_id:
        return jsonify({'error': 'Cannot delete your own account.'}), 400
    
    try:
        user_to_delete = db.session.get(User, user_id)
        if not user_to_delete:
            return jsonify({'error': 'User not found.'}), 404
        
        db.session.delete(user_to_delete)
        db.session.commit()
        return jsonify({'message': 'User deleted successfully.'}), 200
    
    except Exception as e:
        db.session.rollback()
        print(f"Error deleting user {user_id}: {str(e)}")
        return jsonify({'error': f'Database error: {str(e)}'}), 500

@app.route('/mass_register', methods=['POST'])
def mass_register():
    if 'file' not in request.files:
        return 'No file part', 400
    file = request.files['file']
    if file.filename == '':
        return 'No selected file', 400
    
    # Validate file extension
    if not file.filename.endswith('.csv'):
        return 'Invalid file format. Only .csv files are accepted', 400
    
    try:
        # Read CSV file from stream (no need to save to disk)
        stream = io.TextIOWrapper(file.stream, encoding='utf-8')
        reader = csv.DictReader(stream)
        
        # Validate that required columns exist
        if reader.fieldnames is None or 'username' not in reader.fieldnames or 'password' not in reader.fieldnames:
            return 'Invalid CSV format. Required columns: username, password', 400
        
        # Process each row
        for row in reader:
            username = row.get('username', '').strip()
            password = row.get('password', '').strip()
            
            # Skip empty rows
            if not username or not password:
                continue
            
            # Create and add new user
            new_user = User(username=username, password=password, role='Voter', voted=0)
            db.session.add(new_user)
        
        db.session.commit()
        return redirect(url_for('admin_dashboard'))
    
    except Exception as e:
        db.session.rollback()
        return f'Error processing file: {str(e)}', 400

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
