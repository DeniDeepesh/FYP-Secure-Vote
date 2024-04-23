from flask import Flask, render_template, request, jsonify
import cv2
import numpy as np
import mysql.connector
import os
import dlib
import base64

# Initialize Flask app
app = Flask(__name__)

# Connect to MySQL database
db = mysql.connector.connect(
    host='localhost',
    user='root',
    password='D9861066489@',
    database='voter_registration'
)

# Create a cursor to interact with the database
cursor = db.cursor()

# Create the table if it doesn't exist
cursor.execute('''
    CREATE TABLE IF NOT EXISTS voter_info_face_regestration (
        id INT AUTO_INCREMENT PRIMARY KEY,
        name VARCHAR(255),
        citizenship_number INT,
        voter_id INT,
        phone_number VARCHAR(10),
        district VARCHAR(255),
        city VARCHAR(255),
        municipality VARCHAR(255),
        ward_no INT,
        tole VARCHAR(255)
    )
''')

# Initialize the dlib face detector
detector = dlib.get_frontal_face_detector()

# Directory to store cropped face images
FACE_IMAGE_DIR = r"D:\YEAR 3\Final Year Project\program\face image"

# Function to detect and extract face bounding box from the frame
def detect_and_extract_face(frame):
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = detector(gray)
    if len(faces) > 0:
        face = faces[0]
        (x, y, w, h) = (face.left(), face.top(), face.width(), face.height())
        return (x, y, w, h)
    return None

# Function to crop and save the face image
def crop_and_save_face(frame, face_coords, voter_id):
    filename = f"{voter_id}_face.jpg"
    filepath = os.path.join(FACE_IMAGE_DIR, filename)
    (x, y, w, h) = face_coords
    face_image = frame[y:y+h, x:x+w]
    cv2.imwrite(filepath, face_image)

# Function to save voter information to the database
def save_voter_info(first_name, middle_name, last_name, citizenship_number, voter_id, phone_number, district, city, municipality, ward_no, tole):
    full_name = f"{first_name} {middle_name} {last_name}"
    query = '''
        INSERT INTO voter_info_face_regestration (name, citizenship_number, voter_id, phone_number, district, city, municipality, ward_no, tole)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
    '''
    values = (full_name, citizenship_number, voter_id, phone_number, district, city, municipality, ward_no, tole)
    cursor.execute(query, values)

# Function to check if citizenship number is unique
def is_unique_citizenship_number(citizenship_number):
    cursor.execute('SELECT * FROM voter_info_face_regestration WHERE citizenship_number = %s', (citizenship_number,))
    result = cursor.fetchone()
    return result is None

# Function to check if voter ID is unique
def is_unique_voter_id(voter_id):
    cursor.execute('SELECT * FROM voter_info_face_regestration WHERE voter_id = %s', (voter_id,))
    result = cursor.fetchone()
    return result is None

# Define routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['POST'])
def register():
    try:
        # Process registration data from the frontend
        data = request.form
        first_name = data.get('first_name')
        middle_name = data.get('middle_name')
        last_name = data.get('last_name')
        citizenship_number = data.get('citizenship_number')
        voter_id = data.get('voter_id')
        phone_number = data.get('phone_number')
        district = data.get('district')
        city = data.get('city')
        municipality = data.get('municipality')
        ward_no = data.get('ward_no')
        tole = data.get('tole')

        if not is_unique_citizenship_number(citizenship_number):
            return jsonify({"error": "This citizenship number has already been registered."})

        if not is_unique_voter_id(voter_id):
            return jsonify({"error": "This voter ID has already been registered."})

        image_data = data.get('image')
        image_data = base64.b64decode(image_data.split(',')[1])
        image = np.fromstring(image_data, dtype=np.uint8)
        frame = cv2.imdecode(image, cv2.IMREAD_COLOR)

        face_coords = detect_and_extract_face(frame)

        if face_coords is not None:
            crop_and_save_face(frame, face_coords, voter_id)
            save_voter_info(first_name, middle_name, last_name, citizenship_number, voter_id, phone_number, district, city, municipality, ward_no, tole)
            db.commit()  # Commit the changes to the database
            return jsonify({"message": "Voter information has been saved to the database, and the face image has been saved."})
        else:
            return jsonify({"error": "No face detected. Registration failed."})

    except Exception as e:
        db.rollback()  # Rollback the changes if an exception occurs
        return jsonify({"error": str(e)})

# Run the Flask app
if __name__ == '__main__':
    app.run(debug=True)