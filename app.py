from flask import Flask, render_template, request, redirect, url_for, session
import hashlib
# from flask_mysqldb import MySQL
import MySQLdb
import re
import sys
import json

app = Flask(__name__, static_url_path="")
app.secret_key = 'cs4400spring2020'
# mysql = MySQL(app)

#Trying to connect
db_connection = MySQLdb.connect(host="127.0.0.1",
						   user = "root",
						   passwd = "cloud1515",
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

@app.route('/logout', methods=['GET'])
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
			return redirect(url_for('updateBuilding', buildingName=building_select))
		if 'building_select' in request.form and 'update_station' in request.form:
			building_select = request.form['building_select']
			try:
				cursor.execute('SELECT stationName FROM station WHERE buildingName = %s', (building_select,))
			except:
				msg = "Selected building has no station(s)."
				render_template('manage_building_station.html', msg=msg, buildings=buildings, stations=stations)
			station_result = cursor.fetchone()
			return redirect(url_for('updateStation', stationName=station_result['stationName']))
	cursor.close()

	return render_template('manage_building_station.html', msg=msg, buildings=buildings, stations=stations)

@app.route('/manage_food_truck', methods=['GET', 'POST'])
def manage_food_truck():
	msg = ''
	cursor = db_connection.cursor(MySQLdb.cursors.DictCursor)
	cursor.execute('SELECT stationName FROM station')
	stations = cursor.fetchall()
	manager_name = session['username']
	cursor.callproc('mn_filter_foodTruck', (manager_name, None, None, None, None, False))
	db_connection.commit()
	cursor.execute('SELECT * FROM mn_filter_foodtruck_result')
	result = cursor.fetchall()
	print(result, file=sys.stderr)
	if 'filter' in request.form:
		food_truck_name = request.form['food_truck_name']
		station_name = request.form['station_name']
		if food_truck_name == '':
			food_truck_name = None
		if station_name == '':
			station_name = None
		min_staff = request.form['min_staff']
		max_staff = request.form['max_staff']
		if min_staff == '':
			min_staff = None
		if max_staff == '':
			max_staff = None
		if 'remaining' in request.form:
			remaining = True
		else:
			remaining = False
		cursor.callproc('mn_filter_foodTruck', (manager_name, food_truck_name, station_name, min_staff, max_staff, remaining))
		db_connection.commit()
		cursor.execute('SELECT * FROM mn_filter_foodtruck_result')
		result = cursor.fetchall()
		print((manager_name, food_truck_name, station_name, min_staff, max_staff, remaining), file=sys.stderr)
		cursor.close()
		return render_template('manage_food_truck.html', msg=msg, stations=stations, result=result)
	if 'foodTruck_select' in request.form and 'delete_foodTruck' in request.form:
		foodTruck_select = request.form['foodTruck_select']
		try:
			cursor.execute('DELETE FROM foodtruck WHERE foodtruck = %s', (foodTruck_select,))
			db_connection.commit()
			msg = 'Food truck deleted!'
		except:
			msg = 'Cannot delete selected food truck.'
	if 'foodTruck_select' in request.form and 'update_foodTruck' in request.form:
		foodTruck_select = request.form['foodTruck_select']
		return redirect(url_for('updateFoodTruck', foodTruckName=foodTruck_select))		
	cursor.close()
	return render_template('manage_food_truck.html', msg=msg, stations=stations, result=result)

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
			try:
				cursor.callproc('ad_add_building_tag', (building_name, tag))
				db_connection.commit()
			except:
				msg = "No duplicate tags!"
				return render_template('create_building.html', msg=msg)
	return render_template('create_building.html', msg=msg)

# might not need get ??
@app.route('/createFood', methods=['GET', 'POST'])
def createFood():
	msg = ''
	if request.method == 'POST':
		cursor = db_connection.cursor(MySQLdb.cursors.DictCursor)
		cursor.execute("SELECT * FROM Food WHERE foodName =%s", [request.form["foodName"]])
		food = cursor.fetchone()
		if food is None:
			args = []
			args.append(request.form["foodName"])
			cursor.callproc('ad_create_food', args)
			db_connection.commit()
		else:
			msg = "Food already exists."
		cursor.close()
	return render_template('createFood.html', msg=msg)

@app.route('/manageFood', methods=['GET', 'POST'])
def manageFood():
	msg = ''
	cursor = db_connection.cursor(MySQLdb.cursors.DictCursor)
	cursor.execute("SELECT foodName FROM MenuItem")
	menuItems = [item['foodName'] for item in cursor.fetchall()]

	cursor.execute("select foodName, sum(purchaseQuantity) from OrderDetail group by foodName")
	purchaseQuantity = cursor.fetchall()
	purchaseQuantityDict = {}
	for item in purchaseQuantity:
		purchaseQuantityDict[item['foodName']] = int(item['sum(purchaseQuantity)'])

	cursor.execute("SELECT foodName FROM Food")
	foods = cursor.fetchall()
	for food in foods:
		itemCount = 0
		if food['foodName'] in purchaseQuantityDict.keys():
			itemCount = purchaseQuantityDict[food['foodName']]
		food['menuCount'] = menuItems.count(food['foodName'])
		food['purchaseCount'] = itemCount

	if request.method == "POST":
		print(request.form)
		#filter
		if "filter" in request.form:
			try:
				args = [request.form["filterFood"], None, None]
				cursor.callproc('ad_filter_food', args)
				db_connection.commit()
				cursor.execute('SELECT * FROM ad_filter_food_result')
				filtered = cursor.fetchall()
				return render_template('manageFood.html', allFoods=foods, items=filtered)
			except:
				msg = 'Pick a food to filter by.'
				return render_template('manageFood.html', msg=msg, allFoods=foods, items=foods)

		#sorting
		if "sortNameASC" in request.form:
			cursor.callproc('ad_filter_food', [None, "name", "ASC"])
			db_connection.commit()
			cursor.execute('SELECT * FROM ad_filter_food_result')
			sortedList = cursor.fetchall()
			return render_template('manageFood.html', allFoods=foods, items=sortedList)

		if "sortNameDESC" in request.form:
			cursor.callproc('ad_filter_food', [None, "name", "DESC"])
			db_connection.commit()
			cursor.execute('SELECT * FROM ad_filter_food_result')
			sortedList = cursor.fetchall()
			return render_template('manageFood.html', allFoods=foods, items=sortedList)

		if "sortMenuCountASC" in request.form:
			cursor.callproc('ad_filter_food', [None, "menuCount", "ASC"])
			db_connection.commit()
			cursor.execute('SELECT * FROM ad_filter_food_result')
			sortedList = cursor.fetchall()
			return render_template('manageFood.html', allFoods=foods, items=sortedList)

		if "sortMenuCountDESC" in request.form:
			cursor.callproc('ad_filter_food', [None, "menuCount", "DESC"])
			db_connection.commit()
			cursor.execute('SELECT * FROM ad_filter_food_result')
			sortedList = cursor.fetchall()
			return render_template('manageFood.html', allFoods=foods, items=sortedList)

		if "sortPurchCountASC" in request.form:
			cursor.callproc('ad_filter_food', [None, "purchaseCount", "ASC"])
			db_connection.commit()
			cursor.execute('SELECT * FROM ad_filter_food_result')
			sortedList = cursor.fetchall()
			return render_template('manageFood.html', allFoods=foods, items=sortedList)

		if "sortPurchCountDESC" in request.form:
			cursor.callproc('ad_filter_food', [None, "purchaseCount", "DESC"])
			db_connection.commit()
			cursor.execute('SELECT * FROM ad_filter_food_result')
			sortedList = cursor.fetchall()
			return render_template('manageFood.html', allFoods=foods, items=sortedList)

		# delete food
		if "delete" in request.form:
			try:
				args = []
				args.append(request.form["food"])
				cursor.callproc('ad_delete_food', args)
				db_connection.commit()
			except:
				msg = 'Cannot delete food.'
				return render_template('manageFood.html', msg=msg, allFoods=foods, items=foods)
	cursor.close()
	return render_template('manageFood.html', msg=msg, allFoods=foods, items=foods)

@app.route('/updateStation/<stationName>', methods=['GET', 'POST'])
def updateStation(stationName):
	msg = ''
	cursor = db_connection.cursor(MySQLdb.cursors.DictCursor)
	cursor.callproc('ad_view_station', [stationName])
	db_connection.commit()
	cursor.execute('SELECT * FROM ad_view_station_result')
	station = cursor.fetchone()
	cursor.execute('SELECT buildingName FROM Building')
	buildings = [item['buildingName'] for item in cursor.fetchall()]

	if request.method == "POST":
		if int(request.form['capacity']) > 0:
			args = []
			args.append(stationName)
			args.append(request.form['capacity'])
			args.append(request.form['sponsoredBuilding'])
			cursor.callproc('ad_update_station', args)
			db_connection.commit()
		else:
			msg = 'Capacity must be positive.'
	cursor.close()
	return render_template('updateStation.html', msg=msg, stationName=stationName,
		capacity=station['capacity'], sponsoredBuilding=station['buildingName'], buildings=buildings)

@app.route('/createStation', methods=['GET', 'POST'])
def createStation():
	msg = ''
	cursor = db_connection.cursor(MySQLdb.cursors.DictCursor)
	cursor.callproc('ad_get_available_building')
	db_connection.commit()
	cursor.execute('SELECT buildingName FROM ad_get_available_building_result')
	buildings = [item['buildingName'] for item in cursor.fetchall()]

	if request.method == "POST":
		name = request.form['stationName']
		capacity = request.form['capacity']
		sponsoredBuilding = request.form['sponsoredBuilding']

		cursor.execute("SELECT * FROM Station WHERE stationName = %s", [name])
		existingName = cursor.fetchone()

		try:
			if existingName is not None:
				msg = "Station already exists. Please pick another name."

			elif int(request.form['capacity']) <= 0:
				msg = "Capacity must be positive."

			else:
				args = []
				args.append(name)
				args.append(sponsoredBuilding)
				args.append(capacity)
				cursor.callproc('ad_create_station', args)
				db_connection.commit()

		except:
			msg = "Capacity must be an integer."

	cursor.close()
	return render_template('createStation.html', msg=msg, buildings=buildings)

@app.route('/updateBuilding/<buildingName>', methods=['GET', 'POST'])
def updateBuilding(buildingName):
	msg = ''
	cursor = db_connection.cursor(MySQLdb.cursors.DictCursor)
	cursor.callproc('ad_view_building_general', [buildingName])
	db_connection.commit()
	cursor.execute('SELECT * FROM ad_view_building_general_result')
	building = cursor.fetchone()
	description = building['description']

	cursor.callproc('ad_view_building_tags', [buildingName])
	db_connection.commit()
	cursor.execute('SELECT * FROM ad_view_building_tags_result')
	tags = [item['tag'] for item in cursor.fetchall()]

	if request.method == "POST":
		print(request.form)
		print(request.form.getlist('tagList'))
		newName = request.form['buildingName']
		newDescription = request.form['description']
		tagList = request.form.getlist('tagList')

		# name hasn't changed
		if newName == buildingName:
			# do normally
			args = []
			args.append(buildingName)
			args.append(newName)
			args.append(newDescription)
			cursor.callproc('ad_update_building', args)
			db_connection.commit()

		# name changed, need to check if new name already exists
		elif newName != buildingName:
			cursor.execute("SELECT * FROM Building WHERE buildingName = %s", [newName])
			existingName = cursor.fetchone()
			if existingName is not None:
				msg = "A building with this name already exists, pick a new name."
				return render_template('updateBuilding.html', msg=msg, buildingName=buildingName, description=description, tags=tags)
			else:
				# do normally
				args = []
				args.append(buildingName)
				args.append(newName)
				args.append(newDescription)
				cursor.callproc('ad_update_building', args)
				db_connection.commit()

		for tag in tagList:
			if tag in tags:
				# don't do anything
				continue
			if tag not in tags and tag != '':
				# add new tag
				cursor.callproc('ad_add_building_tag', [newName, tag])
				db_connection.commit()
		for tag in tags:
			if tag not in tagList:
				# delete tag
				cursor.callproc('ad_remove_building_tag', [newName, tag])
				db_connection.commit()

	cursor.close()
	return render_template('updateBuilding.html', msg=msg, buildingName=buildingName, description=description, tags=tags)

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

@app.route('/updateFoodTruck/<foodTruckName>', methods=['GET', 'POST'])
def updateFoodTruck(foodTruckName):
	msg = ''
	cursor = db_connection.cursor(MySQLdb.cursors.DictCursor)
	cursor.execute('select Station.stationName, (capacity - count(FoodTruck.foodTruckName)) as remainingCapacity from Station JOIN FoodTruck on Station.stationName = FoodTruck.stationName group by Station.stationName having remainingCapacity > 0')
	stations = [item['stationName'] for item in cursor.fetchall()]

	#	get current station
	cursor.execute('SELECT stationName FROM FoodTruck WHERE foodTruckName = %s', [foodTruckName])
	station = cursor.fetchone()['stationName']

	# get available staff
	cursor.callproc('mn_view_foodTruck_available_staff', [session['username'], foodTruckName])
	db_connection.commit()
	cursor.execute('SELECT * FROM mn_view_foodTruck_available_staff_result')
	availableStaff = [item['availableStaff'] for item in cursor.fetchall()]

	# get assigned staff
	cursor.callproc('mn_view_foodTruck_staff', [foodTruckName])
	db_connection.commit()
	cursor.execute('SELECT * from mn_view_foodTruck_staff_result')
	assignedStaff = [item['assignedStaff'] for item in cursor.fetchall()]

	# get current menu
	cursor.callproc('mn_view_foodTruck_menu', [foodTruckName])
	db_connection.commit()
	cursor.execute('SELECT * from mn_view_foodTruck_menu_result')
	menu = cursor.fetchall()

	# get food items not in current menu
	cursor.execute("SELECT foodName from Food where foodName not in %s", [[item['foodName'] for item in menu]])
	foods = [item['foodName'] for item in cursor.fetchall()]

	if request.method == "POST":
		newStation = request.form['station']
		newStaffList = request.form.getlist('assignedStaff')
		newMenuItems = request.form['addedFoods'].split('#')[:-1]
		newCosts = request.form['addedPrices'].split('#')[:-1]

		if station != newStation:
			# change station 22a
			cursor.callproc('mn_update_foodTruck_station', [foodTruckName, station])
			db_connection.commit()

		# assign new staff 22b
		for staff in newStaffList:
			cursor.execute("SELECT username FROM User WHERE firstName = %s AND lastName = %s", [staff.split(' ')[0], staff.split(' ')[1]])
			username = cursor.fetchone()['username']
			# newly assigned staff
			if staff in availableStaff:

				cursor.callproc('mn_update_foodTruck_staff', [foodTruckName, username])
				db_connection.commit()

		for staff in assignedStaff:
			cursor.execute("SELECT username FROM User WHERE firstName = %s AND lastName = %s", [staff.split(' ')[0], staff.split(' ')[1]])
			username = cursor.fetchone()['username']
			# removed staff
			if staff not in newStaffList:
				cursor.callproc('mn_update_foodTruck_staff', [None, username])
				db_connection.commit()

		# add new menu items 22c
		if len(newMenuItems) > 0:
			for i in range(len(newMenuItems)):
				cursor.callproc('mn_update_foodTruck_menu_item', [foodTruckName, float(newCosts[i]), newMenuItems[i]])
				db_connection.commit()

	return render_template('updateFoodTruck.html', msg=msg, foodTruckName=foodTruckName,
		station=station, stations=stations, assignedStaff=assignedStaff,
		availableStaff=availableStaff, menu=menu, foods=foods)

@app.route('/createFoodTruck', methods=['GET', 'POST'])
def createFoodTruck():
	msg = ''
	cursor = db_connection.cursor(MySQLdb.cursors.DictCursor)
	cursor.execute('select Station.stationName, (capacity - count(FoodTruck.foodTruckName)) as remainingCapacity from Station JOIN FoodTruck on Station.stationName = FoodTruck.stationName group by Station.stationName having remainingCapacity > 0')
	stations = [item['stationName'] for item in cursor.fetchall()]

	# get available staff
	cursor.callproc('mn_view_foodTruck_available_staff', [session['username'], None])
	db_connection.commit()
	cursor.execute('SELECT * FROM mn_view_foodTruck_available_staff_result')
	availableStaff = [item['availableStaff'] for item in cursor.fetchall()]

	# get food items
	cursor.execute("SELECT foodName from Food")
	foods = [item['foodName'] for item in cursor.fetchall()]

	if request.method == "POST":
		print(request.form)
		foodTruckName = request.form['foodTruckName']
		station = request.form['station']
		staff = request.form.getlist('assignedStaff')

		if request.form['addedFoods'] == '':
			msg = "Add at least one menu item."
			return render_template('createFoodTruck.html', msg=msg, availableStaff=availableStaff, foods=foods, stations=stations)

		addedFoods = request.form['addedFoods'].split('#')[:-1]
		prices = request.form['addedPrices'].split('#')[:-1]

		# create food truck
		cursor.execute("SELECT * FROM FoodTruck WHERE foodTruckName = %s", [foodTruckName])
		existingName = cursor.fetchone()
		if existingName is not None:
			msg = "Food truck already exists. Pick a new name."
			return render_template('createFoodTruck.html', msg=msg, availableStaff=availableStaff, foods=foods, stations=stations)

		cursor.callproc('mn_create_foodTruck_add_station', [foodTruckName, station, session['username']])
		db_connection.commit()

		# add staff
		for newStaff in staff:
			# get username
			cursor.execute("SELECT username FROM User WHERE firstName = %s AND lastName = %s", [newStaff.split(' ')[0], newStaff.split(' ')[1]])
			username = cursor.fetchone()['username']
			cursor.callproc('mn_create_foodTruck_add_staff', [foodTruckName, username])
			db_connection.commit()

		# create menu
		for i in range(len(addedFoods)):
			cursor.callproc('mn_create_foodTruck_add_menu_item', [foodTruckName, prices[i], addedFoods[i]])
			db_connection.commit()

	return render_template('createFoodTruck.html', msg=msg, availableStaff=availableStaff, foods=foods, stations=stations)

if __name__ == '__main__':
	app.run(debug=True)