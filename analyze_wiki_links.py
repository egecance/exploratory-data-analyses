#!/usr/bin/env python3
"""
Analyze how many people have valid personal Wikipedia page links
"""

import sqlite3
from pathlib import Path

DB_PATH = Path("public/data/turkish_officials/turkish_officials.db")

def is_person_page(url):
    """Check if a URL is likely a person page (not a list, file, election, etc.)"""
    if not url or 'wikipedia.org' not in url:
        return False
    
    # Exclude non-person pages
    exclude_patterns = [
        'Dosya:',           # Files
        'File:',
        'listesi',          # Lists
        '_list',
        'genel_seçim',      # Elections
        'milletvekil',      # MP lists
        'dönem',            # Parliamentary terms
        'Kategori:',        # Categories
        'Category:',
        'Vikipedi:',        # Wikipedia namespace
        'Wikipedia:',
    ]
    
    for pattern in exclude_patterns:
        if pattern in url:
            return False
    
    return True


conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# Get all tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = [row[0] for row in cursor.fetchall()]

print("=" * 80)
print("WIKIPEDIA PERSON PAGE ANALYSIS")
print("=" * 80)

total_records = 0
total_with_links = 0
total_person_pages = 0
details = []

for table in tables:
    # Count total records
    cursor.execute(f"SELECT COUNT(*) FROM {table}")
    table_count = cursor.fetchone()[0]
    total_records += table_count
    
    # Find wikipedia_link column
    cursor.execute(f"PRAGMA table_info({table})")
    columns = [row[1] for row in cursor.fetchall()]
    
    link_col = None
    for col in columns:
        if 'wikipedia_link' in col.lower():
            link_col = col
            break
    
    if not link_col:
        details.append({
            'table': table,
            'total': table_count,
            'with_links': 0,
            'person_pages': 0
        })
        continue
    
    # Get all links
    cursor.execute(f'SELECT "{link_col}" FROM {table}')
    links = [row[0] for row in cursor.fetchall() if row[0]]
    
    # Count person pages
    person_links = [url for url in links if is_person_page(url)]
    
    total_with_links += len(links)
    total_person_pages += len(person_links)
    
    details.append({
        'table': table,
        'total': table_count,
        'with_links': len(links),
        'person_pages': len(person_links)
    })

conn.close()

# Print results
print(f"\n{'POSITION':<45} {'TOTAL':<8} {'LINKS':<8} {'PERSON':<8} {'%':<8}")
print("-" * 80)

for item in sorted(details, key=lambda x: x['person_pages'], reverse=True):
    table_name = item['table'].replace('_', ' ').title()
    pct = (item['person_pages'] / item['total'] * 100) if item['total'] > 0 else 0
    print(f"{table_name:<45} {item['total']:<8} {item['with_links']:<8} {item['person_pages']:<8} {pct:>6.1f}%")

print("=" * 80)
print(f"{'TOTAL':<45} {total_records:<8} {total_with_links:<8} {total_person_pages:<8} {(total_person_pages/total_records*100):>6.1f}%")
print("=" * 80)

print(f"\n📊 SUMMARY:")
print(f"   Total records: {total_records}")
print(f"   Records with any Wikipedia link: {total_with_links} ({total_with_links/total_records*100:.1f}%)")
print(f"   Records with person page links: {total_person_pages} ({total_person_pages/total_records*100:.1f}%)")
print(f"   Missing person pages: {total_records - total_person_pages}")

if total_person_pages > 0:
    print(f"\n✅ We can scrape biographical info for {total_person_pages} people")
else:
    print(f"\n⚠️  No valid person page links found. The scraper may need adjustment.")

print("=" * 80 + "\n")
