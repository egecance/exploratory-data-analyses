#!/usr/bin/env python3
"""
Query and explore the scraped Turkish officials data
"""

import sqlite3
import pandas as pd
from pathlib import Path

DB_PATH = Path("public/data/turkish_officials/turkish_officials.db")


def list_tables():
    """List all tables in the database"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    conn.close()
    return [table[0] for table in tables]


def query_table(table_name: str, limit: int = None):
    """Query a specific table"""
    conn = sqlite3.connect(DB_PATH)
    query = f"SELECT * FROM {table_name}"
    if limit:
        query += f" LIMIT {limit}"
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df


def search_by_name(name: str):
    """Search for a person by name across all positions"""
    conn = sqlite3.connect(DB_PATH)
    # Try to find name in any column
    query = """
    SELECT * FROM all_officials 
    WHERE LOWER(CAST(rowid AS TEXT) || ' ' || 
    COALESCE((SELECT group_concat(quote(value)) FROM json_each(all_officials.* )), ''))
    LIKE ?
    """
    df = pd.read_sql_query(
        "SELECT * FROM all_officials",
        conn
    )
    conn.close()
    
    # Filter by name
    mask = df.apply(lambda row: name.lower() in str(row.values).lower(), axis=1)
    return df[mask]


def get_stats():
    """Get statistics about the database"""
    conn = sqlite3.connect(DB_PATH)
    
    stats = {}
    for table in list_tables():
        cursor = conn.cursor()
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        count = cursor.fetchone()[0]
        stats[table] = count
    
    conn.close()
    return stats


def main():
    """Interactive exploration"""
    print("=" * 70)
    print("Turkish Officials Database Explorer")
    print("=" * 70)
    
    if not DB_PATH.exists():
        print(f"\n❌ Database not found at {DB_PATH}")
        print("Please run scrape_turkish_officials.py first.")
        return
    
    # Show tables
    print("\n📊 Available tables:")
    print("-" * 70)
    tables = list_tables()
    for i, table in enumerate(tables, 1):
        print(f"{i}. {table}")
    
    # Show statistics
    print("\n📈 Record counts:")
    print("-" * 70)
    stats = get_stats()
    for table, count in stats.items():
        print(f"{table:.<50} {count:>5} records")
    
    # Show sample from combined table
    print("\n📋 Sample data (first 5 records from all_officials):")
    print("-" * 70)
    if 'all_officials' in tables:
        df = query_table('all_officials', limit=5)
        print(df.to_string())
    
    print("\n" + "=" * 70)
    print("To query the database, use:")
    print("  python -c 'import query_officials; print(query_officials.query_table(\"TABLE_NAME\"))'")
    print("Or use SQLite directly:")
    print(f"  sqlite3 {DB_PATH}")
    print("=" * 70)


if __name__ == "__main__":
    main()
