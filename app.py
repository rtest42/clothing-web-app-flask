from flask import Flask, render_template, request, redirect, session, flash
from flask_session import Session
import sqlite3
import requests
import os
from ast import literal_eval
import base64
from datetime import date, datetime
from werkzeug.utils import secure_filename
from werkzeug.security import check_password_hash, generate_password_hash
from dotenv import load_dotenv

app = Flask(__name__)
# Filters
app.jinja_env.filters["usd"] = lambda value: f"${value:,.2f}"
app.jinja_env.filters["decode"] = lambda value: value.decode('utf-8')
app.jinja_env.filters["timestamp"] = lambda timestamp: datetime.fromtimestamp(int(timestamp))
# Auto-reload templates
app.config["TEMPLATES_AUTO_RELOAD"] = True
# Use filesystem instead of cookies
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
# Upload files config
UPLOAD_FOLDER = './static/images'
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024
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


# read_query returns the result given from the SQL command.
# get_all: returns multiple or 1 row
# sql_cmd: the SQL command to execute
# args: parameters
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


# The homepage, when the user first runs the program.
@app.route('/')
def index():
    return render_template("index.html")


# Page shows Fit of the Day and a weather forecast. Must be logged in.
@app.route('/customization', methods=['GET', 'POST'])
def customization():
    username = session.get('username', '')
    if not session.get('place_{}'.format(username)):
        session['place_{}'.format(username)] = 'San Jose'

    if request.method == 'POST':
        if request.form.get('submit') == 'reshuffle_head' and session['head_counter_{}'.format(username)] < len(session['head_result_{}'.format(username)]):
            session['head_counter_{}'.format(username)] += 1
        elif request.form.get('submit') == 'reshuffle_chest' and session['chest_counter_{}'.format(username)] < len(session['chest_result_{}'.format(username)]):
            session['chest_counter_{}'.format(username)] += 1
        elif request.form.get('submit') == 'reshuffle_leg' and session['leg_counter_{}'.format(username)] < len(session['leg_result_{}'.format(username)]):
            session['leg_counter_{}'.format(username)] += 1
        elif request.form.get('submit') == 'reshuffle_foot' and session['foot_counter_{}'.format(username)] < len(session['foot_result_{}'.format(username)]):
            session['foot_counter_{}'.format(username)] += 1
        elif request.form.get('submit') == 'submit' and request.form.get('place') != '':
            session['place_{}'.format(username)] = request.form.get('place')

    place = session['place_{}'.format(username)]
    openweather_key = os.getenv('openweather_key')
    # Convert city to lat/lon
    url = "https://api.openweathermap.org/geo/1.0/direct"
    params = {
        'q': place,
        'appid': openweather_key,
        'limit': 1
    }

    response = requests.get(url, params=params)
    response = response.json()
    coordinates = response[0]

    # Get hourly forecast
    url = "https://api.openweathermap.org/data/2.5/forecast"
    params = {
        'lat': coordinates['lat'],
        'lon': coordinates['lon'],
        'appid': openweather_key,
        'units': 'imperial'
    }

    response = requests.get(url, params=params)
    weather_forecast = response.json()['list']
    forecast = weather_forecast

    # Refresh results once per day
    # Search fit of the day
    if not session.get('date') or session['date'] != date.today():
        session['date'] = date.today()
        serpapi_key = os.getenv('serpapi_key')

        # HEAD (hat)
        # TODO: improve and customize the search query.
        search_query = 'hat for {} weather'.format(forecast[0]['weather'][0]['main'])
        url = 'https://serpapi.com/search'
        params = {
            'q': search_query,
            'api_key': serpapi_key,
            'engine': 'google_shopping'
        }

        response = requests.get(url, params=params)
        session['head_result_{}'.format(username)] = response.json()['shopping_results']
        session['head_counter_{}'.format(username)] = 0

        # CHEST (shirt)
        search_query = 'shirt for {} weather'.format(forecast[0]['weather'][0]['main'])
        url = 'https://serpapi.com/search'
        params = {
            'q': search_query,
            'api_key': serpapi_key,
            'engine': 'google_shopping'
        }

        response = requests.get(url, params=params)
        session['chest_result_{}'.format(username)] = response.json()['shopping_results']
        session['chest_counter_{}'.format(username)] = 0

        # LEG (pants)
        search_query = 'pants for {} weather'.format(forecast[0]['weather'][0]['main'])
        url = 'https://serpapi.com/search'
        params = {
            'q': search_query,
            'api_key': serpapi_key,
            'engine': 'google_shopping'
        }

        response = requests.get(url, params=params)
        session['leg_result_{}'.format(username)] = response.json()['shopping_results']
        session['leg_counter_{}'.format(username)] = 0

        # FOOT (shoes)
        search_query = 'shoes for {} weather'.format(forecast[0]['weather'][0]['main'])
        url = 'https://serpapi.com/search'
        params = {
            'q': search_query,
            'api_key': serpapi_key,
            'engine': 'google_shopping'
        }

        response = requests.get(url, params=params)
        session['foot_result_{}'.format(username)] = response.json()['shopping_results']
        session['foot_counter_{}'.format(username)] = 0

    return render_template('customization.html', place=place, forecast=forecast, head=session['head_result_{}'.format(username)][session['head_counter_{}'.format(username)]], chest=session['chest_result_{}'.format(username)][session['chest_counter_{}'.format(username)]], leg=session['leg_result_{}'.format(username)][session['leg_counter_{}'.format(username)]], foot=session['foot_result_{}'.format(username)][session['foot_counter_{}'.format(username)]])


