"""
Turkish Military Chiefs of Staff Birthplace Analysis
Analyzes and visualizes birthplace distribution of Turkish military chiefs of staff during the Republic era.
"""

import pandas as pd
import folium
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

# Set style
sns.set_style("whitegrid")
plt.rcParams['figure.figsize'] = (12, 8)

# Load data
data_dir = Path(__file__).parent / 'data'
chiefs_df = pd.read_csv(data_dir / 'chiefs_of_staff.csv')
coords_df = pd.read_csv(data_dir / 'city_coordinates.csv')

# Merge data with coordinates
df = chiefs_df.merge(coords_df, left_on='birthplace', right_on='city', how='left')

# Calculate birthplace counts
birthplace_counts = df['birthplace'].value_counts()

print("=" * 60)
print("Turkish Military Chiefs of Staff Birthplace Analysis")
print("=" * 60)
print(f"\nTotal Chiefs of Staff: {len(df)}")
print(f"Unique Birthplaces: {df['birthplace'].nunique()}")
print("\nBirthplace Distribution:")
print(birthplace_counts.to_string())

# Create bar chart
plt.figure(figsize=(14, 8))
birthplace_counts.plot(kind='barh', color='steelblue')
plt.title('Distribution of Birthplaces - Turkish Military Chiefs of Staff', fontsize=16, fontweight='bold')
plt.xlabel('Number of Chiefs', fontsize=12)
plt.ylabel('Birthplace', fontsize=12)
plt.tight_layout()
plt.savefig('birthplace_distribution.png', dpi=300, bbox_inches='tight')
print("\n✓ Saved: birthplace_distribution.png")

# Create timeline by birthplace
plt.figure(figsize=(14, 8))
df['start_year'] = pd.to_datetime(df['start_date']).dt.year
for city in birthplace_counts.index[:10]:  # Top 10 cities
    city_data = df[df['birthplace'] == city]
    plt.scatter(city_data['start_year'], [city] * len(city_data), s=100, alpha=0.6, label=city)

plt.title('Timeline of Chiefs of Staff by Birthplace', fontsize=16, fontweight='bold')
plt.xlabel('Year Started Service', fontsize=12)
plt.ylabel('Birthplace', fontsize=12)
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('timeline_by_birthplace.png', dpi=300, bbox_inches='tight')
print("✓ Saved: timeline_by_birthplace.png")

# Create interactive map
print("\nCreating interactive map...")

# Calculate center of Turkey
turkey_center = [39.0, 35.0]

# Create base map with simpler style
m = folium.Map(
    location=turkey_center,
    zoom_start=6,
    tiles='CartoDB positron'  # Cleaner, more minimal map style
)

# Branch color mapping
branch_colors = {
    'Topçu': '#d62728',      # Red
    'Piyade': '#2ca02c',     # Green
    'Muhabere': '#ff7f0e',   # Orange
}

# Merge counts into dataframe
birthplace_data = birthplace_counts.reset_index()
birthplace_data.columns = ['birthplace', 'count']
map_data = coords_df.merge(birthplace_data, left_on='city', right_on='birthplace', how='inner')

for idx, row in map_data.iterrows():
    # Get chiefs from this location
    city_chiefs = df[df['birthplace'] == row['city']]
    chiefs_list = city_chiefs['name'].tolist()
    
    # Determine dominant branch
    branch_counts_city = city_chiefs['branch'].value_counts()
    dominant_branch = branch_counts_city.index[0]
    branch_color = branch_colors.get(dominant_branch, '#1f77b4')  # Default blue
    
    # Create popup text with branch info
    popup_text = f"""
    <div style="font-family: Arial; width: 280px;">
        <h4 style="margin-bottom: 10px; color: {branch_color};">{row['city']}</h4>
        <p><b>Number of Chiefs:</b> {row['count']}</p>
        <p><b>Dominant Branch:</b> {dominant_branch}</p>
        <p><b>Region:</b> {row['region']}</p>
        <p><b>Country:</b> {row['current_country']}</p>
        <hr>
        <p><b>Branch Distribution:</b></p>
        <ul style="margin: 5px 0; padding-left: 20px;">
    """
    
    for branch, count in branch_counts_city.items():
        popup_text += f"<li>{branch}: {count}</li>"
    
    popup_text += """
        </ul>
        <hr>
        <p><b>Chiefs from this city:</b></p>
        <ul style="margin: 5px 0; padding-left: 20px;">
    """
    
    for chief in chiefs_list:
        popup_text += f"<li>{chief}</li>"
    
    popup_text += """
        </ul>
    </div>
    """
    
    # Determine marker size based on count
    if row['count'] >= 5:
        radius = 18
    elif row['count'] >= 3:
        radius = 14
    elif row['count'] >= 2:
        radius = 11
    else:
        radius = 8
    
    folium.CircleMarker(
        location=[row['latitude'], row['longitude']],
        radius=radius,
        popup=folium.Popup(popup_text, max_width=320),
        color=branch_color,
        fill=True,
        fillColor=branch_color,
        fillOpacity=0.7,
        weight=2.5
    ).add_to(m)

# Add legend
legend_html = '''
<div style="position: fixed; 
     top: 10px; right: 10px; width: 220px; 
     background-color: white; z-index:9999; font-size:13px;
     border:2px solid grey; border-radius: 5px; padding: 12px;
     box-shadow: 0 2px 4px rgba(0,0,0,0.2);">
     <p style="margin: 0 0 8px 0; font-weight: bold; font-size: 14px;">Dominant Branch</p>
     <p style="margin: 5px 0;"><span style="color: #d62728; font-size: 18px;">●</span> Topçu (Artillery)</p>
     <p style="margin: 5px 0;"><span style="color: #2ca02c; font-size: 18px;">●</span> Piyade (Infantry)</p>
     <p style="margin: 5px 0;"><span style="color: #ff7f0e; font-size: 18px;">●</span> Muhabere (Signals)</p>
     <hr style="margin: 8px 0;">
     <p style="margin: 5px 0 0 0; font-size: 11px; color: #666;">
         Circle size = number of chiefs
     </p>
</div>
'''
m.get_root().html.add_child(folium.Element(legend_html))

# Save map
m.save('chiefs_birthplace_map.html')
print("✓ Saved: chiefs_birthplace_map.html")

print("\n" + "=" * 60)
print("Analysis complete! Generated files:")
print("  - birthplace_distribution.png")
print("  - timeline_by_birthplace.png")
print("  - chiefs_birthplace_map.html (open in browser)")
print("=" * 60)

# Regional distribution
print("\nRegional Distribution:")
regional_dist = df.groupby('region')['name'].count().sort_values(ascending=False)
print(regional_dist.to_string())

# Branch distribution by birthplace (top cities)
print("\nBranch Distribution in Top 5 Cities:")
top_5_cities = birthplace_counts.head(5).index
for city in top_5_cities:
    print(f"\n{city}:")
    city_branches = df[df['birthplace'] == city]['branch'].value_counts()
    print(city_branches.to_string())
