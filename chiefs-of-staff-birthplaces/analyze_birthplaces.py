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
    tiles='CartoDB positron'
)

# Military green color scale based on number of chiefs
def get_military_green(count):
    """Return military green shade based on count"""
    if count >= 7:
        return '#2d3a1a'  # Darkest
    elif count >= 5:
        return '#3d4a2a'  # Dark
    elif count >= 3:
        return '#4b5320'  # Base military green
    elif count >= 2:
        return '#697843'  # Medium
    elif count >= 1:
        return '#8a9a5b'  # Light
    else:
        return '#e8e8e8'  # Light grey for cities with no chiefs

# Major Turkish cities for background
all_major_cities = [
    {'city': 'İstanbul', 'lat': 41.0082, 'lon': 28.9784},
    {'city': 'Ankara', 'lat': 39.9334, 'lon': 32.8597},
    {'city': 'İzmir', 'lat': 38.4192, 'lon': 27.1287},
    {'city': 'Bursa', 'lat': 40.1826, 'lon': 29.0665},
    {'city': 'Antalya', 'lat': 36.8969, 'lon': 30.7133},
    {'city': 'Adana', 'lat': 37.0000, 'lon': 35.3213},
    {'city': 'Konya', 'lat': 37.8746, 'lon': 32.4932},
    {'city': 'Gaziantep', 'lat': 37.0662, 'lon': 37.3833},
    {'city': 'Diyarbakır', 'lat': 37.9144, 'lon': 40.2306},
    {'city': 'Kayseri', 'lat': 38.7205, 'lon': 35.4826},
    {'city': 'Eskişehir', 'lat': 39.7767, 'lon': 30.5206},
    {'city': 'Samsun', 'lat': 41.2867, 'lon': 36.3300},
    {'city': 'Trabzon', 'lat': 41.0015, 'lon': 39.7178},
    {'city': 'Erzurum', 'lat': 39.9208, 'lon': 41.2675},
    {'city': 'Van', 'lat': 38.4891, 'lon': 43.4089},
    {'city': 'Edirne', 'lat': 41.6771, 'lon': 26.5557},
    {'city': 'Erzincan', 'lat': 39.7500, 'lon': 39.5000},
    {'city': 'Alaşehir', 'lat': 38.3508, 'lon': 28.5169},
    {'city': 'Burdur', 'lat': 37.7261, 'lon': 30.2889},
    {'city': 'Elazığ', 'lat': 38.6748, 'lon': 39.2228},
    {'city': 'Afyonkarahisar', 'lat': 38.7507, 'lon': 30.5567},
    {'city': 'Kastamonu', 'lat': 41.3887, 'lon': 33.7827},
    {'city': 'Selanik', 'lat': 40.6401, 'lon': 22.9444},
]

# Create a count dictionary
city_counts = birthplace_counts.to_dict()

# Draw all cities
for city_info in all_major_cities:
    city_name = city_info['city']
    count = city_counts.get(city_name, 0)
    color = get_military_green(count)
    
    # Determine radius based on count
    if count >= 5:
        radius = 35000  # meters
    elif count >= 3:
        radius = 28000
    elif count >= 2:
        radius = 22000
    elif count >= 1:
        radius = 18000
    else:
        radius = 15000  # Grey cities
    
    # Create popup
    if count > 0:
        city_chiefs = df[df['birthplace'] == city_name]
        chiefs_list = city_chiefs['name'].tolist()
        branch_dist = city_chiefs['branch'].value_counts()
        
        popup_text = f"""
        <div style="font-family: Arial; width: 280px;">
            <h4 style="margin-bottom: 10px; color: #4b5320;">{city_name}</h4>
            <p><b>Number of Chiefs:</b> {count}</p>
            <hr>
            <p><b>Branch Distribution:</b></p>
            <ul style="margin: 5px 0; padding-left: 20px;">
        """
        for branch, branch_count in branch_dist.items():
            popup_text += f"<li>{branch}: {branch_count}</li>"
        
        popup_text += """
            </ul>
            <hr>
            <p><b>Chiefs from this city:</b></p>
            <ul style="margin: 5px 0; padding-left: 20px;">
        """
        for chief in chiefs_list:
            popup_text += f"<li>{chief}</li>"
        popup_text += "</ul></div>"
    else:
        popup_text = f"""
        <div style="font-family: Arial; width: 200px;">
            <h4 style="margin-bottom: 10px; color: #666;">{city_name}</h4>
            <p style="color: #999;">No chiefs of staff from this city</p>
        </div>
        """
    
    # Draw city circle
    folium.Circle(
        location=[city_info['lat'], city_info['lon']],
        radius=radius,
        popup=folium.Popup(popup_text, max_width=320),
        color=color,
        fill=True,
        fillColor=color,
        fillOpacity=0.6,
        weight=2,
        opacity=0.8
    ).add_to(m)

# Add legend
legend_html = '''
<div style="position: fixed; 
     top: 10px; right: 10px; width: 240px; 
     background-color: white; z-index:9999; font-size:13px;
     border:2px solid grey; border-radius: 5px; padding: 12px;
     box-shadow: 0 2px 4px rgba(0,0,0,0.2);">
     <p style="margin: 0 0 8px 0; font-weight: bold; font-size: 14px;">Number of Chiefs</p>
     <p style="margin: 5px 0;"><span style="background-color: #2d3a1a; padding: 3px 12px; border-radius: 3px; color: white;">7+</span></p>
     <p style="margin: 5px 0;"><span style="background-color: #3d4a2a; padding: 3px 12px; border-radius: 3px; color: white;">5-6</span></p>
     <p style="margin: 5px 0;"><span style="background-color: #4b5320; padding: 3px 12px; border-radius: 3px; color: white;">3-4</span></p>
     <p style="margin: 5px 0;"><span style="background-color: #697843; padding: 3px 12px; border-radius: 3px; color: white;">2</span></p>
     <p style="margin: 5px 0;"><span style="background-color: #8a9a5b; padding: 3px 12px; border-radius: 3px; color: white;">1</span></p>
     <p style="margin: 5px 0;"><span style="background-color: #e8e8e8; padding: 3px 12px; border-radius: 3px; color: #666;">0</span></p>
     <hr style="margin: 8px 0;">
     <p style="margin: 5px 0 0 0; font-size: 11px; color: #666;">
         Circle size reflects number of chiefs
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
