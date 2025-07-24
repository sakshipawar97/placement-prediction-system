#Importing all required libraries

from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_mysqldb import MySQL
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import pickle
import joblib
from flask_mail import Mail, Message
import pandas as pd
import os
import google.auth
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
from google.oauth2.service_account import Credentials
from oauth2client.service_account import ServiceAccountCredentials
import gspread
from datetime import timedelta
from MySQLdb.cursors import DictCursor
from apscheduler.schedulers.background import BackgroundScheduler
import pymysql
import json
from flask import current_app

app = Flask(__name__, instance_relative_config=True)
app.secret_key = '4b4c04282c31243bddaeb87ac11a3db9'  # Replace with a secure key

# Mail configuration
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USERNAME'] = 'sakshi140912@gmail.com'  # Replace with your email
app.config['MAIL_PASSWORD'] = 'scwljfnsijqicnza'  # Use your app password here
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False

# Initialize Flask-Mail
mail = Mail(app)

# MySQL Configuration
# Function to load MySQL credentials from config.json
def load_config():
    with open('config.json') as f:
        config = json.load(f)
    return config

# Load the config
config = load_config()

# Set MySQL configuration in Flask app
app.config['MYSQL_HOST'] = config['DB_HOST']
app.config['MYSQL_USER'] = config['DB_USER']
app.config['MYSQL_PASSWORD'] = config['DB_PASSWORD']
app.config['MYSQL_DB'] = config['DB_NAME']
app.config['MYSQL_PORT'] = config['DB_PORT']

# Initialize MySQL connection
mysql = MySQL(app)


# Paths to saved model and scaler
MODEL_PATH = 'models/best_random_forest_model.pkl'
SCALER_PATH = 'models/scalermajor.pkl'

# Load the model and scaler
def load_model_and_scaler():
    try:
        model = joblib.load(MODEL_PATH)
        scaler = joblib.load(SCALER_PATH)
        return model, scaler
    except Exception as e:
        print(f"Error loading model or scaler: {e}")
        return None, None

model, scaler = load_model_and_scaler()

# The Google Sheet ID (You can find this in the URL of your Google Sheet)
SPREADSHEET_ID = '1XfVhtAQGCMei9AsyvXiIAk6Zz4MAQeVgWTEvlbMp-Jc'

# Define the scopes (permissions)
SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']

# Function to authenticate Google Sheets
def authenticate_google_sheets():
    scope = [
        "https://www.googleapis.com/auth/spreadsheets.readonly",
        "https://www.googleapis.com/auth/drive.metadata.readonly"
    ]

    credentials_path = os.path.join(current_app.instance_path, 'tpo_access.json')  

    if not os.path.exists(credentials_path):
        raise FileNotFoundError(f"Credentials file not found at: {credentials_path}")

    creds = Credentials.from_service_account_file(credentials_path, scopes=scope)
    client = gspread.authorize(creds)

    return client, creds

#App route for form responses
@app.route('/form_responses')
def form_responses():
    # Authenticate and get both gspread client and credentials for Drive API
    client, creds = authenticate_google_sheets()

    # Build the Drive API service using the credentials
    drive_service = build('drive', 'v3', credentials=creds)

    # List all Google Sheets files
    results = drive_service.files().list(
        q="mimeType='application/vnd.google-apps.spreadsheet'",
        fields="files(id, name)"
    ).execute()

    files = results.get("files", [])
    all_responses = []

    # Fetch data from each sheet
    for file in files:
        try:
            # Open the sheet by ID and read the data
            sheet = client.open_by_key(file["id"]).sheet1
            data = sheet.get_all_values()  # Fetch all rows
            if data:  # If the sheet has data
                all_responses.append({"sheet_name": file["name"], "data": data})
        except Exception as e:
            print(f"Error reading sheet {file['name']}: {e}")

    # Pass all responses to the template
    return render_template('form_responses.html', all_responses=all_responses)


def get_sheet_data():
    client, creds = authenticate_google_sheets()
    drive_service = build('drive', 'v3', credentials=creds)

    results = drive_service.files().list(
        q="mimeType='application/vnd.google-apps.spreadsheet'",
        fields="files(id, name)"
    ).execute()

    files = results.get("files", [])
    all_responses = []

    for file in files:
        try:
            sheet = client.open_by_key(file["id"]).sheet1
            data = sheet.get_all_values()
            if data:
                all_responses.append({"sheet_name": file["name"], "data": data})
        except Exception as e:
            print(f"Error reading sheet {file['name']}: {e}")

    return all_responses

#Routes to all the other templates

#Admin route
@app.route('/')
def home():
    return render_template('home.html')

