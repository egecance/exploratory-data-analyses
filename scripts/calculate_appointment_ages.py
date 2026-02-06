#!/usr/bin/env python3
"""
Calculate average age at appointment for Turkish officials
"""
import sqlite3
import re
from pathlib import Path
from collections import defaultdict

DB_PATH = Path("data/turkish_officials.db")

# Turkish month names to numbers
TURKISH_MONTHS = {
    'ocak': 1, 'şubat': 2, 'mart': 3, 'nisan': 4, 'mayıs': 5, 'haziran': 6,
    'temmuz': 7, 'ağustos': 8, 'eylül': 9, 'ekim': 10, 'kasım': 11, 'aralık': 12
}

def extract_year_from_date(date_str: str) -> int:
    """Extract year from Turkish date format"""
    if not date_str or date_str.strip() == '':
        return None
    
    # Try to find 4-digit year
    year_match = re.search(r'\b(19\d{2}|20\d{2})\b', date_str)
    if year_match:
        return int(year_match.group(1))
    
    return None


def calculate_ages_for_table(conn: sqlite3.Connection, table_name: str) -> list:
    """Calculate ages at appointment for a table"""
    cursor = conn.cursor()
    
    # Get column names
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = {row[1] for row in cursor.fetchall()}
    
    # Find start date column
    date_col = None
    for col in columns:
        if 'başla' in col.lower() or 'başlangıç' in col.lower():
            date_col = col
            break
    
    if not date_col:
        return []
    
    # Get data
    query = f"""
    SELECT birth_year, "{date_col}"
    FROM {table_name}
    WHERE birth_year IS NOT NULL 
      AND birth_year != '' 
      AND birth_year != '?'
      AND "{date_col}" IS NOT NULL 
      AND "{date_col}" != ''
    """
    
    cursor.execute(query)
    ages = []
    
    for birth_year_str, start_date in cursor.fetchall():
        try:
            birth_year = int(birth_year_str)
            start_year = extract_year_from_date(start_date)
            
            if start_year and birth_year:
                age = start_year - birth_year
                # Sanity check: age should be between 18 and 100
                if 18 <= age <= 100:
                    ages.append(age)
        except:
            pass
    
    return ages


def main():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Get all tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
    tables = [row[0] for row in cursor.fetchall()]
    
    print("=" * 90)
    print("AVERAGE AGE AT APPOINTMENT BY POSITION")
    print("=" * 90)
    print()
    print(f"{'POSITION':<45} {'N':<6} {'MIN':<6} {'AVG':<6} {'MAX':<6} {'MEDIAN'}")
    print("-" * 90)
    
    all_results = []
    
    for table in sorted(tables):
        ages = calculate_ages_for_table(conn, table)
        
        if ages:
            n = len(ages)
            min_age = min(ages)
            max_age = max(ages)
            avg_age = sum(ages) / len(ages)
            median_age = sorted(ages)[len(ages) // 2]
            
            position_name = table.replace('_', ' ').title()
            print(f"{position_name:<45} {n:<6} {min_age:<6} {avg_age:<6.1f} {max_age:<6} {median_age}")
            
            all_results.append({
                'position': position_name,
                'n': n,
                'avg': avg_age,
                'ages': ages
            })
    
    print("-" * 90)
    
    # Overall statistics
    all_ages = []
    for result in all_results:
        all_ages.extend(result['ages'])
    
    if all_ages:
        overall_avg = sum(all_ages) / len(all_ages)
        overall_median = sorted(all_ages)[len(all_ages) // 2]
        print(f"{'OVERALL':<45} {len(all_ages):<6} {min(all_ages):<6} {overall_avg:<6.1f} {max(all_ages):<6} {overall_median}")
    
    print()
    print("=" * 90)
    print("KEY INSIGHTS")
    print("=" * 90)
    
    # Sort by average age
    all_results.sort(key=lambda x: x['avg'])
    
    print(f"\n📊 Youngest at appointment:")
    for i, result in enumerate(all_results[:3], 1):
        print(f"   {i}. {result['position']}: {result['avg']:.1f} years (n={result['n']})")
    
    print(f"\n📊 Oldest at appointment:")
    for i, result in enumerate(all_results[-3:], 1):
        print(f"   {i}. {result['position']}: {result['avg']:.1f} years (n={result['n']})")
    
    print(f"\n📊 Overall average age at appointment: {overall_avg:.1f} years")
    print(f"📊 Range: {min(all_ages)} to {max(all_ages)} years")
    print(f"📊 Total appointments analyzed: {len(all_ages)}")
    print()
    
    conn.close()


if __name__ == '__main__':
    main()
