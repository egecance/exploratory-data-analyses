#!/usr/bin/env python3
"""
Fix missing birthplace data by re-scraping Wikipedia pages
"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import re
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
    'Accept-Language': 'tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7',
}

SLEEP_TIME = 2

def extract_birthplace_improved(soup: BeautifulSoup, name: str):
    """Enhanced birthplace extraction with multiple strategies"""
    
    # Strategy 1: Look for infobox with "Doğum" field
    infobox = soup.find('table', {'class': 'infobox'})
    if infobox:
        rows = infobox.find_all('tr')
        for row in rows:
            th = row.find('th')
            if th and 'doğum' in th.get_text(strip=True).lower():
                td = row.find('td')
                if td:
                    # Get all text, looking for location
                    full_text = td.get_text(strip=True)
                    
                    # Split by newline and look for city/location
                    lines = full_text.split('\n')
                    for line in lines:
                        # Clean up
                        line = re.sub(r'\[.*?\]', '', line).strip()
                        # Skip if it's just a year or date
                        if re.match(r'^\d{4}$', line) or re.match(r'^\d{1,2}\s+\w+\s+\d{4}$', line):
                            continue
                        # Skip if it contains age notation
                        if '(' in line and 'yaş' in line:
                            continue
                        # If we have a potential location
                        if line and len(line) > 2 and not line.isdigit():
                            # Handle comma-separated values (date, location)
                            parts = [p.strip() for p in line.split(',')]
                            for part in parts:
                                # Skip dates
                                if re.search(r'\d{4}', part):
                                    continue
                                if part and len(part) > 2:
                                    return part
    
    # Strategy 2: Look in categories at bottom of page
    categories = soup.find_all('a', href=re.compile(r'/wiki/Kategori:.*doğumlular'))
    for cat in categories:
        cat_text = cat.get_text()
        # Extract city name from category like "Istanbul doğumlular"
        match = re.match(r'(.+?)\s+doğumlular', cat_text)
        if match:
            return match.group(1)
    
    # Strategy 3: Look in first paragraph for birth info
    paragraphs = soup.find_all('p', limit=5)
    for p in paragraphs:
        text = p.get_text()
        
        # Pattern: "Name, (doğum tarihi, Yer"
        pattern = rf'{re.escape(name)}.*?\(.*?(\d{{4}}).*?[,\n]?\s*([A-ZİĞÜŞÖÇ][a-zığüşöç]+(?:\s+[A-ZİĞÜŞÖÇ][a-zığüşöç]+)*)'
        match = re.search(pattern, text)
        if match:
            return match.group(2)
        
        # Pattern: "Yer'da/de doğdu"
        pattern = r'([A-ZİĞÜŞÖÇ][a-zığüşöç]+(?:\s+[A-ZİĞÜŞÖÇ][a-zığüşöç]+)*)[\'\'](?:da|de|ta|te)\s+doğ'
        match = re.search(pattern, text)
        if match:
            return match.group(1)
    
    return None

def fix_csv_file(csv_path: str):
    """Read CSV, re-scrape missing birthplaces, and update"""
    
    logger.info(f"\n{'='*60}")
    logger.info(f"Processing: {csv_path}")
    logger.info(f"{'='*60}\n")
    
    # Read existing CSV
    df = pd.read_csv(csv_path)
    
    # Find rows with missing birthplace data
    missing_mask = (df['birthplace'].isna()) | (df['birthplace'] == '') | (df['status'] == 'not_found')
    missing_count = missing_mask.sum()
    
    logger.info(f"Found {missing_count} commanders with missing birthplace data")
    
    if missing_count == 0:
        logger.info("No missing data to fix!")
        return df
    
    # Process each missing entry
    updated_count = 0
    for idx, row in df[missing_mask].iterrows():
        name = row['name']
        url = row['url']
        
        logger.info(f"\n[{updated_count + 1}/{missing_count}] {name}")
        logger.info(f"  URL: {url}")
        
        try:
            response = requests.get(url, headers=HEADERS, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            birthplace = extract_birthplace_improved(soup, name)
            
            if birthplace:
                df.at[idx, 'birthplace'] = birthplace
                df.at[idx, 'status'] = 'found'
                updated_count += 1
                logger.info(f"  ✓ Found: {birthplace}")
            else:
                logger.info(f"  ✗ Still not found")
                
        except Exception as e:
            logger.error(f"  ✗ Error: {e}")
        
        # Be respectful with rate limiting
        time.sleep(SLEEP_TIME)
    
    # Save updated CSV
    if updated_count > 0:
        # Create backup
        backup_path = csv_path.replace('.csv', '_backup.csv')
        df_original = pd.read_csv(csv_path)
        df_original.to_csv(backup_path, index=False, encoding='utf-8')
        logger.info(f"\n  Backup saved to: {backup_path}")
        
        # Save updated file
        df.to_csv(csv_path, index=False, encoding='utf-8')
        logger.info(f"  Updated file saved: {csv_path}")
    
    # Print summary
    logger.info(f"\n{'='*60}")
    logger.info(f"SUMMARY for {csv_path}")
    logger.info(f"{'='*60}")
    logger.info(f"Originally missing: {missing_count}")
    logger.info(f"Successfully updated: {updated_count}")
    logger.info(f"Still missing: {missing_count - updated_count}")
    logger.info(f"{'='*60}\n")
    
    return df

def main():
    """Main function"""
    import os
    
    data_dir = 'data'
    
    # Process all CSV files
    csv_files = [
        'air_force_commanders.csv',
        'naval_commanders.csv',
    ]
    
    for csv_file in csv_files:
        csv_path = os.path.join(data_dir, csv_file)
        if os.path.exists(csv_path):
            fix_csv_file(csv_path)
            print("\n" + "="*60 + "\n")
        else:
            logger.warning(f"File not found: {csv_path}")
    
    print("\n✓ Fixing complete!")

if __name__ == "__main__":
    main()
