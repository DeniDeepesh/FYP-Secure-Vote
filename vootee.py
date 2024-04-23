import cv2
import numpy as np
import mysql.connector
import dlib
from imutils import paths
import os
from flask import Flask, render_template, request, redirect, url_for
import face_recognition

app = Flask(__name__)

# Initialize the dlib face detector and facial landmark predictor
detector = dlib.get_frontal_face_detector()
predictor = dlib.shape_predictor("shape_predictor_68_face_landmarks.dat")

voted_voter_ids = set()

def create_connection():
    return mysql.connector.connect(
        host='localhost',
        user='root',
        password='D9861066489@',
        database='voter_registration'
    )

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
    directory = r"D:\YEAR 3\Final Year Project\program\face verification"
    filename = f"{voter_id}_face.jpg"
    filepath = os.path.join(directory, filename)
    (x, y, w, h) = face_coords
    
    # Increase the size of the rectangle by a certain factor (e.g., 1.5 times)
    new_x = max(0, x - int(w * 0.25))  # Adjust the factor (0.25) as needed
    new_y = max(0, y - int(h * 0.25))  # Adjust the factor (0.25) as needed
    new_w = min(frame.shape[1], w + int(w * 0.5))  # Adjust the factor (0.5) as needed
    new_h = min(frame.shape[0], h + int(h * 0.5))  # Adjust the factor (0.5) as needed
    
    face_image = frame[new_y:new_y+new_h, new_x:new_x+new_w]
    cv2.imwrite(filepath, face_image)

def load_face_images(directory):
    face_images = {}
    for image_path in paths.list_images(directory):
        voter_id = os.path.splitext(os.path.basename(image_path))[0].split('_')[0]
        face_images[voter_id] = cv2.imread(image_path)
    return face_images

def preprocess_image(image):
    # Convert the image to grayscale if necessary
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    # Apply any other preprocessing steps if needed
    return gray



def check_eligibility(voter_id):
    conn = create_connection()
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM voting_res WHERE voter_id = %s', (voter_id,))
    result = cursor.fetchone()

    if result:
        conn.close()
        return False, "You have already voted. Each voter is allowed to vote only once."

    cursor.execute('SELECT * FROM voter_info_face_regestration WHERE voter_id = %s', (voter_id,))
    result = cursor.fetchone()

    conn.close()

    if result:
        return True, None
    else:
        return False, "Voter ID not found. Please enter a valid voter ID."



def get_voter_details(voter_id):
    conn = create_connection()
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM voter_info_face_regestration WHERE voter_id = %s', (voter_id,))
    result = cursor.fetchone()

    conn.close()

    if result:
        voter_details = {
            "Name": result[1],
            "Citizenship Number": result[2],
            "Voter ID": result[3],
            "Phone Number": result[4],
            "District": result[5], 
            "City": result[6],
            "Municipality": result[7],
            "Ward Number": result[8],
            "Tole": result[9] if len(result) > 9 else "Not Found"
        }
        return voter_details
    else:
        return None

def store_vote_details(voter_id, voter_details, candidate_choice):
    conn = create_connection()
    cursor = conn.cursor()

    # Insert data into the voting_res table
    cursor.execute('''
        INSERT INTO voting_res (voter_id, name, citizenship_number, phone_number, candidate_choice)
        VALUES (%s, %s, %s, %s, %s)
    ''', (voter_id, voter_details["Name"], voter_details["Citizenship Number"], voter_details["Phone Number"], candidate_choice))

    conn.commit()
    conn.close()

    voted_voter_ids.add(voter_id)

def get_candidate_choice():
    candidates = ["Congress", "UML", "Communist"]

    print("Candidates:")
    for i, candidate in enumerate(candidates, start=1):
        print(f"{i}. {candidate}")

    while True:
        try:
            choice = int(input("Choose the candidate number you want to vote for: "))
            if 1 <= choice <= len(candidates):
                return candidates[choice - 1]
            else:
                print("Invalid choice. Please enter a valid candidate number.")
        except ValueError:
            print("Invalid input. Please enter a valid candidate number.")

def confirm_vote(candidate):
    while True:
        confirmation = input(f"Are you sure you want to cast a vote for {candidate}? (yes/no): ").lower()
        if confirmation == 'yes':
            return True
        elif confirmation == 'no':
            return False
        elif confirmation == 'change':
            return None
        else:
            print("Invalid input. Please enter 'yes', 'no', or 'change'.")



def calculate_winner(votes):
    max_votes = max(votes.values())
    winners = [candidate for candidate, vote_count in votes.items() if vote_count == max_votes]
    return winners, max_votes

