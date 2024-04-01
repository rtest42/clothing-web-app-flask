from flask import Flask, render_template, request, redirect, session, flash
from flask_session import Session
import sqlite3
import requests
import os
from dotenv import load_dotenv

app = Flask(__name__)
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


def read_query(sql_cmd, *args):
    with sqlite3.connect(database) as db:
        cursor = db.cursor()
        cursor.execute(sql_cmd, args)
        query = cursor.fetchall()
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


@app.route('/user-photo-upload')
def user_photo_upload():
    return render_template('user_photo_upload.html')


@app.route('/cart', methods=['GET', 'POST'])
def cart():
    with sqlite3.connect(database) as db:
        cursor = db.cursor()
        sql_cmd = "SELECT * FROM cart WHERE username = ?"
        cursor.execute(sql_cmd, (session['user'][1]))
        shopping_cart = cursor.fetchall()
        db.commit()
    #if request.method == 'GET':
    #    with sqlite3.connect(database) as db:
    #        cursor = db.cursor()
    #        sql_cmd = "SELECT * FROM cart WHERE username = ?"
    #        cursor.execute(sql_cmd, (user,))
    #        shopping_cart = cursor.fetchall()
    #        db.commit()
    #else:
    #    with sqlite3.connect(database) as db:
    #        cursor = db.cursor()
    #        item_id = request.form.get('submit')
    #        sql_cmd = "DELETE FROM cart WHERE id = ?"
    #        cursor.execute(sql_cmd, (item_id,))
    #        sql_cmd = "SELECT * FROM cart"
    #        cursor.execute(sql_cmd)
    #        shopping_cart = cursor.fetchall()
    #        db.commit()

    return render_template('cart.html', cart=shopping_cart)


@app.route('/login', methods=['GET', 'POST'])
def login():
    session.clear()
    err = None
    if request.method == 'POST':
        with sqlite3.connect(database) as db:
            cursor = db.cursor()
            sql_cmd = "SELECT * FROM users WHERE username = ?"
            cursor.execute(sql_cmd, (request.form.get("username"),))
            get_username = cursor.fetchone()
            if get_username is None or get_username[2] != request.form.get("password"):
                err = "Invalid username or password"
            else:
                session['user'] = get_username

                flash("You have successfully logged in.")
                return redirect('/')

    return render_template('login.html', err=err)


@app.route('/register', methods=['GET', 'POST'])
def register():
    err = None
    if request.method == 'POST':
        with sqlite3.connect(database) as db:
            cursor = db.cursor()
            sql_cmd = "SELECT * FROM users WHERE username = ?"
            cursor.execute(sql_cmd, (request.form.get("username"),))
            get_users = cursor.fetchall()
            if len(get_users) != 0:
                err = "Username already exists"
            else:
                sql_cmd = "INSERT INTO users (username, password) VALUES (?, ?);"
                cursor.execute(sql_cmd, (request.form.get("username"), request.form.get("password")))
                db.commit()

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
    with sqlite3.connect(database) as db:
        cursor = db.cursor()
        sql_cmd = ("CREATE TABLE IF NOT EXISTS cart (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT, "
                   "title TEXT, price REAL, link TEXT);")
        cursor.execute(sql_cmd)
        sql_cmd = ("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, username TEXT NOT "
                   "NULL, password TEXT NOT NULL);")
        cursor.execute(sql_cmd)
        sql_cmd = "CREATE UNIQUE INDEX IF NOT EXISTS username ON users (username);"
        cursor.execute(sql_cmd)
        # Guest user
        # sql_cmd = "INSERT OR IGNORE INTO users (username, password) VALUES ('', '');"
        # cursor.execute(sql_cmd)
        db.commit()


# All variables that should only have to be set once
def main():
    load_dotenv()
    # Make sure SerpAPI key is set
    if not os.environ.get("serpapi_key"):
        raise RuntimeError("serpapi_key not set")
    # Initialize armoire.db if not already
    if not os.path.isfile(database):
        open(database, 'x').close()
        init_database()
    app.run(debug=True)


if __name__ == '__main__':
    main()
