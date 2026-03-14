PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS ipos (
    ticker TEXT PRIMARY KEY,
    company_name TEXT NOT NULL,
    ipo_date TEXT NOT NULL,
    exchange TEXT,
    offer_price REAL,
    shares_offered INTEGER,
    total_raise_usd REAL,
    sector TEXT,
    use_of_proceeds TEXT,
    risk_factors_text TEXT
);

CREATE TABLE IF NOT EXISTS financials (
    ticker TEXT PRIMARY KEY REFERENCES ipos(ticker),
    revenue_ttm REAL,
    net_income_ttm REAL,
    gross_margin REAL,
    revenue_growth REAL,
    is_profitable INTEGER
);

CREATE TABLE IF NOT EXISTS vc_history (
    ticker TEXT PRIMARY KEY REFERENCES ipos(ticker),
    total_funding_usd REAL,
    num_rounds INTEGER,
    last_round_type TEXT,
    founding_year INTEGER,
    lead_investor TEXT,
    has_crunchbase INTEGER DEFAULT 1
);

CREATE TABLE IF NOT EXISTS underwriters (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ticker TEXT REFERENCES ipos(ticker),
    underwriter_name TEXT NOT NULL,
    is_lead INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS price_performance (
    ticker TEXT PRIMARY KEY REFERENCES ipos(ticker),
    open_day_price REAL,
    first_day_pop REAL,
    return_1d REAL,
    return_30d REAL,
    return_90d REAL,
    return_180d REAL
);