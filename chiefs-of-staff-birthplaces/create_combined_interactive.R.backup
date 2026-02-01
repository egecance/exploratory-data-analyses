#!/usr/bin/env Rscript

# Combined Interactive Choropleth Map
# User can toggle between Chiefs of General Staff and Army Commanders

library(tidyverse)
library(sf)
library(leaflet)
library(htmlwidgets)
library(rnaturalearth)

message("Loading geographic data...")

# Load all provinces data
all_provinces <- st_read("data/turkey_greece_provinces_with_chiefs.geojson", quiet = TRUE)

# Function to transliterate Turkish characters
transliterate_turkish <- function(text) {
  text %>%
    gsub("İ", "I", .) %>%
    gsub("ı", "i", .) %>%
    gsub("Ğ", "G", .) %>%
    gsub("ğ", "g", .) %>%
    gsub("Ü", "U", .) %>%
    gsub("ü", "u", .) %>%
    gsub("Ş", "S", .) %>%
    gsub("ş", "s", .) %>%
    gsub("Ö", "O", .) %>%
    gsub("ö", "o", .) %>%
    gsub("Ç", "C", .) %>%
    gsub("ç", "c", .)
}

# Transliterate province names in geojson for matching
all_provinces <- all_provinces %>%
  mutate(name_en_clean = transliterate_turkish(name_en))

# Load all four datasets
message("Loading Chiefs of General Staff data...")
chiefs <- read_csv("data/chiefs_of_staff.csv", show_col_types = FALSE)

message("Loading Army Commanders data...")
army <- read_csv("data/army_commanders.csv", show_col_types = FALSE)

message("Loading Naval Commanders data...")
navy <- read_csv("data/naval_commanders.csv", show_col_types = FALSE)

message("Loading Air Force Commanders data...")
airforce <- read_csv("data/air_force_commanders.csv", show_col_types = FALSE)

# Aggregate data for chiefs
message("Aggregating Chiefs data by birthplace...")

chiefs_counts <- chiefs %>%
  mutate(birthplace = case_when(
    birthplace == "Selanik" ~ "Centre Macedonia",
    birthplace == "Rahova" ~ "Olt",
    birthplace == "Manastır" ~ "Bitola",
    TRUE ~ transliterate_turkish(birthplace)
  )) %>%
  group_by(birthplace) %>%
  summarise(
    count = n(),
    names = paste(name, collapse = "; ")
  ) %>%
  rename(name_en_clean = birthplace)

# Aggregate data for army commanders
message("Aggregating Army Commanders data by birthplace...")
army_counts <- army %>%
  mutate(birthplace = case_when(
    birthplace == "Selanik" ~ "Centre Macedonia",
    birthplace == "Rahova" ~ "Olt",
    birthplace == "Manastır" ~ "Bitola",
    TRUE ~ transliterate_turkish(birthplace)
  )) %>%
  group_by(birthplace) %>%
  summarise(
    count = n(),
    names = paste(name, collapse = "; ")
  ) %>%
  rename(name_en_clean = birthplace)

# Aggregate data for naval commanders
message("Aggregating Naval Commanders data by birthplace...")
navy_counts <- navy %>%
  filter(status == "found", !is.na(birthplace), birthplace != "") %>%
  mutate(birthplace = case_when(
    birthplace == "Adalar" ~ "Istanbul",
    str_detect(birthplace, "Sinop") ~ "Sinop",
    str_detect(birthplace, "Osmanlı") ~ NA_character_,
    birthplace == "Türkiye" ~ NA_character_,
    TRUE ~ transliterate_turkish(birthplace)
  )) %>%
  filter(!is.na(birthplace)) %>%
  group_by(birthplace) %>%
  summarise(
    count = n(),
    names = paste(name, collapse = "; ")
  ) %>%
  rename(name_en_clean = birthplace)

# Aggregate data for air force commanders
message("Aggregating Air Force Commanders data by birthplace...")
airforce_counts <- airforce %>%
  filter(status == "found", !is.na(birthplace), birthplace != "") %>%
  mutate(birthplace = case_when(
    birthplace == "Havza" ~ "Samsun",
    birthplace == "Of" ~ "Trabzon",
    str_detect(birthplace, "Osmanlı") ~ NA_character_,
    birthplace == "Türkiye" ~ NA_character_,
    TRUE ~ transliterate_turkish(birthplace)
  )) %>%
  filter(!is.na(birthplace)) %>%
  group_by(birthplace) %>%
  summarise(
    count = n(),
    names = paste(name, collapse = "; ")
  ) %>%
  rename(name_en_clean = birthplace)

