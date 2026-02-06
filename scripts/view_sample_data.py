#!/usr/bin/env python3
"""Display first 10 entries from each table in readable format"""

import sqlite3
import pandas as pd
from pathlib import Path

DB_PATH = Path("data/turkish_officials.db")

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# Get all tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = [row[0] for row in cursor.fetchall()]

for table in sorted(tables):
    print(f"\n{'='*100}")
    print(f"TABLE: {table.replace('_', ' ').upper()}")
    print(f"{'='*100}\n")
    
    # Special handling for prime_minister table - only show entries with proper names
    if table == 'prime_minister':
        query = """
        SELECT Başbakan, wikipedia_link, "Göreve Başlama", "Görevden Ayrılma", Parti 
        FROM prime_minister 
        WHERE Başbakan IS NOT NULL 
        AND Başbakan != '' 
        AND Başbakan LIKE '%(%'
        AND Başbakan LIKE '%)%'
        LIMIT 10
        """
        df = pd.read_sql_query(query, conn)
    else:
        # Read first 10 rows
        df = pd.read_sql_query(f"SELECT * FROM {table} LIMIT 10", conn)
        
        # Display only key columns for readability
        key_columns = []
        for col in df.columns:
            if any(keyword in col.lower() for keyword in ['bakan', 'başkan', 'komutan', 'wikipedia', 'görev', 'parti', 'başlangıç', 'bitişi']):
                key_columns.append(col)
        
        if key_columns:
            df = df[key_columns]
        else:
            # If no key columns found, show first 5 columns
            df = df.iloc[:, :min(5, len(df.columns))]
    
    # Set display options for better formatting
    pd.set_option('display.max_columns', None)
    pd.set_option('display.width', None)
    pd.set_option('display.max_colwidth', 50)
    
    print(df.to_string(index=False))
    print(f"\nTotal rows in table: {len(pd.read_sql_query(f'SELECT * FROM {table}', conn))}")

conn.close()
