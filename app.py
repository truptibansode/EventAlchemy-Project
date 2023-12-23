from flask import Flask, request, flash, render_template, session, redirect, url_for, send_from_directory, jsonify
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
import os
import mysql.connector
import cv2 
import random
import base64
from flask_mail import Mail, Message
from itsdangerous import URLSafeTimedSerializer


# Secret key for token generation
token_serializer = URLSafeTimedSerializer('your_token_secret_key')



app=Flask(__name__)
app.config ['SECRET_KEY'] = "m0ni1989xyzgjhtb" 


app.config['MAIL_SERVER']= 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587 
app.config['MAIL_USERNAME']= 'trptbnsd@gmail.com'
app.config['MAIL_PASSWORD']= 'mlha kfsc wpmf rbyu'
app.config['MAIL_USE_TLS'] = True

mail = Mail(app)


# MySQL database configuration
db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': '',
    'database': 'event_db',
    'pool_name': 'my_connection_pool',  # Define a pool name
    'pool_reset_session': True,  # Reset session variables for each connection from the pool
    'pool_size': 30  # Set the number of connections in the pool
}

# Create a connection pool
connection_pool = mysql.connector.pooling.MySQLConnectionPool(**db_config)


# Define the folder where profile pictures will be stored
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER



def generate_otp():
    otp = ''.join(random.choice('0123456789') for _ in range(6))
    print(f"Generated OTP: {otp}") 
    return otp


@app.route("/")
def home():
    if 'username' in session:
        username = session['username']
    else:
        username = None

    connection = connection_pool.get_connection()
    visit_update_cursor = connection.cursor()

    try:
        # Create a separate cursor for the visit count update
        visit_update_cursor = connection.cursor()

        # Increment the visit count when someone visits the main page
        visit_update_cursor.execute('UPDATE visits SET count = count + 1')

        # Commit the changes
        connection.commit()

        # Close the visit update cursor
        visit_update_cursor.close()

        return render_template('index.html', username=username)

    except Exception as e:
        # Handle exceptions
        return f"An error occurred: {str(e)}"

    finally:
        # Close the cursor and connection in the finally block
        connection.close()  # Close the connection




def get_visit_count():
    try:
        connection = connection_pool.get_connection()
        cursor = connection.cursor()
        cursor.execute('SELECT count FROM visits')
        count = cursor.fetchone()[0]
        return jsonify(visit_count=count)
    except Exception as e:
        return jsonify(error=str(e)), 500




# Route to initiate the password reset process
@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        user_email = request.form.get('email')

        if 'otp' not in session:
            otp = generate_otp()
            session['otp'] = otp

        # Send the OTP to the user's email
        send_otp_email(user_email, session['otp'])

        # Store the user's email for verification
        session['reset_email'] = user_email

        return redirect(url_for('verify_otp'))

    return render_template('forgot_password.html')




@app.route('/send_email/<email>', methods=['GET'])
def send_otp_email(email, otp):
    otp = session.get('otp')  # Retrieve the OTP from the session
    if otp is None:
        return jsonify({'error': 'No OTP found in the session.'})

    msg_title = 'OTP reset Email.'
    sender = 'eventalchemy.inc@app.com'
    msg = Message(msg_title, sender=sender, recipients=[email])
    msg_body = 'Hello, you have recently requested a password reset.'
    msg.body = f"Your OTP for password reset is: {otp}"
    data = {
        'app_name': "EventAlchemy Inc.",
        'title': msg_title,
        'body': msg_body,
    }

    msg.html = render_template("email.html", data=data, otp=otp)

    try:
        mail.send(msg)
        return jsonify({'message': 'Email sent successfully'})  # Return JSON response

    except Exception as e:
        return jsonify({'error': f'Failed to send email: {str(e)}'})  # Return JSON response