@app.route('/admin', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Admin credentials check
        if username == 'admin' and password == 'admin':
            session['admin_logged_in'] = True
            flash('Admin login successful!', 'success')
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Invalid admin credentials.', 'danger')

    return render_template('admin_login.html')

@app.route('/admin_dashboard')
def admin_dashboard():
    if not session.get('admin_logged_in'):
        flash('Please log in as admin first.', 'warning')
        return redirect(url_for('admin_login'))

    try:
        cursor = mysql.connection.cursor()
        cursor.execute("SELECT id, name, username, email, phone FROM students")
        students = cursor.fetchall()

        cursor.execute("SELECT id, name, username, email FROM tpo")
        tpos = cursor.fetchall()

    except Exception as e:
        flash(f'Error fetching data: {str(e)}', 'danger')
        students, tpos = [], []

    return render_template('admin_dashboard.html', students=students, tpos=tpos)

@app.route('/admin/send_notification', methods=['GET', 'POST'])
def send_notification():
    if 'admin_logged_in' in session:
        if request.method == 'POST':
            title = request.form.get('title')
            message = request.form.get('message')
            recipient_type = request.form.get('recipient_type')

            # Validate input values
            if not title or not message:
                flash('Please fill in all the required fields.', 'error')
                return redirect(url_for('send_notification'))

            if recipient_type not in ['student', 'tpo', 'all']:
                flash('Invalid recipient type.', 'error')
                return redirect(url_for('send_notification'))

            # Insert into admin_notifications
            cursor = mysql.connection.cursor()
            cursor.execute("""
                INSERT INTO admin_notifications (title, message, recipient_type, created_at)
                VALUES (%s, %s, %s, NOW())
            """, (title, message, recipient_type))
            mysql.connection.commit()

            # Insert into notifications table for students
            if recipient_type in ['student', 'all']:  # Ensure students see it
                cursor.execute("""
                    INSERT INTO notifications (title, message, recipient_type, created_at)
                    VALUES (%s, %s, 'student', NOW())
                """, (title, message))
                mysql.connection.commit()

            cursor.close()

            # Fetch email recipients
            recipients = []
            cursor = mysql.connection.cursor()
            if recipient_type == 'student':
                cursor.execute("SELECT email FROM students")
            elif recipient_type == 'tpo':
                cursor.execute("SELECT email FROM tpo")
            elif recipient_type == 'all':
                cursor.execute("SELECT email FROM students UNION SELECT email FROM tpo")

            result = cursor.fetchall()
            for row in result:
                recipients.append(row[0])

            cursor.close()

            # Send emails
            try:
                with mail.connect() as conn:
                    for email in recipients:
                        msg = Message(
                            subject=f"Notification: {title}",
                            sender=('Admin Notifications', 'sakshi140912@gmail.com'),
                            recipients=[email]
                        )
                        msg.body = message
                        conn.send(msg)

                flash('Notification sent successfully and emails delivered!', 'success')
            except Exception as e:
                flash(f'Notification saved but failed to send emails: {str(e)}', 'error')

            return redirect(url_for('admin_dashboard'))

        return render_template('send_notification.html')  # Render Admin notification form
    else:
        flash('Please log in as Admin.', 'warning')
        return redirect(url_for('admin_login'))


@app.route('/view_students')
def view_students():
    # Connect to the database
    cursor = mysql.connection.cursor()
    # Execute a query to fetch all students
    query = "SELECT name, email, phone, username FROM students"
    cursor.execute(query)
    # Fetch all the rows from the query result
    students = cursor.fetchall()
    cursor.close()

    # Convert the fetched data to a list of dictionaries
    student_list = []
    for student in students:
        student_list.append({
            'name': student[0],
            'email': student[1],
            'phone': student[2],
            'username': student[3]
        })

    # Render the template with the fetched data
    return render_template('view_students.html', students=student_list)


@app.route('/view_tpos', methods=['GET', 'POST'])
def view_tpos():
    cursor = mysql.connection.cursor()

    # If the request is POST, process the form to fetch details of the selected TPO
    tpo_details = None
    if request.method == 'POST':
        tpo_id = request.form['tpo_id']
        query = "SELECT name, email, phone, username FROM tpo WHERE id = %s"
        cursor.execute(query, (tpo_id,))
        tpo_details = cursor.fetchone()

    # Default GET request: Display the list of TPOs
    query = "SELECT id, name, email, phone, username FROM tpo"
    cursor.execute(query)
    tpos = cursor.fetchall()
    cursor.close()

    # Prepare the list of TPOs for the template
    tpo_list = [{'id': tpo[0], 'name': tpo[1], 'email': tpo[2], 'phone': tpo[3], 'username': tpo[4]} for tpo in tpos]

    return render_template('view_tpos.html', tpos=tpo_list, tpo_details=tpo_details)

@app.route('/admin_logout')
def admin_logout():
    session.pop('admin_logged_in', None)
    flash('You have been logged out.', 'info')
    return redirect(url_for('admin_login'))


#STUDENT ROUTES
@app.route('/student/login', methods=['GET', 'POST'])
def student_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']  # Plain text password entered by the user

        print(f"Form Password: {password}")  # Debugging: print entered password

        cursor = mysql.connection.cursor()
        cursor.execute("SELECT * FROM students WHERE username = %s", (username,))
        student = cursor.fetchone()

        if student:
            print(f"Stored Password Hash: {student[5]}")  # Debugging: print stored password hash

            # Check if the entered password matches the stored hashed password
            if check_password_hash(student[5], password):  
                session['student_logged_in'] = True
                session['student_id'] = student[0]
                session['student_username'] = student[2]  # Username
                session['student_email'] = student[3]  # Email

                print("Session Data:", session)  # Debugging: print session data

                flash(f'Welcome, {student[1]}!', 'success')  # Welcome with name
                return redirect(url_for('student_dashboard'))
            else:
                flash('Invalid login credentials.', 'danger')
        else:
            flash('Invalid login credentials.', 'danger')

    return render_template('student_login.html')

@app.route('/student/signup', methods=['GET', 'POST'])
def student_signup():
    if request.method == 'POST':
        username = request.form['username']
        name = request.form['name']
        email = request.form['email']
        phone = request.form['phone']
        password = request.form['password']  # Plain text password

        # Hash the password before storing it
        hashed_password = generate_password_hash(password)

        # Convert `signup_date` to correct MySQL format
        signup_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        try:
            conn = mysql.connection
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO students (name, username, email, phone, password, signup_date) 
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (name, username, email, phone, hashed_password, signup_date))

            conn.commit()
            cursor.close()

            flash('Student signup successful! Please log in.', 'success')
            return redirect(url_for('student_login'))
        
        except Exception as e:
            conn.rollback()
            flash(f'Error: {e}', 'danger')

    return render_template('student_signup.html')

