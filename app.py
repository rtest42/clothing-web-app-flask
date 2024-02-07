import sys
import requests
import os
from dotenv import load_dotenv

load_dotenv()

# SerpAPI key obtained by signing up
# Default plan: 100 uses per month
SERPAPI_KEY = os.getenv('SERPAPI_KEY')

search_query = input('Search for: ')

wearable_keywords = [
    'shirt',
    't-shirt',
    'top',
    'blouse',
    'dress',
    'skirt',
    'pant',
    'slack',
    'jeans',
    'short',
    'jacket',
    'blazer',
    'parka',
    'coat',
    'sweater',
    'pullover',
    'cardigan',
    'hoodie',
    'sweatshirt',
    'camisole',
    'tankini',
    'bikini',
    'swimsuit',
    'guard',
    'wetsuit',
    'cover-up',
    'sarong',
    'kaftan',
    'kimono',
    'robe',
    'pajama',
    'pj',
    'gown',
    'legging',
    'tight',
    'stocking',
    'pantyhose',
    'sock',
    'socks',
    'underwear',
    'boxer',
    'brief',
    'trunk',
    'thong',
    'bra',
    'bralette',
    'panties',
    'shapewear',
    'bodysuit',
    'corset',
    'camisole',
    'slip',
    'belt',
    'lingerie',
    'set',
    'warmer',
    'glove',
    'mitten',
    'scarf',
    'shawl',
    'wrap',
    'pashmina',
    'snood',
    'bandana',
    'hat',
    'beanie',
    'beret',
    'cap',
    'fedora',
    'visor',
    'headband',
    'hair clip',
    'hair tie',
    'turban',
    'fascinator',
    'tiara',
    'earmuffs',
    'sunglass',
    'eyeglass',
    'glasses',
    'contact lenses',
    'safety goggle',
    'swimming goggle',
    'ski goggle',
    'goggle',
    'tie',
    'cravat',
    'ascot',
    'cufflink',
    'pin',
    'brooch',
    'boutonniere',
    'suspender',
    'belt',
    'sash',
    'garter',
    'bracelet',
    'ring',
    'chain',
    'necklace',
    'pendant',
    'choker',
    'cameo',
    'earring',
    'bangle',
    'anklet',
    'shoe',
    'jewelry',
    'clothing',
    'clothes',
    'wearable'
    ]

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
