#!/usr/bin/env python3
"""
Generate summary statistics for scraped Turkish officials data
"""

import sqlite3
import pandas as pd
from pathlib import Path

DB_PATH = Path("public/data/turkish_officials/turkish_officials.db")

def get_table_stats():
    """Get statistics for each table"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Get all table names
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [row[0] for row in cursor.fetchall()]
    
    stats = []
    for table in tables:
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        count = cursor.fetchone()[0]
        
        # Get a sample name column to understand structure
        cursor.execute(f"PRAGMA table_info({table})")
        columns = [row[1] for row in cursor.fetchall()]
        
        stats.append({
            'Position': table.replace('_', ' ').title(),
            'Records': count,
            'Table Name': table
        })
    
    conn.close()
    return pd.DataFrame(stats).sort_values('Records', ascending=False)


def count_unique_people():
    """Try to count unique people across all positions"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Get all table names
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [row[0] for row in cursor.fetchall()]
    
    all_names = set()
    position_names = {}
    
    for table in tables:
        # Try to find name columns (varies by table)
        df = pd.read_sql_query(f"SELECT * FROM {table}", conn)
        
        # Look for likely name columns
        name_candidates = []
        for col in df.columns:
            col_lower = col.lower()
            if any(keyword in col_lower for keyword in ['başkan', 'bakan', 'komutan', 'isim', 'ad', 'adı']):
                name_candidates.append(col)
        
        # Extract names from the most promising column
        if name_candidates:
            for col in name_candidates:
                names = df[col].dropna().astype(str)
                # Clean names (remove years, extra info)
                clean_names = names.str.replace(r'\(.*?\)', '', regex=True).str.strip()
                clean_names = clean_names[clean_names.str.len() > 3]  # Filter out very short entries
                
                position_names[table] = set(clean_names)
                all_names.update(clean_names)
    
    conn.close()
    return len(all_names), position_names


def main():
    print("\n" + "=" * 80)
    print("TURKISH GOVERNMENT OFFICIALS - DATA SUMMARY")
    print("=" * 80)
    
    # Table statistics
    stats_df = get_table_stats()
    
    print("\n📊 RECORDS BY POSITION:")
    print("-" * 80)
    print(stats_df[['Position', 'Records']].to_string(index=False))
    
    print("\n" + "-" * 80)
    print(f"{'TOTAL RECORDS:':<50} {stats_df['Records'].sum():>10}")
    print(f"{'NUMBER OF POSITIONS:':<50} {len(stats_df):>10}")
    
    # Try to count unique people
    print("\n" + "=" * 80)
    print("👥 UNIQUE PEOPLE ANALYSIS:")
    print("-" * 80)
    
    try:
        unique_count, position_names = count_unique_people()
        print(f"\nEstimated unique individuals across all positions: ~{unique_count}")
        print("\nNote: This is an estimate based on name extraction.")
        print("Some individuals may have held multiple positions.")
    except Exception as e:
        print(f"Could not estimate unique people count: {e}")
    
    print("\n" + "=" * 80)
    print("\n📁 Data Location:")
    print(f"   Database: {DB_PATH.absolute()}")
    print(f"   CSV files: {DB_PATH.parent.absolute()}/")
    print("\n" + "=" * 80 + "\n")


if __name__ == "__main__":
    main()
