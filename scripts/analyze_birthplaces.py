#!/usr/bin/env python3
"""
Analyze birthplace statistics from Turkish officials database
"""
import sqlite3
import re
from pathlib import Path
from collections import Counter
from typing import Dict, List, Tuple

DB_PATH = Path("data/turkish_officials.db")

def clean_city_name(birthplace: str) -> str:
    """Extract the main city from birthplace string"""
    if not birthplace or birthplace == '?':
        return 'Unknown'
    
    # Remove common suffixes
    place = re.sub(r',\s*(Türkiye|Osmanlı İmparatorluğu|Osmanlı Devleti|Osmanlı|Turkey).*$', '', birthplace)
    
    # Split by comma and take the last significant part (usually the city)
    parts = [p.strip() for p in place.split(',')]
    
    # If multiple parts, try to get the city (usually second to last or last)
    if len(parts) >= 2:
        city = parts[-1].strip()
        # Check if it's a province/country name, if so take the district before it
        if city in ['Türkiye', 'Turkey', 'Osmanlı', 'İmparatorluğu', 'Devleti', 'Makedonya', 
                    'Yunanistan', 'Bosna', 'Bulgaristan', 'Mısır', 'Suriye']:
            if len(parts) >= 2:
                city = parts[-2].strip()
        return city
    
    return parts[0].strip() if parts else 'Unknown'


def get_table_stats(conn: sqlite3.Connection, table_name: str) -> List[Tuple[str, int]]:
    """Get top 5 cities for a specific table"""
    query = f"SELECT birth_place FROM {table_name} WHERE birth_place IS NOT NULL AND birth_place != ''"
    
    cursor = conn.cursor()
    cursor.execute(query)
    
    cities = Counter()
    for row in cursor.fetchall():
        birthplace = row[0]
        city = clean_city_name(birthplace)
        cities[city] += 1
    
    return cities.most_common(5)


def get_all_stats(conn: sqlite3.Connection) -> List[Tuple[str, int]]:
    """Get combined statistics across all tables"""
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
    tables = [row[0] for row in cursor.fetchall()]
    
    all_cities = Counter()
    
    for table in tables:
        try:
            cursor.execute(f"SELECT birth_place FROM {table} WHERE birth_place IS NOT NULL AND birth_place != ''")
            for row in cursor.fetchall():
                birthplace = row[0]
                city = clean_city_name(birthplace)
                all_cities[city] += 1
        except:
            pass
    
    return all_cities.most_common()


def main():
    conn = sqlite3.connect(DB_PATH)
    
    # Get list of all tables
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
    tables = [row[0] for row in cursor.fetchall()]
    
    print("=" * 80)
    print("BIRTHPLACE STATISTICS - TOP 5 CITIES PER POSITION")
    print("=" * 80)
    print()
    
    # Stats per table
    for table in tables:
        try:
            top_cities = get_table_stats(conn, table)
            if top_cities:
                print(f"📍 {table.replace('_', ' ').title()}")
                for i, (city, count) in enumerate(top_cities, 1):
                    print(f"   {i}. {city:30s} {count:3d} people")
                print()
        except Exception as e:
            print(f"   ⚠️  Error processing {table}: {e}")
            print()
    
    print("=" * 80)
    print("COMBINED STATISTICS - ALL POSITIONS")
    print("=" * 80)
    print()
    
    all_stats = get_all_stats(conn)
    print(f"Total unique cities: {len(all_stats)}")
    print()
    print("Rank  City                           People")
    print("-" * 50)
    for i, (city, count) in enumerate(all_stats[:30], 1):
        print(f"{i:4d}. {city:30s} {count:4d}")
    
    print()
    print(f"... and {len(all_stats) - 30} more cities")
    print()
    
    # Some interesting stats
    total_people = sum(count for _, count in all_stats)
    istanbul_count = next((count for city, count in all_stats if city == 'İstanbul'), 0)
    ankara_count = next((count for city, count in all_stats if city == 'Ankara'), 0)
    
    print("=" * 80)
    print("KEY INSIGHTS")
    print("=" * 80)
    print(f"Total people with birthplace data: {total_people}")
    print(f"İstanbul-born officials: {istanbul_count} ({istanbul_count/total_people*100:.1f}%)")
    print(f"Ankara-born officials: {ankara_count} ({ankara_count/total_people*100:.1f}%)")
    print(f"Top 2 cities combined: {istanbul_count + ankara_count} ({(istanbul_count + ankara_count)/total_people*100:.1f}%)")
    print()
    
    conn.close()


if __name__ == '__main__':
    main()
