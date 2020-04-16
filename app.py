from flask import Flask, render_template, request, redirect, url_for, session, request
import hashlib
# from flask_mysqldb import MySQL
import MySQLdb
import re
import sys

app = Flask(__name__, static_url_path="")
app.secret_key = 'foodtruck'
# mysql = MySQL(app)

#Trying to connect
db_connection = MySQLdb.connect(host="127.0.0.1",
						   user = "root",
						   passwd = "root",
						   db = "cs4400spring2020",
						   port = 3306)
# If connection is not successful




global_foodtruckName = ''

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
    	if request.method == 'POST':
		    if 'order_history' in request.form:
		    	return redirect(url_for('cus_order_history'))
		    elif 'explore' in request.form:
		    	return redirect(url_for('customer_explore'))
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

	return render_template('manage_building_station.html', msg=msg, buildings=buildings, stations=stations)

# Screen 14
@app.route('/foodtruck_summary',methods=['GET', 'POST'])
def foodtruck_summary():
	msg = ''
	username=session['username']
	cursor = db_connection.cursor(MySQLdb.cursors.DictCursor)
	cursor.callproc('mn_get_station',[username,])
	cursor.execute('SELECT stationName FROM mn_get_station_result')
	stations = cursor.fetchall()


	if request.method == 'POST':
		# Filters
		if 'filter' in request.form:
			sort_by = request.form['sort_by']
			start_date = request.form['start_date']
			end_date = request.form['end_date']
			station_name = request.form['station_name']
			foodtruck_name = request.form['foodtruck_name']
			asc_desc = request.form['asc_desc']

			if sort_by == '':
				sort_by = None
			if start_date == '':
				start_date = None
			if end_date == '':
				end_date = None
			if foodtruck_name == '':
				foodtruck_name = None
			if asc_desc == '':
				asc_desc = None
			cursor.callproc('mn_filter_summary', (username, foodtruck_name, station_name, start_date, end_date, sort_by, asc_desc))
			db_connection.commit()
			cursor.execute('SELECT * FROM mn_filter_summary_result')
			items = cursor.fetchall()

			foodtruck_list=[]
			for item in items:
				order={}
				order['foodTruckName'] = item['foodTruckName']
				order['totalOrder'] = item['totalOrder']
				order['totalRevenue'] = item['totalRevenue']
				order['totalCustomer'] = item['totalCustomer']
				foodtruck_list.append(order)
			return render_template('foodtruck_summary.html', stations=stations, msg=msg, result=foodtruck_list)

		if 'foodtruck_select' in request.form and 'view_detail' in request.form:
			foodtruck_select = request.form['foodtruck_select']
			return redirect(url_for('summary_detail', foodTruckName=foodtruck_select))
	return render_template('foodtruck_summary.html', stations=stations, msg=msg)

# Screen 15
@app.route('/summary_detail', methods=['GET','POST'])
def summary_detail():
	foodTruckName = request.args.get('foodTruckName')
	username=session['username']
	cursor = db_connection.cursor(MySQLdb.cursors.DictCursor)
	cursor.callproc('mn_summary_detail', (username, foodTruckName))
	db_connection.commit()

	cursor.execute('SELECT * FROM mn_summary_detail_result')
	items = cursor.fetchall()
	foodtruck_list=[]
	for item in items:
		order={}
		order['date'] = item['date']
		order['customerName'] = item['customerName']
		order['totalPurchase'] = item['totalPurchase']
		order['orderCount'] = item['orderCount']
		order['foodNames'] = item['foodNames']
		foodtruck_list.append(order)
	return render_template('summary_detail.html', foodTruckName=foodTruckName, foodtruck_list=foodtruck_list)

# Screen 16
@app.route('/customer_explore', methods=['GET','POST'])
def customer_explore():
	msg = ''
	cursor = db_connection.cursor(MySQLdb.cursors.DictCursor)
	cursor.execute('SELECT buildingName from building')
	buildings = cursor.fetchall()
	cursor.execute('SELECT stationName from station')
	stations = cursor.fetchall()
	username=session['username']

	if request.method == 'POST':
		# Filters
		if 'filter' in request.form:
			building_tag = request.form['building_tag']
			if building_tag == '':
				building_tag = None
			foodtruck_name = request.form['foodtruck_name']
			if foodtruck_name == '':
				foodtruck_name = None
			food = request.form['food']
			if food == '':
				food = None
			if 'building_name' in request.form:
				building_name = request.form['building_name']
				if building_name == '':
					building_name = None
			else:
				building_name = None
			if 'station_name' in request.form:
				station_name = request.form['station_name']
				if station_name == '':
					station_name = None
			else:
				station_name = None

			cursor.callproc('cus_filter_explore', (building_name, station_name, building_tag, foodtruck_name, food))
			db_connection.commit()
			cursor.execute('SELECT * FROM cus_filter_explore_result')
			items = cursor.fetchall()

			explore_list=[]
			for item in items:
				order={}
				order['stationName'] = item['stationName']
				order['buildingName'] = item['buildingName']
				order['foodTruckNames'] = item['foodTruckNames']
				order['foodNames'] = item['foodNames']
				explore_list.append(order)

			return render_template('customer_explore.html', buildings=buildings, stations=stations, result=explore_list, msg=msg)

		# Select as current location
		if 'station_select' in request.form and 'select_location' in request.form:
			station_select = request.form['station_select']
			cursor.callproc('cus_select_location', (username, station_select))
			db_connection.commit()
			msg = "station selected!"

	return render_template('customer_explore.html', buildings=buildings, stations=stations, msg=msg)

