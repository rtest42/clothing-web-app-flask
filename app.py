from flask import Flask, render_template, request, redirect
import sys
import requests
import os
from operator import itemgetter
from decimal import Decimal
from dotenv import load_dotenv

app = Flask(__name__)

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
        SERPAPI_KEY = os.getenv('SERPAPI_KEY')

        search_query = request.form.get('search')
        wearable_keywords = []
        with open('wearable_keywords.txt', 'r') as file:
            for keyword in file:
                wearable_keywords.append(keyword.replace('\n', ''))

        # Do not perform search if not clothing-related
        is_wearable = False
        search_query = search_query.lower().strip()
        for wearable in wearable_keywords:
            if search_query.find(wearable) >= 0:
                is_wearable = True
                break

        if not is_wearable:
            return render_template('search_fail.html')

        # Search using SerpAPI
        url = 'https://serpapi.com/search'
        params = {
            'q': search_query,
            'api_key': SERPAPI_KEY,
            'engine': 'google_shopping'
        }

        # Get results in JSON
        response = requests.get(url, params=params)
        results = response.json()

        # Sort
        shopping_results = results['shopping_results']
        shopping_results = sorted(shopping_results, key=lambda k: Decimal(k['price'].strip('$')))

        return render_template('search_passed.html', results=shopping_results)
    else:
        return render_template('search.html')

@app.route('/shopping-cart')
def shopping_cart():
    return render_template('shopping_cart.html')

@app.route('/user-photo-upload')
def user_photo_upload():
    return render_template('user_photo_upload.html')

if __name__ == '__main__':
    load_dotenv()
    app.run(debug=True)
    
