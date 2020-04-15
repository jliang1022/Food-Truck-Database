from flask import Flask, render_template, request, redirect, url_for, session
import hashlib
# from flask_mysqldb import MySQL
import MySQLdb
import re
import sys
import json

app = Flask(__name__, static_url_path="")
app.secret_key = 'foodtruck'
# mysql = MySQL(app)

#Trying to connect
db_connection = MySQLdb.connect(host="127.0.0.1",
						   user = "root",
						   passwd = "Jl102298722321487",
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
		# Check if account exists using MySQL
		cursor = db_connection.cursor(MySQLdb.cursors.DictCursor)
		cursor.callproc('login', (username, password))
		# Fetch one record and return result
		db_connection.commit()
		
		cursor.execute('SELECT * FROM login_result')
		account = cursor.fetchone()
		# If account exists in accounts table in out database
		if account:
			# Create session data, we can access this data in other routes
			session['loggedin'] = True
			session['username'] = account['username']
			session['userType'] = account['userType']
			# Redirect to home page
			return redirect(url_for('home'))
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
	# Check if POST requests exist (user submitted form)
	if request.method == 'POST':
		# Create variables for easy access
		username = request.form['username']
		password = request.form['password']
		confirm_password = request.form['confirm_password']
		firstname = request.form['firstname']
		lastname = request.form['lastname']
		email = request.form['email']
		balance = request.form['balance']

		if balance:
			try:
				float(balance)
			except ValueError:
				msg = 'Balance must be a positive decimal number!'
				return render_template('register.html', msg=msg)
		else:
			balance = None

		if email:
			if not re.match(r'[^@]+@[^@]+\.[^@]+', email):
				msg = 'Invalid email address!'
				return render_template('register.html', msg=msg)
			if 'role' in request.form:
				role = request.form['role']
			else:
				role = None
		else:
			email = None
			role = None

		if not balance and not (email and role):
			msg = 'Please fill out balance (positive decimal) and/or email and select a role!'
			return render_template('register.html', msg=msg)

	# Check if account exists using MySQL
		cursor = db_connection.cursor(MySQLdb.cursors.DictCursor)
		cursor.execute('SELECT * FROM user WHERE username = %s', (username,))
		account = cursor.fetchone()
		# If account exists show error and validation checks
		if account:
			msg = 'Account already exists!'
			return render_template('register.html', msg=msg)
		elif not re.match(r'[A-Za-z0-9]+', username):
			msg = 'Username must contain only characters and numbers!'
			return render_template('register.html', msg=msg)
		elif len(password) < 8:
			msg = 'Please choose a password length of at least 8!'
			return render_template('register.html', msg=msg)
		elif password != confirm_password:
			msg = 'Passwords do not match!'
			return render_template('register.html', msg=msg)

		cursor.callproc('register', (username, email, firstname, lastname, password, balance, role))
		db_connection.commit()
		cursor.close()
		msg = 'You have successfully registered!'
	return render_template('register.html', msg=msg)

@app.route('/home')
def home():
    # Check if user is loggedin
    if 'loggedin' in session:
        # User is loggedin show them the home page
        return render_template('home.html', username=session['username'], userType=session['userType'])
    # User is not loggedin redirect to login page
    return redirect(url_for('login'))

@app.route('/manage_building_station', methods=['GET', 'POST'])
def manage_building_station():
	msg = ''
	# Drop-down menus
	cursor = db_connection.cursor(MySQLdb.cursors.DictCursor)
	cursor.execute('SELECT buildingName from building')
	buildings = cursor.fetchall()
	cursor.execute('SELECT stationName from station')
	stations = cursor.fetchall()

	if request.method == 'POST':
		# Filters
		if 'filter' in request.form:
			building_tag = request.form['building_tag']
			min_capacity = request.form['min_capacity']
			max_capacity = request.form['max_capacity']
			if 'building_name' in request.form:
				building_name = request.form['building_name']
			else:
				building_name = ''
			if 'station_name' in request.form:
				station_name = request.form['station_name']
			else:
				station_name = ''
			if min_capacity == '':
				min_capacity = None
			if max_capacity == '':
				max_capacity = None
			cursor.callproc('ad_filter_building_station', (building_name, building_tag, station_name, min_capacity, max_capacity))
			db_connection.commit()
			cursor.execute('SELECT * FROM ad_filter_building_station_result')
			result = cursor.fetchall()
			return render_template('manage_building_station.html', msg=msg, result=result, buildings=buildings, stations=stations)

		# Delete buttons
		if 'building_select' in request.form and 'delete_building' in request.form:
			building_select = request.form['building_select']
			cursor.callproc('ad_delete_building', (building_select))
			db_connection.commit()
			msg = 'Building deleted!'
		elif 'building_select' in request.form and 'delete_station' in request.form:
			building_select = request.form['building_select']
			cursor.callproc('ad_delete_station', (building_select))
			db_connection.commit()
			msg = 'Station deleted!'
		elif 'delete_building' in request.form or 'delete_station' in request.form:
			msg = 'Select a building or station to delete.'

		# Update buttons
		if 'building_select' in request.form and 'update_building' in request.form:
			building_select = request.form['building_select']
			cursor.execute('SELECT description FROM building WHERE buildingName = %s', (building_select))
			description = cursor.fetchone()
			cursor.execute('SELECT tag FROM buildingtag WHERE buildingName = %s', (building_select))
			tag = cursor.fetchone()
			return redirect(url_for('update_building'))
		if 'building_select' in request.form and 'update_station' in request.form:
			building_select = request.form['building_select']
			cursor.execute('SELECT stationName FROM station WHERE buildingName = %s', (building_select))
			stationName = cursor.fetchone()
			cursor.execute('SELECT capacity FROM station WHERE buildingName = %s', (building_select))
			capacity = cursor.fetchone()
			return redirect(url_for('update_station'))
	cursor.close()
	
	return render_template('manage_building_station.html', msg=msg, buildings=buildings, stations=stations)

@app.route('/create_building', methods=['GET', 'POST'])
def create_building():
	msg = ''
	cursor = db_connection.cursor(MySQLdb.cursors.DictCursor)
	if request.method == "POST":
		tags = request.form["tags"]
		tags = json.loads(tags)
		if tags == []:
			msg = 'Please input at least one tag.'
			return render_template('create_building.html', msg=msg)
		building_name = request.form["building_name"]
		building_description = request.form["building_description"]
		cursor.callproc('ad_create_building', (building_name, building_description))
		db_connection.commit()
		for tag in tags:
			cursor.callproc('ad_add_building_tag', (building_name, tag))
			db_connection.commit()
	return render_template('create_building.html', msg=msg)


if __name__ == '__main__':
	app.run(debug=True)