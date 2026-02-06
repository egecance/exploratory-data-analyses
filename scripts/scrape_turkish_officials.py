#!/usr/bin/env python3
"""
Scrape Turkish government officials from Wikipedia and store in CSV/SQLite
"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
import sqlite3
import re
from pathlib import Path
from typing import Dict, List, Tuple
import time
import random

# Configuration
POSITIONS = {
    "Speaker of the National Assembly": "https://tr.wikipedia.org/wiki/T%C3%BCrkiye_B%C3%BCy%C3%BCk_Millet_Meclisi_ba%C5%9Fkanlar%C4%B1_listesi",
    "Prime Minister": "https://tr.wikipedia.org/wiki/T%C3%BCrkiye_ba%C5%9Fbakanlar%C4%B1_listesi",
    "President of the Constitutional Court": "https://tr.wikipedia.org/wiki/T%C3%BCrkiye_Anayasa_Mahkemesi_ba%C5%9Fkanlar%C4%B1_listesi",
    "Minister of Interior": "https://tr.wikipedia.org/wiki/T%C3%BCrkiye_i%C3%A7i%C5%9Fleri_bakanlar%C4%B1_listesi",
    "Minister of Foreign Relations": "https://tr.wikipedia.org/wiki/T%C3%BCrkiye_d%C4%B1%C5%9Fi%C5%9Fleri_bakanlar%C4%B1_listesi",
    "Minister of Justice": "https://tr.wikipedia.org/wiki/T%C3%BCrkiye_adalet_bakanlar%C4%B1_listesi",
    "Minister of Finance & Treasury": "https://tr.wikipedia.org/wiki/T%C3%BCrkiye_hazine_ve_maliye_bakanlar%C4%B1_listesi",
    "Governor of the Central Bank": "https://tr.wikipedia.org/wiki/T%C3%BCrkiye_Cumhuriyet_Merkez_Bankas%C4%B1_ba%C5%9Fkanlar%C4%B1_listesi",
    "Minister of Education": "https://tr.wikipedia.org/wiki/T%C3%BCrkiye_mill%C3%AE_e%C4%9Fitim_bakanlar%C4%B1_listesi",
    "Minister of Health": "https://tr.wikipedia.org/wiki/T%C3%BCrkiye_sa%C4%9Fl%C4%B1k_bakanlar%C4%B1_listesi",
    "Chief of General Staff": "https://tr.wikipedia.org/wiki/T%C3%BCrk_Silahl%C4%B1_Kuvvetleri_genelkurmay_ba%C5%9Fkanlar%C4%B1_listesi",
    "Commander of the Turkish Army": "https://tr.wikipedia.org/wiki/T%C3%BCrk_Kara_Kuvvetleri_komutanlar%C4%B1_listesi",
    "Commander of the Turkish Naval Forces": "https://tr.wikipedia.org/wiki/T%C3%BCrk_Deniz_Kuvvetleri_komutanlar%C4%B1_listesi",
    "Commander of the Turkish Air Forces": "https://tr.wikipedia.org/wiki/T%C3%BCrk_Hava_Kuvvetleri_komutanlar%C4%B1_listesi",
    "Head of National Intelligence": "https://tr.wikipedia.org/wiki/Mill%C3%AE_%C4%B0stihbarat_Te%C5%9Fkilat%C4%B1_ba%C5%9Fkanlar%C4%B1_listesi"
}

OUTPUT_DIR = Path("public/data/turkish_officials")
DB_PATH = OUTPUT_DIR / "turkish_officials.db"


def fetch_page(url: str) -> BeautifulSoup:
    """Fetch and parse a Wikipedia page"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        return BeautifulSoup(response.content, 'html.parser')
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return None


def clean_text(text: str) -> str:
    """Clean and normalize text"""
    if not text:
        return ""
    # Remove extra whitespace and newlines
    text = re.sub(r'\s+', ' ', text)
    # Remove reference brackets like [1], [2], etc.
    text = re.sub(r'\[\d+\]', '', text)
    return text.strip()


