from flask import Flask, render_template, request, redirect
import sys
import sqlite3
import requests
import os
import ast
import json
from dotenv import load_dotenv

app = Flask(__name__)
database = "armoire.db"
results = None

@app.route('/index')
@app.route('/')
def index():
    return render_template('index.html')


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
        results = response.json()

        shopping_results = results['shopping_results']
        return render_template('search_passed.html', results=shopping_results)
    else:
        return render_template('search.html')


@app.route('/user-photo-upload')
def user_photo_upload():
    return render_template('user_photo_upload.html')


@app.route('/shop/', methods=['GET', 'POST'])
def shop():
    if request.method == 'GET':
        return render_template('shop.html')
    else:
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
                return redirect('shop.html')

            filter = {
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
                'tbs': filter[request.form.get('filter')]
            }

            # Get results in JSON
            response = requests.get(url, params=params)
            global results
            results = response.json()['shopping_results']
        else:
            with sqlite3.connect(database) as db:
                cursor = db.cursor()
                result = request.form.get('submit')
                result = ast.literal_eval(result)
                title = result['title']
                price = result['extracted_price']
                link = result['link']
                sql_cmd = "INSERT INTO armoire (title, price, link) VALUES (?, ?, ?)"
                cursor.execute(sql_cmd, (title, price, link))
                db.commit()

        return render_template('shop.html', results=results)


@app.route('/cart', methods=['GET', 'POST'])
def cart():
    if request.method == 'GET':
        with sqlite3.connect(database) as db:
            cursor = db.cursor()
            sql_cmd = "SELECT * FROM armoire"
            cursor.execute(sql_cmd)
            shopping_cart = cursor.fetchall()
            db.commit()

        return render_template('cart.html', cart=shopping_cart)
    else:
        with sqlite3.connect(database) as db:
            cursor = db.cursor()
            id = request.form.get('submit')
            sql_cmd = "DELETE FROM armoire WHERE id = ?"
            cursor.execute(sql_cmd, (id,))
            db.commit()
            sql_cmd = "SELECT * FROM armoire"
            cursor.execute(sql_cmd)
            shopping_cart = cursor.fetchall()
            db.commit()

        return render_template('cart.html', cart=shopping_cart)


@app.route('/contact')
def contact():
    return render_template('contact.html')

def init_database():
    with sqlite3.connect(database) as db:
        cursor = db.cursor()
        sql_cmd = "CREATE TABLE IF NOT EXISTS armoire (id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT, price REAL, link TEXT);"
        cursor.execute(sql_cmd)
        db.commit()

# All variables that should only have to be set once
def main():
    load_dotenv()
    init_database()
    app.run(debug=True)


if __name__ == '__main__':
    main()