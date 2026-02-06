#!/usr/bin/env python3
"""
Test the biographical scraper on a few sample people
"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
import sqlite3
import re
from pathlib import Path

DB_PATH = Path("public/data/turkish_officials/turkish_officials.db")


def fetch_person_page(url: str):
    """Fetch a person's Wikipedia page"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
    }
    
    response = requests.get(url, headers=headers, timeout=10)
    response.raise_for_status()
    return BeautifulSoup(response.content, 'html.parser')


def extract_birth_info(soup):
    """Extract birth year and birth place from Wikipedia infobox"""
    birth_info = {
        'birth_year': None,
        'birth_place': None,
        'birth_date': None
    }
    
    # Look for infobox
    infobox = soup.find('table', class_='infobox')
    
    if infobox:
        rows = infobox.find_all('tr')
        
        for row in rows:
            header = row.find('th')
            if not header:
                continue
                
            header_text = header.get_text().strip().lower()
            
            if 'doğum' in header_text or 'doğ.' in header_text:
                value_cell = row.find('td')
                if value_cell:
                    value_text = value_cell.get_text().strip()
                    
                    # Extract year
                    year_match = re.search(r'\b(1\d{3}|20\d{2})\b', value_text)
                    if year_match:
                        birth_info['birth_year'] = year_match.group(1)
                    
                    birth_info['birth_date'] = value_text
                    
                    # Extract location
                    links = value_cell.find_all('a')
                    locations = []
                    for link in links:
                        link_text = link.get_text().strip()
                        if not re.match(r'\d+', link_text) and len(link_text) > 2:
                            locations.append(link_text)
                    
                    if locations:
                        birth_info['birth_place'] = ', '.join(locations)
    
    return birth_info


# Get a few sample URLs from the database
conn = sqlite3.connect(DB_PATH)
df = pd.read_sql_query("SELECT * FROM prime_minister LIMIT 5", conn)
conn.close()

print("=" * 80)
print("TESTING BIOGRAPHICAL SCRAPER")
print("=" * 80)

for col in df.columns:
    if 'wikipedia_link' in col.lower():
        link_col = col
        break

for idx, row in df.iterrows():
    url = row[link_col]
    if pd.isna(url):
        continue
    
    print(f"\n{idx + 1}. URL: {url}")
    print("-" * 80)
    
    try:
        soup = fetch_person_page(url)
        birth_info = extract_birth_info(soup)
        
        print(f"   Birth Year:  {birth_info['birth_year']}")
        print(f"   Birth Place: {birth_info['birth_place']}")
        print(f"   Birth Date:  {birth_info['birth_date'][:100] if birth_info['birth_date'] else None}...")
        
    except Exception as e:
        print(f"   Error: {e}")

print("\n" + "=" * 80)