def should_exclude_row(row_data: Dict) -> bool:
    """Check if a row should be excluded (e.g., acting/interim positions)"""
    # Check if any value contains acting/interim keywords
    exclude_keywords = ['vekaleten', 'vekâleten', 'vekil', 'geçici']
    for key, value in row_data.items():
        if isinstance(value, str):
            value_lower = value.lower()
            if any(keyword in value_lower for keyword in exclude_keywords):
                return True
    return False


def extract_table_data(soup: BeautifulSoup, position: str) -> List[Dict]:
    """Extract data from Wikipedia tables"""
    if not soup:
        return []
    
    data = []
    
    # Find all tables with class 'wikitable'
    tables = soup.find_all('table', {'class': 'wikitable'})
    
    for table in tables:
        headers = []
        header_row = table.find('tr')
        
        if header_row:
            # Extract headers and make them unique
            seen_headers = {}
            for th in header_row.find_all(['th', 'td']):
                header_text = clean_text(th.get_text())
                if header_text:
                    # Handle duplicate headers
                    if header_text in seen_headers:
                        seen_headers[header_text] += 1
                        headers.append(f"{header_text}_{seen_headers[header_text]}")
                    else:
                        seen_headers[header_text] = 0
                        headers.append(header_text)
        
        # Extract rows
        rows = table.find_all('tr')[1:]  # Skip header row
        
        for row in rows:
            cells = row.find_all(['td', 'th'])
            if len(cells) >= 2:  # At least name and some other info
                row_data = {
                    'position': position,
                }
                
                # Extract cell data
                for idx, cell in enumerate(cells):
                    # Get column name
                    col_name = headers[idx] if idx < len(headers) else f'column_{idx}'
                    
                    # Extract text
                    text = clean_text(cell.get_text())
                    
                    # Extract person links from ANY cell that has a link to a person page
                    # BUT exclude columns that contain references to other positions (like President in PM table)
                    # AND prioritize links from bold tags (person names are usually bold)
                    col_lower = col_name.lower()
                    is_reference_column = any(keyword in col_lower for keyword in [
                        'cumhurbaşkan', 'president', 'hükümdar', 'monarch', 'padişah', 'sultan'
                    ])
                    
                    if not is_reference_column and 'wikipedia_link' not in row_data:  # Only if we haven't found a link yet
                        # First, try to find link in bold tags (most reliable for person names)
                        bold_tags = cell.find_all('b')
                        for b_tag in bold_tags:
                            link = b_tag.find('a')
                            if link:
                                href = link.get('href', '')
                                if href and href.startswith('/wiki/'):
                                    # Exclude non-person pages
                                    exclude_in_href = ['Dosya:', 'File:', 'listesi', 'Kategori:', 
                                              'dönem', 'genel_seçim', 'seçimleri', 'Hükûmeti', 'milletvekil', 'Category:']
                                    # Exclude president pages (URL encoded Turkish characters)
                                    if 'cumhurba%C5%9Fkan' in href:
                                        continue
                                        
                                    if not any(x in href for x in exclude_in_href):
                                        row_data['wikipedia_link'] = 'https://tr.wikipedia.org' + href
                                        break
                        
                        # If no bold link found, try regular links as fallback
                        if 'wikipedia_link' not in row_data:
                            links = cell.find_all('a')
                            for link in links:
                                href = link.get('href', '')
                                # Only store if it looks like a person page
                                if href and href.startswith('/wiki/'):
                                    # Exclude non-person pages
                                    exclude_in_href = ['Dosya:', 'File:', 'listesi', 'Kategori:', 
                                              'dönem', 'genel_seçim', 'seçimleri', 'Hükûmeti', 'milletvekil', 'Category:']
                                    # Exclude president pages (URL encoded Turkish characters)
                                    if 'cumhurba%C5%9Fkan' in href:
                                        continue
                                        
                                    if not any(x in href for x in exclude_in_href):
                                        # Additional check: person pages usually have names (not all caps, has letters)
                                        page_name = href.split('/')[-1]
                                        if any(c.islower() for c in page_name) or 'C3%' in page_name:  # Has lowercase or Turkish chars
                                            row_data['wikipedia_link'] = 'https://tr.wikipedia.org' + href
                                            break
                    
                    row_data[col_name] = text
                
                # Only add if we have substantial data and not excluded
                if len(row_data) > 2 and not should_exclude_row(row_data):
                    data.append(row_data)
    
    return data