# Create combined summary (any commander from any branch)
message("Creating combined summary...")
all_commanders <- bind_rows(
  chiefs %>% select(name, birthplace) %>% mutate(source = "Chiefs"),
  army %>% select(name, birthplace) %>% mutate(source = "Army"),
  navy %>% filter(status == "found", !is.na(birthplace), birthplace != "") %>% 
    select(name, birthplace) %>% mutate(source = "Navy"),
  airforce %>% filter(status == "found", !is.na(birthplace), birthplace != "") %>% 
    select(name, birthplace) %>% mutate(source = "Air Force")
)

combined_counts <- all_commanders %>%
  mutate(birthplace = case_when(
    birthplace == "Selanik" ~ "Centre Macedonia",
    birthplace == "Rahova" ~ "Olt",
    birthplace == "Manastır" ~ "Bitola",
    birthplace == "Adalar" ~ "Istanbul",
    str_detect(birthplace, "Sinop") ~ "Sinop",
    birthplace == "Havza" ~ "Samsun",
    birthplace == "Of" ~ "Trabzon",
    str_detect(birthplace, "Osmanlı") ~ NA_character_,
    birthplace == "Türkiye" ~ NA_character_,
    TRUE ~ transliterate_turkish(birthplace)
  )) %>%
  filter(!is.na(birthplace)) %>%
  group_by(birthplace, name) %>%
  summarise(
    sources = paste(source, collapse = ", "),
    .groups = "drop"
  ) %>%
  group_by(birthplace) %>%
  summarise(
    count = n(),
    names = paste0(name, " (", sources, ")", collapse = "; ")
  ) %>%
  rename(name_en_clean = birthplace)

# Merge with geographic data
chiefs_provinces <- all_provinces %>%
  left_join(chiefs_counts, by = "name_en_clean") %>%
  mutate(
    count = replace_na(count, 0),
    names = replace_na(names, "")
  )

army_provinces <- all_provinces %>%
  left_join(army_counts, by = "name_en_clean") %>%
  mutate(
    count = replace_na(count, 0),
    names = replace_na(names, "")
  )

navy_provinces <- all_provinces %>%
  left_join(navy_counts, by = "name_en_clean") %>%
  mutate(
    count = replace_na(count, 0),
    names = replace_na(names, "")
  )

airforce_provinces <- all_provinces %>%
  left_join(airforce_counts, by = "name_en_clean") %>%
  mutate(
    count = replace_na(count, 0),
    names = replace_na(names, "")
  )

combined_provinces <- all_provinces %>%
  left_join(combined_counts, by = "name_en_clean") %>%
  mutate(
    count = replace_na(count, 0),
    names = replace_na(names, "")
  )

# Calculate top 3 cities for all datasets
chiefs_top3 <- chiefs %>%
  count(birthplace, sort = TRUE) %>%
  head(3)

army_top3 <- army %>%
  count(birthplace, sort = TRUE) %>%
  head(3)

navy_top3 <- navy %>%
  filter(status == "found", !is.na(birthplace), birthplace != "", 
         !str_detect(birthplace, "Osmanlı"), birthplace != "Türkiye") %>%
  count(birthplace, sort = TRUE) %>%
  head(3)

airforce_top3 <- airforce %>%
  filter(status == "found", !is.na(birthplace), birthplace != "", 
         !str_detect(birthplace, "Osmanlı"), birthplace != "Türkiye") %>%
  count(birthplace, sort = TRUE) %>%
  head(3)

# Create summary HTML strings
chiefs_summary_html <- paste0(
  "1. ", chiefs_top3$birthplace[1], " (", chiefs_top3$n[1], ")<br/>",
  "2. ", chiefs_top3$birthplace[2], " (", chiefs_top3$n[2], ")<br/>",
  "3. ", chiefs_top3$birthplace[3], " (", chiefs_top3$n[3], ")"
)

