from flask import Flask, render_template, request, redirect, flash
from random import choice
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import os
from flask_cors import CORS
from datetime import datetime


web_site = Flask(__name__)
web_site.secret_key = 'hashed_key'

UPLOAD_FOLDER = 'static/images/'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'avif', 'webp'}
web_site.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


def allowed_file(filename):
  return '.' in filename and \
         filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


CORS(web_site)


@web_site.route('/')
def index():
  print("home page")
  return render_template('index.html')


@web_site.route('/home_page')
def Home_page():
  print("home page")
  return render_template('index.html')


@web_site.route('/runonce')
def createDBandTable():
  con = sqlite3.connect('lostproperty.db')
  sql_items = """
  CREATE TABLE Items (id INTEGER,
  name TEXT,
  colour TEXT,
  room TEXT,
  date TEXT,
  description TEXT,
  status TEXT,
  image BLOB,
  PRIMARY KEY(id AUTOINCREMENT))
  """
  sql_users = """
  CREATE TABLE Users (id INTEGER,
  email TEXT,
  firstName TEXT,
  password1 TEXT,
  password2 TEXT,
  PRIMARY KEY(id AUTOINCREMENT))
  """
  sql_admins = """
  CREATE TABLE Admins (id INTEGER,
  admin_name TEXT,
  admin_login TEXT,
  PRIMARY KEY(id AUTOINCREMENT))
  """

  cursor = con.cursor()
  cursor.execute(sql_items)
  cursor.execute(sql_users)
  cursor.execute(sql_admins)
  con.commit()
  return "database and table created"


@web_site.route('/sign_up', methods=['GET', 'POST'])
def sign_up():
  if request.method == 'POST':
    email = request.form["email"]
    firstName = request.form["firstName"]
    password1 = request.form["password1"]
    password2 = request.form["password2"]
    if len(str(email)) < 4:
      flash("Email must be greater than 3 characters", category="error")
    elif len(str(firstName)) < 2:
      flash("firstName must be greater than 1 characters", category="error")
    elif password1 != password2:
      flash("Passwords don't match", category="error")
    elif len(str(password1)) < 7:
      flash("Password must be at least 7 characters", category="error")
    else:
      con = sqlite3.connect('lostproperty.db')
      sql = "INSERT INTO Users (email, firstName, password1, password2) VALUES(?,?,?,?)"
      cursor = con.cursor()
      cursor.execute(sql, (email, firstName, password1, password2))
      con.commit()
      flash("user added", category="success")
      print("user signed-up")

  return render_template("signup.html")


@web_site.route('/log_in', methods=['GET', 'POST'])
def log_in():
  if request.method == 'POST':
    email = request.form["email"]
    password = request.form["password"]
    con = sqlite3.connect('lostproperty.db')
    sql = "SELECT * FROM Users WHERE email = ? AND password1 = ?"
    print("login")
    return render_template("login.html", boolean=True)


@web_site.route('/report_item', methods=['GET', 'POST'])
def itemsadd():
  msg = ""
  if request.method == 'POST':
    name = request.form["name"]
    room = request.form["room"]
    colour = request.form["colour"]
    date = request.form["date"]
    status = request.form["status"]
    description = request.form.get("description")
    image = request.files["image"]

    if description is None:
      flash("Description is required", category="error")
      return render_template("report_item.html", )

    con = sqlite3.connect('lostproperty.db')
    sql = "INSERT INTO Items(name,colour,room,date,status,description) VALUES(?,?,?,?,?,?)"
    cursor = con.cursor()
    cursor.execute(sql, (name, colour, room, date, status, description))
    lastrowid = cursor.lastrowid
    con.commit()
    if image and allowed_file(image.filename):
      filename = secure_filename(
          image.filename) if image.filename else 'default_filename.jpg'
      image.save(os.path.join(web_site.config['UPLOAD_FOLDER'], filename))
      print("image uploaded")
      sql = "UPDATE Items SET image=? WHERE id = ?"  #using parameters
      cursor = con.cursor()
      cursor.execute(sql, (filename, lastrowid))
      con.commit()
    msg = name + " added to the Items table"

  allstatuses = ["LOST", "FOUND", "ARCHIVED"]
  today = datetime.today().strftime('%Y-%m-%d')
  return render_template("report_item.html",
                         msg=msg,
                         allstatuses=allstatuses,
                         date=today)


@web_site.route('/search_item', methods=['GET', 'POST'])
def search():
  allstatuses = ["LOST", "FOUND", "ARCHIVED"]
  print("search_item")
  return render_template("search_item.html", allstatuses=allstatuses)