@app.route('/verify_otp', methods=['GET', 'POST'])
def verify_otp():
    if request.method == 'POST':
        entered_otp = request.form.get('otp')

        if 'otp' in session:
            expected_otp = session['otp']

            if not entered_otp:
                flash('Please enter the OTP.')
            elif entered_otp == expected_otp:
                session.pop('otp')  # Remove the OTP from the session
                return redirect(url_for('reset_password'))
            else:
                flash('Invalid OTP. Please try again.')

        else:
            flash('No OTP found in the session. Please initiate the reset process.')
    return render_template('verify_otp.html')




def validate_password(password):
    if len(password) < 8:
        return False
    has_lowercase = any(char.islower() for char in password)
    has_uppercase = any(char.isupper() for char in password)
    has_digit = any(char.isdigit() for char in password)
    return has_lowercase and has_uppercase and has_digit


def get_user_email(username):
    connection = connection_pool.get_connection()
    cursor = connection.cursor()

    query = "SELECT email FROM users_data WHERE username = %s"
    cursor.execute(query, (username,))
    user = cursor.fetchone()

    cursor.close()
    connection.close()

    if user:
        return user[0]  # Assuming the email is in the first column
    else:
        return None 
    


def send_password_reset_email(username):
    recipient_email = get_user_email(username)
    msg = Message('Password Reset Confirmation', sender="EventAlchemyInc@gmail.com", recipients=[recipient_email])
    msg.body = 'Your password has been successfully reset. If you did not request this change, please contact support@EventAlchemy.'
    mail.send(msg)

    try:
        mail.send(msg)
        return jsonify({'message': 'Email sent successfully'})  # Return JSON response

    except Exception as e:
        return jsonify({'error': f'Failed to send email: {str(e)}'})  # Return JSON response    

@app.route('/reset_password', methods=['GET', 'POST'])
def reset_password():
    if request.method == 'POST':
        username = request.form.get('username')
        new_password = request.form.get('new_password')
        
        if username and new_password:
            if validate_password(new_password):
                # Update the user's password in the database
                connection = connection_pool.get_connection()
                cursor = connection.cursor()

                query = "UPDATE users_data SET password = %s WHERE username = %s"
                cursor.execute(query,(new_password, username))
                connection.commit()
                cursor.close()
                connection.close()

                # Send an email notification
                send_password_reset_email(username)


                flash('Password reset successfully.')
                return redirect(url_for('login'))  # Redirect to the login page or any other appropriate page
            else:
                flash('Invalid password. Password requirements not met.')
        else:
            flash('Please enter your username and a new password.')

    return render_template('reset_password.html')



@app.route("/about")
def about():
    return render_template('about.html')

@app.route("/service")
def service():
    if 'username' in session:
        username = session['username']
    else:
        username = None
    

    return render_template('services.html', username=username)

@app.route("/contact", methods=['GET', 'POST'])
def contact():

    if 'username' in session:
        username = session['username']
    else:
        username = None

    if request.method == 'POST':
        Name = request.form['Name']
        age = request.form['age']
        Phone = request.form['Phone']
        message = request.form['message']
        typeofevent = request.form['typeofevent']
        package= request.form['package']
        eventdate = request.form['eventdate']
        attendees = request.form['attendees']
        location = request.form['location']
        eventtype = request.form.getlist('eventtype')
        eventtype_str = ', '.join(eventtype)  # Convert the list to a comma-separated string

        try:
            connection = mysql.connector.connect(**db_config)
            cursor = connection.cursor()

            # Insert data into the database
            query = "INSERT INTO `event_contact` (Name, age, phone, message, typeofevent, package, eventdate, attendees, location, eventtype) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
            values = (Name, age, Phone, message, typeofevent, package, eventdate, attendees, location, eventtype_str)
            cursor.execute(query, values)

        except Exception as e:
            return f"An error occurred: {str(e)}"
        
        finally:
            connection.commit()
            cursor.close()
            connection.close()
    
    return render_template('contact.html', username=username)

   

@app.route("/eventSchedule")
def eventSchedule():
    return render_template('EventSchedule.html')

@app.route('/testimonials')
def testimonials():
    return render_template('testimonials.html')


