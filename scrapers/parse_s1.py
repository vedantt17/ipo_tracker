# scrapers/parse_s1.py

import pandas as pd
import re

import os
import logging

from bs4 import BeautifulSoup

logging.basicConfig(filename='logs/parse_errors.log', level=logging.WARNING)

def parse_offer_price(text):
    patterns = [
        r'price\s+of\s+\$(\d+\.?\d*)\s+per\s+share',
        r'initial\s+public\s+offering\s+price\s+of\s+\$(\d+\.?\d*)',
        r'offering\s+price\s+per\s+share.*?\$(\d+\.?\d*)',
        r'public\s+offering\s+price.*?\$(\d+\.?\d*)',
    ]
    for pattern in patterns:
        m = re.search(pattern, text, re.IGNORECASE)
        if m:
            return float(m.group(1))
    return None

def parse_shares_offered(text):
    patterns = [
        r'offering\s+of\s+([\d,]+)\s+shares',
        r'([\d,]+)\s+shares\s+of\s+common\s+stock\s+in\s+this\s+offering',
        r'are\s+offering\s+([\d,]+)\s+shares',
    ]
    for pattern in patterns:
        m = re.search(pattern, text, re.IGNORECASE)
        if m:
            return int(m.group(1).replace(',', ''))
    return None

def parse_underwriters(text):
    known = [
        'Goldman Sachs', 'Morgan Stanley', 'J.P. Morgan', 'Citigroup',
        'Bank of America', 'Barclays', 'Credit Suisse', 'Deutsche Bank',
        'UBS', 'Jefferies', 'Cowen', 'Piper Sandler', 'RBC Capital',
        'Wells Fargo', 'Needham', 'William Blair', 'Cantor Fitzgerald',
        'BofA Securities', 'Evercore', 'Lazard', 'Stifel', 'Baird'
    ]
    found = [u for u in known if u.lower() in text.lower()]
    return found

def parse_risk_factors(html):
    soup = BeautifulSoup(html, 'lxml')
    text = soup.get_text(' ')
    pattern = r'RISK\s+FACTORS(.+?)(?=SPECIAL\s+NOTE|USE\s+OF\s+PROCEEDS|DIVIDEND|CAUTIONARY)'
    m = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
    return m.group(1).strip()[:50000] if m else None

def parse_revenue(text):
    patterns = [
        r'revenue.*?\$([\d,\.]+)\s*(million|billion)',
        r'net\s+revenue.*?\$([\d,\.]+)\s*(million|billion)',
        r'total\s+revenue.*?\$([\d,\.]+)\s*(million|billion)',
    ]
    for pattern in patterns:
        m = re.search(pattern, text, re.IGNORECASE)
        if m:
            val = float(m.group(1).replace(',', ''))
            multiplier = 1e6 if m.group(2).lower() == 'million' else 1e9
            return val * multiplier
    return None

def parse_net_income(text):
    patterns = [
        r'net\s+(income|loss).*?\$([\d,\.]+)\s*(million|billion)',
        r'net\s+(loss|income)\s+of\s+\$([\d,\.]+)\s*(million|billion)',
    ]
    for pattern in patterns:
        m = re.search(pattern, text, re.IGNORECASE)
        if m:
            val = float(m.group(2).replace(',', ''))
            multiplier = 1e6 if m.group(3).lower() == 'million' else 1e9
            is_loss = 'loss' in m.group(1).lower()
            return -val * multiplier if is_loss else val * multiplier
    return None

#loading  accessions
df = pd.read_csv('data/cleaned/s1_accessions.csv')
df = df[df['accession_number'].notna()]
print(f'Parsing {len(df)} S-1 filings...')

results = []

for i, row in df.iterrows():
    ticker = row['ticker']
    cache_path = f'data/raw/edgar/{ticker}.html'

    if not os.path.exists(cache_path):
        logging.warning(f'{ticker}: HTML file not found')
        continue

    try:
        with open(cache_path, 'r', encoding='utf-8', errors='ignore') as f:
            html = f.read()

        soup = BeautifulSoup(html, 'lxml')
        text = soup.get_text(' ')

        offer_price = parse_offer_price(text)
        shares = parse_shares_offered(text)
        underwriters = parse_underwriters(text)
        risk_factors = parse_risk_factors(html)
        revenue = parse_revenue(text)
        net_income = parse_net_income(text)

        results.append({
            'ticker': ticker,
            'offer_price': offer_price,
            'shares_offered': shares,
            'underwriters': '|'.join(underwriters) if underwriters else None,
            'lead_underwriter': underwriters[0] if underwriters else None,
            'num_underwriters': len(underwriters),
            'risk_factors_text': risk_factors,
            'revenue_ttm': revenue,
            'net_income_ttm': net_income,
            'is_profitable': 1 if net_income and net_income > 0 else 0
        })

    except Exception as e:
        logging.warning(f'{ticker}: {e}')

    if len(results) % 50 == 0:
        print(f'Progress: {len(results)}/{len(df)}')

result_df = pd.DataFrame(results)
print(f'\nParsed: {len(result_df)} companies')
print(f'offer_price coverage: {result_df["offer_price"].notna().mean():.1%}')
print(f'shares coverage: {result_df["shares_offered"].notna().mean():.1%}')
print(f'underwriter coverage: {result_df["underwriters"].notna().mean():.1%}')
print(f'risk_factors coverage: {result_df["risk_factors_text"].notna().mean():.1%}')
print(f'revenue coverage: {result_df["revenue_ttm"].notna().mean():.1%}')

result_df.to_csv('data/cleaned/s1_parsed.csv', index=False)
print('Saved to data/cleaned/s1_parsed.csv')
