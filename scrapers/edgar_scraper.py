# scrapers/edgar_scraper.py

import requests
import pandas as pd
import time


import logging

logging.basicConfig(filename='logs/edgar_errors.log', level=logging.WARNING)

HEADERS_DATA = {
    'User-Agent': 'UC Davis Research vedant17tiwari@gmail.com',
    'Accept-Encoding': 'gzip, deflate',
}

def find_s1_in_filings(filings_data):
    forms = filings_data.get('form', [])
    accessions = filings_data.get('accessionNumber', [])
    dates = filings_data.get('filingDate', [])
    for i, form in enumerate(forms):
        if form in ('S-1', 'F-1'):
            return accessions[i], dates[i]
    return None, None

def get_s1_accession(cik):
    url = f'https://data.sec.gov/submissions/CIK{cik}.json'
    try:
        r = requests.get(url, headers=HEADERS_DATA)
        if r.status_code != 200:
            return None, None
        data = r.json()

       
        acc, date = find_s1_in_filings(data['filings']['recent'])
        if acc:
            return acc, date

        
        for f in data['filings'].get('files', []):
            file_url = f'https://data.sec.gov/submissions/{f["name"]}'
            r2 = requests.get(file_url, headers=HEADERS_DATA)
            if r2.status_code == 200:
                older = r2.json()
                acc, date = find_s1_in_filings(older)
                if acc:
                    return acc, date
            time.sleep(0.1)

        return None, None
    except Exception as e:
        logging.warning(f'CIK {cik}: {e}')
        return None, None

#loading the CIK map
df = pd.read_csv('data/cleaned/ticker_cik_map.csv')
df = df[df['cik'].notna()]
print(f'Finding S-1 accessions for {len(df)} tickers...')

accessions = []
for i, row in df.iterrows():
    cik_clean = str(int(float(row['cik']))).zfill(10)
    acc, date = get_s1_accession(cik_clean)
    accessions.append({
        'ticker': row['ticker'],
        'cik': row['cik'],
        'accession_number': acc,
        'filing_date': date
    })

    if len(accessions) % 50 == 0:
        print(f'Progress: {len(accessions)}/{len(df)} -- found so far: {sum(1 for a in accessions if a["accession_number"])}')

    time.sleep(0.15)

result = pd.DataFrame(accessions)
found = result['accession_number'].notna().sum()
print(f'\nS-1 found: {found}')
print(f'S-1 missing: {result["accession_number"].isna().sum()}')

result.to_csv('data/cleaned/s1_accessions.csv', index=False)
print('Saved to data/cleaned/s1_accessions.csv')