def scrape_all_positions() -> Dict[str, pd.DataFrame]:
    """Scrape all positions and return DataFrames"""
    all_data = {}
    
    for idx, (position, url) in enumerate(POSITIONS.items(), 1):
        print(f"\n[{idx}/{len(POSITIONS)}] Scraping: {position}")
        print(f"URL: {url}")
        
        soup = fetch_page(url)
        data = extract_table_data(soup, position)
        
        if data:
            df = pd.DataFrame(data)
            all_data[position] = df
            print(f"  ✓ Extracted {len(df)} records")
        else:
            print(f"  ✗ No data extracted")
        
        # Be respectful to Wikipedia servers - random delay between 2-5 seconds
        if idx < len(POSITIONS):  # Don't wait after the last one
            wait_time = random.uniform(2.0, 5.0)
            print(f"  ⏳ Waiting {wait_time:.1f}s before next request...")
            time.sleep(wait_time)
    
    return all_data


def save_to_csv(data: Dict[str, pd.DataFrame], output_dir: Path):
    """Save each position's data to separate CSV files"""
    output_dir.mkdir(parents=True, exist_ok=True)
    
    for position, df in data.items():
        # Create safe filename
        filename = re.sub(r'[^\w\s-]', '', position).strip().replace(' ', '_').lower()
        filepath = output_dir / f"{filename}.csv"
        
        df.to_csv(filepath, index=False, encoding='utf-8-sig')
        print(f"Saved: {filepath}")


def save_to_sqlite(data: Dict[str, pd.DataFrame], db_path: Path):
    """Save all data to SQLite database"""
    db_path.parent.mkdir(parents=True, exist_ok=True)
    
    conn = sqlite3.connect(db_path)
    
    print(f"\nSaving to SQLite: {db_path}")
    
    # Save each position to separate tables
    for position, df in data.items():
        table_name = re.sub(r'[^\w\s-]', '', position).strip().replace(' ', '_').lower()
        df_copy = df.copy()
        
        # Fix duplicate column names (case-insensitive for SQLite compatibility)
        new_cols = []
        col_counts_case_insensitive = {}
        
        for col in df_copy.columns:
            # Use lowercase version for counting to detect case-insensitive duplicates
            col_lower = col.lower()
            
            if col_lower in col_counts_case_insensitive:
                col_counts_case_insensitive[col_lower] += 1
                # Add suffix to make it unique
                new_cols.append(f"{col}_{col_counts_case_insensitive[col_lower]}")
            else:
                col_counts_case_insensitive[col_lower] = 0
                new_cols.append(col)
        
        df_copy.columns = new_cols
        
        df_copy.to_sql(table_name, conn, if_exists='replace', index=False)
        print(f"  ✓ Table: {table_name} ({len(df_copy)} records)")
    
    conn.close()


def main():
    """Main execution function"""
    print("=" * 70)
    print("Turkish Government Officials Scraper")
    print("=" * 70)
    
    # Scrape all data
    print("\n📥 Starting scraping process...\n")
    data = scrape_all_positions()
    
    if not data:
        print("\n❌ No data was scraped. Please check the URLs and try again.")
        return
    
    # Save to CSV
    print("\n" + "=" * 70)
    print("💾 Saving to CSV files...")
    print("=" * 70)
    save_to_csv(data, OUTPUT_DIR)
    
    # Save to SQLite
    print("\n" + "=" * 70)
    print("💾 Saving to SQLite database...")
    print("=" * 70)
    save_to_sqlite(data, DB_PATH)
    
    # Summary
    print("\n" + "=" * 70)
    print("📊 Summary")
    print("=" * 70)
    total_records = sum(len(df) for df in data.values())
    print(f"Total positions scraped: {len(data)}")
    print(f"Total records extracted: {total_records}")
    print(f"\nOutput directory: {OUTPUT_DIR.absolute()}")
    print(f"Database file: {DB_PATH.absolute()}")
    print("\n✅ Scraping completed successfully!")


if __name__ == "__main__":
    main()
