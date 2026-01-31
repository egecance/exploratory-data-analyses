"""
Turkish Military Chiefs of Staff Birthplace Analysis
Analyzes and visualizes birthplace distribution of Turkish military chiefs of staff during the Republic era.
"""

import pandas as pd
import folium
from folium.plugins import MarkerCluster
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

# Create base map
m = folium.Map(
    location=turkey_center,
    zoom_start=6,
    tiles='OpenStreetMap'
)

# Add birthplace markers with clusters
marker_cluster = MarkerCluster().add_to(m)

# Merge counts into dataframe
birthplace_data = birthplace_counts.reset_index()
birthplace_data.columns = ['birthplace', 'count']
map_data = coords_df.merge(birthplace_data, left_on='city', right_on='birthplace', how='inner')

for idx, row in map_data.iterrows():
    # Get chiefs from this location
    chiefs_from_city = df[df['birthplace'] == row['city']]['name'].tolist()
    
    # Create popup text
    popup_text = f"""
    <div style="font-family: Arial; width: 250px;">
        <h4 style="margin-bottom: 10px;">{row['city']}</h4>
        <p><b>Number of Chiefs:</b> {row['count']}</p>
        <p><b>Region:</b> {row['region']}</p>
        <p><b>Country:</b> {row['current_country']}</p>
        <hr>
        <p><b>Chiefs from this city:</b></p>
        <ul style="margin: 5px 0; padding-left: 20px;">
    """
    
    for chief in chiefs_from_city:
        popup_text += f"<li>{chief}</li>"
    
    popup_text += """
        </ul>
    </div>
    """
    
    # Determine marker size and color based on count
    if row['count'] >= 5:
        color = 'red'
        radius = 15
    elif row['count'] >= 3:
        color = 'orange'
        radius = 12
    elif row['count'] >= 2:
        color = 'blue'
        radius = 10
    else:
        color = 'green'
        radius = 8
    
    folium.CircleMarker(
        location=[row['latitude'], row['longitude']],
        radius=radius,
        popup=folium.Popup(popup_text, max_width=300),
        color=color,
        fill=True,
        fillColor=color,
        fillOpacity=0.7,
        weight=2
    ).add_to(marker_cluster)

# Add legend
legend_html = '''
<div style="position: fixed; 
     top: 10px; right: 10px; width: 200px; 
     background-color: white; z-index:9999; font-size:14px;
     border:2px solid grey; border-radius: 5px; padding: 10px">
     <p style="margin: 0; font-weight: bold;">Number of Chiefs:</p>
     <p style="margin: 5px 0;"><span style="color: red;">●</span> 5 or more</p>
     <p style="margin: 5px 0;"><span style="color: orange;">●</span> 3-4</p>
     <p style="margin: 5px 0;"><span style="color: blue;">●</span> 2</p>
     <p style="margin: 5px 0;"><span style="color: green;">●</span> 1</p>
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