army_summary_html <- paste0(
  "1. ", army_top3$birthplace[1], " (", army_top3$n[1], ")<br/>",
  "2. ", army_top3$birthplace[2], " (", army_top3$n[2], ")<br/>",
  "3. ", army_top3$birthplace[3], " (", army_top3$n[3], ")"
)

navy_summary_html <- paste0(
  "1. ", navy_top3$birthplace[1], " (", navy_top3$n[1], ")<br/>",
  "2. ", navy_top3$birthplace[2], " (", navy_top3$n[2], ")<br/>",
  "3. ", navy_top3$birthplace[3], " (", navy_top3$n[3], ")"
)

airforce_summary_html <- paste0(
  "1. ", airforce_top3$birthplace[1], " (", airforce_top3$n[1], ")<br/>",
  "2. ", airforce_top3$birthplace[2], " (", airforce_top3$n[2], ")<br/>",
  "3. ", airforce_top3$birthplace[3], " (", airforce_top3$n[3], ")"
)

# Define city locations
cities <- data.frame(
  city = c("Istanbul", "Ankara", "Erzurum", "Selanik", "Rahova"),
  lat = c(41.0082, 39.9334, 39.9000, 40.6401, 43.6979),
  lng = c(28.9784, 32.8597, 41.2700, 22.9444, 24.7170)
)

message("Creating combined interactive map...")

# Create color palette function with dynamic bins
create_palette <- function(data) {
  max_count <- max(data$count, na.rm = TRUE)
  
  if (max_count <= 1) {
    colorBin(
      palette = c("#e8e8e8", "#6c8450"),
      domain = 0:max_count,
      bins = c(-0.5, 0.5, 1.5),
      na.color = "#e8e8e8"
    )
  } else if (max_count <= 3) {
    colorBin(
      palette = c("#e8e8e8", "#a8b88f", "#6c8450", "#2d3a1a"),
      domain = 0:max_count,
      bins = c(-0.5, 0.5, 1.5, 2.5, max_count + 0.5),
      na.color = "#e8e8e8"
    )
  } else if (max_count <= 9) {
    colorBin(
      palette = c("#e8e8e8", "#a8b88f", "#8a9e6f", "#6c8450", "#4d6a30", "#2d3a1a"),
      domain = 0:max_count,
      bins = c(-0.5, 0.5, 1.5, 2.5, 3.5, 5.5, max_count + 0.5),
      na.color = "#e8e8e8"
    )
  } else if (max_count <= 14) {
    colorBin(
      palette = c("#e8e8e8", "#c4d4a8", "#a8b88f", "#8a9e6f", "#6c8450", "#4d6a30", "#3a5020", "#2d3a1a"),
      domain = 0:max_count,
      bins = c(-0.5, 0.5, 1.5, 2.5, 4.5, 7.5, 10.5, max_count + 0.5),
      na.color = "#e8e8e8"
    )
  } else {
    colorBin(
      palette = c("#e8e8e8", "#d4e0b8", "#c4d4a8", "#a8b88f", "#8a9e6f", "#6c8450", "#4d6a30", "#3a5020", "#2d3a1a", "#1a2410"),
      domain = 0:max_count,
      bins = c(-0.5, 0.5, 1.5, 2.5, 4.5, 7.5, 10.5, 15.5, 20.5, max_count + 0.5),
      na.color = "#e8e8e8"
    )
  }
}

chiefs_pal <- create_palette(chiefs_provinces)
army_pal <- create_palette(army_provinces)
# Use simpler palettes for Navy and Air Force (fewer commanders per city)
navy_pal <- colorBin(
  palette = c("#e8e8e8", "#a8b88f", "#6c8450", "#2d3a1a"),
  domain = 0:10,
  bins = c(-0.5, 0.5, 2.5, 5.5, 10.5),
  na.color = "#e8e8e8"
)
airforce_pal <- colorBin(
  palette = c("#e8e8e8", "#a8b88f", "#6c8450", "#2d3a1a"),
  domain = 0:10,
  bins = c(-0.5, 0.5, 2.5, 5.5, 10.5),
  na.color = "#e8e8e8"
)
combined_pal <- create_palette(combined_provinces)

# Create base map
map <- leaflet() %>%
  setView(lng = 32.5, lat = 39, zoom = 5)