@app.route('/student/dashboard')
def student_dashboard():
    if 'student_logged_in' in session:
        student_username = session['student_username']
        
        # Fetch student's signup_date from the database
        try:
            conn = mysql.connection
            cursor = conn.cursor()
            cursor.execute("SELECT signup_date FROM students WHERE username = %s", (student_username,))
            student_signup_date = cursor.fetchone()[0]  # Get the signup_date of the student
        except Exception as e:
            flash(f'Error: {e}', 'danger')
            return redirect(url_for('student_login'))

        # Fetch notifications that are after the student's signup_date
        try:
            cursor.execute("SELECT title, message, created_at FROM notifications WHERE created_at > %s AND recipient_type = 'student' ORDER BY created_at DESC", (student_signup_date,))
            notifications = cursor.fetchall()
        except Exception as e:
            flash(f'Error: {e}', 'danger')
            notifications = []


        return render_template('student_dashboard.html', name=student_username, notifications=notifications)
    else:
        flash('You need to log in first.', 'warning')
        return redirect(url_for('student_login'))


# Ensure the session lasts longer if needed
app.permanent_session_lifetime = timedelta(hours=2)

from datetime import datetime, date

@app.route('/student/notifications', methods=['GET'])
def student_notification_page():
    if 'student_logged_in' in session:
        student_id = session['student_id']
        cursor = mysql.connection.cursor()

        # Fetch student's signup date
        cursor.execute("SELECT signup_date FROM students WHERE id = %s", (student_id,))
        signup_date = cursor.fetchone()

        if signup_date:
            signup_date = signup_date[0]
            print(f"DEBUG: Student Signup Date: {signup_date}")

            # Ensure signup_date is a datetime (if it's a date, convert to datetime with time 00:00:00)
            if isinstance(signup_date, date) and not isinstance(signup_date, datetime):
                signup_date = datetime.combine(signup_date, datetime.min.time())
            
            # Fetch notifications from `companies` table, sorted by apply_deadline (descending)
            cursor.execute("""
                SELECT company_name, job_role, description, apply_deadline, apply_link
                FROM companies
                WHERE apply_deadline >= %s 
                ORDER BY apply_deadline DESC
            """, (signup_date,))

            notifications = cursor.fetchall() or []  # Ensure it's a list

            # Convert job notifications to match HTML template
            formatted_notifications = [
                {
                    "title": f"{company[0]} - {company[1]}",
                    "message": company[2],
                    "scheduled_date": company[3] if isinstance(company[3], datetime) else datetime.combine(company[3], datetime.min.time()),  # Convert date to datetime if needed
                    "google_form_link": company[4],
                    "type": 'company'
                }
                for company in notifications
            ]

            # Fetch general notifications from `notifications` table (sent by TPO)
            cursor.execute("""
                SELECT title, message, created_at 
                FROM notifications 
                WHERE recipient_type = 'student' AND company_id IS NULL
                ORDER BY created_at DESC
            """)
            general_notifications = cursor.fetchall() or []  # Ensure it's a list

            # Convert general notifications to match HTML format
            formatted_general_notifications = [
                {
                    "title": notification[0],
                    "message": notification[1],
                    "scheduled_date": notification[2] if isinstance(notification[2], datetime) else datetime.combine(notification[2], datetime.min.time()),  # Convert date to datetime if needed
                    "google_form_link": None,  # No link for general notifications
                    "type": 'general'
                }
                for notification in general_notifications
            ]

            # Merge both lists (company job notifications + general notifications)
            formatted_notifications.extend(formatted_general_notifications)

            # Sort notifications by scheduled date in descending order
            formatted_notifications.sort(key=lambda x: x['scheduled_date'], reverse=True)

            cursor.close()

            print(f"DEBUG: Final Merged Notifications Sent to HTML: {formatted_notifications}")

            return render_template('student_notification_page.html', notifications=formatted_notifications)

        else:
            flash('Could not find your registration time.', 'warning')
            return redirect(url_for('student_dashboard'))

    flash('Please log in first.', 'warning')
    return redirect(url_for('student_login'))

@app.route('/delete_notification/<int:notification_id>', methods=['POST'])
def delete_notification(notification_id):
    if 'student_logged_in' not in session:
        flash('Please log in first.', 'warning')
        return redirect(url_for('student_login'))

    deleted_ids = session.get('deleted_notifications', [])
    if notification_id not in deleted_ids:
        deleted_ids.append(notification_id)
        session['deleted_notifications'] = deleted_ids

    return redirect(url_for('student_notification_page'))