#
@app.route('/shop', methods=['GET', 'POST'])
def shop():
    err = None
    shopping_results = None
    if request.method == 'POST':
        # Get SerpAPI key
        serpapi_key = os.getenv('serpapi_key')
        # Get search query
        search_query = request.form.get('shop').lower().strip()

        # Determines if search is acceptable or not
        is_wearable = False
        for wearable in wearable_keywords:
            if search_query.find(wearable) >= 0:
                is_wearable = True
                break

        # Filter (sort) results
        dropdown = {
            'relevance': 'p_ord:r',
            'review': 'p_ord:rv',
            'low2high': 'p_ord:p',
            'high2low': 'p_ord:pd'
        }

        if not is_wearable:
            # Do not perform search if not clothing-related
            err = "Invalid search!"
        else:
            # Search using SerpAPI
            url = 'https://serpapi.com/search'
            params = {
                'q': search_query,
                'api_key': serpapi_key,
                'engine': 'google_shopping',
                'tbs': dropdown[request.form.get('filter', 'relevance')]
            }

            flash("Query successful.")
            # Get results in JSON
            response = requests.get(url, params=params)
            shopping_results = response.json()['shopping_results']

    return render_template('shop.html', err=err, results=shopping_results)


# Adds selected item to shopping cart. Does not require login.
@app.route('/add-to-cart', methods=['POST'])
def add_to_cart():
    result = literal_eval(request.form.get('submit'))
    # Get information about selected item
    title = result['title']
    price = result['extracted_price']
    link = result['link']
    img = result['thumbnail']
    username = session.get('username', '')
    # Adds item to cart
    read_query(True, "INSERT INTO cart (username, title, price, link, img) VALUES (?, ?, ?, ?, ?)", username, title,
               price,
               link, img)
    # Return nothing new, no page
    return '', 204


# @app.route('/remove-from-cart', methods=['POST'])
# def remove_from_cart():
#    read_query(True, "DELETE FROM cart WHERE id = ?", request.form.get('submit'))
#    return '', 204


# A page where users can change user information and upload or delete clothing.
# Must be logged in.
@app.route('/user-photo-upload', methods=['GET', 'POST'])
def user_photo_upload():
    err = None
    username = session.get('username', '')
    # Get details about user
    details = read_query(False,
                         "SELECT height, weight, circumference, max_uploads, uploads FROM details WHERE username = ?",
                         username)
    if request.method == 'POST':
        if request.form.get("submit") == 'update':
            # Get weight, height, waist circumference
            inches = request.form.get("height_inch")
            feet = request.form.get("height_foot")
            if not inches and not feet:
                inches = details[0] % 12
                feet = details[0] // 12
            # Get height
            inches = 0 if not inches else int(inches)
            feet = 0 if not feet else int(feet)
            height = (12 * feet) + inches
            # Get weight
            weight = request.form.get("weight")
            weight = details[1] if not weight else int(weight)
            # Get circumference
            circumference = request.form.get("circumference")
            circumference = details[2] if not circumference else int(circumference)

            flash("Information successfully updated.")
            # Update details
            read_query(True, "UPDATE details SET height = ?, weight = ?, circumference = ? WHERE username = ?", height,
                       weight, circumference, username)
        elif request.form.get("submit") == 'submit':
            parts = read_query(False, "SELECT COUNT(*) FROM images WHERE username = ? AND part = ?",
                               username, request.form.get('part'))[0]
            upload_file = request.files.get('file')
            if upload_file.filename == '':
                err = "No image selected"
            elif upload_file and parts < details[3] / 4:
                # Save uploaded file to static directory
                filename = secure_filename(upload_file.filename)
                os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
                upload_file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

                # Read image
                with open(os.path.join(app.config['UPLOAD_FOLDER'], filename), 'rb') as fp:
                    img = base64.b64encode(fp.read())

                content_type = upload_file.content_type
                flash("Image successfully uploaded.")

                # Increment upload counter
                read_query(True, "UPDATE details SET uploads = ? WHERE username = ?", details[4] + 1, username)
                # Insert image
                read_query(True, "INSERT INTO images (username, img, type, part) values (?, ?, ?, ?)", username, img,
                           content_type, request.form.get('part'))
            else:
                err = "Maximum number of files uploaded already for the {}.".format(request.form.get('part'))
        else:
            flash("Image successfully deleted.")
            # Decrement upload counter
            read_query(True, "UPDATE details SET uploads = ? WHERE username = ?", details[4] - 1, username)
            # Delete image
            read_query(True, "DELETE FROM images WHERE id = ?", request.form.get('submit'))

    # Select all images from user
    part_list = ['head', 'chest', 'leg', 'foot']
    images = sorted(read_query(True, "SELECT * FROM images WHERE username = ?", username), key=lambda part: part_list.index(part[4]))
    # Get other details from user
    details = read_query(False,
                         "SELECT height, weight, circumference, max_uploads, uploads FROM details WHERE username = ?",
                         username)
    return render_template('user_photo_upload.html', err=err, images=images, details=details)


