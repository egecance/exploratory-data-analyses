#!/usr/bin/env python3
"""
Scrape detailed biographical information (birth place, birth year) for each official
"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
import sqlite3
import re
from pathlib import Path
import time
import random
from typing import Dict, Optional

DB_PATH = Path("data/turkish_officials.db")
OUTPUT_DIR = Path("data")


def is_person_page(url: str) -> bool:
    """Check if a URL is a valid person page (not an election, list, or category page)"""
    if not url or 'wikipedia.org' not in url:
        return False
    
    exclude_patterns = [
        'Dosya:', 'File:', 'listesi', '_list', 'genel_seçim', 'seçimleri',
        'milletvekil', 'dönem', 'Kategori:', 'Category:', 
        'Vikipedi:', 'Wikipedia:'
    ]
    
    for pattern in exclude_patterns:
        if pattern in url:
            return False
    
    return True


def fetch_person_page(url: str) -> Optional[BeautifulSoup]:
    """Fetch a person's Wikipedia page"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        return BeautifulSoup(response.content, 'html.parser')
    except Exception as e:
        print(f"  ✗ Error fetching {url}: {e}")
        return None


def extract_birth_info(soup: BeautifulSoup) -> Dict[str, str]:
    """Extract birth year and birth place from Wikipedia infobox"""
    birth_info = {
        'birth_year': None,
        'birth_place': None,
        'birth_date': None
    }
    
    if not soup:
        return birth_info
    
    # Look for infobox (Turkish Wikipedia uses 'bilgi kutusu' class)
    infobox = soup.find('table', class_='infobox')
    
    if infobox:
        # Find rows in the infobox
        rows = infobox.find_all('tr')
        
        for row in rows:
            # Get the header cell
            header = row.find('th')
            if not header:
                continue
                
            header_text = header.get_text().strip().lower()
            
            # Look for "Doğum" field specifically (not "Doğum yeri" or other variations)
            if header_text == 'doğum' or header_text == 'doğ.':
                value_cell = row.find('td')
                if value_cell:
                    value_text = value_cell.get_text().strip()
                    
                    # Extract year - look for 4-digit Gregorian year (1800-2099)
                    # Match only years in reasonable range to avoid Hijri calendar dates (1315, etc.)
                    year_match = re.search(r'\b(18\d{2}|19\d{2}|20\d{2})\b', value_text)
                    if year_match:
                        birth_info['birth_year'] = year_match.group(1)
                    
                    # Store full birth date/place
                    birth_info['birth_date'] = value_text
                    
                    # Try to extract location
                    # Look for links (cities/countries are usually linked)
                    links = value_cell.find_all('a')
                    locations = []
                    for link in links:
                        link_text = link.get_text().strip()
                        # Skip date-related links
                        if not re.match(r'\d+', link_text) and len(link_text) > 2:
                            locations.append(link_text)
                    
                    if locations:
                        birth_info['birth_place'] = ', '.join(locations)
                    else:
                        # Fallback: try to extract location from text
                        # Remove date parts and common words
                        place_text = re.sub(r'\d+\s+\w+\s+\d{4}', '', value_text)
                        place_text = re.sub(r'\(.*?\)', '', place_text)
                        place_text = place_text.strip('., ')
                        if place_text and len(place_text) > 2:
                            birth_info['birth_place'] = place_text
    
    # Alternative: Look in the first paragraph
    if not birth_info['birth_year'] or not birth_info['birth_place']:
        first_para = soup.find('p')
        if first_para:
            para_text = first_para.get_text()
            
            # Look for birth year if not found
            if not birth_info['birth_year']:
                year_match = re.search(r'\b(d\.\s*)?(\d{1,2}\s+\w+\s+)?(1\d{3}|20\d{2})\b', para_text)
                if year_match:
                    birth_info['birth_year'] = year_match.group(3)
            
            # Look for birth place pattern: "d. YYYY, PLACE" or "(d. YYYY)"
            if not birth_info['birth_place']:
                place_match = re.search(r'd\.\s*\d+[^,]*,\s*([^)]+)', para_text)
                if place_match:
                    birth_info['birth_place'] = place_match.group(1).strip()
    
    return birth_info


