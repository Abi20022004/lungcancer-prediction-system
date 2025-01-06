from flask import Flask, render_template, request, redirect, session, jsonify
from flask_mysqldb import MySQL
import bcrypt
import pickle
import numpy as np
import pymysql.cursors

filename = 'Lung_Cancer.pkl'
with open(filename, 'rb') as f:
    lung_cancer_model = pickle.load(f)

app = Flask(__name__)
app.secret_key = 'your_secret_key'

app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = '996567'
app.config['MYSQL_DB'] = 'lung_cancer_prediction_system'

mysql = MySQL(app)
def get_db():
    return mysql.connection
def get_doctors():
    cur = mysql.connection.cursor()
    cur.execute("SELECT id, name FROM doctors")
    doctors = cur.fetchall()
    cur.close()
    return doctors

@app.route('/')
def home():
    if 'username' in session:
        return render_template('lung_cancer.html')
    else:
        return redirect('/login')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        try:
            cur = mysql.connection.cursor()
            cur.execute("SELECT * FROM login WHERE username = %s", (username,))
            user = cur.fetchone()

            if user and bcrypt.checkpw(password.encode('utf-8'), user[2].encode('utf-8')):
                session['username'] = username
                return redirect('/')
            else:
                error_message = 'Invalid username or password'
                return render_template('login.html', message=error_message)
        except Exception as e:
            print("Error during login:", e)  # Print detailed error message
            error_message = 'An error occurred while logging in'
            return render_template('login.html', message=error_message)
        finally:
            cur.close()
    else:
        if 'username' in session:
            return redirect('/')
        else:
            return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        try:
            hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())  # Hash the password
            cur = mysql.connection.cursor()
            cur.execute("INSERT INTO login (username, password) VALUES (%s, %s)", (username, hashed_password.decode('utf-8')))
            mysql.connection.commit()
            return redirect('/login')
        except Exception as e:
            print("Error during signup:", e)
            error_message = 'An error occurred while signing up'
            return render_template('signup.html', message=error_message)
        finally:
            cur.close()

    else:
        if 'username' in session:
            return redirect('/')
        else:
            return render_template('signup.html')

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect('/login')

@app.route('/delete_account', methods=['GET', 'POST'])
def delete_account():
    if 'username' in session:
        try:
            cur = mysql.connection.cursor()
            cur.execute("DELETE FROM login WHERE username = %s", (session['username'],))
            mysql.connection.commit()
            session.pop('username', None)
            return redirect('/login')
        except Exception as e:
            print("Error:", e)
            error_message = 'An error occurred while deleting the account'
            return render_template('error.html', message=error_message)  # Render an error template
        finally:
            cur.close()
    else:
        return redirect('/login')  # Redirect to login page if not logged in

@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    global cur
    if request.method == 'POST':
        username = request.form['username']
        new_password = request.form['new_password']

        try:
            cur = mysql.connection.cursor()
            cur.execute("SELECT * FROM login WHERE username = %s", (username,))
            user = cur.fetchone()

            if not user:
                error_message = 'Invalid username'
                return render_template('forgot.html', message=error_message)

            hashed_password = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt())
            cur.execute("UPDATE login SET password = %s WHERE username = %s",
                        (hashed_password.decode('utf-8'), username))
            mysql.connection.commit()
            print("Password updated successfully")
            return redirect('/login')
        except Exception as e:
            print("Error during password update:", e)
            error_message = 'An error occurred while updating the password'
            return render_template('forgot.html', message=error_message)
        finally:
            cur.close()
    else:
        return render_template('forgot.html')


@app.route('/predict', methods=['POST'])
def predict():
    if request.method == 'POST':

        name = request.form['name']
        gender = int(request.form['GENDER'])
        age = int(request.form['AGE'])
        smoking = int(request.form['SMOKING'])
        yellow_fingers = int(request.form['YELLOW_FINGERS'])
        anxiety = int(request.form['ANXIETY'])
        peer_pressure = int(request.form['PEER_PRESSURE'])
        chronic_disease = int(request.form['CHRONIC_DISEASE'])
        fatigue = int(request.form['FATIGUE'])
        allergy = int(request.form['ALLERGY'])
        wheezing = int(request.form['WHEEZING'])
        alcohol_consuming = int(request.form['ALCOHOL_CONSUMING'])
        coughing = int(request.form['COUGHING'])
        shortness_of_breath = int(request.form['SHORTNESS_OF_BREATH'])
        swallowing_difficulty = int(request.form['SWALLOWING_DIFFICULTY'])
        chest_pain = int(request.form['CHEST_PAIN'])


        features = np.array([gender, age, smoking, yellow_fingers, anxiety, peer_pressure,
                             chronic_disease, fatigue, allergy, wheezing, alcohol_consuming,
                             coughing, shortness_of_breath, swallowing_difficulty, chest_pain]).reshape(1, -1)

        # Make prediction
        prediction = lung_cancer_model.predict(features)


        if 'username' in session:
            try:
                cur = mysql.connection.cursor()
                cur.execute("INSERT INTO patient_details (name, age, result) VALUES (%s, %s, %s)",
                            (name, age, prediction[0]))
                mysql.connection.commit()
            except Exception as e:
                print("Error during saving prediction result:", e)
                mysql.connection.rollback()
            finally:
                cur.close()

        if prediction == 0:
            result = "Person Has Lung Cancer"
        else:
            result = "Person Does Not Have Lung Cancer"

        return render_template('lung_cancer.html', prediction_result=result)
    else:
        return redirect('/login')