# Shows the shopping cart where the user can view or delete items from their cart.
@app.route('/cart', methods=['GET', 'POST'])
def cart():
    if request.method == 'POST':
        # Delete item from cart
        read_query(True, "DELETE FROM cart WHERE id = ?", request.form.get('submit'))

    # Get list of items
    shopping_cart = read_query(True, "SELECT * FROM cart WHERE username = ?", session.get('username', ''))
    return render_template('cart.html', cart=shopping_cart)


# Logs in the user. Only appears when not logged in.
@app.route('/login', methods=['GET', 'POST'])
def login():
    # session.clear()
    session['user_id'] = None
    session['username'] = None
    err = None
    if request.method == 'POST':
        # Looks up username and password
        user = read_query(False, "SELECT * FROM users WHERE username = ?", request.form.get("username"))
        if request.form.get("username") == '' or user is None:
            err = "Invalid username"
        elif not check_password_hash(user[2], request.form.get("password")):
            err = "Invalid password"
        else:
            # Stores session
            session['user_id'] = user[0]
            session['username'] = user[1]

            flash("You have successfully logged in.")
            return redirect('/')

    return render_template('login.html', err=err)


# Makes a new user. Only appears when not logged in.
@app.route('/register', methods=['GET', 'POST'])
def register():
    err = None
    if request.method == 'POST':
        # Looks up username
        username = read_query(False, "SELECT * FROM users WHERE username = ?", request.form.get("username"))
        if request.form.get("username") == '':
            err = "Username cannot be empty"
        elif username is not None:
            err = "Username already exists"
        else:
            read_query(True, "INSERT INTO users (username, password) VALUES (?, ?);", request.form.get("username"),
                       generate_password_hash(request.form.get("password"), method='pbkdf2:sha256', salt_length=8))
            # Default values are the average American man
            default_height = 69
            default_weight = 200
            default_circumference = 40
            # Default maximum uploads (no plan)
            default_max_uploads = 12
            # Make a new user
            read_query(True,
                       "INSERT INTO details (username, height, weight, circumference, max_uploads) VALUES (?, ?, ?, ?, ?);",
                       request.form.get("username"), default_height, default_weight, default_circumference,
                       default_max_uploads)

            flash("You have successfully registered for an account.")
            return redirect('/')

    return render_template('register.html', err=err)


# Logs out the user. Page only appears when logged in.
@app.route('/logout')
def logout():
    # Logs out user
    # session.clear()
    session['user_id'] = None
    session['username'] = None

    flash("You have successfully logged out.")
    return redirect('/')


# Brings up contact information.
@app.route('/contact')
def contact():
    return render_template('contact.html')


# Initializes SQLite database file
def init_database():
    read_query(True,
               "CREATE TABLE IF NOT EXISTS cart (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT NOT NULL, title TEXT NOT NULL, price DECIMAL NOT NULL, link TEXT NOT NULL, img TXT NOT NULL);")
    read_query(True,
               "CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, username TEXT NOT NULL, password TEXT NOT NULL);")
    read_query(True, "CREATE UNIQUE INDEX IF NOT EXISTS username ON users (username);")
    read_query(True,
               "CREATE TABLE IF NOT EXISTS images (id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, username TEXT NOT NULL, img BLOB NOT NULL, type TEXT NOT NULL, part TEXT);")
    # Store user information with imperial units
    read_query(True,
               "CREATE TABLE IF NOT EXISTS details (username TEXT NOT NULL, height INTEGER NOT NULL, weight INTEGER NOT NULL, circumference INTEGER NOT NULL, max_uploads INTEGER NOT NULL, uploads INTEGER NOT NULL DEFAULT 0);")
    # Treat an empty username as a guest
    read_query(True, "INSERT OR IGNORE INTO users (username, password) VALUES ('', '');")


# All variables that should only have to be set once
def main():
    # Load environment variables
    load_dotenv()
    # Make sure API keys are set
    if not os.environ.get("serpapi_key"):
        raise RuntimeError("serpapi_key not set")
    if not os.environ.get("openweather_key"):
        raise RuntimeError("openweather_key not set")
    # Initialize armoire.db if not already
    if not os.path.isfile(database):
        open(database, 'x').close()
        init_database()
    # Run Flask
    app.run(debug=True)


# The main program
if __name__ == '__main__':
    main()