# Function to annotate landmarks on the frame
def annotate_landmarks(frame, face_coords):
    (x, y, w, h) = face_coords
    
    # Increase the size of the frame by a certain factor (e.g., 1.5 times)
    new_x = max(0, x - int(w * 0.25))  # Adjust the factor (0.25) as needed
    new_y = max(0, y - int(h * 0.25))  # Adjust the factor (0.25) as needed
    new_w = min(frame.shape[1], w + int(w * 0.5))  # Adjust the factor (0.5) as needed
    new_h = min(frame.shape[0], h + int(h * 0.5))  # Adjust the factor (0.5) as needed
    
    cv2.rectangle(frame, (new_x, new_y), (new_x + new_w, new_y + new_h), (0, 255, 0), 2)
    return frame

# Function to capture and store the voter's facial landmarks
def capture_and_store_landmarks():
    video_capture = cv2.VideoCapture(0)

    while True:
        ret, frame = video_capture.read()

        face_coords = detect_and_extract_face(frame)

        if face_coords is not None:
            frame = annotate_landmarks(frame, face_coords)
            cv2.imshow('Capture Face', frame)

            if cv2.waitKey(1) & 0xFF == ord(' '):
                video_capture.release()
                cv2.destroyAllWindows()
                return frame, face_coords  # Return both frame and face_coords

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    video_capture.release()
    cv2.destroyAllWindows()

    return None, None  # Return None for both frame and face_coords if no face is detected

def load_face_image(filename, directory):
    filepath = os.path.join(directory, filename)
    if os.path.exists(filepath):
        return cv2.imread(filepath)
    return None

def load_face_encodings(directory):
    face_encodings = {}
    for filename in os.listdir(directory):
        voter_id = os.path.splitext(filename)[0].split('_')[0]
        image = face_recognition.load_image_file(os.path.join(directory, filename))
        face_encodings[voter_id] = face_recognition.face_encodings(image)[0]
    return face_encodings

def get_votes():
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT candidate_choice, COUNT(*) AS vote_count FROM voting_res GROUP BY candidate_choice')
    votes = {
        "Congress": 0,
        "UML": 0,
        "Communist": 0
    }
    for candidate, vote_count in cursor.fetchall():
        votes[candidate] = vote_count
    conn.close()
    return votes





@app.route('/')
def index():
    error = request.args.get('error')
    return render_template('index1.html', error=error)

@app.route('/voter_details', methods=['GET', 'POST'])
def voter_details():
    registered_faces_directory = r"D:\YEAR 3\Final Year Project\program\face image"
    registered_faces = load_face_encodings(registered_faces_directory)

    if request.method == 'POST':
        voter_id = request.form['voter_id']
        eligible, error_message = check_eligibility(voter_id)
        
        if not eligible:
            return render_template('index1.html', error=error_message)
        
        candidate_choice = request.form['candidate_choice']
        voter_details = get_voter_details(voter_id)
        frame, face_coords = capture_and_store_landmarks()
        
        if frame is not None and face_coords is not None:
            crop_and_save_face(frame, face_coords, voter_id)
            captured_face_directory = r"D:\YEAR 3\Final Year Project\program\face verification"
            captured_face = face_recognition.load_image_file(os.path.join(captured_face_directory, f"{voter_id}_face.jpg"))
            captured_face_encoding = face_recognition.face_encodings(captured_face)[0]
            registered_face_encoding = registered_faces.get(voter_id)
            
            if captured_face_encoding is not None and registered_face_encoding is not None:
                results = face_recognition.compare_faces([registered_face_encoding], captured_face_encoding)
                
                if results[0]:
                    votes = get_votes()
                    votes[candidate_choice] += 1
                    store_vote_details(voter_id, voter_details, candidate_choice)
                    return render_template('result.html', result=f"Thank you for voting! You have voted for {candidate_choice}.", voter_id=voter_id)
                else:
                    return render_template('result.html', result="Face not matched with the registered voter.", voter_id=voter_id)
            else:
                return render_template('result.html', result="Error capturing face image. Please try again.", voter_id=voter_id)

    else:  # This is the GET request handling part
        voter_id = request.args.get('voter_id')
        eligible, error_message = check_eligibility(voter_id)
        
        if not eligible:
            return render_template('index1.html', error=error_message)
        
        voter_details = get_voter_details(voter_id)
        candidates = ["Congress", "UML", "Communist"]
        return render_template('voter_details.html', voter_details=voter_details, candidates=candidates)


@app.route('/result', methods=['GET', 'POST'])
def result():
    if request.method == 'POST':
        new_voter = request.form.get('new_voter', 'no')
        if new_voter == 'yes':
            return redirect(url_for('index'))
        else:
            return redirect(url_for('winner_result'))
    
    voter_id = request.args.get('voter_id')
    result_message = request.args.get('result_message')
    return render_template('result.html', result=result_message, voter_id=voter_id)

@app.route('/winner_result', methods=['GET'])
def winner_result():
    votes = get_votes()
    winners, max_votes = calculate_winner(votes)
    if len(winners) > 1:
        result_message = f"It's a draw between {', '.join(winners)} with {max_votes} votes each."
    else:
        result_message = f"The winner is {winners[0]} with {max_votes} votes."
    return render_template('winner_results.html', result_message=result_message, votes=votes)

if __name__ == '__main__':
    app.run(port=8080)