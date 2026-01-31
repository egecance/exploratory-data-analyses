import pandas as pd

# Manual updates from Wikipedia category pages
naval_updates = {
    "Mehmet Ali Ülgen": "İstanbul",
    "Sadık Altıncan": "İstanbul", 
    "Necdet Uran": "İstanbul",
    "Hilmi Fırat": "İstanbul",
    "İrfan Tınaz": "İstanbul"
}

# Read CSV
df = pd.read_csv('data/naval_commanders.csv')

# Update birthplaces
for name, birthplace in naval_updates.items():
    df.loc[df['name'] == name, 'birthplace'] = birthplace
    df.loc[df['name'] == name, 'status'] = 'found'

# Save
df.to_csv('data/naval_commanders.csv', index=False)

print("Naval commanders updated!")
print(f"Remaining not_found: {df[df['status'] == 'not_found'].shape[0]}")
print("\nRemaining commanders:")
print(df[df['status'] == 'not_found'][['name', 'start_year', 'end_year']])