@app.route('/student/submit_query', methods=['POST'])
def submit_student_query():
    if 'student_username' not in session:
        flash('Please log in to submit a query.', 'danger')
        return redirect(url_for('login'))

    student_username = session['student_username']
    query_text = request.form.get('query_text')

    cur = mysql.connection.cursor()

    # Fetch student ID and email
    cur.execute("SELECT id, email FROM students WHERE username = %s", (student_username,))
    student = cur.fetchone()
    if not student:
        cur.close()
        flash('Student not found.', 'danger')
        return redirect(url_for('student_query_page'))

    student_id, student_email = student
    submitted_at = datetime.now()

    # Insert query into the database
    cur.execute(
        "INSERT INTO queries (student_id, query_text, status, submitted_at) VALUES (%s, %s, %s, %s)",
        (student_id, query_text, 'pending', submitted_at)
    )
    mysql.connection.commit()

    # Fetch all TPO email addresses from the tpo table
    cur.execute("SELECT email FROM tpo")
    tpo_emails = [row[0] for row in cur.fetchall()]
    cur.close()

    if not tpo_emails:
        flash("No TPO registered to receive queries.", "warning")
        return redirect(url_for('student_query_page'))

    # Send email to each TPO
    try:
        msg = Message(
            subject=f"New Query from {student_username} - Campcruit",
            sender=('Campcruit', 'sakshi140912@gmail.com'),
            recipients=tpo_emails  # List of emails
        )
        msg.body = f"""
Dear TPO,

A new query has been submitted by a student via the Campcruit platform.

🧑 Student Username: {student_username}
📩 Email: {student_email}
📝 Query: 
{query_text}

📅 Submitted at: {submitted_at.strftime('%Y-%m-%d %H:%M:%S')}

Please visit the TPO panel to respond.

Regards,  
Campcruit Team
        """
        mail.send(msg)
        print("Query email sent to TPO(s) successfully.")
    except Exception as e:
        print(f"Error sending email: {str(e)}")

    flash("Your query has been submitted successfully!", "success")
    return redirect(url_for('student_query_page'))


@app.route('/student/student_query_page')
def student_query_page():
    if 'student_username' not in session:
        return redirect(url_for('login'))

    student_username = session['student_username']
    cur = mysql.connection.cursor()

    # Debug: Print session username
    print(f"Fetching queries for student: {student_username}")

    # Fetch student ID
    cur.execute("SELECT id FROM students WHERE username = %s", (student_username,))
    student = cur.fetchone()

    if not student:
        cur.close()
        return "Student not found", 404

    student_id = student[0]
    print(f"Student ID: {student_id}")

    # Fetch queries and convert to dictionaries
    cur.execute("SELECT query_text, status, reply_text, submitted_at FROM queries WHERE student_id = %s", (student_id,))
    rows = cur.fetchall()
    queries = [
        {
            'query_text': row[0],
            'status': row[1].lower() if row[1] else '',
            'reply_text': row[2],
            'submitted_at': row[3]
        } for row in rows
    ]

    print(f"Queries fetched: {queries}")  # Debugging

    cur.close()

    return render_template('student_query_page.html', queries=queries)

@app.route('/delete_account', methods=['POST'])
def delete_account():
    if 'student_logged_in' in session:
        # Debugging: Print session data
        print("Session data:", session)

        # Get the student's email from the session
        student_email = session.get('student_email')
        
        if not student_email:
            flash("Error: No email found in session.", "error")
            return redirect(url_for('student_dashboard'))
        
        try:
            # Debugging: Print email being deleted
            print("Attempting to delete account for email:", student_email)
            
            # Connect to the database and execute the delete query
            cursor = mysql.connection.cursor()
            cursor.execute("DELETE FROM students WHERE email = %s", (student_email,))
            rows_deleted = cursor.rowcount  # Check how many rows were deleted

            # Commit the transaction
            mysql.connection.commit()

            # Debugging: Check if a row was deleted
            if rows_deleted > 0:
                print("Account successfully deleted for email:", student_email)
                flash('Your account has been successfully deleted.', 'success')
            else:
                print("No account found for email:", student_email)
                flash('No account found to delete.', 'error')
            
            # Clear the session and log the student out
            session.clear()
            return redirect(url_for('home'))  # Redirect to home or login page

        except Exception as e:
            # Print the error for debugging
            print("Error deleting account:", str(e))
            flash(f"Error deleting account: {str(e)}", "error")
            return redirect(url_for('student_dashboard'))

    else:
        flash('You must be logged in to delete your account.', 'warning')
        return redirect(url_for('login'))


@app.route('/prediction')
def prediction():
    return render_template('prediction.html')

@app.route('/placement_tips')
def placement_tips():
    tips = [
        "1. Stay updated with the latest technologies and trends in your field.",
        "2. Practice coding regularly, focusing on data structures and algorithms.",
        "3. Work on personal projects to showcase your skills to recruiters.",
        "4. Attend online courses and certifications to enhance your skills.",
        "5. Build a solid resume highlighting your skills, projects, and experiences.",
        "6. Prepare for aptitude tests and practice solving problems.",
        "7. Focus on mastering core subjects relevant to your field.",
        "8. Participate in hackathons and coding challenges to gain experience.",
        "9. Practice mock interviews to improve your communication and confidence.",
        "10. Network with professionals in your field to gain insights and advice.",
        "11. Join LinkedIn and actively connect with industry professionals.",
        "12. Focus on improving your soft skills like teamwork and communication.",
        "13. Volunteer for internship programs to gain industry experience.",
        "14. Keep a positive attitude and be ready for setbacks.",
        "15. Research companies and understand their work culture before interviews.",
        "16. Be well-versed with your own projects and be ready to explain them.",
        "17. Develop problem-solving skills and the ability to think on your feet.",
        "18. Learn how to manage time effectively, balancing studies and practice.",
        "19. Prepare thoroughly for technical interviews with hands-on coding.",
        "20. Review common interview questions and prepare answers in advance.",
        "21. Stay healthy and get enough rest, especially before interviews.",
        "22. Take part in group discussions to improve your speaking skills.",
        "23. Join placement preparation groups for peer-to-peer learning.",
        "24. Always ask for feedback after interviews to know areas for improvement.",
        "25. Be open to different roles and opportunities, even if they're not exactly as you envisioned.",
        "26. Be proactive in seeking guidance from mentors and faculty members."
    ]
    return render_template('placement_tips.html', tips=tips)

