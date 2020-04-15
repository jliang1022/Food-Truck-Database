from flask import Flask, render_template, request, redirect, url_for, session
import hashlib
import MySQLdb
import re

app = Flask(__name__, static_url_path="")
# app.secret_key = 'foodtruck'

#Trying to connect
db_connection = MySQLdb.connect(host="127.0.0.1",
						   user = "root",
						   passwd = "root",
						   db = "cs4400spring2020",
						   port = 3306)
# If connection is not successful





@app.route('/', methods=['GET', 'POST'])
def login():
	msg = ''
	# Making Cursor Object For Query Execution
	if request.method == 'POST' and 'username' in request.form and 'password' in request.form:
		# Create variables for easy access
		username = request.form['username']
		password = request.form['password']
		password = hashlib.md5(password.encode()).hexdigest()
		# Check if account exists using MySQL
		cursor = db_connection.cursor(MySQLdb.cursors.DictCursor)
		cursor.execute('SELECT * FROM user WHERE username = %s AND password = %s', (username, password,))
		# Fetch one record and return result
		account = cursor.fetchone()
		# If account exists in accounts table in out database
		if account:
			# Create session data, we can access this data in other routes
			session['loggedin'] = True
			# Redirect to home page
			return 'Logged in successfully!'
		else:
			# Account doesnt exist or username/password incorrect
			msg = 'Incorrect username/password!'
	return render_template('index.html', msg=msg)

@app.route('/logout')
def logout():
	session.pop('loggedin', None)
	session.pop('username', None)
	return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
	# Output message if something goes wrong...
	msg = ''
	# Check if "username", "password" and "email" POST requests exist (user submitted form)
	if request.method == 'POST' and 'username' in request.form and 'password' in request.form and 'confirm_password' in request.form and 'firstname' in request.form and 'lastname' in request.form:
		# Create variables for easy access
		username = request.form['username']
		password = request.form['password']
		confirm_password = request.form['confirm_password']
		firstname = request.form['firstname']
		lastname = request.form['lastname']

	# Check if account exists using MySQL
		cursor = db_connection.cursor(MySQLdb.cursors.DictCursor)
		cursor.execute('SELECT * FROM user WHERE username = %s', (username,))
		account = cursor.fetchone()
		# If account exists show error and validation checks
		if account:
			msg = 'Account already exists!'
		elif not re.match(r'[A-Za-z0-9]+', username):
			msg = 'Username must contain only characters and numbers!'
		elif len(password) < 8:
			msg = 'Please choose a password length of at least 8!'
		elif password != confirm_password:
			msg = 'Passwords do not match!'
		elif not username or not password or not confirm_password or not firstname or not lastname:
			msg = 'Please fill out the form!'
		elif 'balance' in request.form:
			balance = request.form['balance']
			# Account doesnt exists and the form data is valid, now insert new account into accounts table
			try:
				float(balance)
			except ValueError:
				msg = 'Balance must be a postiive decimal number!'
			if msg == '':
				if float(balance) > 0:
					password = hashlib.md5(password.encode()).hexdigest()
					cursor.execute('INSERT INTO user VALUES (%s, %s, %s, %s)', (username, password, firstname, lastname))
					cursor.execute('INSERT INTO customer VALUES(%s, %s, NULL)', (username, balance,))
					db_connection.commit()
					msg = 'You have successfully registered!'
		elif 'email' in request.form:
			email = request.form['email']
			if not re.match(r'[^@]+@[^@]+\.[^@]+', email):
				msg = 'Invalid email address!'
			elif role:
				role = request.form['role']
				password = hashlib.md5(password.encode()).hexdigest()
				cursor.execute('INSERT INTO user VALUES (%s, %s, %s, %s)', (username, password, firstname, lastname))
				cursor.execute('INSERT INTO employee VALUES(%s, %s)', (username, email))
				if role == 'admin':
					cursor.execute('INSERT INTO admin VALUES(%s, %s)', (username, email))
				elif role == 'manager':
					cursor.execute('INSERT INTO manager VALUES(%s, %s)', (username, email))
				elif role == 'staff':
					cursor.execute('INSERT INTO staff VALUES(%s, %s, NULL)', (username, email))
				db_connection.commit()
				msg = 'You have successfully registered!'
			else:
				msg = 'Please select a role!'
		elif 'balance' in request.form and 'email' in request.form:
			balance = request.form['balance']
			email = request.form['email']
			try:
				float(balance)
			except ValueError:
				msg = 'Balance must be a postive decimal number!'
				if msg == '':
					if float(balance) > 0:
						if role:
							role = request.form['role']
							password = hashlib.md5(password.encode()).hexdigest()
							cursor.execute('INSERT INTO user VALUES (%s, %s, %s, %s)', (username, password, firstname, lastname))
							cursor.execute('INSERT INTO customer VALUES(%s, %s, NULL)', (username, balance,))
							cursor.execute('INSERT INTO employee VALUES(%s, %s)', (username, email))
							if role == 'admin':
								cursor.execute('INSERT INTO admin VALUES(%s, %s)', (username, email))
							elif role == 'manager':
								cursor.execute('INSERT INTO manager VALUES(%s, %s)', (username, email))
							elif role == 'staff':
								cursor.execute('INSERT INTO staff VALUES(%s, %s, NULL)', (username, email))
							db_connection.commit()
							msg = 'You have successfully registered!'
						else:
							msg = 'Please select a role!'
		else:
			msg = 'Please fill out balance (positve decimal) and/or email!'

	return render_template('register.html', msg=msg)

@app.route('/orderhistory', methods=['GET', 'POST'])
def cus_order_history():
	cursor = db_connection.cursor(MySQLdb.cursors.DictCursor)
	cursor.callproc('cus_order_history', ["customer1",])
	# for result in cursor.stored_results():
	# 	print(result.fetchall())
	cursor.execute('SELECT * FROM cus_order_history_result')
	items = cursor.fetchall()
	history_list=[]

	for item in items:
		print(item)
		order={}
		order['date'] = item['date']
		order['orderID'] = item['orderID']
		order['orderTotal'] = item['orderTotal']
		order['foodNames'] = item['foodNames']
		order['foodQuantity'] = item['foodQuantity']
		history_list.append(order)

	# for order in history_list:
	# 	print(order['orderID'])

	return render_template('orderhistory.html', history_list=history_list)

if __name__ == '__main__':
	app.run(debug=True)