@web_site.route('/items_list')
def listall():
  con = sqlite3.connect('lostproperty.db')
  con.row_factory = sqlite3.Row
  cursor = con.cursor()
  sql = 'SELECT * FROM Items ORDER BY date DESC'
  cursor.execute(sql)
  con.commit()
  rows = cursor.fetchall()
  return render_template("items_list.html", rows=rows)


@web_site.route('/items_list_filter', methods=['POST'])
def listsome():
  name = request.form["name"]
  room = request.form["room"]
  colour = request.form["colour"]
  date = request.form["date"]
  status = request.form["status"]
  description = request.form["description"]
  con = sqlite3.connect('lostproperty.db')
  con.row_factory = sqlite3.Row
  cursor = con.cursor()
  items = 0
  # add perameterized queries
  sql = "SELECT * FROM Items "
  if name != "":
    sql = sql + "WHERE name LIKE '%" + name + "%' "
    items += 1

  if colour != "":
    if items == 0:
      sql = sql + "WHERE "
    if items >= 1:
      sql = sql + "AND"
    sql = sql + " colour LIKE '%" + colour + "%'"
    items += 1

  if room != "":
    if items == 0:
      sql = sql + "WHERE "
    if items >= 1:
      sql = sql + "AND"
    sql = sql + " room LIKE '%" + room + "%'"
    items += 1

  if date != "":
    if items == 0:
      sql = sql + "WHERE "
    if items >= 1:
      sql = sql + "AND"
    sql = sql + " date >= '" + date + "'"
    items += 1

  if status != "":
    if items == 0:
      sql = sql + "WHERE "
    if items >= 1:
      sql = sql + "AND"
    sql = sql + " status LIKE '%" + status + "%'"
    items += 1

  if description != "":
    if items == 0:
      sql = sql + "WHERE "
    if items >= 1:
      sql = sql + "AND"
    sql = sql + " description LIKE '%" + description + "%'"
    items += 1
  cursor.execute(sql)
  #cursor.execute("SELECT * FROM Items WHERE name LIKE %?% AND colour LIKE %?% AND room LIKE %?% AND date >= ?", (name, colour, room, date))
  con.commit()
  rows = cursor.fetchall()
  return render_template("items_list.html", rows=rows)


@web_site.route('/edit_item', methods=['GET', 'POST'])
def edit_item():
  id = request.args.get('id', None)
  msg = ""  #initialise this for later
  if request.method == 'POST':
    name = request.form["name"]
    room = request.form["room"]
    colour = request.form["colour"]
    date = request.form["date"]
    status = request.form["status"]
    image = request.files["image"]  # uploaded file NEW
    con = sqlite3.connect('lostproperty.db')
    # NEW to add images
    if image and allowed_file(image.filename):
      filename = secure_filename(image.filename)
      print("hello")
      image.save(os.path.join(web_site.config['UPLOAD_FOLDER'], filename))
      sql = "UPDATE Items SET name='"+name+"',room='"+room+"',colour='"+colour+"', date='"+date+"', status='"+status+"', image='"+filename+"' WHERE id = "+id
      #sql = "UPDATE Items SET name=?,room=?,colour=?, date=?, status=?, image=? WHERE id = ?" 
      print(sql)
      print(filename)
      cursor=con.cursor()
      #cursor.execute(sql, (name, room, colour, date, status,filename, id))
      cursor.execute(sql)
    #END NEW to add images
    else:
      con = sqlite3.connect('lostproperty.db')

      sql = "UPDATE Items SET name=?,room=?,colour=?, date=?, status=? WHERE id = ?"  #using parameters
      cursor = con.cursor()
      cursor.execute(sql, (name, room, colour, date, status, id))
      con.commit()

    msg = name + " was successfully edited"

  con = sqlite3.connect('lostproperty.db')
  con.row_factory = sqlite3.Row
  cursor = con.cursor()

  allstatuses = ["LOST", "FOUND", "ARCHIVED"]

  #reload item
  if id is not None:
    sql = "SELECT * FROM Items WHERE id=" + id
    cursor.execute(sql)
    con.commit()
    rows = cursor.fetchall()
    print(rows)
    for row in rows:
      return render_template(
          "report_item.html",
          name=row["name"],
          colour=row["colour"],
          room=row["room"],
          date=row["date"],
          status=row["status"],
          image=row["image"],
          msg=msg,allstatuses=allstatuses
      )
  else:
    return "item not found"


@web_site.route('/delete_item')
def delete_item():
  id = request.args.get('id')
  print("delete item")
  con = sqlite3.connect('lostproperty.db')
  con.row_factory = sqlite3.Row
  cursor = con.cursor()
  sql = "DELETE FROM Items WHERE id = ?"
  #sql ="SELECT * FROM Items WHERE id = ?"
  cursor.execute(sql, (id, ))
  con.commit()
  return redirect("/search_item")


web_site.run(host='0.0.0.0', port=8080, debug=True)
