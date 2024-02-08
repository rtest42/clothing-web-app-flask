import sys
import requests
import os
from dotenv import load_dotenv

load_dotenv()

# SerpAPI key obtained by signing up
# Default plan: 100 uses per month
SERPAPI_KEY = os.getenv('SERPAPI_KEY')

search_query = input('Search for: ')

wearable_keywords = []
with open('wearable_keywords.txt', 'r') as file:
    for keyword in file:
        wearable_keywords.append(keyword.replace('\n', ''))

# Do not perform search if not clothing-related
is_wearable = False
for wearable in wearable_keywords:
    if wearable.find(search_query) != -1:
        is_wearable = True

if not is_wearable:
    print('Not a valid search term!')
    sys.exit(1)

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

for result in results['shopping_results']:
    print(result['title'] + ' - ' + result['price'] + '\n' + result['link'] + '\n')
