#!/usr/bin/env python3
"""
Create an interactive choropleth map of Turkish officials' birthplaces
"""
import sqlite3
import json
import re
from pathlib import Path
from collections import Counter
import folium
from folium import plugins

DB_PATH = Path("data/turkish_officials.db")
OUTPUT_FILE = Path("turkish_officials_birthplace_map.html")

# Major Turkish cities/provinces mapping
CITY_MAPPING = {
    'istanbul': 'İstanbul',
    'ankara': 'Ankara',
    'izmir': 'İzmir',
    'bursa': 'Bursa',
    'antalya': 'Antalya',
    'adana': 'Adana',
    'konya': 'Konya',
    'gaziantep': 'Gaziantep',
    'şanlıurfa': 'Şanlıurfa',
    'kocaeli': 'Kocaeli',
    'mersin': 'Mersin',
    'diyarbakır': 'Diyarbakır',
    'kayseri': 'Kayseri',
    'eskişehir': 'Eskişehir',
    'samsun': 'Samsun',
    'denizli': 'Denizli',
    'şanlıurfa': 'Şanlıurfa',
    'adapazarı': 'Sakarya',
    'malatya': 'Malatya',
    'kahramanmaraş': 'Kahramanmaraş',
    'erzurum': 'Erzurum',
    'van': 'Van',
    'batman': 'Batman',
    'elazığ': 'Elazığ',
    'erzincan': 'Erzincan',
    'sivas': 'Sivas',
    'çorum': 'Çorum',
    'tokat': 'Tokat',
    'ordu': 'Ordu',
    'giresun': 'Giresun',
    'trabzon': 'Trabzon',
    'rize': 'Rize',
    'artvin': 'Artvin',
    'gümüşhane': 'Gümüşhane',
    'bayburt': 'Bayburt',
    'kastamonu': 'Kastamonu',
    'sinop': 'Sinop',
    'çankırı': 'Çankırı',
    'amasya': 'Amasya',
    'yozgat': 'Yozgat',
    'kırşehir': 'Kırşehir',
    'nevşehir': 'Nevşehir',
    'kırıkkale': 'Kırıkkale',
    'aksaray': 'Aksaray',
    'niğde': 'Niğde',
    'kars': 'Kars',
    'iğdır': 'Iğdır',
    'ağrı': 'Ağrı',
    'muş': 'Muş',
    'bitlis': 'Bitlis',
    'hakkari': 'Hakkari',
    'şırnak': 'Şırnak',
    'mardin': 'Mardin',
    'siirt': 'Siirt',
    'adıyaman': 'Adıyaman',
    'kilis': 'Kilis',
    'osmaniye': 'Osmaniye',
    'hatay': 'Hatay',
    'balıkesir': 'Balıkesir',
    'çanakkale': 'Çanakkale',
    'edirne': 'Edirne',
    'kırklareli': 'Kırklareli',
    'tekirdağ': 'Tekirdağ',
    'bolu': 'Bolu',
    'düzce': 'Düzce',
    'zonguldak': 'Zonguldak',
    'karabük': 'Karabük',
    'bartın': 'Bartın',
    'afyonkarahisar': 'Afyonkarahisar',
    'afyon': 'Afyonkarahisar',
    'kütahya': 'Kütahya',
    'manisa': 'Manisa',
    'uşak': 'Uşak',
    'aydın': 'Aydın',
    'muğla': 'Muğla',
    'burdur': 'Burdur',
    'isparta': 'Isparta',
    'karaman': 'Karaman',
}

def normalize_city(birthplace: str) -> str:
    """Normalize city name to standard province name"""
    if not birthplace or birthplace == '?':
        return None
    
    # Remove country/state suffixes
    place = re.sub(r',\s*(Türkiye|Osmanlı İmparatorluğu|Osmanlı Devleti|Osmanlı|Turkey).*$', '', birthplace)
    
    # Split by comma and get parts
    parts = [p.strip() for p in place.split(',')]
    
    # Try to match with known provinces
    for part in reversed(parts):
        part_lower = part.lower()
        # Direct match
        if part_lower in CITY_MAPPING:
            return CITY_MAPPING[part_lower]
        # Partial match
        for key, value in CITY_MAPPING.items():
            if key in part_lower or part_lower in key:
                return value
    
    # If no match found, return the last significant part
    if len(parts) >= 2:
        return parts[-1]
    return parts[0] if parts else None


def get_birthplace_counts(conn: sqlite3.Connection):
    """Get birthplace counts from all tables"""
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
    tables = [row[0] for row in cursor.fetchall()]
    
    city_counts = Counter()
    
    for table in tables:
        try:
            cursor.execute(f"SELECT birth_place FROM {table} WHERE birth_place IS NOT NULL AND birth_place != ''")
            for row in cursor.fetchall():
                city = normalize_city(row[0])
                if city and city not in ['Unknown', '?', 'Osmanlı', 'Turkey']:
                    city_counts[city] += 1
        except:
            pass
    
    return city_counts


