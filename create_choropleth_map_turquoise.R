#!/usr/bin/env Rscript
# Create interactive choropleth map of Turkish officials' birthplaces using leaflet
# Turquoise color scheme version

library(DBI)
library(RSQLite)
library(leaflet)
library(sf)
library(dplyr)
library(jsonlite)
library(stringr)
library(htmlwidgets)

# Connect to database
con <- dbConnect(RSQLite::SQLite(), "data/turkish_officials.db")

# Get all tables
tables <- dbListTables(con)

# Function to normalize city names to provinces
normalize_city <- function(birthplace) {
  if (is.na(birthplace) || birthplace == "" || birthplace == "?") {
    return(NA)
  }
  
  # Remove country suffixes
  place <- gsub(",\\s*(Türkiye|Osmanlı İmparatorluğu|Osmanlı Devleti|Osmanlı|Turkey).*$", "", birthplace)
  
  # Split by comma
  parts <- strsplit(place, ",")[[1]]
  parts <- trimws(parts)
  
  # Mapping to standard province names
  province_map <- c(
    "istanbul" = "İstanbul",
    "ankara" = "Ankara",
    "izmir" = "İzmir",
    "bursa" = "Bursa",
    "antalya" = "Antalya",
    "adana" = "Adana",
    "konya" = "Konya",
    "gaziantep" = "Gaziantep",
    "kocaeli" = "Kocaeli",
    "izmit" = "Kocaeli",
    "mersin" = "Mersin",
    "diyarbakır" = "Diyarbakır",
    "kayseri" = "Kayseri",
    "eskişehir" = "Eskişehir",
    "samsun" = "Samsun",
    "denizli" = "Denizli",
    "adapazarı" = "Sakarya",
    "malatya" = "Malatya",
    "kahramanmaraş" = "Kahramanmaraş",
    "erzurum" = "Erzurum",
    "van" = "Van",
    "batman" = "Batman",
    "elazığ" = "Elâzığ",
    "elazığ" = "Elâzığ",
    "erzincan" = "Erzincan",
    "sivas" = "Sivas",
    "çorum" = "Çorum",
    "tokat" = "Tokat",
    "ordu" = "Ordu",
    "giresun" = "Giresun",
    "trabzon" = "Trabzon",
    "rize" = "Rize",
    "artvin" = "Artvin",
    "gümüşhane" = "Gümüşhane",
    "bayburt" = "Bayburt",
    "kastamonu" = "Kastamonu",
    "sinop" = "Sinop",
    "çankırı" = "Çankırı",
    "amasya" = "Amasya",
    "yozgat" = "Yozgat",
    "kırşehir" = "Kırşehir",
    "nevşehir" = "Nevşehir",
    "kırıkkale" = "Kırıkkale",
    "aksaray" = "Aksaray",
    "niğde" = "Niğde",
    "kars" = "Kars",
    "iğdır" = "Iğdır",
    "ağrı" = "Ağrı",
    "muş" = "Muş",
    "bitlis" = "Bitlis",
    "hakkari" = "Hakkâri",
    "şırnak" = "Şırnak",
    "mardin" = "Mardin",
    "siirt" = "Siirt",
    "adıyaman" = "Adıyaman",
    "kilis" = "Kilis",
    "osmaniye" = "Osmaniye",
    "hatay" = "Hatay",
    "balıkesir" = "Balıkesir",
    "çanakkale" = "Çanakkale",
    "edirne" = "Edirne",
    "kırklareli" = "Kırklareli",
    "tekirdağ" = "Tekirdağ",
    "bolu" = "Bolu",
    "düzce" = "Düzce",
    "zonguldak" = "Zonguldak",
    "karabük" = "Karabük",
    "bartın" = "Bartın",
    "sakarya" = "Sakarya",
    "yalova" = "Yalova",
    "bilecik" = "Bilecik",
    "afyonkarahisar" = "Afyonkarahisar",
    "afyon" = "Afyonkarahisar",
    "kütahya" = "Kütahya",
    "manisa" = "Manisa",
    "uşak" = "Uşak",
    "aydın" = "Aydın",
    "muğla" = "Muğla",
    "burdur" = "Burdur",
    "isparta" = "Isparta",
    "şanlıurfa" = "Şanlıurfa",
    "urfa" = "Şanlıurfa",
    "trablusşam" = "Trablusşam",
    "şam" = "Şam",
    "selanik" = "Selanik"
  )
  
  # Try the last part first (usually the province)
  for (i in length(parts):1) {
    part_lower <- tolower(parts[i])
    if (part_lower %in% names(province_map)) {
      return(province_map[[part_lower]])
    }
  }
  
  # Return the last part as-is if no mapping found
  return(parts[length(parts)])
}

