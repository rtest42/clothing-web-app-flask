from flask import Flask, render_template, request, redirect, session, flash
from flask_session import Session
import sqlite3
import requests
import os
import ast
import base64
from dotenv import load_dotenv

app = Flask(__name__)
# Filters
app.jinja_env.filters["usd"] = lambda value: f"${value:,.2f}"
app.jinja_env.filters["decode"] = lambda value: value.decode('utf-8')
# Auto-reload templates
app.config["TEMPLATES_AUTO_RELOAD"] = True
# Use filesystem instead of cookies
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

database = "armoire.db"

# Populate valid searches
wearable_keywords = []
with open('wearable_keywords.txt', 'r') as file:
    for keyword in file:
        wearable_keywords.append(keyword.replace('\n', ''))


@app.after_request
def after_request(response):
    # Ensure responses aren't cached
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


def read_query(get_all, sql_cmd, *args):
    with sqlite3.connect(database) as db:
        cursor = db.cursor()
        cursor.execute(sql_cmd, args)
        if get_all:
            query = cursor.fetchall()
        else:
            query = cursor.fetchone()
        db.commit()
        return query


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/shop', methods=['GET', 'POST'])
def shop():
    err = None
    shopping_results = None
    if request.method == 'POST':
        # SerpAPI key obtained by signing up at https://serpapi.com
        # Default plan: 100 uses per month
        serpapi_key = os.getenv('serpapi_key')

        search_query = request.form.get('shop').lower().strip()

        # Determines if search is acceptable or not
        is_wearable = False
        for wearable in wearable_keywords:
            if search_query.find(wearable) >= 0:
                is_wearable = True
                break

        dropdown = {
            'relevance': 'p_ord:r',
            'review': 'p_ord:rv',
            'low2high': 'p_ord:p',
            'high2low': 'p_ord:pd'
        }

        # Do not perform search if not clothing-related
        if not is_wearable:
            err = "Invalid search!"
        else:
            # Search using SerpAPI
            url = 'https://serpapi.com/search'
            params = {
                'q': search_query,
                'api_key': serpapi_key,
                'engine': 'google_shopping',
                'tbs': dropdown[request.form.get('filter')]
            }

            # Get results in JSON
            response = requests.get(url, params=params)
            shopping_results = response.json()['shopping_results']

    return render_template('shop.html', err=err, results=shopping_results)


@app.route('/add-to-cart', methods=['POST'])
def add_to_cart():
    result = request.form.get('submit')
    result = ast.literal_eval(result)
    title = result['title']
    price = result['extracted_price']
    link = result['link']
    img = result['thumbnail']
    username = session.get('username', '')
    read_query(True, "INSERT INTO cart (username, title, price, link, img) VALUES (?, ?, ?, ?, ?)", username, title, price,
               link, img)
    # Return nothing new
    return '', 204


# @app.route('/remove-from-cart', methods=['POST'])
# def remove_from_cart():
#    read_query(True, "DELETE FROM cart WHERE id = ?", request.form.get('submit'))
#    return '', 204


@app.route('/user-photo-upload', methods=['GET', 'POST'])
def user_photo_upload():
    err = None
    username = session.get('username', '')
    details = read_query(False, "SELECT height, weight, circumference FROM details WHERE username = ?", username)
    if request.method == 'POST':
        if request.form.get("submit") == 'update':
            inches = request.form.get("height_inch")
            feet = request.form.get("height_foot")
            if not inches and not feet:
                inches = details[0] % 12
                feet = details[0] // 12
            elif inches and not feet:
                inches = int(inches)
                feet = 0
            elif feet and not inches:
                feet = int(feet)
                inches = 0
            else:
                inches = int(inches)
                feet = int(feet)
            height = (12 * feet) + inches
            weight = request.form.get("weight")
            if not weight:
                weight = details[1]
            else:
                weight = int(weight)
            circumference = request.form.get("circumference")
            if not circumference:
                circumference = details[2]
            else:
                circumference = int(circumference)
            flash("Information successfully updated.")
            read_query(True, "UPDATE details SET height = ?, weight = ?, circumference = ? WHERE username = ?", height, weight, circumference, username)
        elif not request.files.get('file'):
            err = "No file selected"
        elif request.form.get("submit") == 'submit':
            f = request.files.get('file')
            file_name = f.filename
            if not os.path.isfile(file_name):
                err = "File not in directory"
            else:
                with open(file_name, 'rb') as fp:
                    img = base64.b64encode(fp.read())

                content_type = f.content_type
                flash("Image successfully uploaded.")
                read_query(True, "INSERT INTO images (username, img, type) values (?, ?, ?)", username, img, content_type)
        else:
            flash("Image successfully deleted.")
            read_query(True, "DELETE FROM images WHERE id = ?", request.form.get('submit'))

    images = read_query(True, "SELECT * FROM images WHERE username = ?", username)
    details = read_query(False, "SELECT height, weight, circumference FROM details WHERE username = ?", username)
    return render_template('user_photo_upload.html', err=err, images=images, details=details)


