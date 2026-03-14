import requests
import pandas as pd
import time

WIKIDATA_URL = 'https://query.wikidata.org/sparql'
WIKIDATA_SEARCH = 'https://www.wikidata.org/w/api.php'

HEADERS = {
    'User-Agent': 'UC Davis MSBA Research IPO Project',
    'Accept': 'application/json'
}

def get_founding_year(company_name):
    # clean name
    name = company_name
    for word in [', Inc.', ', Inc', ' Inc.', ' Inc', ', Corp.', ', Corp', 
                 ' Corp.', ' Corp', ', Ltd.', ', Ltd', ' Ltd.', ' Ltd',
                 ', LLC', ' LLC', '.com']:
        name = name.replace(word, '')
    name = name.strip()

    try:
        # step 1: search for the entity
        search_params = {
            'action': 'wbsearchentities',
            'search': name,
            'language': 'en',
            'format': 'json',
            'limit': 3,
            'type': 'item'
        }
        r = requests.get(WIKIDATA_SEARCH, params=search_params, headers=HEADERS)
        if r.status_code != 200:
            return None
        
        results = r.json().get('search', [])
        if not results:
            return None

        # step 2: get founding year from first result
        entity_id = results[0]['id']
        entity_url = f'https://www.wikidata.org/wiki/Special:EntityData/{entity_id}.json'
        r2 = requests.get(entity_url, headers=HEADERS)
        if r2.status_code != 200:
            return None

        data = r2.json()
        claims = data['entities'][entity_id].get('claims', {})
        
        # P571 is inception/founding date
        if 'P571' in claims:
            inception = claims['P571'][0]['mainsnak']['datavalue']['value']['time']
            return int(inception[1:5])
        
        return None

    except:
        return None

# load master list
df = pd.read_csv('data/cleaned/ipo_master_validated.csv')
print(f'Fetching founding years for {len(df)} companies...')

founding_years = []
found = 0

for i, row in df.iterrows():
    year = get_founding_year(row['company_name'])
    founding_years.append({'ticker': row['ticker'], 'founding_year_wiki': year})
    
    if year:
        found += 1

    if (i + 1) % 50 == 0:
        print(f'Progress: {i+1}/{len(df)} -- found: {found}')
    
    time.sleep(0.3)

result = pd.DataFrame(founding_years)
print(f'\nFounding year found: {found} out of {len(df)}')
print(f'Coverage: {found/len(df):.1%}')

result.to_csv('data/cleaned/wikidata_founding.csv', index=False)
print('Saved to data/cleaned/wikidata_founding.csv')