def create_map(city_counts):
    """Create an interactive choropleth map"""
    
    # Create base map centered on Turkey
    m = folium.Map(
        location=[39.0, 35.0],
        zoom_start=6,
        tiles='CartoDB positron',
        control_scale=True
    )
    
    # Add title
    title_html = '''
    <div style="position: fixed; 
                top: 10px; left: 50px; width: 400px; height: 50px; 
                background-color: white; border:2px solid grey; z-index:9999; 
                font-size:16px; font-weight: bold; padding: 10px">
    Turkish Officials Birthplaces (1920-2024)
    </div>
    '''
    m.get_root().html.add_child(folium.Element(title_html))
    
    # Add markers for each city
    max_count = max(city_counts.values())
    
    # Approximate coordinates for major Turkish cities
    city_coords = {
        'İstanbul': [41.0082, 28.9784],
        'Ankara': [39.9334, 32.8597],
        'İzmir': [38.4237, 27.1428],
        'Bursa': [40.1826, 29.0665],
        'Antalya': [36.8969, 30.7133],
        'Adana': [37.0000, 35.3213],
        'Konya': [37.8667, 32.4833],
        'Gaziantep': [37.0662, 37.3833],
        'Kayseri': [38.7205, 35.4826],
        'Eskişehir': [39.7767, 30.5206],
        'Samsun': [41.2867, 36.33],
        'Diyarbakır': [37.9144, 40.2306],
        'Malatya': [38.3552, 38.3095],
        'Erzurum': [39.9000, 41.2700],
        'Erzincan': [39.7500, 39.4900],
        'Trabzon': [41.0015, 39.7178],
        'Sivas': [39.7477, 37.0179],
        'Rize': [41.0201, 40.5234],
        'Kastamonu': [41.3887, 33.7827],
        'Yozgat': [39.8200, 34.8147],
        'Kırşehir': [39.1425, 34.1709],
        'Çanakkale': [40.1553, 26.4142],
        'Karaman': [37.1759, 33.2287],
        'Kocaeli': [40.8533, 29.8815],
        'Ordu': [40.9839, 37.8764],
        'Manisa': [38.6191, 27.4289],
        'Balıkesir': [39.6484, 27.8826],
        'Afyonkarahisar': [38.7507, 30.5567],
        'Sinop': [42.0231, 35.1531],
        'Kütahya': [39.4242, 29.9833],
        'Aydın': [37.8560, 27.8416],
        'Edirne': [41.6771, 26.5557],
        'Muğla': [37.2153, 28.3636],
        'Denizli': [37.7765, 29.0864],
        'Tekirdağ': [40.9833, 27.5167],
        'Isparta': [37.7648, 30.5566],
        'Giresun': [40.9128, 38.3895],
        'Artvin': [41.1828, 41.8183],
        'Gümüşhane': [40.4386, 39.4814],
        'Niğde': [37.9667, 34.6833],
        'Çorum': [40.5506, 34.9556],
        'Sakarya': [40.7569, 30.3783],
        'Tokat': [40.3167, 36.5500],
        'Bolu': [40.7339, 31.6061],
        'Mersin': [36.8121, 34.6415],
    }
    
    # Add circles for each city
    for city, count in city_counts.items():
        if city in city_coords:
            # Calculate circle size and color based on count
            radius = 5000 + (count / max_count) * 50000
            opacity = 0.3 + (count / max_count) * 0.5
            
            # Color gradient from light to dark green
            color_intensity = int(50 + (count / max_count) * 150)
            color = f'#{color_intensity:02x}{min(200, color_intensity + 50):02x}{color_intensity:02x}'
            
            folium.Circle(
                location=city_coords[city],
                radius=radius,
                popup=f'<b>{city}</b><br>{count} officials',
                tooltip=f'{city}: {count}',
                color=color,
                fill=True,
                fillColor=color,
                fillOpacity=opacity,
                weight=2
            ).add_to(m)
    
    return m


def main():
    conn = sqlite3.connect(DB_PATH)
    
    print("Extracting birthplace data from database...")
    city_counts = get_birthplace_counts(conn)
    
    print(f"\nFound {len(city_counts)} unique cities")
    print(f"Total officials: {sum(city_counts.values())}")
    print(f"\nTop 10 cities:")
    for city, count in city_counts.most_common(10):
        print(f"  {city}: {count}")
    
    print(f"\nCreating interactive map...")
    m = create_map(city_counts)
    
    # Save map
    m.save(str(OUTPUT_FILE))
    print(f"\n✅ Map saved to: {OUTPUT_FILE}")
    print(f"📂 Open the file in your browser to view the map")
    
    conn.close()


if __name__ == '__main__':
    main()
