#!/usr/bin/env Rscript
# Turkish Army Commanders - Interactive Choropleth Map with leaflet

options(repos = c(CRAN = 'https://cloud.r-project.org'))

# Install and load packages
packages <- c("tidyverse", "sf", "rnaturalearth", "leaflet", "htmlwidgets")
for (pkg in packages) {
  if (!require(pkg, character.only = TRUE, quietly = TRUE)) {
    install.packages(pkg)
    library(pkg, character.only = TRUE)
  }
}

library(tidyverse)
library(sf)
library(rnaturalearth)
library(leaflet)
library(htmlwidgets)

cat("============================================================\n")
cat("Turkish Army Commanders - Interactive Choropleth Map\n")
cat("============================================================\n\n")

# Read the army commanders data
army_data <- read.csv("data/army_commanders.csv", stringsAsFactors = FALSE, fileEncoding = "UTF-8")

cat("Total Army Commanders:", nrow(army_data), "\n")
cat("Unique Birthplaces:", length(unique(army_data$birthplace)), "\n\n")

# Map cities to provinces
city_to_province <- tibble(
  city = c("Selanik", "Sivas", "İstanbul", "Ankara", "Rahova", "Edirne", 
           "Erzurum", "Erzincan", "Manastır", "Bolu", "Bursa", "Manisa",
           "Çanakkale", "Konya", "Amasya", "Adana", "Tokat", "Çankırı",
           "Kocaeli", "Artvin", "Bilecik", "Kütahya", "Afyonkarahisar",
           "İzmir", "Kayseri", "Trabzon", "Ardahan", "Gümüşhane"),
  province = c("Thessaloniki", "Sivas", "Istanbul", "Ankara", "Olt", "Edirne",
               "Erzurum", "Erzincan", "Pelagonia", "Bolu", "Bursa", "Manisa",
               "Canakkale", "Konya", "Amasya", "Adana", "Tokat", "Cankiri",
               "Kocaeli", "Artvin", "Bilecik", "Kutahya", "Afyonkarahisar",
               "Izmir", "Kayseri", "Trabzon", "Ardahan", "Gumushane"),
  country = c("Greece", "Turkey", "Turkey", "Turkey", "Romania", "Turkey",
              "Turkey", "Turkey", "North Macedonia", "Turkey", "Turkey", "Turkey",
              "Turkey", "Turkey", "Turkey", "Turkey", "Turkey", "Turkey",
              "Turkey", "Turkey", "Turkey", "Turkey", "Turkey",
              "Turkey", "Turkey", "Turkey", "Turkey", "Turkey")
)

# Add province mapping and count
province_counts <- army_data %>%
  left_join(city_to_province, by = c("birthplace" = "city")) %>%
  group_by(province, country) %>%
  summarise(
    count = n(),
    commanders = paste(name, collapse = ", "),
    .groups = "drop"
  )

cat("Downloading province boundaries...\n")
turkey_provinces <- ne_states(country = "turkey", returnclass = "sf")
greece_provinces <- ne_states(country = "greece", returnclass = "sf")
bulgaria_provinces <- ne_states(country = "bulgaria", returnclass = "sf")
macedonia_provinces <- ne_states(country = "macedonia", returnclass = "sf")
romania_provinces <- ne_states(country = "romania", returnclass = "sf")

cat("Loaded", nrow(turkey_provinces), "Turkish provinces\n")
cat("Loaded", nrow(greece_provinces), "Greek provinces\n")
cat("Loaded", nrow(bulgaria_provinces), "Bulgarian provinces\n")
cat("Loaded", nrow(macedonia_provinces), "North Macedonian provinces\n")
cat("Loaded", nrow(romania_provinces), "Romanian provinces\n")

# Combine all provinces
all_provinces <- bind_rows(turkey_provinces, greece_provinces, bulgaria_provinces, macedonia_provinces, romania_provinces)

# Clean province names for matching
all_provinces <- all_provinces %>%
  mutate(
    province_match = case_when(
      name == "İstanbul" ~ "Istanbul",
      name == "İzmir" ~ "Izmir",
      name == "Çanakkale" ~ "Canakkale",
      name == "Çankırı" ~ "Cankiri",
      name == "Kütahya" ~ "Kutahya",
      name == "Gümüşhane" ~ "Gumushane",
      name == "Kentrikí Makedonía" ~ "Thessaloniki",
      name == "Kentriki Makedonia" ~ "Thessaloniki",
      name == "Pelagoniski" ~ "Pelagonia",
      name == "Olt" ~ "Olt",
      TRUE ~ name
    )
  )

# Join with commander counts
provinces_with_commanders <- all_provinces %>%
  left_join(province_counts, by = c("province_match" = "province")) %>%
  mutate(
    count = replace_na(count, 0),
    commanders = replace_na(commanders, "No commanders")
  )

cat("Total provinces/regions:", nrow(provinces_with_commanders), "\n")
cat("Total commanders mapped:", sum(provinces_with_commanders$count, na.rm = TRUE), "\n\n")

# Create color palette
pal <- colorBin(
  palette = c("#e8e8e8", "#a8b88f", "#8a9e6f", "#6c8450", "#4d6a30", "#2d3a1a"),
  domain = provinces_with_commanders$count,
  bins = c(0, 1, 2, 3, 5, 7, max(provinces_with_commanders$count, na.rm = TRUE) + 1),
  na.color = "#e8e8e8"
)

# Create labels for popup
provinces_with_commanders <- provinces_with_commanders %>%
  mutate(
    popup_text = sprintf(
      "<strong>%s</strong><br/>Country: %s<br/>Commanders: %d<br/><small>%s</small>",
      province_match,
      ifelse(is.na(country), admin, as.character(country)),
      count,
      ifelse(count > 0, substr(commanders, 1, 200), "No commanders")
    )
  )

# Create interactive map
cat("Creating interactive leaflet map...\n")
map <- leaflet(provinces_with_commanders) %>%
  addProviderTiles(providers$CartoDB.Positron) %>%
  addPolygons(
    fillColor = ~pal(count),
    weight = 1,
    opacity = 1,
    color = "white",
    fillOpacity = 0.7,
    highlightOptions = highlightOptions(
      weight = 3,
      color = "#666",
      fillOpacity = 0.9,
      bringToFront = TRUE
    ),
    popup = ~popup_text
  ) %>%
  addLegend(
    pal = pal,
    values = ~count,
    opacity = 0.7,
    title = "Number of<br/>Army<br/>Commanders",
    position = "bottomright"
  ) %>%
  setView(lng = 32.5, lat = 39, zoom = 5)

# Save the map
output_file <- "army_commanders_interactive.html"
saveWidget(map, output_file, selfcontained = TRUE)
cat("✓ Saved:", output_file, "\n")

cat("\n============================================================\n")
cat("Interactive map generation complete!\n")
cat("Open", output_file, "in your browser to view the interactive map.\n")
cat("============================================================\n")
