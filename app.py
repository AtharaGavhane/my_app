from flask import Flask, request, render_template, redirect, url_for
import mysql.connector
from mysql.connector import Error

app = Flask(__name__)

# --- Configuration ---
# Make sure this database name matches the one you are using
db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': 'admin', 
    'database': 'registration_app7'
}
# Define the price on the server for security
PRICE_PER_PERSON = 100.00 

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['POST'])
def register_user():
    conn = None
    cursor = None
    try:
        # --- 1. Get All Form Data ---
        guardian_name = request.form['name']
        guardian_email = request.form['email']
        # This line is crucial for getting the payment method
        payment_method = request.form['payment_method']
        
        guardian_phone = request.form.get('phone')
        guardian_address = request.form.get('address')
        
        member_names = request.form.getlist('member_name')
        member_phones = request.form.getlist('member_phone')

        # --- 2. Securely Calculate Totals on the Server ---
        # This logic calculates the values that were previously NULL
        total_members = len(member_names)
        total_people = 1 + total_members 
        total_payment = total_people * PRICE_PER_PERSON

        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()

        # --- 3. Insert the Main Registration with Payment Details ---
        # Note that the query now includes the payment columns
        guardian_query = """INSERT INTO registrations 
                              (name, email, phone, address, payment_method, total_members, total_payment) 
                              VALUES (%s, %s, %s, %s, %s, %s, %s)"""
        guardian_data = (guardian_name, guardian_email, guardian_phone, guardian_address, payment_method, total_members, total_payment)
        cursor.execute(guardian_query, guardian_data)
        
        registration_id = cursor.lastrowid

        # --- 4. Loop Through and Insert Members ---
        if member_names:
            member_query = "INSERT INTO members (registration_id, name, phone) VALUES (%s, %s, %s)"
            for name, phone in zip(member_names, member_phones):
                if name:
                    member_data = (registration_id, name, phone)
                    cursor.execute(member_query, member_data)

        # --- 5. Commit all database changes ---
        conn.commit()

        return redirect(url_for('success', 
                                user_name=guardian_name, 
                                payment=total_payment, 
                                method=payment_method))

    except Error as e:
        print(f"DATABASE ERROR: {e}")
        if conn: 
            conn.rollback()
        return f"An error occurred during registration: {e}"

    finally:
        if cursor: 
            cursor.close()
        if conn and conn.is_connected(): 
            conn.close()

@app.route('/success')
def success():
    name = request.args.get('user_name')
    payment = request.args.get('payment')
    method = request.args.get('method')
    # This requires a 'success.html' file in your templates folder
    return render_template('success.html', name=name, payment=payment, method=method)

if __name__ == '__main__':
    app.run(debug=True, port=5000)