@app.route('/cart', methods=['GET', 'POST'])
def cart():
    if request.method == 'POST':
        read_query(True, "DELETE FROM cart WHERE id = ?", request.form.get('submit'))

    shopping_cart = read_query(True, "SELECT * FROM cart WHERE username = ?", session.get('username', ''))
    return render_template('cart.html', cart=shopping_cart)


@app.route('/login', methods=['GET', 'POST'])
def login():
    session.clear()
    err = None
    if request.method == 'POST':
        username = read_query(False, "SELECT * FROM users WHERE username = ?", request.form.get("username"))
        if request.form.get("username") == '' or username is None:
            err = "Invalid username"
        elif username[2] != request.form.get("password"):
            err = "Invalid password"
        else:
            session['user_id'] = username[0]
            session['username'] = username[1]

            flash("You have successfully logged in.")
            return redirect('/')

    return render_template('login.html', err=err)


@app.route('/register', methods=['GET', 'POST'])
def register():
    err = None
    if request.method == 'POST':
        username = read_query(False, "SELECT * FROM users WHERE username = ?", request.form.get("username"))
        if request.form.get("username") == '':
            err = "Username cannot be empty"
        elif username is not None:
            err = "Username already exists"
        else:
            read_query(True, "INSERT INTO users (username, password) VALUES (?, ?);", request.form.get("username"),
                       request.form.get("password"))
            # Default values are the average American man
            default_height = 69
            default_weight = 200
            default_circumference = 40
            read_query(True, "INSERT INTO details (username, height, weight, circumference) VALUES (?, ?, ?, ?);", request.form.get("username"), default_height, default_weight, default_circumference)

            flash("You have successfully registered for an account.")
            return redirect('/')

    return render_template('register.html', err=err)


@app.route('/logout')
def logout():
    session.clear()
    flash("You have successfully logged out.")
    return redirect('/')


@app.route('/contact')
def contact():
    return render_template('contact.html')


def init_database():
    read_query(True,
               "CREATE TABLE IF NOT EXISTS cart (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT NOT NULL, title TEXT NOT NULL, price DECIMAL NOT NULL, link TEXT NOT NULL, img TXT NOT NULL);")
    read_query(True,
               "CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, username TEXT NOT NULL, password TEXT NOT NULL);")
    read_query(True, "CREATE UNIQUE INDEX IF NOT EXISTS username ON users (username);")
    read_query(True, "CREATE TABLE IF NOT EXISTS images (id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, username TEXT NOT NULL, img BLOB NOT NULL, type TEXT NOT NULL);")
    # Imperial units
    read_query(True, "CREATE TABLE IF NOT EXISTS details (username TEXT NOT NULL, height INTEGER NOT NULL, weight INTEGER NOT NULL, circumference INTEGER NOT NULL);")
    # Treat an empty username as a guest
    read_query(True, "INSERT OR IGNORE INTO users (username, password) VALUES ('', '');")


# All variables that should only have to be set once
def main():
    # Load environment variables
    load_dotenv()
    # Make sure SerpAPI key is set
    if not os.environ.get("serpapi_key"):
        raise RuntimeError("serpapi_key not set")
    # Initialize armoire.db if not already
    if not os.path.isfile(database):
        open(database, 'x').close()
        init_database()
    # Run Flask
    app.run(debug=True)


if __name__ == '__main__':
    main()
