#!/usr/bin/env python3
"""
Count unique people vs total records across all positions
"""

import sqlite3
from pathlib import Path

DB_PATH = Path("public/data/turkish_officials/turkish_officials.db")

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# Get all tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = [row[0] for row in cursor.fetchall()]

print("=" * 80)
print("UNIQUE PEOPLE VS TOTAL RECORDS")
print("=" * 80)
print(f"\n{'POSITION':<45} {'RECORDS':<10} {'UNIQUE':<10} {'DIFF':<10}")
print("-" * 80)

total_records = 0
total_unique = 0

for table in sorted(tables):
    # Count total and unique
    cursor.execute(f"SELECT COUNT(*) FROM {table}")
    record_count = cursor.fetchone()[0]
    
    cursor.execute(f"""
        SELECT COUNT(DISTINCT wikipedia_link) 
        FROM {table} 
        WHERE wikipedia_link IS NOT NULL AND wikipedia_link != ''
    """)
    unique_count = cursor.fetchone()[0]
    
    total_records += record_count
    total_unique += unique_count
    
    diff = record_count - unique_count
    table_name = table.replace('_', ' ').title()
    
    print(f"{table_name:<45} {record_count:<10} {unique_count:<10} {diff:<10}")

print("=" * 80)
print(f"{'TOTAL':<45} {total_records:<10} {total_unique:<10} {total_records - total_unique:<10}")
print("=" * 80)

print(f"\n📊 Summary:")
print(f"   Total records: {total_records}")
print(f"   Unique people (with links): {total_unique}")
print(f"   Duplicate appointments: {total_records - total_unique}")
print(f"\n   Many officials served in multiple governments or terms.")
print("=" * 80 + "\n")

conn.close()