# Screen 17
@app.route('/current_information', methods=['GET','POST'])
def current_information():
	username=session['username']
	# gets username's current information
	cursor = db_connection.cursor(MySQLdb.cursors.DictCursor)
	cursor.callproc('cus_current_information_basic', [username,])
	db_connection.commit()

	cursor.execute('SELECT * FROM cus_current_information_basic_result')
	items = cursor.fetchall()

	current_list=[]
	for item in items:
		order={}
		order['stationName'] = item['stationName']
		order['buildingName'] = item['buildingName']
		order['tags'] = item['tags']
		order['description'] = item['description']
		order['balance'] = item['balance']
		current_list.append(order)

	# get username's foodtruck information
	cursor.callproc('cus_current_information_foodtruck', [username,])
	cursor.execute('SELECT * FROM cus_current_information_foodtruck_result')
	items = cursor.fetchall()
	db_connection.commit()

	foodtruck_list=[]
	for item in items:
		order={}
		order['foodTruckName'] = item['foodTruckName']
		order['managerName'] = item['managerName']
		order['foodNames'] = item['foodNames']
		foodtruck_list.append(order)

	if request.method == 'POST':
		if 'foodtruck_select' in request.form and 'select_order' in request.form:
			foodtruck_select = request.form['foodtruck_select']
			return redirect(url_for('customer_order', foodTruckName=foodtruck_select))

	print(current_list)
	return render_template('current_information.html', current_list=current_list, foodtruck_list=foodtruck_list)

# Screen 18
@app.route('/customer_order', methods=['GET', 'POST'])
def customer_order():
	msg = ''
	foodTruckName = request.args.get('foodTruckName')
	cursor = db_connection.cursor(MySQLdb.cursors.DictCursor)
	cursor.execute('SELECT * FROM menuitem WHERE foodtruckName = %s', (foodTruckName,))
	items = cursor.fetchall()
	menu_list=[]
	for item in items:
		order={}
		order['price'] = item['price']
		order['foodName'] = item['foodName']
		menu_list.append(order)
	if request.method == 'POST':
		if 'submit_order' in request.form:
			date = request.form['date']
			if date != '':
				cursor.callproc('cus_order', (date, session['username']))
				db_connection.commit()
				cursor.execute('SELECT orderID FROM orders WHERE date = %s AND customerUsername = %s', (date,session['username']))
				items = cursor.fetchall()

				print(items[0])
				orderID = items[0]['orderID']
				purchase_quantity = request.form.getlist('purchase_quantity')
				food_list = request.form.getlist('food_select')

				j = 0
				for i in range(len(purchase_quantity)):
					if purchase_quantity[i] != '':
						foodName = food_list[j]
						quantity = purchase_quantity[i]
						j+=1

						cursor.callproc('cus_add_item_to_order', (foodTruckName, foodName, quantity, orderID))

				msg = 'order placed successfully!'


	return render_template('customer_order.html', foodTruckName=foodTruckName, menu_list=menu_list, msg = msg)

# Screen 19
@app.route('/order_history', methods=['GET', 'POST'])
def cus_order_history():
	username=session['username']
	cursor = db_connection.cursor(MySQLdb.cursors.DictCursor)
	cursor.callproc('cus_order_history', [username,])

	cursor.execute('SELECT * FROM cus_order_history_result')
	items = cursor.fetchall()
	history_list=[]

	for item in items:
		order={}
		order['date'] = item['date']
		order['orderID'] = item['orderID']
		order['orderTotal'] = item['orderTotal']
		order['foodNames'] = item['foodNames']
		order['foodQuantity'] = item['foodQuantity']
		history_list.append(order)

	return render_template('orderhistory.html', history_list=history_list)

if __name__ == '__main__':
	app.run(debug=True)