# Add Chiefs polygons (visible by default)
map <- map %>%
  addPolygons(
    data = chiefs_provinces,
    fillColor = ~chiefs_pal(count),
    fillOpacity = 0.9,
    color = "white",
    weight = 1,
    opacity = 0.5,
    label = ~lapply(paste0(
      "<div style='min-width: 200px;'>",
      "<strong style='font-size: 15px; color: #2d3a1a;'>", name_en, "</strong><br/>",
      "<span style='font-size: 14px; font-weight: 600; margin-top: 6px; display: inline-block;'>Chiefs: ", count, "</span>",
      ifelse(count > 0, 
        paste0("<br/><span style='font-size: 12px; color: #555; margin-top: 4px; display: inline-block; line-height: 1.4;'>", 
               gsub(";", ";<br/>", names), 
               "</span>"),
        ""),
      "</div>"
    ), htmltools::HTML),
    labelOptions = labelOptions(
      style = list(
        "font-family" = "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif",
        "padding" = "10px 14px",
        "border-radius" = "8px",
        "box-shadow" = "0 3px 10px rgba(0,0,0,0.2)",
        "background" = "rgba(255,255,255,0.98)"
      ),
      direction = "auto"
    ),
    highlightOptions = highlightOptions(
      weight = 2,
      color = "#2d3a1a",
      fillOpacity = 0.95,
      bringToFront = TRUE
    ),
    group = "Chiefs of General Staff",
    layerId = ~paste0("chiefs_", name_en)
  )

# Add Army Commanders polygons (hidden by default)
map <- map %>%
  addPolygons(
    data = army_provinces,
    fillColor = ~army_pal(count),
    fillOpacity = 0.9,
    color = "white",
    weight = 1,
    opacity = 0.5,
    label = ~lapply(paste0(
      "<div style='min-width: 200px;'>",
      "<strong style='font-size: 15px; color: #2d3a1a;'>", name_en, "</strong><br/>",
      "<span style='font-size: 14px; font-weight: 600; margin-top: 6px; display: inline-block;'>Commanders: ", count, "</span>",
      ifelse(count > 0, 
        paste0("<br/><span style='font-size: 12px; color: #555; margin-top: 4px; display: inline-block; line-height: 1.4;'>", 
               gsub(";", ";<br/>", names), 
               "</span>"),
        ""),
      "</div>"
    ), htmltools::HTML),
    labelOptions = labelOptions(
      style = list(
        "font-family" = "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif",
        "padding" = "10px 14px",
        "border-radius" = "8px",
        "box-shadow" = "0 3px 10px rgba(0,0,0,0.2)",
        "background" = "rgba(255,255,255,0.98)"
      ),
      direction = "auto"
    ),
    highlightOptions = highlightOptions(
      weight = 2,
      color = "#2d3a1a",
      fillOpacity = 0.95,
      bringToFront = TRUE
    ),
    group = "Army Commanders",
    layerId = ~paste0("army_", name_en)
  )

# Add Naval Commanders polygons (hidden by default)
map <- map %>%
  addPolygons(
    data = navy_provinces,
    fillColor = ~navy_pal(count),
    fillOpacity = 0.9,
    color = "white",
    weight = 1,
    opacity = 0.5,
    label = ~lapply(paste0(
      "<div style='min-width: 200px;'>",
      "<strong style='font-size: 15px; color: #2d3a1a;'>", name_en, "</strong><br/>",
      "<span style='font-size: 14px; font-weight: 600; margin-top: 6px; display: inline-block;'>Naval Commanders: ", count, "</span>",
      ifelse(count > 0, 
        paste0("<br/><span style='font-size: 12px; color: #555; margin-top: 4px; display: inline-block; line-height: 1.4;'>", 
               gsub(";", ";<br/>", names), 
               "</span>"),
        ""),
      "</div>"
    ), htmltools::HTML),
    labelOptions = labelOptions(
      style = list(
        "font-family" = "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif",
        "padding" = "10px 14px",
        "border-radius" = "8px",
        "box-shadow" = "0 3px 10px rgba(0,0,0,0.2)",
        "background" = "rgba(255,255,255,0.98)"
      ),
      direction = "auto"
    ),
    highlightOptions = highlightOptions(
      weight = 2,
      color = "#2d3a1a",
      fillOpacity = 0.95,
      bringToFront = TRUE
    ),
    group = "Naval Commanders",
    layerId = ~paste0("navy_", name_en)
  )

