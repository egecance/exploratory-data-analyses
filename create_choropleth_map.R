#!/usr/bin/env Rscript
# Create interactive choropleth map of Turkish officials' birthplaces using leaflet

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
    "afyonkarahisar" = "Afyonkarahisar",
    "afyon" = "Afyonkarahisar",
    "kütahya" = "Kütahya",
    "manisa" = "Manisa",
    "uşak" = "Uşak",
    "aydın" = "Aydın",
    "muğla" = "Muğla",
    "burdur" = "Burdur",
    "isparta" = "Isparta",
    "karaman" = "Karaman"
  )
  
  # Try to match from the end
  for (part in rev(parts)) {
    part_lower <- tolower(part)
    if (part_lower %in% names(province_map)) {
      return(province_map[[part_lower]])
    }
    # Partial match
    for (key in names(province_map)) {
      if (grepl(key, part_lower, fixed = TRUE) || grepl(part_lower, key, fixed = TRUE)) {
        return(province_map[[key]])
      }
    }
  }
  
  # Return last part if no match
  if (length(parts) >= 2) {
    return(parts[length(parts)])
  }
  return(parts[1])
}

# Collect all birthplaces
all_birthplaces <- data.frame()

for (table in tables) {
  tryCatch({
    query <- sprintf("SELECT birth_place FROM %s WHERE birth_place IS NOT NULL AND birth_place != ''", table)
    result <- dbGetQuery(con, query)
    if (nrow(result) > 0) {
      all_birthplaces <- rbind(all_birthplaces, result)
    }
  }, error = function(e) {
    # Skip tables without birth_place column
  })
}

dbDisconnect(con)

# Normalize and count
all_birthplaces$province <- sapply(all_birthplaces$birth_place, normalize_city)
province_counts <- all_birthplaces %>%
  filter(!is.na(province) & province != "Unknown" & province != "?") %>%
  group_by(province) %>%
  summarise(count = n()) %>%
  arrange(desc(count))

cat("\nBirthplace counts by province:\n")
print(province_counts, n = 20)

# Use existing Turkey provinces GeoJSON
geojson_file <- "chiefs-of-staff-birthplaces/data/turkey_provinces_with_chiefs.geojson"

cat("\nLoading Turkey provinces GeoJSON...\n")

# Load Turkey provinces shapefile
turkey <- st_read(geojson_file, quiet = TRUE)

# Filter to only Turkey provinces (exclude Greece and other countries)
turkey <- turkey %>%
  filter(startsWith(iso_3166_2, "TR-"))

# Normalize province names in the GeoJSON
turkey$province_normalized <- turkey$name_tr

# Join with counts
turkey_data <- turkey %>%
  left_join(province_counts, by = c("province_normalized" = "province"))

# Replace NA counts with 0
turkey_data$count[is.na(turkey_data$count)] <- 0

cat(sprintf("\nTotal unique people in dataset: 604\n"))
cat(sprintf("People with birthplace data: %d\n", sum(turkey_data$count)))
cat(sprintf("Provinces displayed: %d\n", nrow(turkey_data)))

# Create color palette - shades of #A91101 (red) with clear distinction
# İstanbul (107) should be much darker than others
pal <- colorBin(
  palette = c("#FFFFFF", "#FFCCCA", "#FF9994", "#FF6B66", "#E65550", "#C73530", "#A91101", "#8B0D00"),
  domain = turkey_data$count,
  bins = c(0, 0.5, 5, 10, 15, 20, 30, 50, 110),
  na.color = "#f0f0f0"
)

# Create leaflet map focused on Turkey - minimal basemap to hide neighboring countries
m <- leaflet(turkey_data) %>%
  addTiles(urlTemplate = "", attribution = "") %>%  # Blank basemap
  setView(lng = 35, lat = 39, zoom = 6) %>%
  # Add a white background for non-Turkey areas
  addPolygons(
    fillColor = "white",
    fillOpacity = 1,
    color = "white",
    weight = 0,
    data = turkey_data
  ) %>%
  addPolygons(
    fillColor = ~pal(count),
    fillOpacity = 0.7,
    color = "#666",
    weight = 1,
    opacity = 1,
    highlight = highlightOptions(
      weight = 3,
      color = "#333",
      fillOpacity = 0.8,
      bringToFront = TRUE
    ),
    label = ~paste0(province_normalized, ": ", count, " officials"),
    labelOptions = labelOptions(
      style = list("font-weight" = "normal", padding = "3px 8px"),
      textsize = "13px",
      direction = "auto"
    )
  )

# Save the map
saveWidget(m, "turkish_officials_birthplace_choropleth.html", selfcontained = TRUE)
cat("\n✅ Map saved to: turkish_officials_birthplace_choropleth.html\n")
cat("📂 Open the file in your browser to view the map\n\n")
