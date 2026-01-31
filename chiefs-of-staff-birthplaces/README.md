# Turkish Military Chiefs of Staff - Birthplace Analysis

This project analyzes the birthplaces of Turkish Armed Forces Chiefs of Staff during the Republic era (1920-present).

## Data Source

Data compiled from the [Turkish Wikipedia list of Chiefs of Staff](https://tr.wikipedia.org/wiki/T%C3%BCrk_Silahl%C4%B1_Kuvvetleri_genelkurmay_ba%C5%9Fkanlar%C4%B1_listesi) and individual biographical pages.

## Files

- `data/chiefs_of_staff.csv` - List of 31 chiefs with dates, branch, and birthplace
- `data/city_coordinates.csv` - Geographic coordinates for each city
- `analyze_birthplaces.py` - Main analysis script
- `analysis.ipynb` - Interactive Jupyter notebook

## Quick Start

```bash
# Install dependencies
pip install -r ../requirements.txt

# Run analysis
python analyze_birthplaces.py
```

This will generate:
- `birthplace_distribution.png` - Bar chart of birthplace distribution
- `timeline_by_birthplace.png` - Timeline showing when chiefs from each city served
- `chiefs_birthplace_map.html` - Interactive map (open in browser)

## Key Findings

- **31 chiefs** served from 1920 to present (excluding caretakers)
- **14 unique birthplaces** across Turkey and historical Ottoman territories
- **İstanbul** produced the most chiefs (10), followed by **Ankara** (5)
- Historical cities like **Selanik** (Thessaloniki, now Greece) contributed 3 chiefs
- Geographic diversity includes cities from Aegean to Eastern Anatolia regions

## Data Notes

- Caretaker/acting chiefs excluded from analysis
- Birthplaces verified against individual Wikipedia pages
- Coordinates represent modern city centers
- "Selanik" refers to Thessaloniki (now in Greece), part of Ottoman Empire when chiefs were born
