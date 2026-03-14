# scrapers/vc_history_from_s1.py
# Written by V

import pandas as pd
import re
import os
import logging
from bs4 import BeautifulSoup, XMLParsedAsHTMLWarning
import warnings
warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)

logging.basicConfig(filename='logs/vc_errors.log', level=logging.WARNING)

def parse_founding_year(text):
    patterns = [
        r'incorporated\s+in\s+(?:the\s+)?(?:State\s+of\s+)?(?:Delaware|California|Nevada|New York|Florida|Texas|Washington|Maryland|Massachusetts|Colorado|Georgia|Illinois|Virginia|Minnesota|Oregon|Pennsylvania|Ohio|Utah|Connecticut|New Jersey|North Carolina|Wyoming|Arizona|Montana|Louisiana)\s+in\s+(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{4})',
        r'incorporated\s+in\s+(?:the\s+)?(?:State\s+of\s+)?(?:Delaware|California|Nevada|New York|Florida|Texas|Washington|Maryland|Massachusetts|Colorado|Georgia|Illinois|Virginia|Minnesota|Oregon|Pennsylvania|Ohio|Utah|Connecticut|New Jersey|North Carolina|Wyoming|Arizona|Montana|Louisiana)\s+in\s+(\d{4})',
        r'incorporated\s+under\s+the\s+laws\s+of\s+the\s+State\s+of\s+\w+\s+in\s+(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{4})',
        r'incorporated\s+under\s+the\s+laws\s+of\s+the\s+State\s+of\s+\w+\s+in\s+(\d{4})',
        r'incorporated\s+in\s+(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{4})',
        r'incorporated\s+in\s+(\d{4})',
        r'founded\s+in\s+(\d{4})',
        r'organized\s+in\s+(\d{4})',
        r'formed\s+in\s+(\d{4})',
        r'established\s+in\s+(\d{4})',
    ]
    for pattern in patterns:
        m = re.search(pattern, text, re.IGNORECASE)
        if m:
            year = int(m.group(1))
            if 1990 <= year <= 2025:
                return year
    return None

def parse_funding_rounds(text):
    pattern = r'Series\s+([A-F])\s+[Pp]referred'
    matches = re.findall(pattern, text)
    if not matches:
        return 0, None
    rounds = len(set(matches))
    last_round = f'Series {sorted(set(matches))[-1]}'
    return rounds, last_round

def parse_total_funding(text):
    patterns = [
        r'aggregate\s+of\s+\$([\d,\.]+)\s*(million|billion)',
        r'total\s+of\s+\$([\d,\.]+)\s*(million|billion)',
        r'raised\s+\$([\d,\.]+)\s*(million|billion)',
        r'received\s+\$([\d,\.]+)\s*(million|billion)\s+in\s+(?:aggregate\s+)?(?:gross\s+)?proceeds',
    ]
    for pattern in patterns:
        m = re.search(pattern, text, re.IGNORECASE)
        if m:
            val = float(m.group(1).replace(',', ''))
            multiplier = 1e6 if m.group(2).lower() == 'million' else 1e9
            return val * multiplier
    return None

# load accessions to get list of tickers
df = pd.read_csv('data/cleaned/s1_accessions.csv')
df = df[df['accession_number'].notna()]
print(f'Extracting VC history from {len(df)} S-1 filings...')

results = []

for i, row in df.iterrows():
    ticker = row['ticker']
    cache_path = f'data/raw/edgar/{ticker}.html'

    if not os.path.exists(cache_path):
        continue

    try:
        with open(cache_path, 'r', encoding='utf-8', errors='ignore') as f:
            html = f.read()

        soup = BeautifulSoup(html, 'lxml')
        text = soup.get_text(' ')

        founding_year = parse_founding_year(text)
        num_rounds, last_round = parse_funding_rounds(text)
        total_funding = parse_total_funding(text)

        results.append({
            'ticker': ticker,
            'founding_year': founding_year,
            'num_rounds': num_rounds if num_rounds > 0 else None,
            'last_round_type': last_round,
            'total_funding_usd': total_funding,
            'has_crunchbase': 0,
            'source': 'edgar_s1'
        })

    except Exception as e:
        logging.warning(f'{ticker}: {e}')

    if len(results) % 100 == 0:
        print(f'Progress: {len(results)}/{len(df)}')

result_df = pd.DataFrame(results)
print(f'\nParsed: {len(result_df)} companies')
print(f'founding_year coverage: {result_df["founding_year"].notna().mean():.1%}')
print(f'num_rounds coverage: {result_df["num_rounds"].notna().mean():.1%}')
print(f'total_funding coverage: {result_df["total_funding_usd"].notna().mean():.1%}')

result_df.to_csv('data/cleaned/vc_history.csv', index=False)
print('Saved to data/cleaned/vc_history.csv')