# Define the custom threshold
custom_threshold = 0.55

@app.route('/result', methods=['POST'])
def result():
    try:
        # Retrieve input data from the form
        cgpa = float(request.form['cgpa'])
        major_projects = int(request.form['major_projects'])
        workshops_certifications = int(request.form['workshops_certifications'])
        mini_projects = int(request.form['mini_projects'])
        skills = int(request.form['skills'])
        communication_skill_rating = float(request.form['communication_skill_rating'])
        internship = 1 if request.form['internship'].lower() == 'yes' else 0
        hackathon = 1 if request.form['hackathon'].lower() == 'yes' else 0
        percentage_12th = float(request.form['percentage_12th'])
        percentage_10th = float(request.form['percentage_10th'])
        backlogs = int(request.form['backlogs'])

        # Combine inputs into a feature vector
        features = [
            cgpa, major_projects, workshops_certifications, mini_projects,
            skills, communication_skill_rating, internship, hackathon,
            percentage_12th, percentage_10th, backlogs
        ]

        # Create a DataFrame with the same column order as during training
        data_point = pd.DataFrame({
            'CGPA': [cgpa],
            'Major Projects': [major_projects],
            'Workshops/Certificatios': [workshops_certifications],
            'Mini Projects': [mini_projects],
            'Skills': [skills],
            'Communication Skill Rating': [communication_skill_rating],
            'Internship': [internship],
            'Hackathon': [hackathon],
            '12th Percentage': [percentage_12th],
            '10th Percentage': [percentage_10th],
            'backlogs': [backlogs]
        })

        # Make sure the columns are in the correct order before scaling
        data_point = data_point[['CGPA', 'Major Projects', 'Workshops/Certificatios', 'Mini Projects', 
                                 'Skills', 'Communication Skill Rating', 'Internship', 'Hackathon', 
                                 '12th Percentage', '10th Percentage', 'backlogs']]

        # Scale the input features using the same scaler used during training
        features_scaled = scaler.transform(data_point)

        # Get the probability prediction
        probabilities = model.predict_proba(features_scaled)
        placed_probability = probabilities[0][1]  # Probability for class 1 (placed)

        # Define the custom threshold (e.g., 0.55)
        prediction = placed_probability >= custom_threshold

        # Debugging output for Flask:
        print("Prediction Probability:", placed_probability)
        print("Custom Threshold:", custom_threshold)
        print("Final Prediction:", prediction)

        # Render the result with properly formatted probability
        return render_template('result.html', prediction=bool(prediction), prediction_probability=round(placed_probability * 100, 2))

    except Exception as e:
        return f"An error occurred: {e}"

#TPO ROUTES

@app.route('/tpo/login', methods=['GET', 'POST'])
def tpo_login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        # Fetch TPO from the database
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM tpo WHERE username = %s", (username,))
        tpo = cur.fetchone()
        cur.close()

        if tpo:
            print(f"TPO Data: {tpo}")  # Debugging output

            #  Ensure password is hashed and matches
            if check_password_hash(tpo[4], password):  # Password is at index 4
                # Set session for TPO
                session['user_id'] = tpo[0]
                session['user_role'] = 'tpo'
                session['tpo_name'] = tpo[1]
                session['tpo_email'] = tpo[3]
                session.permanent = True

                print("Session Data: ", session)  # Debugging: Print session data

                flash(f'Welcome, {tpo[1]}!', 'success')
                return redirect(url_for('tpo_dashboard'))
            else:
                flash('❌ Invalid password. Please try again.', 'danger')
        else:
            flash('❌ Username not found. Please check and try again.', 'danger')

    return render_template('tpo_login.html')


@app.route('/tpo/signup', methods=['GET', 'POST'])
def tpo_signup():
    if request.method == 'POST':
        name = request.form['name']
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        hashed_password = generate_password_hash(password)
        try:
            conn = mysql.connection
            cursor = conn.cursor()
            cursor.execute("INSERT INTO tpo (name, username, email, password) VALUES (%s, %s, %s, %s)",
                           (name, username, email, hashed_password))
            conn.commit()
            flash('TPO signup successful! Please log in.', 'success')
            return redirect(url_for('tpo_login'))
        except Exception as e:
            flash(f'Error: {e}', 'danger')

    return render_template('tpo_signup.html')

@app.route('/tpo/dashboard', methods=['GET', 'POST'])
def tpo_dashboard():
    if 'user_role' in session and session['user_role'] == 'tpo':
        sheet_data = get_sheet_data()
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM companies")
        companies = cur.fetchall()
        cur.close()
        return render_template('tpo_dashboard.html', 
                               name=session['tpo_name'], 
                               data=sheet_data, 
                               companies=companies,)
    else:
        flash('You need to log in first.', 'warning')
        return redirect(url_for('tpo_login'))

