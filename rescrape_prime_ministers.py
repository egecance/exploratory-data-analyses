#!/usr/bin/env python3
"""
Rescrape Prime Ministers table with better link filtering
"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
import sqlite3
import re
from pathlib import Path

DB_PATH = Path("data/turkish_officials.db")
CSV_PATH = Path("data/prime_minister.csv")
URL = "https://tr.wikipedia.org/wiki/T%C3%BCrkiye_ba%C5%9Fbakanlar%C4%B1_listesi"

def is_person_link(link_elem):
    """Check if a link is to a person page by comparing title and text"""
    if not link_elem:
        return False
    
    href = link_elem.get('href', '')
    title = link_elem.get('title', '')
    text = link_elem.get_text().strip()
    
    # Must have href starting with /wiki/
    if not href.startswith('/wiki/'):
        return False
    
    # Exclude known non-person pages
    exclude_patterns = [
        'Dosya:', 'File:', 'listesi', '_list', 'genel_seçim', 'seçimleri',
        'Hükûmeti', 'Hükümet', 'milletvekil', 'dönem', 'Kategori:', 
        'Category:', 'Vikipedi:', 'Wikipedia:', 'cumhurbaşkan'
    ]
    
    for pattern in exclude_patterns:
        if pattern in href or pattern in title:
            return False
    
    # Person pages have title matching the text (name)
    # Government pages have title like "62. Türkiye Hükümeti" but text shows person name
    if title and text:
        # Clean both for comparison
        title_clean = title.split('(')[0].strip()
        text_clean = text.split('(')[0].strip()
        
        # If title contains "Türkiye", "Hükümet", or numbers at start, it's a government page
        if re.match(r'^\d+\.', title) or 'Türkiye' in title or 'ükümet' in title:
            return False
        
        # Title should roughly match text (accounting for some differences)
        # For person pages: title="Recep Tayyip Erdoğan" text="Recep Tayyip Erdoğan"
        if title_clean.lower() == text_clean.lower() or text_clean.lower() in title_clean.lower():
            return True
    
    return False


def scrape_prime_ministers():
    """Scrape prime ministers table with proper filtering"""
    print("Fetching Prime Minister page...")
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
    }
    
    response = requests.get(URL, headers=headers, timeout=10)
    response.raise_for_status()
    soup = BeautifulSoup(response.content, 'html.parser')
    
    # Find the main table
    tables = soup.find_all('table', {'class': 'wikitable'})
    
    data = []
    
    for table in tables:
        rows = table.find_all('tr')
        
        # Get headers
        header_row = rows[0]
        headers_list = []
        seen_headers = {}
        for th in header_row.find_all(['th', 'td']):
            header_text = th.get_text().strip()
            # Handle duplicate headers by adding suffix
            if header_text in seen_headers:
                seen_headers[header_text] += 1
                headers_list.append(f"{header_text}_{seen_headers[header_text]}")
            else:
                seen_headers[header_text] = 0
                headers_list.append(header_text)
        
        # Process data rows
        for row in rows[1:]:
            cells = row.find_all(['td', 'th'])
            
            if len(cells) < 2:
                continue
            
            row_data = {'position': 'Prime Minister'}
            
            # Extract data from each cell
            for idx, cell in enumerate(cells):
                col_name = headers_list[idx] if idx < len(headers_list) else f'column_{idx}'
                
                # Clean text
                text = re.sub(r'\s+', ' ', cell.get_text()).strip()
                text = re.sub(r'\[\d+\]', '', text)  # Remove references
                
                row_data[col_name] = text
                
                # Look for person link ONLY from <b> tags (Başbakan names are always bold)
                if 'wikipedia_link' not in row_data:
                    # Find bold tags first
                    bold_tags = cell.find_all('b')
                    for b_tag in bold_tags:
                        # Look for link inside the bold tag
                        link = b_tag.find('a')
                        if link and is_person_link(link):
                            href = link.get('href')
                            row_data['wikipedia_link'] = 'https://tr.wikipedia.org' + href
                            break
            
            # Only add rows with substantial data and exclude acting/interim positions
            if len(row_data) > 3:
                # Check if any value contains acting/interim keywords
                skip = False
                for value in row_data.values():
                    if isinstance(value, str):
                        value_lower = value.lower()
                        if any(keyword in value_lower for keyword in ['geçici', 'vekaleten', 'vekil', 'vekâleten']):
                            skip = True
                            break
                if not skip:
                    data.append(row_data)
    
    return data


def main():
    print("="*80)
    print("RESCRAPING PRIME MINISTERS")
    print("="*80)
    
    # Scrape data
    data = scrape_prime_ministers()
    
    print(f"\nScraped {len(data)} rows")
    
    # Create DataFrame
    df = pd.DataFrame(data)
    
    # Fix duplicate column names (case-insensitive duplicates)
    df = df.rename(columns={'Görev süresi': 'Görev_süresi_1', 'Görev Süresi': 'Görev_Süresi_2'})
    
    # Fix duplicate column names in DataFrame
    df.columns = [f"{col}_{i}" if list(df.columns).count(col) > 1 and list(df.columns)[:i].count(col) > 0 else col 
                  for i, col in enumerate(df.columns)]
    
    # Show summary
    print(f"\nColumns: {list(df.columns)}")
    print(f"\nRows with Wikipedia links: {df['wikipedia_link'].notna().sum()}")
    print(f"Unique Wikipedia links: {df['wikipedia_link'].nunique()}")
    
    # Show sample
    print("\n" + "="*80)
    print("SAMPLE DATA (first 10 with links)")
    print("="*80)
    sample = df[df['wikipedia_link'].notna()].head(10)
    for idx, row in sample.iterrows():
        name = str(row.get('Başbakan', row.get('Hükûmet başkanıÜnvanı', '?')))
        link = row['wikipedia_link'].split('/')[-1] if pd.notna(row.get('wikipedia_link')) else 'N/A'
        print(f"  {name[:50]:50} -> {link}")
    
    # Save to CSV
    df.to_csv(CSV_PATH, index=False, encoding='utf-8-sig')
    print(f"\n✓ Saved to {CSV_PATH}")
    
    # Update database
    conn = sqlite3.connect(DB_PATH)
    df.to_sql('prime_minister', conn, if_exists='replace', index=False)
    conn.close()
    print(f"✓ Updated database: {DB_PATH}")
    
    print("\n" + "="*80)
    print("✅ RESCRAPING COMPLETE")
    print("="*80)


if __name__ == "__main__":
    main()
