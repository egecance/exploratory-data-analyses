#!/usr/bin/env python3
"""
Check data completeness for age calculation across all tables
"""
import sqlite3
from pathlib import Path

DB_PATH = Path("data/turkish_officials.db")

def main():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Get all tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
    tables = [row[0] for row in cursor.fetchall()]
    
    print("=" * 100)
    print("DATA COMPLETENESS CHECK - Age Calculation Feasibility")
    print("=" * 100)
    print()
    print(f"{'TABLE':<40} {'TOTAL':<8} {'BIRTH':<8} {'START':<8} {'BOTH':<8} {'%BOTH'}")
    print("-" * 100)
    
    total_all = 0
    total_with_both = 0
    
    for table in sorted(tables):
        # Get column names
        cursor.execute(f"PRAGMA table_info({table})")
        columns = {row[1] for row in cursor.fetchall()}
        
        # Find date column (start date)
        date_col = None
        for col in columns:
            if 'başla' in col.lower() or 'başlangıç' in col.lower() or 'göreve başla' in col.lower():
                date_col = col
                break
        
        if not date_col:
            print(f"{table:<40} {'N/A':<8} {'N/A':<8} {'N/A':<8} {'N/A':<8} No start date column")
            continue
        
        # Count records
        query = f"""
        SELECT 
            COUNT(*) as total,
            SUM(CASE WHEN birth_year IS NOT NULL AND birth_year != '' AND birth_year != '?' THEN 1 ELSE 0 END) as with_birth,
            SUM(CASE WHEN "{date_col}" IS NOT NULL AND "{date_col}" != '' THEN 1 ELSE 0 END) as with_date,
            SUM(CASE WHEN birth_year IS NOT NULL AND birth_year != '' AND birth_year != '?' 
                     AND "{date_col}" IS NOT NULL AND "{date_col}" != '' THEN 1 ELSE 0 END) as with_both
        FROM {table}
        """
        
        try:
            cursor.execute(query)
            total, with_birth, with_date, with_both = cursor.fetchone()
            
            if total > 0:
                pct = (with_both / total * 100) if total > 0 else 0
                print(f"{table:<40} {total:<8} {with_birth:<8} {with_date:<8} {with_both:<8} {pct:5.1f}%")
                total_all += total
                total_with_both += with_both
        except Exception as e:
            print(f"{table:<40} ERROR: {str(e)[:50]}")
    
    print("-" * 100)
    overall_pct = (total_with_both / total_all * 100) if total_all > 0 else 0
    print(f"{'TOTAL':<40} {total_all:<8} {'':<8} {'':<8} {total_with_both:<8} {overall_pct:5.1f}%")
    print()
    print("=" * 100)
    print("SUMMARY")
    print("=" * 100)
    print(f"Total records: {total_all}")
    print(f"Records with both birth year and start date: {total_with_both}")
    print(f"Completeness: {overall_pct:.1f}%")
    print()
    
    if overall_pct >= 70:
        print("✅ SUFFICIENT DATA - We can calculate average age at appointment for most positions")
    elif overall_pct >= 50:
        print("⚠️  MODERATE DATA - Age calculations possible but with some gaps")
    else:
        print("❌ INSUFFICIENT DATA - Too many missing values for reliable age calculations")
    
    conn.close()

if __name__ == '__main__':
    main()
