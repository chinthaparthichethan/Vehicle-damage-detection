from flask import Flask, render_template, redirect, url_for, flash, request, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from ultralytics import YOLO
from PIL import Image
import numpy as np
import cv2

# Initialize the Flask app and configure the database
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'

# Initialize extensions
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)

# Model for User table in the database
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    gender = db.Column(db.String(1), nullable=False)
    mobile = db.Column(db.String(15), nullable=False)

# Routes for pages
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/contact')
def contact():
    return render_template('contact.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        user = User.query.filter_by(email=email).first()
        if user and bcrypt.check_password_hash(user.password, password):
            session['user_id'] = user.id  # Store user ID in session
            return redirect(url_for('home'))
        else:
            flash('Invalid email or password.', 'danger')
    return render_template('auth.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        age = request.form.get('age')
        gender = request.form.get('gender')
        mobile = request.form.get('mobile')

        # Age validation
        if not age.isdigit() or int(age) <= 0 or int(age) > 120:
            flash('Please enter a valid age between 1 and 120.', 'danger')
            return render_template('auth.html')


        if len(mobile) != 10 or not mobile.isdigit():
            flash('Mobile number must be exactly 10 digits.', 'danger')
            return render_template('auth.html')

        if User.query.filter_by(email=email).first():
            flash('Email address already in use. Please choose a different one.', 'danger')
            return render_template('auth.html')

        if password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return render_template('auth.html')

        if len(password) < 8:
            flash('Password must be at least 8 characters long.', 'danger')
            return render_template('auth.html')

        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        new_user = User(username=username, email=email, password=hashed_password, age=age, gender=gender, mobile=mobile)
        db.session.add(new_user)
        db.session.commit()

        flash('Registration successful! You can now log in.', 'success')
        return redirect(url_for('login'))
    return render_template('auth.html')

@app.route('/home')
def home():
    return render_template('home.html')

# YOLO model paths
MODEL_PATHS = {
    "2wheeler": r'2_best.pt',
    "4wheeler": r'4_best.pt',
    "6wheeler": r'6_best.pt'
}

PARTS_COST = {
    "2wheeler": {
        "Hero Splendor": {'broken': 50000, 'Scratch': 1500, 'headlight': 2500, 'seat': 1500, 'tire': 800, 'mirror': 300},
        "Honda Activa": {'broken': 48000, 'Scratch': 1400, 'headlight': 2300, 'seat': 1400, 'tire': 700, 'mirror': 250},
        "Honda Shine": {'broken': 49000, 'Scratch': 1450, 'headlight': 2400, 'seat': 1450, 'tire': 750, 'mirror': 280},
        "Bajaj Pulsar": {'broken': 48000, 'Scratch': 1400, 'headlight': 2300, 'seat': 1400, 'tire': 700, 'mirror': 250},
        "TVS Jupiter": {'broken': 49000, 'Scratch': 1450, 'headlight': 2400, 'seat': 1450, 'tire': 750, 'mirror': 280}
    },
    "4wheeler": {
        "Maruti Suzuki: Swift": {'Bumper': 8000, 'Fender': 6000, 'Front-Windshield': 7000, 'Rear-Windshield': 7000, 'Side-Mirror': 1500,
                   'Side-Screen': 2000, 'door': 13000, 'headlamp': 2900, 'hood': 4000},
        "Tata Motors: Nexon": {'Bumper': 8500, 'Fender': 6200, 'Front-Windshield': 7100, 'Rear-Windshield': 7100, 'Side-Mirror': 1600,
                  'Side-Screen': 2100, 'door': 13500, 'headlamp': 3000, 'hood': 4200},
        "Hyundai: Creta": {'Bumper': 9000, 'Fender': 6500, 'Front-Windshield': 7200, 'Rear-Windshield': 7200, 'Side-Mirror': 1700,
                 'Side-Screen': 2200, 'door': 14000, 'headlamp': 3100, 'hood': 4400},
        "Mahindra: Scorpio": {'Bumper': 9000, 'Fender': 6500, 'Front-Windshield': 7200, 'Rear-Windshield': 7200, 'Side-Mirror': 1700,
                 'Side-Screen': 2200, 'door': 14000, 'headlamp': 3100, 'hood': 4400},
        "Toyota: Innova Crysta": {'Bumper': 9000, 'Fender': 6500, 'Front-Windshield': 7200, 'Rear-Windshield': 7200, 'Side-Mirror': 1700,
                 'Side-Screen': 2200, 'door': 14000, 'headlamp': 3100, 'hood': 4400}
    },
    "6wheeler": {
        "Bharat Benz 1923C Tipper": {'Rearlamp -L- - damaged': 1000, 'Rearlamp -R- - damaged': 1000, 'Sideboard -L- - damaged': 1500,
                  'Sideboard -R- - damaged': 1500},
        "Tata LPT 1916": {'Rearlamp -L- - damaged': 1200, 'Rearlamp -R- - damaged': 1200, 'Sideboard -L- - damaged': 1700,
                     'Sideboard -R- - damaged': 1700},
        "Tata Signa 1918.k": {'Rearlamp -L- - damaged': 1100, 'Rearlamp -R- - damaged': 1100, 'Sideboard -L- - damaged': 1600,
                   'Sideboard -R- - damaged': 1600},
        "Mahindra Furio 16 Truck": {'Rearlamp -L- - damaged': 1200, 'Rearlamp -R- - damaged': 1200, 'Sideboard -L- - damaged': 1700,
                     'Sideboard -R- - damaged': 1700},
        "Bharat Benz 1415RE Truck": {'Rearlamp -L- - damaged': 1100, 'Rearlamp -R- - damaged': 1100, 'Sideboard -L- - damaged': 1600,
                   'Sideboard -R- - damaged': 1600}
    }
}

def load_yolo_model(vehicle_type):
    model_path = MODEL_PATHS.get(vehicle_type)
    if model_path:
        return YOLO(model_path)
    return None

def draw_bounding_boxes(image, results, class_names):
    
    color = (0, 0, 255) 

    if not isinstance(image, np.ndarray):
        image = np.array(image)[:, :, ::-1]  

    for box, cls in zip(results[0].boxes.xyxy, results[0].boxes.cls):
        x1, y1, x2, y2 = map(int, box.tolist())  
        cls = int(cls) 
        label = class_names[cls]  

        cv2.rectangle(image, (x1, y1), (x2, y2), color, 2)

        label_size, _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.7, 2)
        label_width, label_height = label_size
        text_x = x1 + 5
        text_y = y1 + label_height + 5
        text_y = min(image.shape[0] - 5, max(text_y, 0))

        cv2.rectangle(image, (x1, y1 - label_height - 5),
                      (x1 + label_width + 10, y1), color, -1)

        cv2.putText(image, label, (text_x, text_y - label_height),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2)

    return image


@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if request.method == 'POST':
        vehicle_type = request.form.get('vehicle_type')
        print(111111, vehicle_type)
        brand = request.form.get('vehicle_brand')
        print(2222, brand)
        uploaded_file = request.files.get('image_file')

        if not uploaded_file or vehicle_type not in MODEL_PATHS or not brand:
            flash('Invalid vehicle type, brand, or file.', 'danger')
            return render_template('upload.html')

        model = load_yolo_model(vehicle_type)
        if not model:
            flash('Failed to load YOLO model.', 'danger')
            return render_template('upload.html')

        image = Image.open(uploaded_file)
        results = model(image)
        if not results:
            flash('No objects detected in the image.', 'danger')
            return render_template('upload.html')

        result = results[0]
        class_names = result.names
        detected_classes = [int(cls) for cls in result.boxes.cls]
        print(55555, detected_classes)

        damage_details = []
        for detected_class in detected_classes:
            damage_detected = class_names[detected_class]  
            cost = PARTS_COST.get(vehicle_type, {}).get(brand, {}).get(damage_detected, 0)
            damage_details.append({'damage_type': damage_detected, 'cost': cost})

        total_cost = sum(d['cost'] for d in damage_details)

        image_with_boxes = draw_bounding_boxes(np.array(image), results, class_names)
        image_path = "static/output.jpg"
        cv2.imwrite(image_path, image_with_boxes)

        return render_template(
            'upload.html',
            image_path=image_path,
            repair_cost=total_cost,
            damage_details=damage_details
        )

    return render_template('upload.html')


@app.route('/logout')
def logout():
    session.pop('user_id', None)
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
