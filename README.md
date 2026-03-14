# 📈 IPO Performance Tracker



---

## What is this project?

When a company goes public on the stock market (called an **IPO** - Initial Public Offering), its stock price over the next few months tells the real story of whether investors thought it was a good deal or not.

This project builds an **end-to-end data pipeline** that:
1. Collects information about every major IPO from 2019 to 2025
2. Downloads the official documents companies filed before going public
3. Tracks what happened to their stock price after listing
4. Stores everything in a clean database ready for analysis

Think of it like building a **research database for a venture capital firm** that wants to understand what makes an IPO succeed or fail.

---

## What data did we collect?

We pulled data from **3 sources** and combined them into one database:

| Source | What we got | How |
|--------|-------------|-----|
| **SEC EDGAR** | Company financials, underwriter names, risk factors text from official S-1 filings | Web scraping |
| **stockanalysis.com** | List of all IPOs by year with offer price and ticker | Web scraping |
| **yfinance** | Stock price performance at 30, 90, and 180 days after IPO | Python library |

---

## How big is the dataset?

We started with **2,655 raw IPOs** and ended up with a clean, analysis-ready dataset:

```
Raw scrape:              2,655 IPOs
After removing SPACs:    1,723 IPOs   (932 shell companies removed)
After price filter:      1,675 IPOs   (48 with no IPO price removed)
After yfinance check:    1,198 IPOs   (477 delisted or unavailable removed)
Final with full data:      702 IPOs   (have 90-day return data)
```

---

## What is a SPAC?

A **SPAC** (Special Purpose Acquisition Company) is basically a blank shell company with no real business. It raises money on the stock market first, then goes looking for a real company to buy. We removed these because they have no real financials to analyze.

2020 and 2021 were peak SPAC years, which is why we removed 932 of them.

---

## Database Structure

We store everything in a **SQLite database** with 5 tables that connect to each other:

```
ipos (main table)
  ├── financials      → revenue, net income, profitability
  ├── vc_history      → founding year, funding rounds, total funding raised
  ├── price_performance → 30d, 90d, 180d stock returns
  └── underwriters    → which banks took the company public (many per IPO)
```

### Key numbers after all 5 phases:
- **ipos**: 1,191 companies
- **financials**: 866 companies with revenue data
- **underwriters**: 2,648 records (Goldman Sachs leads with 283 deals)
- **vc_history**: 1,036 companies with founding year and funding data
- **price_performance**: 702 companies with full return data

---

## What did we find? (Quick Insights)

### 📅 IPO Performance by Year
| Year | IPOs | Avg 90-Day Return |
|------|------|-------------------|
| 2019 | 124  | -0.3%  |
| 2020 | 159  | +45.8% 🚀 |
| 2021 | 319  | -23.2% |
| 2022 | 88   | -39.0% 📉 |
| 2023 | 106  | -28.3% |
| 2024 | 167  | -22.5% |
| 2025 | 228  | -4.9%  |

**2020 was an extraordinary year** for IPOs due to pandemic-era stimulus and low interest rates. **2022 was the worst** as the Federal Reserve raised interest rates aggressively.


**What's an Underwriter?** An underwriter is an investment bank that helps a company go public.

### 🏦 Top Underwriters by Deal Count
| Bank | Deals | Avg 90-Day Return |
|------|-------|-------------------|
| Goldman Sachs | 283 | +1.2% |
| Morgan Stanley | 280 | -1.4% |
| J.P. Morgan | 239 | +1.8% |
| Jefferies | 143 | +12.0% |
| Barclays | 131 | +7.1% |

Interestingly, **Jefferies and Barclays** outperformed the larger banks on 90-day returns, suggesting mid-tier banks may be more selective in the deals they choose.

---

## Project Structure

```
ipo_tracker/
│
├── scrapers/
│   ├── master_list.py          # scrapes IPO list from stockanalysis.com
│   ├── edgar_scraper.py        # finds S-1 filing accession numbers on EDGAR
│   ├── fetch_s1_html.py        # downloads and caches S-1 HTML files
│   ├── parse_s1.py             # extracts structured fields from S-1 text
│   ├── vc_history_from_s1.py   # extracts VC history from S-1 text
│   └── fetch_prices.py         # pulls stock price data via yfinance
│
├── database/
│   ├── schema.sql              # defines all 5 tables
│   ├── db.py                   # database connection helper
│   └── load_data.py            # loads CSVs into SQLite
│
├── notebooks/
│   ├── clean_master_list.ipynb # Phase 1 cleaning and validation
│   ├── data_quality.ipynb      # Phase 5 QA and cross-table checks
│   └── ipo_analytics.ipynb     # exploratory analysis and visualizations
│
├── data/
│   ├── raw/
│   │   └── edgar/              # 1,041 cached S-1 HTML files
│   └── cleaned/
│       ├── ipo_master.csv
│       ├── ipo_master_validated.csv
│       ├── s1_accessions.csv
│       ├── s1_parsed.csv
│       ├── vc_history.csv
│       ├── price_performance_clean.csv
│       └── ipo_analysis_ready.csv  ← final dataset
│
└── logs/                       # error logs from all scrapers
```

---

## How to Run This Project

### 1. Clone the repo
```bash
git clone https://github.com/vedantt17/ipo_tracker.git
cd ipo_tracker
```

### 2. Set up the environment
```bash
python -m venv .venv
.venv\Scripts\activate        # Windows
source .venv/bin/activate     # Mac/Linux
pip install requests beautifulsoup4 pandas lxml yfinance playwright exchange-calendars
playwright install chromium
```

### 3. Run the pipeline in order
```bash
python scrapers/master_list.py        # Phase 1: build IPO universe
python scrapers/edgar_scraper.py      # Phase 2: find S-1 accessions
python scrapers/fetch_s1_html.py      # Phase 2: download S-1 files
python scrapers/parse_s1.py           # Phase 2: parse structured fields
python database/db.py                 # Phase 2: initialize database
python database/load_data.py          # Phase 2: load data into SQLite
python scrapers/vc_history_from_s1.py # Phase 3: extract VC history
python scrapers/fetch_prices.py       # Phase 4: pull price data
```

### 4. Open the notebooks for QA and analysis
```bash
jupyter notebook
```

---

## Challenges We Faced

| Challenge | What Happened | How We Fixed It |
|-----------|---------------|-----------------|
| Crunchbase blocked | Bot detection blocked all scraping attempts | Switched to extracting VC data directly from S-1 text |
| SEC homepage cached | Fetcher grabbed wrong URL, saved SEC homepage instead of S-1 | Fixed link finder to only accept /Archives/ paths |
| CIK formatting bug | CIK numbers stored as floats (1757840.0) broke EDGAR lookups | Converted with str(int(float(cik))).zfill(10) |
| UBS false positives | 3-letter string matched in 983 wrong filings | Removed UBS from underwriter parser, deleted bad rows |
| stockanalysis.com only goes back to 2019 | 404 errors for 2012-2018 | Extended forward to 2025 instead, got 2,655 rows |

---



## Data Sources

- [SEC EDGAR](https://www.sec.gov/cgi-bin/browse-edgar) - U.S. Securities and Exchange Commission public filings
- [stockanalysis.com](https://stockanalysis.com/ipos/) - Historical IPO data
- [yfinance](https://pypi.org/project/yfinance/) - Yahoo Finance price data via Python

*This project is for academic research purposes only.*