@app.route('/tpo/add_company', methods=['GET', 'POST'])
def add_company():
    if 'user_role' in session and session['user_role'] == 'tpo':

        if request.method == 'POST':
            company_name = request.form['company_name']
            job_role = request.form['job_role']
            notification = request.form['notification']
            apply_link = request.form['apply_link']
            apply_deadline = request.form['apply_deadline']

            cur = mysql.connection.cursor()
            cur.execute("INSERT INTO companies (company_name, job_role, description, apply_link, apply_deadline) VALUES (%s, %s, %s, %s, %s)", 
                        (company_name, job_role, notification, apply_link, apply_deadline))
            mysql.connection.commit()
            company_id = cur.lastrowid  # Get the last inserted company ID
            cur.close()
            
            flash('Company added successfully!', 'success')
                        
            # OR use this if tpo_dashboard requires company_id
            return redirect(url_for('tpo_dashboard', company_id=company_id))  
        
        return render_template('add_company.html', company_id=0)
    else:
        flash('You need to log in first.', 'warning')
        return redirect(url_for('tpo_login'))

@app.route('/tpo/view_queries', methods=['GET'])
def view_queries():
    print(session)  # Debugging session values
    if 'user_role' in session and session['user_role'] == 'tpo':  # Corrected session check
        cursor = mysql.connection.cursor()
        cursor.execute("""
        SELECT q.id, s.name, q.query_text, q.submitted_at, q.status, q.reply_text 
        FROM queries q
        JOIN students s ON q.student_id = s.id
        ORDER BY q.submitted_at DESC
        """)
        queries = cursor.fetchall()
        cursor.close()
        return render_template('view_queries.html', queries=queries)
    
    flash('You need to log in as TPO to view the queries.', 'warning')
    return redirect(url_for('tpo_login'))

@app.route('/tpo/reply_query/<int:query_id>', methods=['POST'])
def tpo_reply_query(query_id):
    reply_text = request.form['reply_text']

    cursor = mysql.connection.cursor()

    # Fetch student email and name based on query_id
    cursor.execute("""
        SELECT s.email, s.name, q.query_text
        FROM queries q
        JOIN students s ON q.student_id = s.id
        WHERE q.id = %s
    """, (query_id,))
    result = cursor.fetchone()

    if not result:
        cursor.close()
        flash("Query not found.", "danger")
        return redirect(url_for('view_queries'))

    student_email, student_name, original_query = result

    # Update the query with reply
    cursor.execute("UPDATE queries SET reply_text = %s, status = 'replied' WHERE id = %s", (reply_text, query_id))
    mysql.connection.commit()
    cursor.close()

    # Send email to student
    try:
        msg = Message(
            subject="TPO has replied to your query - Campcruit",
            sender=('Campcruit', 'sakshi140912@gmail.com'),
            recipients=[student_email]
        )
        msg.body = f"""
Dear {student_name},

👋 Your query submitted through Campcruit has been reviewed by the TPO.

📝 Original Query:
{original_query}

📬 TPO Reply:
{reply_text}

Thank you for using Campcruit!

Warm regards,  
Campcruit Team
        """
        mail.send(msg)
        print("Reply email sent to student successfully.")
    except Exception as e:
        print(f"Error sending reply email: {str(e)}")

    flash("Reply sent successfully and email notification sent to student!", "success")
    return redirect(url_for('view_queries'))
@app.route('/tpo/send_notification/<int:company_id>', methods=['POST'])
def tpo_send_notification(company_id):
    print("Session Data: ", session)  # Debug session output

    if session.get('user_role') != 'tpo':
        flash('Please log in as TPO.', 'warning')
        return redirect(url_for('tpo_login'))

    cur = mysql.connection.cursor(DictCursor)
    cur.execute("SELECT * FROM companies WHERE id = %s", (company_id,))
    company = cur.fetchone()
    cur.close()

    if not company:
        flash("Company not found!", "danger")
        return redirect(url_for('tpo_dashboard'))

    notification_message = f"""
    {company['company_name']} - {company['job_role']} 

    Job Role: {company['job_role']}
    Description : {company['description']}
    Apply Link: {company['apply_link']}
    Apply Deadline: {company['apply_deadline']}
    """

    cur = mysql.connection.cursor()
    cur.execute("""
        INSERT INTO notifications (title, message, company_id, recipient_type, created_at)
        VALUES (%s, %s, %s, 'student', NOW())
    """, (f"{company['company_name']} - {company['job_role']}", notification_message, company_id))
    mysql.connection.commit()
    cur.close()

    print("Notification inserted successfully!")

    student_emails = get_student_emails()
    for email in student_emails:
        try:
            msg = Message(
                subject=f"{company['company_name']} - {company['job_role']}",
                sender=('TPO Notifications', 'sakshi140912@gmail.com'),
                recipients=[email]
            )
            msg.body = notification_message
            mail.send(msg)
        except Exception as e:
            print(f'Error sending email to {email}: {str(e)}')

    flash('Notification sent successfully to all students!', 'success')
    return redirect(url_for('tpo_dashboard'))


def get_student_emails():
    # Fetching student emails from the database
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT email FROM students")  # Query to get all student emails
    student_emails = cursor.fetchall()
    cursor.close()  # Close the cursor after fetching

    # Extracting email addresses from the result
    emails = [email[0] for email in student_emails]

    print("📧 Retrieved Emails:", emails)  # Debugging line
    return emails

