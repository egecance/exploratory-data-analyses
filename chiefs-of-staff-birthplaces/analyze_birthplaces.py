#!/usr/bin/env python3
"""
Turkish Military Chiefs of Staff - Birthplace Analysis with Voronoi Polygons
Uses Voronoi diagrams to create regions around cities
"""

import pandas as pd
import folium
from folium import plugins
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

def get_military_green(count):
    """Return military green color based on count of chiefs"""
    if count >= 7:
        return '#2d3a1a'  # Darkest
    elif count >= 5:
        return '#3d4a2a'
    elif count >= 3:
        return '#4b5320'  # Base military green
    elif count == 2:
        return '#697843'
    elif count == 1:
        return '#8a9a5b'  # Lightest green
    else:
        return '#e8e8e8'  # Grey for no chiefs

# Load data
df = pd.read_csv('data/chiefs_of_staff.csv')
coords = pd.read_csv('data/city_coordinates.csv')

# Merge data
df = df.merge(coords, left_on='birthplace', right_on='city', how='left')

print("=" * 60)
print("Turkish Military Chiefs of Staff Birthplace Analysis")
print("=" * 60)
print(f"\nTotal Chiefs of Staff: {len(df)}")
print(f"Unique Birthplaces: {df['birthplace'].nunique()}")
print(f"\nBirthplace Distribution:")
print(df['birthplace'].value_counts())

# Get all major Turkish cities including those with 0 chiefs
all_major_cities = ['İstanbul', 'Ankara', 'İzmir', 'Bursa', 'Antalya', 'Adana',
                    'Konya', 'Gaziantep', 'Şanlıurfa', 'Kocaeli', 'Mersin', 'Diyarbakır',
                    'Hatay', 'Manisa', 'Kayseri', 'Samsun', 'Balıkesir', 'Kahramanmaraş',
                    'Van', 'Denizli', 'Batman', 'Elazığ', 'Erzurum', 'Erzincan', 'Trabzon',
                    'Kütahya', 'Malatya', 'Ordu', 'Aydın', 'Tekirdağ', 'Edirne',
                    'Çanakkale', 'Zonguldak', 'Afyonkarahisar', 'Kastamonu', 'Burdur',
                    'Rize', 'Muğla', 'Tokat', 'Giresun']

# Create city count dictionary
city_counts = df['birthplace'].value_counts().to_dict()

# Create map centered on Turkey
m = folium.Map(
    location=[39.0, 35.0],
    zoom_start=6,
    tiles='CartoDB positron',
    prefer_canvas=True,
    max_bounds=True
)

# Add filled polygons for each city using large circles
for city_name in all_major_cities:
    count = city_counts.get(city_name, 0)
    color = get_military_green(count)
    
    # Get coordinates
    city_info = coords[coords['city'] == city_name]
    if city_info.empty:
        continue
    
    city_info = city_info.iloc[0]
    
    # Determine radius based on count - very large for area effect
    if count >= 7:
        radius = 60000  # meters
    elif count >= 5:
        radius = 50000
    elif count >= 3:
        radius = 42000
    elif count >= 2:
        radius = 35000
    elif count >= 1:
        radius = 28000
    else:
        radius = 22000  # Grey cities
    
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
    
    # Draw city area - no border, high opacity for filled area effect, semi-transparent so overlaps blend
    folium.Circle(
        location=[city_info['latitude'], city_info['longitude']],
        radius=radius,
        popup=folium.Popup(popup_text, max_width=320),
        tooltip=f"{city_name}: {count} chief(s)",
        color=color,
        fill=True,
        fillColor=color,
        fillOpacity=0.7 if count > 0 else 0.3,
        weight=0.5 if count > 0 else 0,
        opacity=0.3 if count > 0 else 0
    ).add_to(m)

# Add title
title_html = '''
<div style="position: fixed; 
            top: 10px; left: 50px; width: 550px; height: 90px; 
            background-color: white; border:2px solid grey; z-index:9999; 
            font-size:14px; padding: 10px; border-radius: 5px;">
            
<h4 style="margin-bottom: 5px; color: #4b5320;">Turkish Chiefs of Staff - Birthplace Distribution</h4>
<p style="margin: 0; font-size: 12px;">Republic Era (1920-Present)</p>
<p style="margin: 5px 0 0 0; font-size: 11px; color: #666;">
Colored by number of chiefs. Hover or click for details. Data from Turkish Wikipedia.
</p>
</div>
'''
m.get_root().html.add_child(folium.Element(title_html))