# Query all birthplaces from all tables
birthplaces <- data.frame()
for (table in tables) {
  query <- sprintf("SELECT birth_place FROM %s WHERE birth_place IS NOT NULL AND birth_place != ''", table)
  result <- dbGetQuery(con, query)
  if (nrow(result) > 0) {
    birthplaces <- rbind(birthplaces, result)
  }
}

dbDisconnect(con)

# Normalize birthplaces to provinces
birthplaces$province <- sapply(birthplaces$birth_place, normalize_city)

# Remove NA values and non-Turkish provinces
birthplaces <- birthplaces %>%
  filter(!is.na(province)) %>%
  filter(!province %in% c("Selanik", "Manastır", "Üsküp", "Drama", "Gümülcine", 
                          "Kavala", "Makedonya", "Yunanistan", "Bulgaristan",
                          "Trablusşam", "Şam", "Suriye", "Irak", "?"))

# Count by province
province_counts <- birthplaces %>%
  group_by(province) %>%
  summarise(count = n()) %>%
  arrange(desc(count))

print("Birthplace counts by province:")
print(province_counts)

# Load Turkey GeoJSON
turkey <- st_read("chiefs-of-staff-birthplaces/data/turkey_provinces_with_chiefs.geojson", quiet = TRUE)

# Filter to Turkey only (exclude neighboring countries)
turkey <- turkey %>%
  filter(startsWith(iso_3166_2, "TR-"))

# Normalize province names in the GeoJSON
turkey$province_normalized <- turkey$name_tr

# Merge counts with geographic data
turkey <- turkey %>%
  left_join(province_counts, by = c("province_normalized" = "province"))

# Replace NA counts with 0
turkey$count[is.na(turkey$count)] <- 0

# Define turquoise color palette with consistent intervals
# Base turquoise: #77dde7 (119, 221, 231)
# Light grey for 0, then darker turquoise shades with much darker shade for highest bin
pal <- colorBin(
  palette = c("#999999", "#A8E4EB", "#77dde7", "#5BC4D1", "#3FA9B8", 
              "#2A8C9A", "#1F6B74", "#0A3038"),
  bins = c(0, 1, 6, 11, 16, 21, 26, 31, 110),
  na.color = "#999999"
)

# Create leaflet map
map <- leaflet(turkey) %>%
  addTiles(urlTemplate = "", attribution = "") %>%
  addPolygons(
    fillColor = ~pal(count),
    weight = 1,
    opacity = 1,
    color = "#666666",
    fillOpacity = 0.7,
    highlightOptions = highlightOptions(
      weight = 2,
      color = "#333333",
      fillOpacity = 0.9,
      bringToFront = TRUE
    ),
    label = ~paste0(province_normalized, ": ", count, " official", ifelse(count != 1, "s", "")),
    labelOptions = labelOptions(
      style = list("font-weight" = "normal", padding = "3px 8px"),
      textsize = "12px",
      direction = "auto"
    )
  ) %>%
  setView(lng = 35, lat = 39, zoom = 6) %>%
  addControl(
    html = "<div style='margin: 10px; background: rgba(255, 255, 255, 0.95); padding: 15px; border-radius: 5px; max-width: 280px; box-shadow: 0 2px 4px rgba(0,0,0,0.2);'>
            <h3 style='margin: 0 0 10px 0; font-size: 16px;'>Turkish Officials' Birthplaces by Province</h3>
            <div style='font-size: 11px; line-height: 1.5;'>
            <strong>Included Officials:</strong>
            <ul style='margin: 5px 0; padding-left: 18px;'>
              <li>Prime Ministers</li>
              <li>Ministers (Interior, Foreign, Justice, Finance, Education, Health)</li>
              <li>Military Commanders (Chief of Staff, Army, Navy, Air Force)</li>
              <li>Speaker of National Assembly</li>
              <li>President of Constitutional Court</li>
              <li>Governor of Central Bank</li>
              <li>Head of National Intelligence</li>
            </ul>
            </div>
            </div>",
    position = "topleft"
  )

# Save the map
saveWidget(map, "turkish_officials_birthplace_choropleth_turquoise.html", selfcontained = TRUE)

cat("\nMap saved to turkish_officials_birthplace_choropleth_turquoise.html\n")
cat("Total unique people in dataset:", sum(province_counts$count), "\n")
cat("Provinces displayed:", nrow(turkey), "\n")
