import requests
import json

# Try multiple sources
sources = [
    "https://raw.githubusercontent.com/cihadturhan/tr-geojson/master/il-utf8.json",
    "https://raw.githubusercontent.com/cihadturhan/tr-geojson/master/il.json",
    "https://raw.githubusercontent.com/alpers/Turkey-Maps-GeoJSON/master/tr-cities-utf8.json",
    "https://raw.githubusercontent.com/gazcreate/Turkey-Maps-Geojson/refs/heads/master/turkey-cities.json"
]

for url in sources:
    try:
        print(f"Trying: {url}")
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Success! Found {len(data.get('features', []))} features")
            print(f"  URL: {url}")
            
            # Save it
            with open('data/turkey_provinces.geojson', 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False)
            print("  Saved to data/turkey_provinces.geojson")
            
            # Show first feature properties
            if data.get('features'):
                print(f"  Sample properties: {data['features'][0]['properties']}")
            break
    except Exception as e:
        print(f"  ✗ Failed: {e}")