# Add legend
legend_html = '''
<div style="position: fixed; 
            bottom: 50px; right: 50px; width: 200px; 
            background-color: white; border:2px solid grey; z-index:9999; 
            font-size:12px; padding: 10px; border-radius: 5px;">
            
<p style="margin: 0 0 10px 0; font-weight: bold; color: #4b5320;">Number of Chiefs</p>
<p style="margin: 5px 0;"><span style="background-color: #2d3a1a; padding: 3px 10px; color: white; border-radius: 3px;">7+</span> Largest area</p>
<p style="margin: 5px 0;"><span style="background-color: #3d4a2a; padding: 3px 10px; color: white; border-radius: 3px;">5-6</span></p>
<p style="margin: 5px 0;"><span style="background-color: #4b5320; padding: 3px 10px; color: white; border-radius: 3px;">3-4</span></p>
<p style="margin: 5px 0;"><span style="background-color: #697843; padding: 3px 10px; color: white; border-radius: 3px;">2</span></p>
<p style="margin: 5px 0;"><span style="background-color: #8a9a5b; padding: 3px 10px; color: white; border-radius: 3px;">1</span></p>
<p style="margin: 5px 0;"><span style="background-color: #e8e8e8; padding: 3px 10px; border-radius: 3px;">0</span> Smallest area</p>
</div>
'''
m.get_root().html.add_child(folium.Element(legend_html))

# Save map
output_file = 'chiefs_birthplace_map.html'
m.save(output_file)
print(f"\n✓ Saved: {output_file}")

print("\n" + "=" * 60)
print("Analysis complete! Generated file:")
print(f"  - {output_file} (open in browser)")
print("=" * 60)

# Also generate the charts
print("\nGenerating additional visualizations...")

# 1. Bar chart of birthplace distribution
plt.figure(figsize=(12, 6))
birthplace_counts = df['birthplace'].value_counts()
sns.barplot(x=birthplace_counts.values, y=birthplace_counts.index, palette='Greens_r')
plt.xlabel('Number of Chiefs of Staff')
plt.ylabel('Birthplace')
plt.title('Distribution of Turkish Chiefs of Staff by Birthplace (Republic Era)', 
          fontsize=14, fontweight='bold', color='#4b5320')
plt.tight_layout()
plt.savefig('birthplace_distribution.png', dpi=300, bbox_inches='tight')
print("✓ Saved: birthplace_distribution.png")

# 2. Timeline visualization
plt.figure(figsize=(14, 8))
df_timeline = df[df['end_date'] != 'görevde'].copy()  # Exclude current chief
df_timeline['start_year'] = pd.to_datetime(df_timeline['start_date']).dt.year
df_timeline['end_year'] = pd.to_datetime(df_timeline['end_date']).dt.year

# Color by birthplace
unique_birthplaces = df_timeline['birthplace'].unique()
colors = sns.color_palette('Greens', len(unique_birthplaces))
color_map = dict(zip(unique_birthplaces, colors))

for idx, row in df_timeline.iterrows():
    plt.barh(y=idx, width=row['end_year']-row['start_year'], 
             left=row['start_year'], height=0.8,
             color=color_map[row['birthplace']], 
             edgecolor='white', linewidth=0.5)

plt.xlabel('Year', fontsize=12)
plt.ylabel('Chiefs of Staff (in order)', fontsize=12)
plt.title('Timeline of Turkish Chiefs of Staff by Birthplace', 
          fontsize=14, fontweight='bold', color='#4b5320')
plt.yticks(range(len(df_timeline)), df_timeline['name'], fontsize=8)
plt.grid(axis='x', alpha=0.3)

# Add legend
from matplotlib.patches import Patch
legend_elements = [Patch(facecolor=color_map[bp], label=bp) 
                   for bp in sorted(unique_birthplaces)]
plt.legend(handles=legend_elements, bbox_to_anchor=(1.05, 1), 
          loc='upper left', fontsize=9)
plt.tight_layout()
plt.savefig('timeline_by_birthplace.png', dpi=300, bbox_inches='tight')
print("✓ Saved: timeline_by_birthplace.png")

print("\n" + "=" * 60)
print("All visualizations complete!")
print("=" * 60)