# Add Air Force Commanders polygons (hidden by default)
map <- map %>%
  addPolygons(
    data = airforce_provinces,
    fillColor = ~airforce_pal(count),
    fillOpacity = 0.9,
    color = "white",
    weight = 1,
    opacity = 0.5,
    label = ~lapply(paste0(
      "<div style='min-width: 200px;'>",
      "<strong style='font-size: 15px; color: #2d3a1a;'>", name_en, "</strong><br/>",
      "<span style='font-size: 14px; font-weight: 600; margin-top: 6px; display: inline-block;'>Air Force Commanders: ", count, "</span>",
      ifelse(count > 0, 
        paste0("<br/><span style='font-size: 12px; color: #555; margin-top: 4px; display: inline-block; line-height: 1.4;'>", 
               gsub(";", ";<br/>", names), 
               "</span>"),
        ""),
      "</div>"
    ), htmltools::HTML),
    labelOptions = labelOptions(
      style = list(
        "font-family" = "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif",
        "padding" = "10px 14px",
        "border-radius" = "8px",
        "box-shadow" = "0 3px 10px rgba(0,0,0,0.2)",
        "background" = "rgba(255,255,255,0.98)"
      ),
      direction = "auto"
    ),
    highlightOptions = highlightOptions(
      weight = 2,
      color = "#2d3a1a",
      fillOpacity = 0.95,
      bringToFront = TRUE
    ),
    group = "Air Force Commanders",
    layerId = ~paste0("airforce_", name_en)
  )

# Add Combined Summary polygons (hidden by default)
map <- map %>%
  addPolygons(
    data = combined_provinces,
    fillColor = ~combined_pal(count),
    fillOpacity = 0.9,
    color = "white",
    weight = 1,
    opacity = 0.5,
    label = ~lapply(paste0(
      "<div style='min-width: 250px;'>",
      "<strong style='font-size: 15px; color: #2d3a1a;'>", name_en, "</strong><br/>",
      "<span style='font-size: 14px; font-weight: 600; margin-top: 6px; display: inline-block;'>Total Commanders: ", count, "</span>",
      ifelse(count > 0, 
        paste0("<br/><span style='font-size: 11px; color: #555; margin-top: 4px; display: inline-block; line-height: 1.4;'>", 
               gsub(";", ";<br/>", names), 
               "</span>"),
        ""),
      "</div>"
    ), htmltools::HTML),
    labelOptions = labelOptions(
      style = list(
        "font-family" = "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif",
        "padding" = "10px 14px",
        "border-radius" = "8px",
        "box-shadow" = "0 3px 10px rgba(0,0,0,0.2)",
        "background" = "rgba(255,255,255,0.98)"
      ),
      direction = "auto"
    ),
    highlightOptions = highlightOptions(
      weight = 2,
      color = "#2d3a1a",
      fillOpacity = 0.95,
      bringToFront = TRUE
    ),
    group = "Combined Summary",
    layerId = ~paste0("combined_", name_en)
  )

# Add city markers
for (i in 1:nrow(cities)) {
  map <- map %>%
    addCircleMarkers(
      lng = cities$lng[i], lat = cities$lat[i],
      radius = 4,
      color = "#c41e3a",
      fillColor = "#c41e3a",
      fillOpacity = 0.8,
      weight = 2,
      opacity = 1,
      popup = cities$city[i],
      group = "Cities"
    ) %>%
    addLabelOnlyMarkers(
      lng = cities$lng[i], lat = cities$lat[i],
      label = cities$city[i],
      labelOptions = labelOptions(
        noHide = TRUE,
        direction = "top",
        textOnly = TRUE,
        style = list(
          "color" = "#c41e3a",
          "font-family" = "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif",
          "font-size" = "12px",
          "font-weight" = "600",
          "text-shadow" = "1px 1px 2px white, -1px -1px 2px white, 1px -1px 2px white, -1px 1px 2px white"
        )
      ),
      group = "Cities"
    )
}

