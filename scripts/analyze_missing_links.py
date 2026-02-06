#!/usr/bin/env python3
"""
Analyze missing Wikipedia links by unique people
"""

import sqlite3
from pathlib import Path

DB_PATH = Path("data/turkish_officials.db")

def is_person_page(url):
    """Check if a URL is a valid person page"""
    if not url or 'wikipedia.org' not in url:
        return False
    
    exclude_patterns = ['Dosya:', 'File:', 'listesi', '_list', 'genel_seçim', 
                       'milletvekil', 'dönem', 'Kategori:', 'Category:', 
                       'Vikipedi:', 'Wikipedia:']
    
    for pattern in exclude_patterns:
        if pattern in url:
            return False
    
    return True


conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# Get all tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = [row[0] for row in cursor.fetchall()]

print("=" * 90)
print("MISSING WIKIPEDIA LINKS ANALYSIS")
print("=" * 90)
print(f"\n{'POSITION':<40} {'TOTAL':<8} {'W/LINK':<8} {'UNIQUE':<8} {'NO LINK':<8} {'%UNIQUE':<8}")
print("-" * 90)

total_records = 0
total_with_links = 0
total_unique_with_links = 0
total_without_links = 0
missing_examples = {}

for table in sorted(tables):
    # For minister tables, only count records where Bakan column has data (not deputies)
    cursor.execute(f"PRAGMA table_info({table})")
    columns = [col[1] for col in cursor.fetchall()]
    
    bakan_filter = ""
    if 'Bakan' in columns and 'minister' in table.lower():
        bakan_filter = " AND Bakan IS NOT NULL AND Bakan != ''"
    elif 'Başbakan' in columns and table == 'prime_minister':
        # For prime minister, only count entries with parentheses containing years
        # Like "İsmet İnönü(1884–1973)" or "Recep Tayyip Erdoğan(1954–)"
        bakan_filter = """ AND Başbakan IS NOT NULL AND Başbakan != ''
            AND Başbakan LIKE '%(%'
            AND Başbakan LIKE '%)%'"""
    
    # Total records
    cursor.execute(f"SELECT COUNT(*) FROM {table} WHERE 1=1{bakan_filter}")
    record_count = cursor.fetchone()[0]
    
    # Records with any link
    cursor.execute(f"""
        SELECT COUNT(*) 
        FROM {table} 
        WHERE wikipedia_link IS NOT NULL AND wikipedia_link != ''
        {bakan_filter}
    """)
    with_link = cursor.fetchone()[0]
    
    # Get all links and filter for person pages
    cursor.execute(f"""
        SELECT DISTINCT wikipedia_link 
        FROM {table} 
        WHERE wikipedia_link IS NOT NULL AND wikipedia_link != ''
        {bakan_filter}
    """)
    links = [row[0] for row in cursor.fetchall()]
    person_links = [link for link in links if is_person_page(link)]
    unique_count = len(person_links)
    
    # Records without links
    without_link = record_count - with_link
    
    # Get an example of a missing link
    if without_link > 0:
        # Find the name column (try multiple columns in order, exclude deputies)
        if table == 'prime_minister':
            name_cols = ['Başbakan']
        else:
            name_cols = ['Bakan', 'Başkan', 'Komutan', 'Vali', 'Kurmay Başkanı']
        found_name = None
        
        for name_col in name_cols:
            if name_col in columns and not found_name:
                try:
                    extra_filter = ""
                    if name_col == 'Bakan' and 'minister' in table.lower():
                        extra_filter = bakan_filter
                    elif name_col == 'Başbakan':
                        extra_filter = bakan_filter
                    
                    filter_clause = extra_filter.replace(f'AND {name_col}', 'AND 1=1')
                    cursor.execute(f"""
                        SELECT "{name_col}"
                        FROM {table} 
                        WHERE (wikipedia_link IS NULL OR wikipedia_link = '')
                          {filter_clause}
                        LIMIT 1
                    """)
                    result = cursor.fetchone()
                    if result and result[0]:
                        found_name = result[0]
                        break
                except:
                    pass
        
        if found_name:
            missing_examples[table] = found_name
    
    # Calculate coverage
    coverage = (unique_count / record_count * 100) if record_count > 0 else 0
    
    total_records += record_count
    total_with_links += with_link
    total_unique_with_links += unique_count
    total_without_links += without_link
    
    table_name = table.replace('_', ' ').title()
    
    print(f"{table_name:<40} {record_count:<8} {with_link:<8} {unique_count:<8} {without_link:<8} {coverage:>6.1f}%")

print("=" * 90)
total_coverage = (total_unique_with_links / total_records * 100) if total_records > 0 else 0
print(f"{'TOTAL':<40} {total_records:<8} {total_with_links:<8} {total_unique_with_links:<8} {total_without_links:<8} {total_coverage:>6.1f}%")
print("=" * 90)

print(f"\n📊 SUMMARY:")
print(f"   Total appointments/records: {total_records}")
print(f"   Records with any Wikipedia link: {total_with_links}")
print(f"   Unique people with valid person pages: {total_unique_with_links}")
print(f"   Records without links: {total_without_links}")
print(f"\n💡 INTERPRETATION:")
print(f"   - We can scrape biographical info for {total_unique_with_links} unique individuals")
print(f"   - {total_without_links} records have no Wikipedia link")
print(f"   - Some of these {total_without_links} records may be:")
print(f"     • Duplicate terms by people already captured")
print(f"     • People without Wikipedia pages")
print(f"     • Errors in the original Wikipedia tables")
print(f"\n   - Best estimate: We have good coverage of prominent officials")

if missing_examples:
    print(f"\n📝 EXAMPLE NAMES WITHOUT LINKS (for spot checking):")
    for table, name in sorted(missing_examples.items()):
        table_name = table.replace('_', ' ').title()
        print(f"   • {table_name}: {name}")

conn.close()
print(f"     who are notable enough to have Wikipedia pages")
print("=" * 90 + "\n")

conn.close()
