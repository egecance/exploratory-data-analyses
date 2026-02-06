#!/usr/bin/env python3
"""
Count truly unique people across ALL positions
(since one person may have held multiple different positions)
"""

import sqlite3
from pathlib import Path

DB_PATH = Path("public/data/turkish_officials/turkish_officials.db")

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

print("=" * 80)
print("CROSS-POSITION UNIQUE PEOPLE ANALYSIS")
print("=" * 80)

# Collect ALL Wikipedia links across all tables
all_links = set()
person_links = set()

position_data = []

for table in tables:
    cursor.execute(f"""
        SELECT DISTINCT wikipedia_link 
        FROM {table} 
        WHERE wikipedia_link IS NOT NULL AND wikipedia_link != ''
    """)
    links = [row[0] for row in cursor.fetchall()]
    
    valid_person_links = [link for link in links if is_person_page(link)]
    
    all_links.update(links)
    person_links.update(valid_person_links)
    
    position_data.append({
        'name': table.replace('_', ' ').title(),
        'unique_people': len(valid_person_links)
    })

print("\n📊 UNIQUE PEOPLE BY POSITION:")
print("-" * 80)
for item in sorted(position_data, key=lambda x: x['unique_people'], reverse=True):
    print(f"  {item['name']:<45} {item['unique_people']:>4} people")

print("\n" + "=" * 80)
print("CROSS-POSITION ANALYSIS")
print("=" * 80)

# Now check for people who held multiple positions
people_positions = {}

for table in tables:
    cursor.execute(f"""
        SELECT DISTINCT wikipedia_link 
        FROM {table} 
        WHERE wikipedia_link IS NOT NULL AND wikipedia_link != ''
    """)
    links = [row[0] for row in cursor.fetchall()]
    valid_links = [link for link in links if is_person_page(link)]
    
    for link in valid_links:
        if link not in people_positions:
            people_positions[link] = []
        people_positions[link].append(table.replace('_', ' ').title())

# Count people by number of positions held
position_counts = {}
for person, positions in people_positions.items():
    count = len(positions)
    if count not in position_counts:
        position_counts[count] = []
    position_counts[count].append((person, positions))

print(f"\nTotal unique people across ALL positions: {len(person_links)}")
print(f"Total Wikipedia links collected: {len(all_links)}")
print(f"Valid person pages: {len(person_links)}")

print("\n" + "-" * 80)
print("PEOPLE BY NUMBER OF POSITIONS HELD:")
print("-" * 80)

for num_positions in sorted(position_counts.keys(), reverse=True):
    people = position_counts[num_positions]
    print(f"\n{len(people)} people held {num_positions} position(s):")
    
    if num_positions > 1:
        # Show examples of people with multiple positions
        for i, (link, positions) in enumerate(people[:5], 1):
            name = link.split('/')[-1].replace('_', ' ')
            print(f"  {i}. {name[:40]:<40} → {', '.join(positions)}")
        if len(people) > 5:
            print(f"  ... and {len(people) - 5} more")

print("\n" + "=" * 80)
print("FINAL SUMMARY")
print("=" * 80)
print(f"\n  Total appointments/records across all positions: 924")
print(f"  Sum of unique people per position: {sum(item['unique_people'] for item in position_data)}")
print(f"  Actual unique individuals (cross-position): {len(person_links)}")
print(f"  \n  ➜ {sum(item['unique_people'] for item in position_data) - len(person_links)} people held multiple different positions")
print(f"  ➜ We can scrape biographical info for {len(person_links)} unique individuals")

# Calculate missing
total_records = 924
cursor.execute("SELECT COUNT(DISTINCT wikipedia_link) FROM (" + 
               " UNION ALL ".join([f"SELECT wikipedia_link FROM {table}" for table in tables]) + 
               ") WHERE wikipedia_link IS NOT NULL AND wikipedia_link != ''")
total_with_some_link = cursor.fetchone()[0]

print(f"\n  Records with no Wikipedia link: {924 - total_with_some_link}")
print(f"  Coverage: {len(person_links)/924*100:.1f}% of all appointments")

print("\n" + "=" * 80 + "\n")

conn.close()