# Registration Route
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        contactinfo = request.form['contactinfo']
        email = request.form['email']
        gender = request.form['gender']
        age = request.form['Age']
        username = request.form['username']
        password = request.form['password']

        # Remove password hashing
        
        # Check if a profile picture was uploaded
        pfp = request.files.get('pfp')
        if pfp:
            # Ensure the filename is safe and unique
            pfp_filename = secure_filename(pfp.filename)
            pfp_path = os.path.join(app.config['UPLOAD_FOLDER'], pfp_filename)
            pfp.save(pfp_path)
            print("Profile picture path:", pfp_path)  # Add this line for debugging
        else:
            # Use a default profile picture
            pfp_path = 'static/def-pfp.jpg'  # Update the path as per your file structure

        try:
            connection = mysql.connector.connect(**db_config)
            cursor = connection.cursor()

            # Insert data into the database
            query = "INSERT INTO users_data (name, contactinfo, email, gender, age, username, password, pfp) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"
            values = (name, contactinfo, email, gender, age, username, password, pfp_path)
            print("Query:", query)  # Add this line for debugging
            cursor.execute(query, values)

            connection.commit()
            cursor.close()
            connection.close()

            session['username'] = username

            # Use Flask's flash message to store the registration success message
            flash("Registration successful. You can now log in.", "success")

            return render_template("login.html")
        except Exception as e:
            return f"An error occurred: {str(e)}"
    
    return render_template('register.html')



@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)





@app.route('/user-profile')
def user_profile():
    if 'username' in session:
        username = session['username']
        
        # Fetch user details from the database based on the username
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor()
        query = "SELECT * FROM users_data WHERE username = %s"
        cursor.execute(query, (username,))
        user_data = cursor.fetchone()
        
        # Fetch events and their status for the user
        query_events = "SELECT event_id, event_name, event_date, event_location, event_theme, event_attendees,  status FROM event WHERE username = %s"
        cursor.execute(query_events, (username,))
        events = cursor.fetchall()
        
        cursor.close()
        connection.close()

        if user_data:
            # Extract user details
            username, name, age, Email, gender, contactinfo, pfp = user_data[6], user_data[0], user_data[4], user_data[2], user_data[3], user_data[1], user_data[5]
            
            # Render user_profile.html template with user details and events
            return render_template('user_profile.html', username=username, name=name, age=age, Email=Email, gender=gender, contactinfo=contactinfo, pfp=pfp, events=events)
        else:
            return "User not found"
    else:
        return redirect(url_for("register"))  # Handle the case when the user is not logged in


@app.route('/edit-profile', methods=['GET', 'POST'])
def edit_profile():
    if 'username' in session:
        username = session['username']

        if request.method == 'POST':
            connection = connection_pool.get_connection()
            cursor = connection.cursor()

            # Update other user information first
            new_name = request.form.get('name')
            new_age = request.form.get('age')
            new_contactinfo = request.form.get('contactinfo')
            new_email = request.form.get('email')
            new_gender = request.form.get('gender')

            cursor.execute("UPDATE users_data SET name = %s, age = %s, contactinfo = %s, email = %s, gender = %s WHERE username = %s",
                           (new_name, new_age, new_contactinfo, new_email, new_gender, username))

            # Now update the username
            new_username = request.form.get('username')
            cursor.execute("UPDATE users_data SET username = %s WHERE username = %s", (new_username, username))

            # Handle profile picture cropping and updating
            if 'pfp' in request.files:
                pfp = request.files['pfp']
                if pfp.filename != '':
                    # Ensure the filename is safe and unique
                    pfp_filename = secure_filename(pfp.filename)
                    pfp_path = os.path.join(app.config['UPLOAD_FOLDER'], pfp_filename)
                    pfp.save(pfp_path)

                    # Open the uploaded image with OpenCV
                    image = cv2.imread(pfp_path)

                    # Perform image cropping (you can customize the coordinates)
                    x, y, w, h = 0, 0, min(image.shape[1], image.shape[0]), min(image.shape[1], image.shape[0])

                    cropped_image = image[y:y+h, x:x+w]

                    # Save the cropped image
                    cv2.imwrite(pfp_path, cropped_image)

                    # Update the user's profile picture path in the database
                    cursor.execute("UPDATE users_data SET pfp = %s WHERE username = %s", (pfp_path, username))

                    # Commit the changes
                    connection.commit()

            cursor.close()
            connection.close()

            # After successfully updating the profile, update the session's username
            session['username'] = new_username

            # Redirect the user back to their profile page.
            return redirect('/user-profile')

        # If it's a GET request, fetch the user's current profile information.
        connection = connection_pool.get_connection()
        cursor = connection.cursor()
        cursor.execute("SELECT name, email, age, gender, contactinfo, pfp FROM users_data WHERE username = %s", (username,))
        user_data = cursor.fetchone()
        cursor.close()
        connection.close()

        if user_data:
            name, email, age, gender, contactinfo, pfp_path = user_data
            encoded_pfp = base64.b64encode(open(pfp_path, "rb").read()).decode('utf-8') if pfp_path else None

            return render_template('edit_profile.html', username=username, name=name, email=email, age=age, gender=gender, contactinfo=contactinfo, encoded_pfp=encoded_pfp)

    else:
        return redirect(url_for("register"))  


