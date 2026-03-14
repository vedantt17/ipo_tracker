# 📈 IPO Performance Tracker

An end-to-end data pipeline that collects, parses, and analyzes U.S. IPO performance from 2019–2025. 

---

## What It Does

1. Scrapes IPO listings (offer price, ticker, date) from stockanalysis.com
2. Finds and downloads official S-1 filings from SEC EDGAR
3. Parses structured fields from S-1 text: financials, underwriters, VC history
4. Fetches post-IPO stock price performance at 30, 90, and 180 days
5. Loads everything into a normalized SQLite database for analysis

---

## Data Sources

| Source | What We Collected | Method |
|---|---|---|
| [stockanalysis.com](https://stockanalysis.com/ipos/) | IPO list, offer price, ticker | Web scraping |
| [SEC EDGAR](https://www.sec.gov/cgi-bin/browse-edgar) | S-1 filings: financials, underwriters, risk factors | Web scraping |
| [yfinance](https://pypi.org/project/yfinance/) | Post-IPO stock returns at 30/90/180 days | Python library |

---

## Dataset Overview

```
Raw scrape:              2,655 IPOs
After removing SPACs:    1,723 IPOs   (932 shell companies removed)
After price filter:      1,675 IPOs   (48 with no IPO price removed)
After yfinance check:    1,198 IPOs   (477 delisted or unavailable removed)
Final with full data:      702 IPOs   (have 90-day return data)
```

SPACs (Special Purpose Acquisition Companies) were excluded because they are shell vehicles with no operating financials to analyze. 2020–2021 were peak SPAC years, accounting for most of the 932 removed.

---

## Database Schema

5-table SQLite schema:

```
ipos (main table)
  ├── financials         → revenue, net income, profitability
  ├── vc_history         → founding year, funding rounds, total raised
  ├── price_performance  → 30d, 90d, 180d stock returns
  └── underwriters       → banks that underwrote the IPO (many-to-one)
```

**Row counts after full pipeline:**

| Table | Rows |
|---|---|
| ipos | 1,191 |
| financials | 866 |
| underwriters | 2,648 |
| vc_history | 1,036 |
| price_performance | 702 |

---

## Key Findings

### IPO Performance by Year

| Year | IPOs | Avg 90-Day Return | Notes |
|---|---|---|---|
| 2019 | 124 | -0.3% | |
| 2020 | 159 | +45.8% 🚀 | Pandemic stimulus + low rates |
| 2021 | 319 | -23.2% | Peak SPAC era, rate hike fears begin |
| 2022 | 88 | -39.0% 📉 | Aggressive Fed rate hikes |
| 2023 | 106 | -28.3% | |
| 2024 | 167 | -22.5% | |
| 2025 | 228 | -4.9% | *Partial year* |

### Top Underwriters by Deal Count

| Bank | Deals | Avg 90-Day Return |
|---|---|---|
| Goldman Sachs | 283 | +1.2% |
| Morgan Stanley | 280 | -1.4% |
| J.P. Morgan | 239 | +1.8% |
| Jefferies | 143 | +12.0% |
| Barclays | 131 | +7.1% |

Jefferies and Barclays outperformed the bulge-bracket banks on 90-day returns, which may reflect more selective deal sourcing at the mid-tier level.

---

## Project Structure

```
ipo_tracker/
│
├── scrapers/
│   ├── master_list.py          # Phase 1: scrape IPO list from stockanalysis.com
│   ├── edgar_scraper.py        # Phase 2: find S-1 accession numbers on EDGAR
│   ├── fetch_s1_html.py        # Phase 2: download and cache S-1 HTML files
│   ├── parse_s1.py             # Phase 2: extract structured fields from S-1 text
│   ├── vc_history_from_s1.py   # Phase 3: extract VC/funding history from S-1 text
│   └── fetch_prices.py         # Phase 4: pull post-IPO stock price data
│
├── database/
│   ├── schema.sql              # table definitions
│   ├── db.py                   # connection helper
│   └── load_data.py            # loads cleaned CSVs into SQLite
│
├── notebooks/
│   ├── clean_master_list.ipynb # Phase 1: cleaning and validation
│   ├── data_quality.ipynb      # Phase 5: QA and cross-table checks
│   └── ipo_analytics.ipynb     # exploratory analysis and visualizations
│
├── data/
│   └── cleaned/                # cleaned CSVs (raw/ is gitignored due to size)
│       ├── ipo_master.csv
│       ├── ipo_master_validated.csv
│       ├── s1_accessions.csv
│       ├── s1_parsed.csv
│       ├── vc_history.csv
│       ├── price_performance_clean.csv
│       └── ipo_analysis_ready.csv   ← final dataset
│
├── .env.example                # template for API keys and config
├── requirements.txt
└── logs/                       # runtime logs (gitignored)
```

---

## Setup

### 1. Clone the repo

```bash
git clone https://github.com/vedantt17/ipo_tracker.git
cd ipo_tracker
```

### 2. Create environment and install dependencies

```bash
python -m venv .venv
source .venv/bin/activate        # Mac/Linux
.venv\Scripts\activate           # Windows

pip install -r requirements.txt
playwright install chromium
```

### 3. Configure API keys

```bash
cp .env.example .env
# edit .env and add your Alpha Vantage key
```

### 4. Run the pipeline in order

```bash
python scrapers/master_list.py        # Phase 1: build IPO universe
python scrapers/edgar_scraper.py      # Phase 2: find S-1 accessions
python scrapers/fetch_s1_html.py      # Phase 2: download S-1 files
python scrapers/parse_s1.py           # Phase 2: parse structured fields
sqlite3 database/ipo_tracker.db < database/schema.sql   # initialize DB
python database/load_data.py          # Phase 2: load CSVs into SQLite
python scrapers/vc_history_from_s1.py # Phase 3: extract VC history
python scrapers/fetch_prices.py       # Phase 4: pull price data
```

### 5. Open the notebooks

```bash
jupyter notebook
```

---

## Challenges

| Challenge | What Happened | Fix |
|---|---|---|
| Crunchbase blocked | Bot detection blocked all scraping attempts | Extracted VC data from S-1 text instead |
| SEC homepage cached | Fetcher saved SEC homepage instead of actual S-1 | Fixed link finder to only accept `/Archives/` paths |
| CIK formatting bug | CIK numbers stored as floats broke EDGAR lookups | Converted with `str(int(float(cik))).zfill(10)` |
| UBS false positives | 3-letter string matched in 983 wrong filings | Removed UBS from underwriter parser, deleted bad rows |
| stockanalysis.com range | 404 errors for years before 2019 | Extended scrape forward to 2025 instead |

---

*For academic research purposes only.*
