# scrapers/crunchbase_scraper.py
# Written by V

from playwright.sync_api import sync_playwright
import time
import json

def test_crunchbase(slug):
    url = f'https://www.crunchbase.com/organization/{slug}'
    print(f'Testing: {url}')
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.set_extra_http_headers({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        page.goto(url, timeout=30000)
        page.wait_for_timeout(4000)
        
        html = page.content()
        print(f'Page length: {len(html)} characters')
        print(f'Blocked: {"captcha" in html.lower() or "blocked" in html.lower()}')
        print(f'Has funding data: {"total funding" in html.lower() or "funding rounds" in html.lower()}')
        
        browser.close()

# test with a few known companies
test_crunchbase('snowflake')
time.sleep(3)
test_crunchbase('airbnb')