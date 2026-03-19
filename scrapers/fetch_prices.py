# scrapers/fetch_prices.py

import yfinance as yf
import pandas as pd
import sqlite3

import time
import logging


import exchange_calendars as xcals

logging.basicConfig(filename='logs/price_errors.log', level=logging.WARNING)

def compute_returns(ticker, ipo_date, offer_price):
    try:
        data = yf.download(ticker, start=ipo_date, progress=False, auto_adjust=True)
        if data.empty:
            return None

        data.index = pd.to_datetime(data.index)
        data = data.sort_index()

        #getting thr trading calendar
        cal =   xcals.get_calendar('XNYS')
        sessions =  cal.sessions_in_range(ipo_date, data.index[-1].strftime('%Y-%m-%d'))
        trade_days = [s for s in sessions if pd.Timestamp(s) >= pd.Timestamp(ipo_date)]

        if not trade_days:
            return None

        def get_price(n):
            if len(trade_days) <= n:
                return None
            target  = pd.Timestamp(trade_days[n])
            if target in data.index:
                return float(data.loc[target, 'Close'].iloc[0] if hasattr(data.loc[target, 'Close'], 'iloc') else data.loc[target, 'Close'])
            return None

        p0 =  get_price(0)
        p1 =  get_price(1)
        p30 =   get_price(30)
        p90 =  get_price(90)
        p180  = get_price(180)

        def ret(p):
            return round((p - p0) / p0, 4) if p and p0 else None

        first_day_pop = round((p0 - float(offer_price)) / float(offer_price), 4) if p0 and offer_price else None

        return {
            'ticker': ticker,
            'open_day_price': p0,
            'first_day_pop': first_day_pop,
            'return_1d': ret(p1),
            'return_30d': ret(p30),
            'return_90d': ret(p90),
            'return_180d': ret(p180),
        }
    except Exception as e:
        logging.warning(f'{ticker}: {e}')
        return None

#loading data
conn = sqlite3.connect('database/ipo_tracker.db')
df =  pd.read_sql('SELECT ticker, ipo_date, offer_price FROM ipos', conn)
df =  df[df['offer_price'].notna()]
print(f'Fetching prices for {len(df)} tickers...')

results = []
failed = 0

for i, row in df.iterrows():
    result = compute_returns(row['ticker'], row['ipo_date'], row['offer_price'])
    if result:
        results.append(result)
    else:
        failed += 1

    if (len(results) + failed) % 50 == 0:
        print(f'Progress: {len(results) + failed}/{len(df)} -- success: {len(results)} failed: {failed}')

    time.sleep(0.3)

print(f'\nDone. Success: {len(results)} Failed: {failed}')

#loading into the database
loaded =  0
for r in results:
    try:
        conn.execute('''INSERT OR REPLACE INTO price_performance
            (ticker, open_day_price, first_day_pop, return_1d,
             return_30d, return_90d, return_180d)
            VALUES (?,?,?,?,?,?,?)''',
            (r['ticker'], r['open_day_price'], r['first_day_pop'],
             r['return_1d'], r['return_30d'], r['return_90d'], r['return_180d']))
        loaded += 1
    except Exception as e:
        logging.warning(f'DB insert {r["ticker"]}: {e}')

conn.commit()
count = conn.execute('SELECT COUNT(*) FROM price_performance').fetchone()[0]
print(f'price_performance table: {count} rows')
conn.close()

#also save csv backup
pd.DataFrame(results).to_csv('data/cleaned/price_performance.csv', index=False)
print('Saved to data/cleaned/price_performance.csv')