@app.route('/tpo/general_notification', methods=['GET', 'POST'])
def tpo_general_notification():
    if session.get('user_role') != 'tpo':
        flash('Please log in as TPO.', 'warning')
        return redirect(url_for('tpo_login'))

    if request.method == 'POST':
        title = request.form.get('title')
        message = request.form.get('message')

        if not title or not message:
            flash('Title and message are required!', 'danger')
            return redirect(url_for('tpo_general_notification'))

        try:
            cur = mysql.connection.cursor()
            cur.execute("""
                INSERT INTO notifications (title, message, company_id, recipient_type, created_at)
                VALUES (%s, %s, NULL, 'student', NOW())
            """, (title, message))
            mysql.connection.commit()
            cur.close()

            print("✅ Notification successfully inserted into the database.")

        except Exception as db_error:
            mysql.connection.rollback()  # Rollback in case of an error
            print(f"❌ Database Error: {db_error}")
            flash('Failed to save notification. Please try again.', 'danger')
            return redirect(url_for('tpo_general_notification'))

        student_emails = get_student_emails()  # Function to fetch student emails
        for email in student_emails:
            try:
                msg = Message(
                    subject=title,
                    sender=('TPO Notifications', 'your_email@example.com'),
                    recipients=[email]
                )
                msg.body = message
                mail.send(msg)
            except Exception as email_error:
                print(f'⚠️ Error sending email to {email}: {email_error}')

        flash('General Notification sent successfully!', 'success')
        return redirect(url_for('tpo_dashboard'))

    return render_template('tpo_general_notification.html')



@app.route('/delete_tpo_account', methods=['POST'])
def delete_tpo_account():
    if 'tpo_logged_in' in session:
        # Debugging: Print session data
        print("Session data:", session)

        # Get the TPO's email from the session
        tpo_email = session.get('tpo_email')

        if not tpo_email:
            flash("Error: No email found in session.", "error")
            return redirect(url_for('tpo_dashboard'))

        try:
            # Debugging: Print email being deleted
            print("Attempting to delete TPO account for email:", tpo_email)

            # Connect to the database and execute the delete query
            cursor = mysql.connection.cursor()
            cursor.execute("DELETE FROM tpo WHERE email = %s", (tpo_email,))
            rows_deleted = cursor.rowcount  # Check how many rows were deleted

            # Commit the transaction
            mysql.connection.commit()

            # Debugging: Check if a row was deleted
            if rows_deleted > 0:
                print("TPO account successfully deleted for email:", tpo_email)
                flash('Your account has been successfully deleted.', 'success')
            else:
                print("No TPO account found for email:", tpo_email)
                flash('No account found to delete.', 'error')

            # Clear the session and log the TPO out
            session.clear()
            return redirect(url_for('home'))  # Redirect to home or login page

        except Exception as e:
            # Print the error for debugging
            print("Error deleting TPO account:", str(e))
            flash(f"Error deleting account: {str(e)}", "error")
            return redirect(url_for('tpo_dashboard'))

    else:
        flash('You must be logged in to delete your account.', 'warning')
        return redirect(url_for('tpo_login'))



#PASSWORD RESET
@app.route('/forgot_password/<user_type>', methods=['GET', 'POST'])
def forgot_password(user_type):
    # Validate user_type to ensure it's either 'student' or 'tpo'
    if user_type not in ['student', 'tpo']:
        flash('Invalid user type!', 'danger')
        return redirect(url_for('home'))  # Redirect to a safe page like home

    if request.method == 'POST':
        username = request.form['username']

        # Check user in the appropriate table
        cursor = mysql.connection.cursor()
        table_name = 'students' if user_type == 'student' else 'tpo'
        query = f"SELECT * FROM {table_name} WHERE username = %s"
        cursor.execute(query, (username,))
        user = cursor.fetchone()

        if user:
            session['reset_user_id'] = user[0]  # Assuming 'id' is the first column in your table
            session['reset_user_type'] = user_type
            flash('User found! Redirecting to reset password page.', 'success')
            return redirect(url_for('reset_password', user_type=user_type))
        else:
            flash('User not found. Please check the username.', 'danger')

    return render_template('forgot_password.html', user_type=user_type)


@app.route('/reset_password/<user_type>', methods=['GET', 'POST'])
def reset_password(user_type):
    if request.method == 'POST':
        new_password = request.form['new_password']
        confirm_password = request.form['confirm_password']

        if new_password == confirm_password:
            user_id = session.get('reset_user_id')
            table_name = 'students' if user_type == 'student' else 'tpo'
            cursor = mysql.connection.cursor()
            query = f"UPDATE {table_name} SET password = %s WHERE id = %s"
            cursor.execute(query, (new_password, user_id))
            mysql.connection.commit()
            flash('Password reset successfully. Please log in.', 'success')
            return redirect(url_for(f'{user_type}_login'))
        else:
            flash('Passwords do not match. Please try again.', 'danger')

    login_route = f'{user_type}_login'  # Create the endpoint dynamically
    return render_template('reset_password.html', user_type=user_type, login_route=login_route)


#COMPANY ROUTES

