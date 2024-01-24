import requests
import os
from dotenv import load_dotenv

load_dotenv()

# API KEY AND SEARCH ENGINE ID are free to obtain
API_KEY = os.getenv('API_KEY')
SEARCH_ENGINE_ID = os.getenv('SEARCH_ENGINE_ID')

search_query = input('Search for: ')

url = 'https://www.googleapis.com/customsearch/v1'
params = {
    'q': search_query,
    'key': API_KEY,
    'cx': SEARCH_ENGINE_ID
}

response = requests.get(url, params=params)
results = response.json()['items']

for result in results:
    print(result['link'])