def process_table(table_name: str, conn: sqlite3.Connection, processed_urls: set) -> pd.DataFrame:
    """Process all people in a table and extract birth information"""
    print(f"\n📋 Processing: {table_name.replace('_', ' ').title()}")
    
    # Read the table
    df = pd.read_sql_query(f"SELECT * FROM {table_name}", conn)
    
    # Find the wikipedia_link column
    link_col = None
    for col in df.columns:
        if 'wikipedia_link' in col.lower():
            link_col = col
            break
    
    if not link_col:
        print(f"  ⚠️  No wikipedia_link column found, skipping...")
        return df
    
    # Add new columns if they don't exist
    if 'birth_year' not in df.columns:
        df['birth_year'] = None
    if 'birth_place' not in df.columns:
        df['birth_place'] = None
    if 'birth_date' not in df.columns:
        df['birth_date'] = None
    
    # Process each person
    new_people = 0
    cached_people = 0
    skipped = 0
    
    for idx, row in df.iterrows():
        url = row[link_col]
        
        if pd.isna(url) or not url:
            continue
        
        # For prime_minister table, only process rows where Başbakan has actual names (with years)
        if table_name == 'prime_minister' and 'Başbakan' in df.columns:
            basbakan = row['Başbakan']
            if pd.isna(basbakan) or not basbakan:
                continue
            # Skip entries without birth years (like "II. İnönü", "IV. İnönü")
            if not re.search(r'\d{4}', str(basbakan)):
                skipped += 1
                continue
        
        # Skip non-person pages (elections, lists, etc.)
        if not is_person_page(url):
            skipped += 1
            continue
        
        # Skip if already processed
        if url in processed_urls:
            cached_people += 1
            continue
        
        new_people += 1
        print(f"  [{new_people}] Fetching: {url.split('/')[-1][:50]}...", end='')
        
        # Fetch and parse the page
        soup = fetch_person_page(url)
        birth_info = extract_birth_info(soup)
        
        # Update the dataframe
        df.at[idx, 'birth_year'] = birth_info['birth_year']
        df.at[idx, 'birth_place'] = birth_info['birth_place']
        df.at[idx, 'birth_date'] = birth_info['birth_date']
        
        # Mark as processed
        processed_urls.add(url)
        
        # Show what we found
        if birth_info['birth_year'] or birth_info['birth_place']:
            print(f" ✓ {birth_info['birth_year'] or '?'} - {birth_info['birth_place'] or '?'}")
        else:
            print(f" ✗ No birth info found")
        
        # Be respectful to Wikipedia
        time.sleep(random.uniform(1.5, 3.5))
    
    print(f"  Summary: {new_people} new, {cached_people} cached, {skipped} skipped")
    
    return df


def main():
    print("=" * 80)
    print("BIOGRAPHICAL INFO SCRAPER - Birth Year & Place")
    print("=" * 80)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Get all tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [row[0] for row in cursor.fetchall()]
    
    print(f"\nFound {len(tables)} tables to process")
    
    # Keep track of already processed URLs to avoid duplicates
    processed_urls = set()
    
    # Process each table
    for i, table in enumerate(tables, 1):
        print(f"\n{'='*80}")
        print(f"Table {i}/{len(tables)}")
        print(f"{'='*80}")
        
        # Process and get updated dataframe
        df_updated = process_table(table, conn, processed_urls)
        
        # Save back to database
        df_updated.to_sql(table, conn, if_exists='replace', index=False)
        print(f"  💾 Updated database table: {table}")
        
        # Also update CSV
        csv_path = OUTPUT_DIR / f"{table}.csv"
        df_updated.to_csv(csv_path, index=False, encoding='utf-8-sig')
        print(f"  💾 Updated CSV: {csv_path.name}")
    
    conn.close()
    
    # Final summary
    print("\n" + "=" * 80)
    print("📊 FINAL SUMMARY")
    print("=" * 80)
    print(f"Total unique people processed: {len(processed_urls)}")
    print(f"Tables updated: {len(tables)}")
    print("\n✅ Biographical scraping completed!")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    main()