@app.route('/book_appointment', methods=['GET', 'POST'])
def book_appointment():
        if 'username' not in session:
            return redirect('/login')

        if request.method == 'POST':
            doctor_id = request.form['doctor']
            appointment_date = request.form['appointment_date']
            patient_name = request.form['patient_name']

            try:
                cur = mysql.connection.cursor()
                cur.execute("INSERT INTO appointments (doctor_id, patient_name, appointment_date) VALUES (%s, %s, %s)",
                            (doctor_id, patient_name, appointment_date))
                mysql.connection.commit()
                cur.close()

                return "Appointment booked successfully!"

            except Exception as e:
                print("Error booking appointment:", e)
                return "An error occurred while booking the appointment."

        else:
            doctors = get_doctors()

            return render_template('book_appointment.html', doctors=doctors)

@app.route('/view_appointments')
def view_appointments():
    if 'username' not in session:
        return redirect('/login')

    appointments = []

    try:
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM appointments WHERE patient_name = %s", (session['username'],))
        rows = cur.fetchall()

        # Convert each row into a dictionary and append to the appointments list
        for row in rows:
            appointment = {
                'id': row[0],
                'doctor_id': row[1],
                'patient_name': row[2],
                'appointment_date': row[3]
            }
            appointments.append(appointment)

    except Exception as e:
        print("Error fetching appointments:", e)
        appointments = []

    finally:
        cur.close()

    return render_template('view_appointments.html', appointments=appointments)

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if 'is_admin' in session and session['is_admin']:
        return redirect('/admin/dashboard')

    if request.method == 'POST':
        admin_id = request.form['admin_id']
        password = request.form['password']

        try:
            cur = mysql.connection.cursor()
            cur.execute("SELECT * FROM admin WHERE admin_ID = %s", (admin_id,))
            admin = cur.fetchone()

            if admin and bcrypt.checkpw(password.encode('utf-8'), admin[1].encode('utf-8')):
                session['username'] = admin_id
                session['is_admin'] = True
                return redirect('/admin/dashboard')
            else:
                return render_template('admin_login.html', message='Invalid admin credentials')  # Failed login
        except Exception as e:
            print("Error during admin login:", e)
            return render_template('admin_login.html', message='An error occurred during login')
        finally:
            cur.close()
    else:
        return render_template('admin_login.html')

@app.route('/admin/dashboard')
def admin_dashboard():
    # Check if the user is an admin; redirect to login if not
    if 'is_admin' not in session or not session['is_admin']:
        return redirect('/admin/login')

    # Initialize the patient results list
    patient_results = []

    try:
        # Establish a connection to the MySQL database
        cur = mysql.connection.cursor()
        # Fetch name, age, and result from the patient_details table
        cur.execute("SELECT name, age, result FROM patient_details")
        # Store the fetched results
        patient_results = cur.fetchall()
    except Exception as e:
        # Print the error message if something goes wrong
        print("Error fetching patient results:", e)
    finally:
        # Ensure the cursor is closed to avoid resource leaks
        cur.close()

    # Render the admin dashboard and pass the patient results to the template
    return render_template('admin_dashboard.html', patient_results=patient_results)


@app.route('/admin/logout', methods=['GET', 'POST'])
def admin_logout():
    session.pop('username', None)
    session.pop('is_admin', None)
    return redirect('/admin/login')
@app.route("/appointments/<int:id>", methods=["DELETE"])
def delete_appointment(id):
    try:
        cur = mysql.connection.cursor()

        cur.execute("DELETE FROM appointments WHERE id = %s", (id,))

        mysql.connection.commit()

        if cur.rowcount == 0:
            return jsonify({"error": "Appointment not found"}), 404

        return "", 204

    except Exception as e:
        print("Error during delete:", e)
        return jsonify({"error": "An error occurred during deletion"}), 500

    finally:
        cur.close()

if __name__ == '__main__':
    app.run(debug=True)
