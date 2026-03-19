# scrapers/fetch_s1_html.py

import requests
import pandas as pd
import os
import time
import logging
from bs4 import BeautifulSoup, XMLParsedAsHTMLWarning
import warnings
warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)

logging.basicConfig(filename='logs/fetch_errors.log', level=logging.WARNING)

HEADERS = {
    'User-Agent': 'UC Davis Research vedant17tiwari@gmail.com',
    'Accept-Encoding': 'gzip, deflate',
}

HEADERS_WWW = {**HEADERS, 'Host': 'www.sec.gov'}

def fetch_s1_html(ticker, cik, accession):
    cache_path  = f'data/raw/edgar/{ticker}.html'

    if os.path.exists(cache_path):
        return True

    try:
        cik_int = int(float(cik))
        acc_nodash = accession.replace('-', '')

        index_url  = f'https://www.sec.gov/Archives/edgar/data/{cik_int}/{acc_nodash}/{accession}-index.htm'
        idx_r  = requests.get(index_url, headers=HEADERS_WWW)

        if idx_r.status_code != 200:
            logging.warning(f'{ticker}: index page {idx_r.status_code}')
            return False

        soup = BeautifulSoup(idx_r.text, 'lxml')
        doc_url = None

        for link in soup.find_all('a', href=True):
            href = link['href']
            
            if not href.startswith('/Archives/'):
                continue
            #skipoing exhibits
            if any(x in href.lower() for x in ['exhibit', 'ex-', 'ex1', 'ex2', 'ex3', 'ex4', 'ex9']):
                continue
            if href.endswith('.htm'):
                doc_url = 'https://www.sec.gov' + href
                break

        if not doc_url:
            logging.warning(f'{ticker}: no document URL found in index')
            return False

        doc_r = requests.get(doc_url, headers=HEADERS_WWW)
        if doc_r.status_code != 200:
            logging.warning(f'{ticker}: doc page {doc_r.status_code}')
            return False

        with open(cache_path, 'w', encoding='utf-8', errors='ignore') as f:
            f.write(doc_r.text)

        return True

    except Exception as e:
        logging.warning(f'{ticker}: {e}')
        return False

#load the accessions
df =  pd.read_csv('data/cleaned/s1_accessions.csv')
df= df[df['accession_number'].notna()]
print(f'Fetching S-1 HTML for {len(df)} companies...')
print('This will take 1-2 hours. Let it run overnight.')

success  = 0
failed = 0

for i, row in df.iterrows():
    result = fetch_s1_html(row['ticker'], row['cik'], row['accession_number'])
    if result:
        success += 1
    else:
        failed += 1

    if (success + failed) % 50 == 0:
        print(f'Progress: {success + failed}/{len(df)} -- success: {success} failed: {failed}')

    time.sleep(0.2)

print(f'\nDone. Success: {success} Failed: {failed}')
print(f'HTML files cached in data/raw/edgar/')
