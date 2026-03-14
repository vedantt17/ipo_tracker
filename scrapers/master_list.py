import requests
import pandas as pd
import time
from io import StringIO

# scrapers/master_list.py
# Written by V

import requests
import pandas as pd
import time
from io import StringIO

headers = {
    'User-Agent': 'Mozilla/5.0 (academic research project, UC Davis MSBA)'
}

all_ipos = []

for year in range(2019, 2026):
    url = f'https://stockanalysis.com/ipos/{year}/'
    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        print(f'Failed: {year} -- status {response.status_code}')
        continue

    tables = pd.read_html(StringIO(response.text))

    if not tables:
        print(f'No table found: {year}')
        continue

    df = tables[0]
    
    # filter to only rows actually from this year
    df['IPO Date'] = pd.to_datetime(df['IPO Date'], errors='coerce')
    df = df[df['IPO Date'].dt.year == year]
    
    df['year'] = year
    all_ipos.append(df)
    print(f'OK: {year} -- {len(df)} rows')
    time.sleep(2)

combined = pd.concat(all_ipos, ignore_index=True)
print(f'\nTotal rows: {len(combined)}')
print(f'Columns: {list(combined.columns)}')

combined.to_csv('data/raw/ipo_master_raw.csv', index=False)
print('Saved to data/raw/ipo_master_raw.csv')