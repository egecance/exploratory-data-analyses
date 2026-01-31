#!/usr/bin/env python3
"""
Turkish Military Chiefs of Staff - Birthplace Analysis with Province Polygons
"""

import pandas as pd
import folium
from folium import GeoJson
import json
import requests
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

# Fetch Turkey provinces GeoJSON
print("\nFetching Turkey province boundaries...")
try:
    # Try to load local file first
    geojson_path = Path('data/turkey_provinces.geojson')
    if geojson_path.exists() and geojson_path.stat().st_size > 100:
        with open(geojson_path, 'r', encoding='utf-8') as f:
            turkey_geojson = json.load(f)
        print("✓ Loaded local GeoJSON file")
    else:
        # Fetch from GitHub
        url = "https://raw.githubusercontent.com/cihadturhan/tr-geojson/master/geo/il-utf8.json"
        response = requests.get(url)
        response.raise_for_status()
        turkey_geojson = response.json()
        
        # Save it for future use
        with open(geojson_path, 'w', encoding='utf-8') as f:
            json.dump(turkey_geojson, f, ensure_ascii=False, indent=2)
        print("✓ Downloaded and saved GeoJSON file")
        
except Exception as e:
    print(f"✗ Error loading GeoJSON: {e}")
    print("Falling back to circle-based map...")
    # Fall back to the original circle-based approach
    import subprocess
    subprocess.run(['python3', 'analyze_birthplaces.py'])
    exit()

# Create a mapping of city names to count
# We need to normalize city names to match the GeoJSON
city_mapping = {
    'İstanbul': 'İstanbul',
    'Ankara': 'Ankara',
    'Selanik': None,  # Not in Turkey anymore
    'Edirne': 'Edirne',
    'Erzurum': 'Erzurum',
    'Trabzon': 'Trabzon',
    'Erzincan': 'Erzincan',
    'İzmir': 'İzmir',
    'Alaşehir': 'Manisa',  # Alaşehir is in Manisa province
    'Burdur': 'Burdur',
    'Elazığ': 'Elazığ',
    'Afyonkarahisar': 'Afyonkarahisar',
    'Kastamonu': 'Kastamonu',
    'Van': 'Van'
}

# Count chiefs per city
city_counts = df['birthplace'].value_counts().to_dict()

# Create province-level counts
province_counts = {}
province_details = {}  # Store details for popups

for city, count in city_counts.items():
    province = city_mapping.get(city)
    if province:
        if province not in province_counts:
            province_counts[province] = 0
            province_details[province] = {'chiefs': [], 'branches': []}
        
        province_counts[province] += count
        
        # Get chiefs from this city
        city_chiefs = df[df['birthplace'] == city]
        province_details[province]['chiefs'].extend(city_chiefs['name'].tolist())
        province_details[province]['branches'].extend(city_chiefs['branch'].tolist())

print(f"\nProvince counts: {province_counts}")

# Create map centered on Turkey
m = folium.Map(
    location=[39.0, 35.0],
    zoom_start=6,
    tiles='CartoDB positron',
    prefer_canvas=True
)

# Style function for provinces
def style_function(feature):
    """Style each province based on number of chiefs"""
    province_name = feature['properties'].get('name') or feature['properties'].get('NAME') or feature['properties'].get('il_adi')
    count = province_counts.get(province_name, 0)
    color = get_military_green(count)
    
    return {
        'fillColor': color,
        'color': 'white',
        'weight': 1,
        'fillOpacity': 0.85
    }

# Highlight function for hover
def highlight_function(feature):
    """Highlight on hover"""
    return {
        'fillColor': '#ffff00',
        'color': 'white',
        'weight': 2,
        'fillOpacity': 0.95
    }

# Add GeoJSON layer with styling
geojson_layer = GeoJson(
    turkey_geojson,
    style_function=style_function,
    highlight_function=highlight_function,
    tooltip=folium.GeoJsonTooltip(
        fields=['name'],
        aliases=['Province:'],
        style=("background-color: white; color: #333333; font-family: arial; font-size: 12px; padding: 10px;")
    )
)

