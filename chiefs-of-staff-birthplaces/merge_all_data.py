#!/usr/bin/env python3
"""
Merge all commander data into a single CSV file
"""

import pandas as pd
import os

def main():
    data_dir = 'data'
    
    # Read all CSV files
    chiefs_df = pd.read_csv(os.path.join(data_dir, 'chiefs_of_staff.csv'))
    army_df = pd.read_csv(os.path.join(data_dir, 'army_commanders.csv'))
    naval_df = pd.read_csv(os.path.join(data_dir, 'naval_commanders.csv'))
    air_force_df = pd.read_csv(os.path.join(data_dir, 'air_force_commanders.csv'))
    
    # Standardize columns
    # Chiefs has: no, name, start_date, end_date, branch, birthplace
    # Army has: no, name, start_date, end_date, birthplace
    # Naval has: name, birthplace, start_year, end_year, status, url
    # Air Force has: name, birthplace, start_year, end_year, status, url
    
    # Add branch column to each
    chiefs_df['force'] = 'Chiefs'
    army_df['force'] = 'Army'
    naval_df['force'] = 'Navy'
    air_force_df['force'] = 'Air Force'
    
    # Standardize column names
    # For naval and air force, rename start_year/end_year to start_date/end_date
    naval_df = naval_df.rename(columns={'start_year': 'start_date', 'end_year': 'end_date'})
    air_force_df = air_force_df.rename(columns={'start_year': 'start_date', 'end_year': 'end_date'})
    
    # Select only the columns we need
    common_cols = ['name', 'birthplace', 'start_date', 'end_date', 'force']
    
    chiefs_df = chiefs_df[common_cols]
    army_df = army_df[common_cols]
    naval_df = naval_df[common_cols]
    air_force_df = air_force_df[common_cols]
    
    # Combine all dataframes
    merged_df = pd.concat([chiefs_df, army_df, naval_df, air_force_df], ignore_index=True)
    
    # Sort by force, then start_date
    merged_df['start_date'] = pd.to_datetime(merged_df['start_date'], errors='coerce')
    merged_df = merged_df.sort_values(['force', 'start_date'])
    
    # Convert dates back to string for CSV
    merged_df['start_date'] = merged_df['start_date'].dt.strftime('%Y-%m-%d')
    merged_df['start_date'] = merged_df['start_date'].replace('NaT', '')
    
    # Save merged file
    output_file = os.path.join(data_dir, 'all_commanders.csv')
    merged_df.to_csv(output_file, index=False, encoding='utf-8')
    
    # Print summary
    print("="*60)
    print("MERGED DATA SUMMARY")
    print("="*60)
    print(f"\nTotal commanders: {len(merged_df)}")
    print("\nBy force:")
    print(merged_df['force'].value_counts().to_string())
    print(f"\nWith birthplace data: {merged_df['birthplace'].notna().sum()}")
    print(f"Missing birthplace: {merged_df['birthplace'].isna().sum()}")
    print(f"\nSaved to: {output_file}")
    print("="*60)
    
    # Show sample
    print("\nSample of merged data:")
    print(merged_df.head(10).to_string(index=False))
    
    return merged_df

if __name__ == "__main__":
    main()
