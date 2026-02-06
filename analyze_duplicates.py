import pandas as pd

df = pd.read_csv('public/data/turkish_officials/prime_minister.csv')

print("ALL COLUMNS IN PRIME MINISTER CSV:")
print("=" * 70)
for i, col in enumerate(df.columns, 1):
    print(f"{i:2d}. {col}")

print("\n" + "=" * 70)
print("GÖREV-RELATED COLUMNS WITH SAMPLE DATA:")
print("=" * 70)

gorev_cols = [col for col in df.columns if 'görev' in col.lower()]
if gorev_cols:
    print(f"\nFound {len(gorev_cols)} görev-related columns:\n")
    for col in gorev_cols:
        print(f"  • {col}")
    print("\nSample data (first 5 rows):\n")
    for idx in range(min(5, len(df))):
        print(f"Row {idx}:")
        for col in gorev_cols:
            val = df[col].iloc[idx]
            if pd.notna(val) and str(val).strip():
                print(f"  {col}: {val}")
        print()
        
print("\n" + "=" * 70)
print("CHECKING FOR EXACT DUPLICATES:")
print("=" * 70)
cols_list = df.columns.tolist()
duplicates = {}
for col in cols_list:
    count = cols_list.count(col)
    if count > 1 and col not in duplicates:
        duplicates[col] = count
        
if duplicates:
    for col, count in duplicates.items():
        print(f"  '{col}' appears {count} times")
else:
    print("  ✓ No exact duplicate column names in CSV")