# Login Route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'registration_message' in session:
        registration_message = session.pop('registration_message')
        alert_message = f"alert('{registration_message}');"
    else:
        alert_message = ""

    if request.method == 'POST':
        input_username = request.form['username']
        input_password = request.form['password']

        try:
            connection = mysql.connector.connect(**db_config)
            cursor = connection.cursor()

            query = "SELECT username, password FROM users_data WHERE username = %s"
            cursor.execute(query, (input_username,))
            result = cursor.fetchone()

            if result:
                db_username, db_password = result

                # Check the entered password directly (no hashing)
                if db_password == input_password:
                    # Password is correct
                    session['username'] = input_username
                    print("Logged in successfully")  # Add this line
                    return render_template("index.html")
                else:
                    flash("Incorrect password. Please try again.")
            else:
                flash("Invalid username. Please try again.")
                return render_template("login.html")    

        except Exception as e:
            return f"An error occurred: {str(e)}"

        finally:
            cursor.close()
            connection.close()

    return render_template('login.html', alert_message=alert_message)

@app.route('/logout')
def logout():
    session.pop('username', None)

    return redirect(url_for('login'))  # Redirect to the login page after logging out


"""@app.route("/login-error-redirecting-to-registration", methods=['GET'])
def custom_error_handler():
    flash("Error loading user, cannot find credentials. Please try again later.", "error")
    return render_template("login.html")"""



# Admin login route
@app.route('/admin_login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Check if the entered username and password are valid (you'll need to query your 'admin' table)

        connection = connection_pool.get_connection()
        cursor = connection.cursor()
        query="SELECT username, password FROM admin WHERE username = %s AND password = %s"
        cursor.execute(query, (username, password))
        result= cursor.fetchone()

        cursor.close()
        connection.close()

        # If valid, set a session variable to indicate admin login.
        if result:
            session['admin_logged_in'] = True
            return redirect('/admin')  # Redirect to the admin page if login is successful

        else:
            # Invalid credentials, show an error message or redirect to an error page
            return "Invalid admin credentials"
        

    return render_template('admin-login.html')


# admin page route
@app.route('/admin')
def admin():
          
    if 'admin_logged_in' in session and session['admin_logged_in']:
        try:
            
            connection = mysql.connector.connect(**db_config)
            cursor1 = connection.cursor(buffered=True)

            # Fetch the first query
            query1 = "SELECT id, username, name, email, age, gender, contactinfo FROM users_data"
            cursor1.execute(query1)
            users = cursor1.fetchall()
            
            # Close cursor1
            cursor1.close()
            


            # Fetch the visit count
            visit_cursor = connection.cursor(buffered=True)
            visit_cursor.execute('SELECT count FROM visits')
            visit_count = visit_cursor.fetchone()[0]
            
            # Close visit_cursor
            visit_cursor.close()

            # Commit the changes (if needed)
            connection.commit()

            # Close the connection
            connection.close()

            return render_template('admin.html', users=users, visit_count=visit_count)

        except Exception as e:
            return f"An error occurred: {str(e)}"


    else:
        return redirect('/admin_login')
    