@app.route('/company/<int:company_id>', methods=['GET', 'POST'])
def company_details(company_id):
    conn = mysql.connection
    cursor = conn.cursor()

    # Fetch Company Data
    cursor.execute("SELECT * FROM companies WHERE id=%s", (company_id,))
    company = cursor.fetchone()

    if not company:
        flash('Company not found.', 'error')
        return redirect(url_for('view_companies'))

    company_data = {
        "id": company[0],
        "company_name": company[1],
        "job_role": company[2],
        "description": company[3],
        "apply_link": company[4],
        "apply_deadline": company[5]
    }

    if request.method == 'POST':
        title = f"New Opportunity at {company_data['company_name']}"
        message = f"""
        Dear Student,

        Exciting news! A new opportunity is available at {company_data['company_name']}.

        - Job Role: {company_data['job_role']}
        - Description: {company_data['description']}
        - Apply Here: {company_data['apply_link']}
        - Deadline: {company_data['apply_deadline']}

        Regards,
        TPO Office
        """
        
        cursor.execute("SELECT email FROM users WHERE role='student'")
        student_emails = [row[0] for row in cursor.fetchall()]
        
        cursor.execute("""
            INSERT INTO notifications (company_id, title, message, recipient_type, created_at)
            VALUES (%s, %s, %s, %s, NOW())
        """, (company_id, title, message, 'student'))
        conn.commit()
        
        send_email_notification(title, message, student_emails)
        
        flash('Notification sent successfully!', 'success')
        return redirect(url_for('company_details', company_id=company_id))

    cursor.close()
    return render_template('company_details.html', company=company_data)

@app.route('/view_companies')
def view_companies():
    conn = mysql.connection  # Remove parentheses
    cursor = conn.cursor()
    cursor.execute("SELECT id, company_name, job_role, apply_deadline FROM companies")  # Fix table name typo

    companies = cursor.fetchall()
    cursor.close()

    companies_list = []
    for company in companies:
        companies_list.append({
            'id': company[0],
            'company_name': company[1],
            'job_role': company[2],
            'apply_deadline': company[3]
        })

    return render_template('view_companies.html', companies=companies_list)

'''
@app.route('/view_companies')
def view_companies():
    conn = mysql.connection
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM companies")
    companies = cursor.fetchall()
    cursor.close()
    return render_template('company_list.html', companies=companies)
'''




@app.route('/update_company/<int:company_id>', methods=['GET', 'POST'])
def update_company(company_id):
    conn = mysql.connection  # Get database connection
    cursor = conn.cursor()  # Create cursor

    if request.method == 'POST':
        company_name = request.form['company_name']
        job_role = request.form['job_role']
        notification = request.form['notification']
        apply_link = request.form['apply_link']
        apply_deadline = request.form['apply_deadline']

        cursor.execute("""
            UPDATE companies 
            SET company_name=%s, job_role=%s, description=%s, apply_link=%s, apply_deadline=%s 
            WHERE id=%s
        """, (company_name, job_role, notification, apply_link, apply_deadline, company_id))
        
        conn.commit()  # Commit changes
        cursor.close()  # Close cursor
        return redirect(url_for('view_companies'))

    cursor.execute("SELECT * FROM companies WHERE id=%s", (company_id,))
    company = cursor.fetchone()  # Fetch the company details

    cursor.close()
    return render_template('update_company.html', company=company)

@app.route('/delete_company/<int:company_id>')
def delete_company(company_id):
    cur = mysql.connection.cursor()  # Get the cursor from Flask-MySQL
    cur.execute("DELETE FROM companies WHERE id=%s", (company_id,))
    mysql.connection.commit()  # Commit the changes
    cur.close()  # Close the cursor

    return redirect(url_for('view_companies'))


@app.route('/profile', methods=['GET', 'POST'])
def profile():
    if 'student_username' not in session:
        return redirect(url_for('login'))

    cursor = mysql.connection.cursor()

    # Fetch current user details
    cursor.execute("SELECT name, username, email, phone FROM students WHERE username = %s", (session['student_username'],))
    student = cursor.fetchone()

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        phone = request.form.get('phone', '').strip()

        if not username or not email or not phone:
            flash('All fields are required!', 'danger')
            return redirect(url_for('profile'))

        try:
            cursor.execute("""
                UPDATE students 
                SET username = %s, email = %s, phone = %s 
                WHERE username = %s
            """, (username, email, phone, session['student_username']))
            mysql.connection.commit()

            session['student_username'] = username
            flash('Profile updated successfully!', 'success')
        except Exception as e:
            mysql.connection.rollback()
            flash(f'Error updating profile: {str(e)}', 'danger')

        return redirect(url_for('profile'))

    return render_template('profile.html', student=student)


@app.route('/tpo/profile', methods=['GET', 'POST'])
def tpo_profile():
    # Check if the user is logged in and is a TPO
    if session.get('user_role') != 'tpo':
        flash('Please log in to access this page.', 'warning')
        return redirect(url_for('tpo_login'))

    # Fetch the TPO profile data from the database
    cur = mysql.connection.cursor()
    cur.execute("SELECT name, username, email, phone FROM tpo WHERE id = %s", (session['user_id'],))
    tpo = cur.fetchone()
    cur.close()

    # If it's a POST request (form submission), update the profile
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        phone = request.form.get('phone')

        # Update the TPO profile data in the database
        cur = mysql.connection.cursor()
        cur.execute("UPDATE tpo SET username = %s, email = %s, phone = %s WHERE id = %s",
                    (username, email, phone, session['user_id']))
        mysql.connection.commit()
        cur.close()

        # Flash a success message
        flash("✅ Profile updated successfully!", "success")

        # Fetch the updated profile data after the update
        cur = mysql.connection.cursor()
        cur.execute("SELECT name, username, email, phone FROM tpo WHERE id = %s", (session['user_id'],))
        tpo = cur.fetchone()
        cur.close()

    # Render the profile page with the current (or updated) TPO data
    return render_template('tpo_profile.html', tpo=tpo)


@app.route('/logout')
def logout():
    session.clear()  # Clear session data
    flash('Logged out successfully.', 'info')
    return redirect(url_for('home'))


if __name__ == '__main__':
    app.run(debug=True)
