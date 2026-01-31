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

# Load both datasets
message("Loading Chiefs of General Staff data...")
chiefs <- read_csv("data/chiefs_of_staff.csv", show_col_types = FALSE)

message("Loading Army Commanders data...")
army <- read_csv("data/army_commanders.csv", show_col_types = FALSE)

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
  
  # Ensure 0 gets its own bin (light gray) and other values get green shades
  # Using .5 values to separate integers but will format labels as integers
  colorBin(
    palette = c("#e8e8e8", "#a8b88f", "#8a9e6f", "#6c8450", "#4d6a30", "#2d3a1a"),
    domain = 0:max_count,
    bins = c(-0.5, 0.5, 1.5, 2.5, 3.5, 5.5, max_count + 0.5),
    na.color = "#e8e8e8"
  )
}

chiefs_pal <- create_palette(chiefs_provinces)
army_pal <- create_palette(army_provinces)

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
    baseGroups = c("Chiefs of General Staff", "Army Commanders"),
    overlayGroups = "Cities",
    options = layersControlOptions(collapsed = FALSE),
    position = "topleft"
  ) %>%
  hideGroup("Army Commanders") %>%  # Hide army by default
  addLegend(
    position = "bottomright",
    colors = c("#e8e8e8", "#a8b88f", "#8a9e6f", "#6c8450", "#4d6a30", "#2d3a1a"),
    labels = c("0", "1", "2", "3", "4", "5 - 9"),
    title = "Number of<br/>Chiefs/Commanders",
    opacity = 0.9
  ) %>%
  addControl(
    html = '<div id="map-info-panel" style="background: rgba(255,255,255,0.97); padding: 18px 24px; border-radius: 10px; box-shadow: 0 4px 12px rgba(0,0,0,0.15); font-family: -apple-system, BlinkMacSystemFont, \'Segoe UI\', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif; margin-top: 10px;">
              <div id="info-chiefs" style="display: block;">
                <h4 style="margin: 0 0 10px 0; color: #2d3a1a; font-size: 16px; font-weight: 600;">Chiefs of General Staff</h4>
                <p style="margin: 6px 0; color: #444; font-size: 14px; line-height: 1.6;">Republic Era (1923-Present)</p>
                <p style="margin: 6px 0; color: #444; font-size: 14px; font-weight: 500;">Total: 30 Chiefs</p>
                <p style="margin: 6px 0 0 0; font-size: 13px; color: #666; line-height: 1.4; font-style: italic;">4 from Thessaloniki/Greece<br/>1 from Rahova/Romania</p>
              </div>
              <div id="info-army" style="display: none;">
                <h4 style="margin: 0 0 10px 0; color: #2d3a1a; font-size: 16px; font-weight: 600;">Army Commanders</h4>
                <p style="margin: 6px 0; color: #444; font-size: 14px; line-height: 1.6;">1949-Present</p>
                <p style="margin: 6px 0; color: #444; font-size: 14px; font-weight: 500;">Total: 52 Commanders</p>
                <p style="margin: 6px 0 0 0; font-size: 13px; color: #666; line-height: 1.4; font-style: italic;">2 from Thessaloniki/Greece<br/>1 from Rahova/Romania<br/>1 from Bitola/N. Macedonia</p>
              </div>
            </div>
            <script>
              (function() {
                function updateInfoPanel(mapType) {
                  var chiefsDiv = document.getElementById(\'info-chiefs\');
                  var armyDiv = document.getElementById(\'info-army\');
                  
                  if (chiefsDiv && armyDiv) {
                    if (mapType === \'chiefs\') {
                      chiefsDiv.style.display = \'block\';
                      armyDiv.style.display = \'none\';
                    } else if (mapType === \'army\') {
                      chiefsDiv.style.display = \'none\';
                      armyDiv.style.display = \'block\';
                    }
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
                        }
                      });
                    });
                  }, 300);
                }
              })();
            </script>',
    position = "topleft"
  )

message("Saving combined interactive map...")
saveWidget(map, "combined_birthplace_interactive.html", selfcontained = TRUE)

message("\n============================================================")
message("Combined interactive map complete!")
message("Open combined_birthplace_interactive.html in your browser")
message("Use the selector to switch between Chiefs and Army Commanders")
message("============================================================\n")