@app.route('/user-contact-info')
def user_inquiry():   
    if 'admin_logged_in' in session and session['admin_logged_in']:
        try:
            connection = mysql.connector.connect(**db_config)
            cursor = connection.cursor(buffered=True)

            # Fetch the second query
            query = "SELECT * FROM event_contact"
            cursor.execute(query)
            data1 = cursor.fetchall()
                        
            cursor.close()
            connection.commit()
            connection.close()

            return render_template('user-inquiry.html', data1=data1)

        except Exception as e:
                return f"An error occurred: {str(e)}"


    else:
        return redirect('/admin_login')



@app.route('/event-created-admin')
def admin_events():
    if 'admin_logged_in' in session and session['admin_logged_in']:
        try:
            connection = mysql.connector.connect(**db_config)
            cursor = connection.cursor(buffered=True)

            query = "SELECT * FROM event"
            cursor.execute(query)
            pending_events = cursor.fetchall()

            cursor.close()
                        
            cursor.close()
            connection.commit()
            connection.close()

            return render_template('adminevents.html', pending_events=pending_events)

        except Exception as e:
                return f"An error occurred: {str(e)}"



@app.route('/events-approval')
def approval_panel():
    if 'admin_logged_in' in session and session['admin_logged_in']:
        try:
            connection = mysql.connector.connect(**db_config)
            cursor = connection.cursor(buffered=True)

            query = "SELECT username, event_name, event_date, event_location, event_theme, event_attendees, status, event_id FROM event WHERE status = 'pending'"
            cursor.execute(query)
            pending_events = cursor.fetchall()

            cursor.close()
                        
            cursor.close()
            connection.commit()
            connection.close()

            return render_template('approval-panel.html', pending_events=pending_events)

        except Exception as e:
                return f"An error occurred: {str(e)}"
    





@app.route('/send_approval_email/<int:event_id>', methods=['POST'])
def send_approval_email(event_id):
    if 'admin_logged_in' in session and session['admin_logged_in']:
        try:
            connection = mysql.connector.connect(**db_config)
            cursor = connection.cursor()

            # Fetch event details based on event_id
            query = "SELECT username, event_name, event_date, event_location, event_theme, event_attendees, status FROM event WHERE event_id = %s"
            cursor.execute(query, (event_id,))
            event_data = cursor.fetchone()

            if event_data:
                username, event_name, event_date, event_location, event_theme, event_attendees, status = event_data
                recipient_email = get_user_email(username)

                msg = Message('Event Approval Notification Email', sender="EventAlchemyInc@gmail.com", recipients=[recipient_email])
                msg.body = f'Your event, "{event_name}", has been approved by our admin. Event Details: Date: {event_date}, Location: {event_location}, Theme: {event_theme}, Attendees: {event_attendees}.'
                mail.send(msg)

                # Update the event status in the database
                update_status_query = "UPDATE event SET status = 'approved' WHERE event_id = %s"
                cursor.execute(update_status_query, (event_id,))
                connection.commit()

                cursor.close()
                connection.close()

                flash('Event approval email sent successfully.', 'success')
                return redirect(url_for('approval_panel'))
            else:
                return 'Event not found', 404

        except Exception as e:
            return f'Error sending approval email: {str(e)}', 500
    else:
        return 'Unauthorized', 401

