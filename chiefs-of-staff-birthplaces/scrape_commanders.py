#!/usr/bin/env python3
"""
Web scraper to collect birthplace information for Turkish Naval and Air Force commanders
Uses Beautiful Soup with rate limiting and user-agent headers
"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import re
from typing import Optional, Dict
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# User agent to identify ourselves politely
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7',
}

# Sleep time between requests (in seconds)
SLEEP_TIME = 2

# Naval Commanders (Deniz Kuvvetleri Komutanları)
NAVAL_COMMANDERS = [
    {"name": "Mehmet Ali Ülgen", "start": "1949", "end": "1950"},
    {"name": "Sadık Altıncan", "start": "1950", "end": "1957"},
    {"name": "Fahri Korutürk", "start": "1957", "end": "1960"},
    {"name": "Ahmet Zeki Özak", "start": "1960", "end": "1961"},
    {"name": "Necdet Uran", "start": "1961", "end": "1968"},
    {"name": "Celal Eyiceoğlu", "start": "1968", "end": "1972"},
    {"name": "Kemal Kayacan", "start": "1972", "end": "1974"},
    {"name": "Hilmi Fırat", "start": "1974", "end": "1977"},
    {"name": "Bülent Ulusu", "start": "1977", "end": "1980"},
    {"name": "Nejat Tümer", "start": "1980", "end": "1983"},
    {"name": "Zahit Atakan", "start": "1983", "end": "1986"},
    {"name": "Emin Göksan", "start": "1986", "end": "1988"},
    {"name": "Orhan Karabulut", "start": "1988", "end": "1990"},
    {"name": "İrfan Tınaz", "start": "1990", "end": "1992"},
    {"name": "Vural Beyazıt", "start": "1992", "end": "1995"},
    {"name": "Güven Erkaya", "start": "1995", "end": "1997"},
    {"name": "Salim Dervişoğlu", "start": "1997", "end": "1999"},
    {"name": "İlhami Erdil", "start": "1999", "end": "2001"},
    {"name": "Bülent Alpkaya", "start": "2001", "end": "2003"},
    {"name": "Özden Örnek", "start": "2003", "end": "2005"},
    {"name": "Yener Karahanoğlu", "start": "2005", "end": "2007"},
    {"name": "Metin Ataç", "start": "2007", "end": "2009"},
    {"name": "Uğur Yiğit", "start": "2009", "end": "2011"},
    {"name": "Murat Bilgel", "start": "2011", "end": "2013"},
    {"name": "Bülent Bostanoğlu", "start": "2013", "end": "2017"},
    {"name": "Adnan Özbal", "start": "2017", "end": "2022"},
    {"name": "Ercüment Tatlıoğlu", "start": "2022", "end": "Present"},
]

# Air Force Commanders (Hava Kuvvetleri Komutanları)
AIR_FORCE_COMMANDERS = [
    {"name": "Zeki Doğan", "start": "1944", "end": "1950"},
    {"name": "Muzaffer Göksenin", "start": "1950", "end": "1953"},
    {"name": "Fevzi Uçaner", "start": "1953", "end": "1957"},
    {"name": "Hamdullah Suphi Göker", "start": "1957", "end": "1959"},
    {"name": "Tekin Arıburun", "start": "1959", "end": "1960"},
    {"name": "İhsan Orgun", "start": "1960", "end": "1960"},
    {"name": "İrfan Tansel", "start": "1960", "end": "1961"},
    {"name": "Süleyman Tulgan", "start": "1961", "end": "1961"},
    {"name": "İrfan Tansel", "start": "1961", "end": "1968"},
    {"name": "Reşat Mater", "start": "1968", "end": "1969"},
    {"name": "Muhsin Batur", "start": "1969", "end": "1973"},
    {"name": "Emin Alpkaya", "start": "1973", "end": "1976"},
    {"name": "Cemal Engin", "start": "1976", "end": "1976"},
    {"name": "Ethem Ayan", "start": "1976", "end": "1978"},
    {"name": "Tahsin Şahinkaya", "start": "1978", "end": "1983"},
    {"name": "Halil Sözer", "start": "1983", "end": "1986"},
    {"name": "Cemil Çuha", "start": "1986", "end": "1988"},
    {"name": "Saftar Necioğlu", "start": "1988", "end": "1990"},
    {"name": "Siyami Taştan", "start": "1990", "end": "1992"},
    {"name": "Halis Burhan", "start": "1992", "end": "1995"},
    {"name": "Ahmet Çörekçi", "start": "1995", "end": "1997"},
    {"name": "İlhan Kılıç", "start": "1997", "end": "1999"},
    {"name": "Ergin Celasin", "start": "1999", "end": "2001"},
    {"name": "Cumhur Asparuk", "start": "2001", "end": "2003"},
    {"name": "İbrahim Fırtına", "start": "2003", "end": "2005"},
    {"name": "Faruk Cömert", "start": "2005", "end": "2007"},
    {"name": "Aydoğan Babaoğlu", "start": "2007", "end": "2009"},
    {"name": "Hasan Aksay", "start": "2009", "end": "2011"},
    {"name": "Mehmet Erten", "start": "2011", "end": "2013"},
    {"name": "Akın Öztürk", "start": "2013", "end": "2015"},
    {"name": "Abidin Ünal", "start": "2015", "end": "2017"},
    {"name": "Hasan Küçükakyüz", "start": "2017", "end": "2022"},
    {"name": "Atilla Gülan", "start": "2022", "end": "2023"},
    {"name": "Ziya Cemal Kadıoğlu", "start": "2023", "end": "Present"},
]


def get_wikipedia_url(name: str) -> str:
    """Convert name to Wikipedia URL format"""
    # Replace spaces with underscores
    url_name = name.replace(" ", "_")
    return f"https://tr.wikipedia.org/wiki/{url_name}"


def extract_birthplace_from_infobox(soup: BeautifulSoup) -> Optional[str]:
    """Extract birthplace from Wikipedia infobox"""
    
    # Look for infobox
    infobox = soup.find('table', {'class': 'infobox'})
    if not infobox:
        return None
    
    # Look for rows containing birth information
    rows = infobox.find_all('tr')
    for row in rows:
        th = row.find('th')
        if th:
            header_text = th.get_text(strip=True).lower()
            # Look for birth-related fields (Doğum means birth in Turkish)
            if any(keyword in header_text for keyword in ['doğum', 'doğ.', 'birth']):
                td = row.find('td')
                if td:
                    # Extract text and clean it
                    text = td.get_text(strip=True)
                    
                    # Wikipedia format is typically: "Date, Location" or "Date\nLocation"
                    # Example: "15 Şubat 1926, Adana, Türkiye" or "23 Ağustos 1989\nKemal Yamak"
                    
                    # Remove reference markers [1], [2], etc.
                    text = re.sub(r'\[.*?\]', '', text)
                    
                    # Split by comma or newline
                    parts = re.split(r'[,\n]', text)
                    
                    # The birthplace is usually the first part after the date
                    # Date patterns: "15 Şubat 1926" or "1926" or "23 Ağustos 1989"
                    for i, part in enumerate(parts):
                        part = part.strip()
                        
                        # Skip empty parts
                        if not part:
                            continue
                        
                        # If this part contains a date (with year), the next part is likely the location
                        if re.search(r'\d{4}', part):
                            # Look at the next part
                            if i + 1 < len(parts):
                                location = parts[i + 1].strip()
                                # Clean up common suffixes like ", Türkiye"
                                location = re.sub(r',?\s*Türkiye$', '', location)
                                location = re.sub(r',?\s*Turkey$', '', location)
                                if location and len(location) > 1:
                                    return location
                            continue
                        
                        # If this part doesn't contain a year and we've passed the first part (date),
                        # this might be the location
                        if i > 0 and not re.search(r'\d{4}', part):
                            location = part.strip()
                            location = re.sub(r',?\s*Türkiye$', '', location)
                            location = re.sub(r',?\s*Turkey$', '', location)
                            if location and len(location) > 1:
                                return location
    
    return None


def extract_birthplace_from_text(soup: BeautifulSoup, name: str) -> Optional[str]:
    """Try to extract birthplace from article text"""
    
    # Look in the first few paragraphs
    paragraphs = soup.find_all('p', limit=5)
    
    for p in paragraphs:
        text = p.get_text()
        
        # Look for patterns like "X'da/de doğdu" or "doğum yeri"
        patterns = [
            r"([A-ZİĞÜŞÖÇ][a-zığüşöç]+(?:\s+[A-ZİĞÜŞÖÇ][a-zığüşöç]+)*)'(?:da|de|ta|te)\s+doğ",
            r"doğum\s+yeri[:\s]+([A-ZİĞÜŞÖÇ][a-zığüşöç]+(?:\s+[A-ZİĞÜŞÖÇ][a-zığüşöç]+)*)",
            r"([A-ZİĞÜŞÖÇ][a-zığüşöç]+(?:\s+[A-ZİĞÜŞÖÇ][a-zığüşöç]+)*)\s+doğumlu",
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(1)
    
    return None


def scrape_birthplace(name: str) -> Dict:
    """Scrape birthplace for a single commander"""
    
    logger.info(f"Fetching data for: {name}")
    
    url = get_wikipedia_url(name)
    result = {
        "name": name,
        "birthplace": None,
        "url": url,
        "status": "not_found"
    }
    
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Try infobox first
        birthplace = extract_birthplace_from_infobox(soup)
        
        # If not found, try article text
        if not birthplace:
            birthplace = extract_birthplace_from_text(soup, name)
        
        if birthplace:
            result["birthplace"] = birthplace
            result["status"] = "found"
            logger.info(f"  ✓ Found: {birthplace}")
        else:
            logger.warning(f"  ✗ Birthplace not found")
            
    except requests.exceptions.RequestException as e:
        logger.error(f"  ✗ Error fetching page: {e}")
        result["status"] = "error"
    
    return result


def scrape_commanders(commanders: list, output_file: str, force_name: str = None):
    """Scrape all commanders and save to CSV"""
    
    logger.info(f"\n{'='*60}")
    logger.info(f"Starting to scrape {len(commanders)} commanders")
    logger.info(f"Output file: {output_file}")
    logger.info(f"{'='*60}\n")
    
    results = []
    
    for i, commander in enumerate(commanders, 1):
        logger.info(f"[{i}/{len(commanders)}] Processing...")
        
        result = scrape_birthplace(commander["name"])
        result["start_year"] = commander["start"]
        result["end_year"] = commander["end"]
        
        results.append(result)
        
        # Sleep between requests to be respectful
        if i < len(commanders):
            time.sleep(SLEEP_TIME)
    
    # Create DataFrame
    df = pd.DataFrame(results)
    
    # Reorder columns
    df = df[["name", "birthplace", "start_year", "end_year", "status", "url"]]
    
    # Save to CSV
    df.to_csv(output_file, index=False, encoding='utf-8')
    
    # Print summary
    logger.info(f"\n{'='*60}")
    logger.info(f"SUMMARY")
    logger.info(f"{'='*60}")
    logger.info(f"Total commanders: {len(results)}")
    logger.info(f"Found birthplaces: {sum(1 for r in results if r['status'] == 'found')}")
    logger.info(f"Not found: {sum(1 for r in results if r['status'] == 'not_found')}")
    logger.info(f"Errors: {sum(1 for r in results if r['status'] == 'error')}")
    logger.info(f"Saved to: {output_file}")
    logger.info(f"{'='*60}\n")
    
    return df


def main():
    """Main function"""
    
    print("Turkish Military Commanders Birthplace Scraper")
    print("=" * 60)
    print("\nWhich commanders would you like to scrape?")
    print("1. Naval Commanders (Deniz Kuvvetleri Komutanları)")
    print("2. Air Force Commanders (Hava Kuvvetleri Komutanları)")
    print("3. Both")
    
    choice = input("\nEnter your choice (1/2/3): ").strip()
    
    if choice == "1":
        scrape_commanders(
            NAVAL_COMMANDERS,
            "data/naval_commanders.csv",
            "Naval Commanders"
        )
    elif choice == "2":
        scrape_commanders(
            AIR_FORCE_COMMANDERS,
            "data/air_force_commanders.csv",
            "Air Force Commanders"
        )
    elif choice == "3":
        scrape_commanders(
            NAVAL_COMMANDERS,
            "data/naval_commanders.csv",
            "Naval Commanders"
        )
        print("\n" + "="*60 + "\n")
        scrape_commanders(
            AIR_FORCE_COMMANDERS,
            "data/air_force_commanders.csv",
            "Air Force Commanders"
        )
    else:
        print("Invalid choice. Exiting.")
        return
    
    print("\nScraping complete! Check the CSV files in the data/ directory.")


if __name__ == "__main__":
    main()