# Add custom popups with chief details
for feature in turkey_geojson['features']:
    province_name = feature['properties'].get('name') or feature['properties'].get('NAME') or feature['properties'].get('il_adi')
    count = province_counts.get(province_name, 0)
    
    if count > 0:
        details = province_details[province_name]
        chiefs_list = details['chiefs']
        
        # Count branches
        from collections import Counter
        branch_counts = Counter(details['branches'])
        
        popup_html = f"""
        <div style="font-family: Arial; width: 300px;">
            <h4 style="margin-bottom: 10px; color: #4b5320;">{province_name}</h4>
            <p><b>Number of Chiefs:</b> {count}</p>
            <hr>
            <p><b>Branch Distribution:</b></p>
            <ul style="margin: 5px 0; padding-left: 20px;">
        """
        for branch, branch_count in branch_counts.items():
            popup_html += f"<li>{branch}: {branch_count}</li>"
        
        popup_html += """
            </ul>
            <hr>
            <p><b>Chiefs from this province:</b></p>
            <ul style="margin: 5px 0; padding-left: 20px;">
        """
        for chief in chiefs_list:
            popup_html += f"<li>{chief}</li>"
        popup_html += "</ul></div>"
        
        # Find the centroid of the province for popup placement
        # This is a simplified approach
        coords_list = feature['geometry']['coordinates']
        
        # Get a representative point (this is simplified, ideally we'd use the actual centroid)
        if feature['geometry']['type'] == 'Polygon':
            # Get first coordinate of the polygon
            lat = coords_list[0][0][1]
            lon = coords_list[0][0][0]
        elif feature['geometry']['type'] == 'MultiPolygon':
            lat = coords_list[0][0][0][1]
            lon = coords_list[0][0][0][0]
        else:
            continue
            
        # Add an invisible marker for the popup
        folium.Marker(
            location=[lat, lon],
            popup=folium.Popup(popup_html, max_width=350),
            icon=folium.DivIcon(html='')
        ).add_to(m)

geojson_layer.add_to(m)

# Add title
title_html = '''
<div style="position: fixed; 
            top: 10px; left: 50px; width: 500px; height: 90px; 
            background-color: white; border:2px solid grey; z-index:9999; 
            font-size:14px; padding: 10px; border-radius: 5px;">
            
<h4 style="margin-bottom: 5px; color: #4b5320;">Turkish Chiefs of Staff - Birthplace Distribution</h4>
<p style="margin: 0; font-size: 12px;">Republic Era (1920-Present)</p>
<p style="margin: 5px 0 0 0; font-size: 11px; color: #666;">
Colored by number of chiefs. Hover for details. Data from Turkish Wikipedia.
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
<p style="margin: 5px 0;"><span style="background-color: #2d3a1a; padding: 3px 10px; color: white;">7+</span></p>
<p style="margin: 5px 0;"><span style="background-color: #3d4a2a; padding: 3px 10px; color: white;">5-6</span></p>
<p style="margin: 5px 0;"><span style="background-color: #4b5320; padding: 3px 10px; color: white;">3-4</span></p>
<p style="margin: 5px 0;"><span style="background-color: #697843; padding: 3px 10px; color: white;">2</span></p>
<p style="margin: 5px 0;"><span style="background-color: #8a9a5b; padding: 3px 10px; color: white;">1</span></p>
<p style="margin: 5px 0;"><span style="background-color: #e8e8e8; padding: 3px 10px;">0</span></p>
</div>
'''
m.get_root().html.add_child(folium.Element(legend_html))

# Save map
output_file = 'chiefs_birthplace_map_polygon.html'
m.save(output_file)
print(f"\n✓ Saved: {output_file}")

print("\n" + "=" * 60)
print("Analysis complete! Generated file:")
print(f"  - {output_file} (open in browser)")
print("=" * 60)