# Similar function for sending rejection email
@app.route('/send_rejection_email/<int:event_id>', methods=['POST'])
def send_rejection_email(event_id):
    if 'admin_logged_in' in session and session['admin_logged_in']:
        try:
            connection = mysql.connector.connect(**db_config)
            cursor = connection.cursor()

            # Fetch event details based on event_id
            query = "SELECT username, event_name, event_date, event_location, event_theme, event_attendees, status FROM event WHERE event_id = %s"
            cursor.execute(query, (event_id,))
            event_data = cursor.fetchone()

            if event_data:
                username, event_name, event_date, event_location, event_theme, event_attendees, status = event_data
                recipient_email = get_user_email(username)

                msg = Message('Event Rejection Notification Email', sender="EventAlchemyInc@gmail.com", recipients=[recipient_email])
                msg.body = f'Sorry, your event, "{event_name}", has been rejected by our admin. Event Details: Date: {event_date}, Location: {event_location}, Theme: {event_theme}, Attendees: {event_attendees}.'
                mail.send(msg)

                # Update the event status in the database
                update_status_query = "UPDATE event SET status = 'rejected' WHERE event_id = %s"
                cursor.execute(update_status_query, (event_id,))
                connection.commit()

                cursor.close()
                connection.close()

                flash('Event rejection email sent successfully.', 'success')
                return redirect(url_for('approval_panel'))
            else:
                return 'Event not found', 404

        except Exception as e:
            return f'Error sending rejection email: {str(e)}', 500
    else:
        return 'Unauthorized', 401




@app.route('/approve_event/<int:event_id>', methods=['POST'])
def approve_event(event_id):
    if 'admin_logged_in' in session and session['admin_logged_in']:
        if request.method == 'POST':
            # Update the event's status to "approved" in your database
            connection = mysql.connector.connect(**db_config)
            cursor = connection.cursor()
            query = "UPDATE event SET status = 'approved' WHERE event_id = %s"
            cursor.execute(query, (event_id,))
            connection.commit()
            cursor.close()
            connection.close()
            
            message = "Event approved successfully."
            send_approval_email(event_id)
        else:
            message = "Invalid request method."
    else:
        message = "Admin not logged in."

    # Redirect back to the admin page with a message
    return redirect(url_for('approval_panel', message=message))

@app.route('/reject_event/<int:event_id>', methods=['POST'])
def reject_event(event_id):
    if 'admin_logged_in' in session and session['admin_logged_in']:
        if request.method == 'POST':
            # Update the event's status to "rejected" in your database
            connection = mysql.connector.connect(**db_config)
            cursor = connection.cursor()
            query = "UPDATE event SET status = 'rejected' WHERE event_id = %s"
            cursor.execute(query, (event_id,))
            connection.commit()
            cursor.close()
            connection.close()
            
            message = "Event rejected successfully."
            send_rejection_email(event_id)
        else:
            message = "Invalid request method."
    else:
        message = "Admin not logged in."

    # Redirect back to the admin page with a message
    return redirect(url_for('approval_panel', message=message))


@app.route('/admin-logout')
def admin_logout():
    # Remove the user's session data (in this case, the username)
    session.pop('admin_logged_in', None)

    # Redirect to the login page or any other appropriate page
    return redirect(url_for('admin_login'))  # Redirect to the login page after logging out



def send_eventcreated_mail(username):
    recipient_email = get_user_email(username)
    msg = Message('Event Application Confirmation', sender="EventAlchemyInc@gmail.com", recipients=[recipient_email])
    msg.body = 'Your Event has been created successfully. We will notify you about further status of your event application once our admin representative(s) take action. If you did not request this event, please reply to this mail or contact support@EventAlchemy.'
    mail.send(msg)

    try:
        mail.send(msg)
        return jsonify({'message': 'Email sent successfully'})  # Return JSON response

    except Exception as e:
        return jsonify({'error': f'Failed to send email: {str(e)}'})  # Return JSON response 