# Add custom control for switching datasets
map <- map %>%
  addLayersControl(
    baseGroups = c("Chiefs of General Staff", "Army Commanders", "Naval Commanders", "Air Force Commanders", "Combined Summary"),
    overlayGroups = "Cities",
    options = layersControlOptions(collapsed = FALSE),
    position = "topleft"
  ) %>%
  hideGroup(c("Army Commanders", "Naval Commanders", "Air Force Commanders", "Combined Summary", "Cities")) %>%  # Hide all except chiefs by default, and hide city labels
  addLegend(
    position = "bottomright",
    colors = c("#e8e8e8", "#d4e0b8", "#c4d4a8", "#a8b88f", "#8a9e6f", "#6c8450", "#4d6a30", "#3a5020", "#2d3a1a", "#1a2410"),
    labels = c("0", "1", "2", "3-4", "5-7", "8-10", "11-15", "16-20", "21-25", "26+"),
    title = "Number of<br/>Commanders",
    opacity = 0.9
  ) %>%
  addControl(
    html = paste0('<div id="map-info-panel" style="background: rgba(255,255,255,0.97); padding: 18px 24px; border-radius: 10px; box-shadow: 0 4px 12px rgba(0,0,0,0.15); font-family: -apple-system, BlinkMacSystemFont, \'Segoe UI\', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif; margin-top: 10px;">
              <div id="info-chiefs" style="display: block;">
                <h4 style="margin: 0 0 10px 0; color: #2d3a1a; font-size: 16px; font-weight: 600;">Chiefs of General Staff</h4>
                <p style="margin: 6px 0; color: #444; font-size: 14px; line-height: 1.6;"><strong>Period:</strong> 1923-Present</p>
                <p style="margin: 6px 0; color: #444; font-size: 14px; font-weight: 500;"><strong>Total:</strong> 30 Chiefs</p>
                <p style="margin: 6px 0; color: #444; font-size: 13px; line-height: 1.5;"><strong>Key Facts:</strong></p>
                <p style="margin: 2px 0 0 8px; font-size: 12px; color: #666; line-height: 1.4;">• 26 from Turkey<br/>• 4 from Greece (Thessaloniki)<br/>• 1 from Romania (Rahova)<br/>• Highest concentration: Istanbul (8)</p>
              </div>
              <div id="info-army" style="display: none;">
                <h4 style="margin: 0 0 10px 0; color: #2d3a1a; font-size: 16px; font-weight: 600;">Army Commanders</h4>
                <p style="margin: 6px 0; color: #444; font-size: 14px; line-height: 1.6;"><strong>Period:</strong> 1949-Present</p>
                <p style="margin: 6px 0; color: #444; font-size: 14px; font-weight: 500;"><strong>Total:</strong> 52 Commanders</p>
                <p style="margin: 6px 0; color: #444; font-size: 13px; line-height: 1.5;"><strong>Key Facts:</strong></p>
                <p style="margin: 2px 0 0 8px; font-size: 12px; color: #666; line-height: 1.4;">• 48 from Turkey<br/>• 2 from Greece (Thessaloniki)<br/>• 1 from Romania (Rahova)<br/>• 1 from North Macedonia (Bitola)<br/>• Highest concentration: Istanbul (12)</p>
              </div>
              <div id="info-navy" style="display: none;">
                <h4 style="margin: 0 0 10px 0; color: #2d3a1a; font-size: 16px; font-weight: 600;">Naval Commanders</h4>
                <p style="margin: 6px 0; color: #444; font-size: 14px; line-height: 1.6;"><strong>Period:</strong> 1949-Present</p>
                <p style="margin: 6px 0; color: #444; font-size: 14px; font-weight: 500;"><strong>Total:</strong> 27 Commanders</p>
                <p style="margin: 6px 0; color: #444; font-size: 13px; line-height: 1.5;"><strong>Key Facts:</strong></p>
                <p style="margin: 2px 0 0 8px; font-size: 12px; color: #666; line-height: 1.4;">• All data verified (100%)<br/>• Highest concentration: Istanbul (8)<br/>• Notable: Kocaeli (2)<br/>• Geographic spread: 14 cities</p>
              </div>
              <div id="info-airforce" style="display: none;">
                <h4 style="margin: 0 0 10px 0; color: #2d3a1a; font-size: 16px; font-weight: 600;">Air Force Commanders</h4>
                <p style="margin: 6px 0; color: #444; font-size: 14px; line-height: 1.6;"><strong>Period:</strong> 1944-Present</p>
                <p style="margin: 6px 0; color: #444; font-size: 14px; font-weight: 500;"><strong>Total:</strong> 34 Commanders</p>
                <p style="margin: 6px 0; color: #444; font-size: 13px; line-height: 1.5;"><strong>Key Facts:</strong></p>
                <p style="margin: 2px 0 0 8px; font-size: 12px; color: #666; line-height: 1.4;">• Data found: 21 of 34 (62%)<br/>• 13 commanders missing birthplace data<br/>• Notable: Tahsin Şahinkaya (Amasya)<br/>• Geographic spread: 15 cities</p>
              </div>
              <div id="info-combined" style="display: none;">
                <h4 style="margin: 0 0 10px 0; color: #2d3a1a; font-size: 16px; font-weight: 600;">Combined Summary</h4>
                <p style="margin: 6px 0; color: #444; font-size: 14px; line-height: 1.6;"><strong>Period:</strong> 1923-Present</p>
                <p style="margin: 6px 0; color: #444; font-size: 14px; font-weight: 500;"><strong>Total:</strong> 143 Commanders</p>
                <p style="margin: 6px 0; color: #444; font-size: 13px; line-height: 1.5;"><strong>Breakdown:</strong></p>
                <p style="margin: 2px 0 0 8px; font-size: 12px; color: #666; line-height: 1.4;">• Chiefs: 30<br/>• Army: 52<br/>• Navy: 27<br/>• Air Force: 34<br/>• Shows any city with ≥1 commander</p>
              </div>
            </div>
            <div id="map-summary-panel" style="background: rgba(255,255,255,0.97); padding: 18px 24px; border-radius: 10px; box-shadow: 0 4px 12px rgba(0,0,0,0.15); font-family: -apple-system, BlinkMacSystemFont, \'Segoe UI\', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif; margin-top: 10px;">
              <h4 style="margin: 0 0 12px 0; color: #2d3a1a; font-size: 15px; font-weight: 600;">Top Birthplaces</h4>
              <div id="summary-chiefs" style="margin-bottom: 14px; display: block;">
                <p style="margin: 0 0 6px 0; color: #2d3a1a; font-size: 13px; font-weight: 600;">Chiefs of General Staff:</p>
                <p style="margin: 2px 0; color: #444; font-size: 12px; line-height: 1.6;">', chiefs_summary_html, '</p>
              </div>
              <div id="summary-army" style="margin-bottom: 14px; display: none;">
                <p style="margin: 0 0 6px 0; color: #2d3a1a; font-size: 13px; font-weight: 600;">Army Commanders:</p>
                <p style="margin: 2px 0; color: #444; font-size: 12px; line-height: 1.6;">', army_summary_html, '</p>
              </div>
              <div id="summary-navy" style="margin-bottom: 14px; display: none;">
                <p style="margin: 0 0 6px 0; color: #2d3a1a; font-size: 13px; font-weight: 600;">Naval Commanders:</p>
                <p style="margin: 2px 0; color: #444; font-size: 12px; line-height: 1.6;">', navy_summary_html, '</p>
              </div>
              <div id="summary-airforce" style="margin-bottom: 14px; display: none;">
                <p style="margin: 0 0 6px 0; color: #2d3a1a; font-size: 13px; font-weight: 600;">Air Force Commanders:</p>
                <p style="margin: 2px 0; color: #444; font-size: 12px; line-height: 1.6;">', airforce_summary_html, '</p>
              </div>
              <div id="summary-combined" style="display: none;">
                <p style="margin: 0 0 6px 0; color: #2d3a1a; font-size: 13px; font-weight: 600;">Cities with Commanders:</p>
                <p style="margin: 2px 0; color: #444; font-size: 12px; line-height: 1.6;">Shows any city that produced at least one commander across all branches</p>
              </div>
            </div>
            <script>
              (function() {
                function updateInfoPanel(mapType) {
                  var infoIds = [\'info-chiefs\', \'info-army\', \'info-navy\', \'info-airforce\', \'info-combined\'];
                  var summaryIds = [\'summary-chiefs\', \'summary-army\', \'summary-navy\', \'summary-airforce\', \'summary-combined\'];
                  
                  infoIds.forEach(function(id) {
                    var el = document.getElementById(id);
                    if (el) el.style.display = \'none\';
                  });
                  
                  summaryIds.forEach(function(id) {
                    var el = document.getElementById(id);
                    if (el) el.style.display = \'none\';
                  });
                  
                  if (mapType === \'chiefs\') {
                    document.getElementById(\'info-chiefs\').style.display = \'block\';
                    document.getElementById(\'summary-chiefs\').style.display = \'block\';
                  } else if (mapType === \'army\') {
                    document.getElementById(\'info-army\').style.display = \'block\';
                    document.getElementById(\'summary-army\').style.display = \'block\';
                  } else if (mapType === \'navy\') {
                    document.getElementById(\'info-navy\').style.display = \'block\';
                    document.getElementById(\'summary-navy\').style.display = \'block\';
                  } else if (mapType === \'airforce\') {
                    document.getElementById(\'info-airforce\').style.display = \'block\';
                    document.getElementById(\'summary-airforce\').style.display = \'block\';
                  } else if (mapType === \'combined\') {
                    document.getElementById(\'info-combined\').style.display = \'block\';
                    document.getElementById(\'summary-combined\').style.display = \'block\';
                  }
                }
                
                if (document.readyState === \'loading\') {
                  document.addEventListener(\'DOMContentLoaded\', init);
                } else {
                  init();
                }
                
                function init() {
                  updateInfoPanel(\'chiefs\');
                  
                  var attempts = 0;
                  var checkLeaflet = setInterval(function() {
                    attempts++;
                    var mapContainer = document.querySelector(\'.leaflet-container\');
                    
                    if (mapContainer && mapContainer._leaflet_map) {
                      clearInterval(checkLeaflet);
                      setupListeners(mapContainer._leaflet_map);
                    } else if (attempts >= 20) {
                      clearInterval(checkLeaflet);
                    }
                  }, 100);
                }
                
                function setupListeners(leafletMap) {
                  leafletMap.on(\'baselayerchange\', function(e) {
                    if (e.name && e.name.indexOf(\'Chiefs\') >= 0) {
                      updateInfoPanel(\'chiefs\');
                    } else if (e.name && e.name.indexOf(\'Army\') >= 0) {
                      updateInfoPanel(\'army\');
                    } else if (e.name && e.name.indexOf(\'Naval\') >= 0) {
                      updateInfoPanel(\'navy\');
                    } else if (e.name && e.name.indexOf(\'Air Force\') >= 0) {
                      updateInfoPanel(\'airforce\');
                    } else if (e.name && e.name.indexOf(\'Combined\') >= 0) {
                      updateInfoPanel(\'combined\');
                    }
                  });
                  
                  setTimeout(function() {
                    var radios = document.querySelectorAll(\'.leaflet-control-layers-base input[type="radio"]\');
                    radios.forEach(function(radio) {
                      radio.addEventListener(\'click\', function() {
                        var labelText = this.nextSibling ? this.nextSibling.textContent : \'\';
                        if (!labelText && this.parentElement) {
                          labelText = this.parentElement.textContent;
                        }
                        labelText = labelText.trim();
                        
                        if (labelText.indexOf(\'Chiefs\') >= 0) {
                          updateInfoPanel(\'chiefs\');
                        } else if (labelText.indexOf(\'Army\') >= 0) {
                          updateInfoPanel(\'army\');
                        } else if (labelText.indexOf(\'Naval\') >= 0) {
                          updateInfoPanel(\'navy\');
                        } else if (labelText.indexOf(\'Air Force\') >= 0) {
                          updateInfoPanel(\'airforce\');
                        } else if (labelText.indexOf(\'Combined\') >= 0) {
                          updateInfoPanel(\'combined\');
                        }
                      });
                    });
                  }, 300);
                }
              })();
            </script>'),
    position = "topleft"
  )

message("Saving combined interactive map...")
saveWidget(map, "docs/commanders-map.html", selfcontained = TRUE)

message("\n============================================================")
message("Combined interactive map complete!")
message("Open combined_birthplace_interactive.html in your browser")
message("Use the selector to switch between all 5 views:")
message("  - Chiefs of General Staff")
message("  - Army Commanders")
message("  - Naval Commanders")
message("  - Air Force Commanders")
message("  - Combined Summary")
message("============================================================\n")
