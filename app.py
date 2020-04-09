from flask import Flask, render_template
# from flask_mysqldb import MySQL
import MySQLdb

app = Flask(__name__, static_url_path="")

# mysql = MySQL(app)

#Trying to connect
db_connection = MySQLdb.connect(host="",
                           user = "",
                           passwd = "",
                           db = "",
                           port = )
# If connection is not successful





@app.route('/', methods=['GET'])
def index():
  # Making Cursor Object For Query Execution
  cursor=db_connection.cursor()
  cursor.execute('SELECT * FROM admin')
  items = cursor.fetchall()
  admin_list=[]

  for item in items:
      admin={}
      admin['username'] = item[0]
      admin['email'] = item[1]
      admin_list.append(admin)

  # for admin in admin_list:
  #     print(admin['username'])

  # Closing Database Connection
  # db_connection.close()
  return render_template('index.html', admin_list=admin_list)

@app.route('/form', methods=['GET', 'POST'])
def form():
    return render_template('form.html')

if __name__ == '__main__':
    app.run(debug=True)