@app.route('/create_event', methods=['GET', 'POST'])
def create_event():
    if 'username' in session:
        if request.method == 'POST':
            event_name = request.form['event_name']
            event_date = request.form['event_date']
            event_location = request.form['event_location']
            event_theme = request.form['event_theme']
            event_attendees = request.form['event_attendees']

            username = session['username']

            connection = mysql.connector.connect(**db_config)
            cursor = connection.cursor()
            status = "pending"
            query = "INSERT INTO event (event_name, event_date, event_location, event_theme, event_attendees, status, username) VALUES (%s, %s, %s, %s, %s, %s, %s)"
            values = (event_name, event_date, event_location, event_theme, event_attendees, status, username)
            cursor.execute(query, values)
            connection.commit()
            

            send_eventcreated_mail(username) #sending event created mail


            # For now, let's print the event details for testing purposes.
            print(f"Event Name: {event_name}")
            print(f"Event Date: {event_date}")
            print(f"Event Location: {event_location}")
            print(f"Event Theme: {event_theme}")
            print(f"Event Theme: {event_attendees}")
            print(f"username: {username}")


            # After processing, you can redirect to a success page or any other appropriate page.
            return redirect(url_for("user_profile"))

        return render_template('create_event.html')
    else:
        # Redirect to the login page if the user is not logged in
        return redirect(url_for('login'))


@app.route('/delete_user/<int:id>', methods=['POST'])
def delete_user(id):
    if 'admin_logged_in' in session and session['admin_logged_in']:
        try:
            connection = mysql.connector.connect(**db_config)
            cursor = connection.cursor()

            # Delete the user's information from the database
            query = "DELETE FROM users_data WHERE id = %s"
            cursor.execute(query, (id,))
            connection.commit()
            cursor.close()
            connection.close()

            return 'User deleted successfully', 200  # Respond with a success status

        except Exception as e:
            return f'Error deleting user: {str(e)}', 500  # Respond with an error status

    else:
        return 'Unauthorized', 401  # Respond with an unauthorized status


@app.route('/edit_user/<id>', methods=['GET', 'POST'])
def edit_user(id):
    if 'admin_logged_in' in session and session['admin_logged_in']:
        if request.method == 'POST':
            try:
                connection = mysql.connector.connect(**db_config)
                cursor = connection.cursor()

                # Retrieve the updated data from the form
                new_name = request.form.get('name')
                new_age = request.form.get('age')
                new_contactinfo = request.form.get('contactinfo')
                new_email = request.form.get('email')
                new_gender = request.form.get('gender')

                # Update the user's information in the database
                query = "UPDATE users_data SET name = %s, age = %s, contactinfo = %s, email = %s, gender = %s WHERE id = %s"
                values = (new_name, new_age, new_contactinfo, new_email, new_gender, id)
                cursor.execute(query, values)
                connection.commit()

                cursor.close()
                connection.close()

                # Flash a success message to the user
                flash('User information updated successfully.', 'success')

                # Redirect the user to the admin page
                return redirect(url_for('admin'))

            except Exception as e:
                # Return an error response to the user
                return jsonify({'error': str(e)}), 500
        else:
            return "Unauthorized", 401

@app.route('/update_user/<int:id>', methods=['GET', 'POST'])
def update_user(id):
    if 'admin_logged_in' in session and session['admin_logged_in']:
        if request.method == 'POST':
            connection = connection_pool.get_connection()
            cursor = connection.cursor()

            username = request.form.get('username')
            new_name = request.form.get('name')
            new_email = request.form.get('email')
            new_contactinfo = request.form.get('contactinfo')
            new_gender = request.form.get('gender')
            new_age = request.form.get('age')

            query = "UPDATE users_data SET username = %s, name = %s, email = %s, contactinfo = %s, gender = %s, age = %s WHERE id = %s"
            cursor.execute(query, (username, new_name, new_email, new_contactinfo, new_gender, new_age, id))
            
            connection.commit()
            cursor.close()
            connection.close()
            return redirect('/admin')


        # If it's a GET request, fetch the user's current profile information.
        connection = connection_pool.get_connection()
        cursor = connection.cursor()
        cursor.execute("SELECT username, name, email, age, gender, contactinfo FROM users_data WHERE id = %s", (id,))
        user_data = cursor.fetchone()
        cursor.close()
        connection.close()

        if user_data:
            username ,name, email, age, gender, contactinfo= user_data

            return render_template('edituser.html', username=username, id=id, name=name, email=email, age=age, gender=gender, contactinfo=contactinfo)

    else:
        return "You are not authorized to access this page."
       
        


if __name__ == '__main__':
    app.run(debug=True, port=5000)
