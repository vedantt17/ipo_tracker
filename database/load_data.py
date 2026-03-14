# database/load_data.py
# Written by V

import pandas as pd
import sqlite3
import sys
sys.path.append('.')
from database.db import get_conn

conn = get_conn()

# load master list and parsed S1 data
master = pd.read_csv('data/cleaned/ipo_master_validated.csv')
parsed = pd.read_csv('data/cleaned/s1_parsed.csv')

# merge them
df = master.merge(parsed, on='ticker', how='left')
print(f'Merged dataset: {len(df)} rows')

# load ipos table
print('Loading ipos table...')
ipos_loaded = 0
for _, row in df.iterrows():
    try:
        conn.execute('''INSERT OR REPLACE INTO ipos
            (ticker, company_name, ipo_date, offer_price, 
             shares_offered, risk_factors_text)
            VALUES (?,?,?,?,?,?)''',
            (row['ticker'], row['company_name'], str(row['ipo_date']),
             row.get('offer_price'), row.get('shares_offered'),
             row.get('risk_factors_text')))
        ipos_loaded += 1
    except Exception as e:
        print(f'ipos error {row["ticker"]}: {e}')

conn.commit()
print(f'ipos table: {ipos_loaded} rows loaded')

# load financials table
print('Loading financials table...')
fin_loaded = 0
for _, row in df.iterrows():
    try:
        if pd.notna(row.get('revenue_ttm')) or pd.notna(row.get('net_income_ttm')):
            conn.execute('''INSERT OR REPLACE INTO financials
                (ticker, revenue_ttm, net_income_ttm, is_profitable)
                VALUES (?,?,?,?)''',
                (row['ticker'], row.get('revenue_ttm'),
                 row.get('net_income_ttm'), row.get('is_profitable')))
            fin_loaded += 1
    except Exception as e:
        print(f'financials error {row["ticker"]}: {e}')

conn.commit()
print(f'financials table: {fin_loaded} rows loaded')

# load underwriters table
print('Loading underwriters table...')
uw_loaded = 0
for _, row in df.iterrows():
    try:
        if pd.notna(row.get('underwriters')):
            underwriters = str(row['underwriters']).split('|')
            for i, uw in enumerate(underwriters):
                conn.execute('''INSERT INTO underwriters
                    (ticker, underwriter_name, is_lead)
                    VALUES (?,?,?)''',
                    (row['ticker'], uw.strip(), 1 if i == 0 else 0))
                uw_loaded += 1
    except Exception as e:
        print(f'underwriters error {row["ticker"]}: {e}')

conn.commit()
print(f'underwriters table: {uw_loaded} rows loaded')

# verify
print('\nVerification:')
for table in ['ipos', 'financials', 'underwriters']:
    count = conn.execute(f'SELECT COUNT(*) FROM {table}').fetchone()[0]
    print(f'{table}: {count} rows')

conn.close()
print('\nDatabase loaded successfully')