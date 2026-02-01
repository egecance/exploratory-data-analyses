#!/usr/bin/env Rscript
# Proof of Concept: Simple interactive map for GitHub Pages embedding
# Reads from CSV and creates a lightweight leaflet map

library(leaflet)
library(dplyr)
library(htmlwidgets)

# Read the combined data
commanders <- read.csv("data/all_commanders.csv", stringsAsFactors = FALSE)

# Get unique birthplaces with coordinates (we'll need to add lat/lng)
# For now, let's create a simple aggregation by birthplace
city_counts <- commanders %>%
  filter(!is.na(birthplace) & birthplace != "") %>%
  group_by(birthplace) %>%
  summarise(
    count = n(),
    commanders = paste(name, collapse = "; "),
    .groups = 'drop'
  )

# Add coordinates manually for top cities (POC - will automate later)
city_coords <- data.frame(
  birthplace = c("İstanbul", "Ankara", "Erzurum", "Selanik", "Trabzon", "Manisa", 
                 "Konya", "Kayseri", "Erzincan", "Samsun", "Afyonkarahisar"),
  Latitude = c(41.0082, 39.9334, 39.9, 40.6401, 41.0, 38.62, 37.87, 38.73, 39.75, 41.29, 38.75),
  Longitude = c(28.9784, 32.8597, 41.27, 22.9444, 39.72, 27.43, 32.48, 35.49, 39.49, 36.33, 30.54)
)

city_counts <- city_counts %>%
  left_join(city_coords, by = "birthplace") %>%
  filter(!is.na(Latitude))

# Create a simple color palette
pal <- colorNumeric(
  palette = c("#e8e8e8", "#a8b88f", "#6c8450", "#2d3a1a", "#1a2410"),
  domain = city_counts$count
)

# Create the map
map <- leaflet(city_counts) %>%
  addTiles() %>%
  setView(lng = 35, lat = 39, zoom = 6) %>%
  addCircleMarkers(
    ~Longitude, ~Latitude,
    radius = ~sqrt(count) * 3,
    color = ~pal(count),
    fillOpacity = 0.7,
    stroke = TRUE,
    weight = 1,
    popup = ~paste0(
      "<strong>", birthplace, "</strong><br/>",
      "Commanders: ", count, "<br/>",
      "<small>", commanders, "</small>"
    )
  ) %>%
  addLegend(
    position = "bottomright",
    pal = pal,
    values = ~count,
    title = "# of Commanders",
    opacity = 0.9
  )

# Save to docs folder for GitHub Pages
dir.create("docs", showWarnings = FALSE, recursive = TRUE)
saveWidget(map, file = "docs/commanders-map.html", selfcontained = TRUE)

cat("✓ Map created: docs/commanders-map.html\n")
cat("✓ Ready for GitHub Pages!\n")
