from flask import Flask, render_template, request, redirect
import sqlite3
import requests
import os
import ast
from dotenv import load_dotenv

app = Flask(__name__)
database = "armoire.db"
results = None
user = ""


@app.route('/')
def index():
    return render_template('index.html', user=user)


@app.route('/search_fail')
def search_fail():
    return render_template('search_fail.html')


@app.route('/search', methods=['GET', 'POST'])
def search():
    if request.method == 'POST':
        # SerpAPI key obtained by signing up
        # Default plan: 100 uses per month
        serpapi_key = os.getenv('serpapi_key')

        search_query = request.form.get('search').lower().strip()
        wearable_keywords = []
        with open('wearable_keywords.txt', 'r') as file:
            for keyword in file:
                wearable_keywords.append(keyword.replace('\n', ''))

        # Determines if search is acceptable or not
        is_wearable = False
        for wearable in wearable_keywords:
            if search_query.find(wearable) >= 0:
                is_wearable = True
                break

        # Do not perform search if not clothing-related
        if not is_wearable:
            return render_template('search_fail.html')

        # Search using SerpAPI
        url = 'https://serpapi.com/search'
        params = {
            'q': search_query,
            'api_key': serpapi_key,
            'engine': 'google_shopping',
            'tbs': 'p_ord:pd'
        }

        # Get results in JSON
        response = requests.get(url, params=params)
        shopping_results = response.json()['shopping_results']
        return render_template('search_passed.html', results=shopping_results, user=user)
    else:
        return render_template('search.html')


@app.route('/user-photo-upload')
def user_photo_upload():
    return render_template('user_photo_upload.html')


@app.route('/shop/', methods=['GET', 'POST'])
def shop():
    if request.method == 'GET':
        return render_template('shop.html', shopping_err=False, user=user)
    else:
        global results
        if request.form.get('submit') == 'Submit':
            # SerpAPI key obtained by signing up
            # Default plan: 100 uses per month
            serpapi_key = os.getenv('serpapi_key')

            search_query = request.form.get('shop').lower().strip()
            wearable_keywords = []
            with open('wearable_keywords.txt', 'r') as file:
                for keyword in file:
                    wearable_keywords.append(keyword.replace('\n', ''))

            # Determines if search is acceptable or not
            is_wearable = False
            for wearable in wearable_keywords:
                if search_query.find(wearable) >= 0:
                    is_wearable = True
                    break

            # Do not perform search if not clothing-related
            if not is_wearable:
                return render_template('shop.html', shopping_err=True, user=user)

            dropdown = {
                'relevance': 'p_ord:r',
                'review': 'p_ord:rv',
                'low2high': 'p_ord:p',
                'high2low': 'p_ord:pd'
            }

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
            results = response.json()['shopping_results']
        else:
            with sqlite3.connect(database) as db:
                cursor = db.cursor()
                result = request.form.get('submit')
                result = ast.literal_eval(result)
                title = result['title']
                price = result['extracted_price']
                link = result['link']
                sql_cmd = "INSERT INTO cart (username, title, price, link) VALUES (?, ?, ?, ?);"
                cursor.execute(sql_cmd, (user, title, price, link))
                db.commit()

        return render_template('shop.html', shopping_err=False, results=results, user=user)


@app.route('/cart', methods=['GET', 'POST'])
def cart():
    if request.method == 'GET':
        with sqlite3.connect(database) as db:
            cursor = db.cursor()
            sql_cmd = "SELECT * FROM cart WHERE username = ?"
            cursor.execute(sql_cmd, (user,))
            shopping_cart = cursor.fetchall()
            db.commit()

        return render_template('cart.html', cart=shopping_cart, user=user)
    else:
        with sqlite3.connect(database) as db:
            cursor = db.cursor()
            item_id = request.form.get('submit')
            sql_cmd = "DELETE FROM cart WHERE id = ?"
            cursor.execute(sql_cmd, (item_id,))
            sql_cmd = "SELECT * FROM cart"
            cursor.execute(sql_cmd)
            shopping_cart = cursor.fetchall()
            db.commit()

        return render_template('cart.html', cart=shopping_cart, user=user)


@app.route('/login', methods=['GET', 'POST'])
def login():
    global user
    if request.method == 'GET':
        return render_template('login.html', err_login=False, user=user)
    else:
        with sqlite3.connect(database) as db:
            cursor = db.cursor()
            sql_cmd = "SELECT * FROM users WHERE username = ?"
            cursor.execute(sql_cmd, (request.form.get("username"),))
            get_user = cursor.fetchall()
            db.commit()
            if request.form.get("username") == '' or len(get_user) != 1 or get_user[0][2] != request.form.get("password"):
                return render_template('login.html', err_login=True, user=user)

            user = request.form.get("username")
            return render_template('index.html', user=user)


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'GET':
        return render_template('register.html', err_register=False, user=user)
    else:
        with sqlite3.connect(database) as db:
            cursor = db.cursor()
            sql_cmd = "SELECT * FROM users WHERE username = ?"
            cursor.execute(sql_cmd, (request.form.get("username"),))
            get_user = cursor.fetchall()
            if len(get_user) != 0:
                return render_template('register.html', err_register=True, user=user)

            sql_cmd = "INSERT INTO users (username, password) VALUES (?, ?);"
            cursor.execute(sql_cmd, (request.form.get("username"), request.form.get("password")))
            db.commit()
            return render_template('index.html', user=user)


@app.route('/logout')
def logout():
    global user
    user = ""
    return render_template('index.html', user=user)


@app.route('/contact')
def contact():
    return render_template('contact.html', user=user)


def init_database():
    if not os.path.isfile(database):
        open(database, 'x').close()

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
        sql_cmd = "INSERT OR IGNORE INTO users (username, password) VALUES ('', '');"
        cursor.execute(sql_cmd)
        db.commit()


# All variables that should only have to be set once
def main():
    load_dotenv()
    init_database()
    app.run(debug=True)


if __name__ == '__main__':
    main()
