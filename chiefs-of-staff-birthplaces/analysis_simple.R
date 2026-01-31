#!/usr/bin/env Rscript
# Turkish Military Chiefs of Staff - Birthplace Analysis with ggplot2
# Using geom_polygon to color actual province boundaries (Simplified version)

# Set CRAN mirror
options(repos = c(CRAN = "https://cloud.r-project.org"))

# Install and load required packages
packages <- c("tidyverse", "sf", "jsonlite")
for (pkg in packages) {
  if (!require(pkg, character.only = TRUE, quietly = TRUE)) {
    install.packages(pkg)
    library(pkg, character.only = TRUE)
  }
}

library(tidyverse)
library(sf)
library(jsonlite)

# Read the chiefs of staff data
chiefs_data <- read.csv("data/chiefs_of_staff.csv", stringsAsFactors = FALSE, fileEncoding = "UTF-8")

cat("============================================================\n")
cat("Turkish Military Chiefs of Staff Birthplace Analysis (R)\n")
cat("============================================================\n\n")
cat("Total Chiefs of Staff:", nrow(chiefs_data), "\n")
cat("Unique Birthplaces:", length(unique(chiefs_data$birthplace)), "\n\n")

# Count chiefs per city
city_counts <- chiefs_data %>%
  group_by(birthplace) %>%
  summarise(count = n(), .groups = 'drop') %>%
  arrange(desc(count))

print(city_counts)

# Map city names to province names
city_to_province <- tibble(
  city = c("İstanbul", "Ankara", "Selanik", "Edirne", "Erzurum", "Trabzon", 
           "Erzincan", "İzmir", "Alaşehir", "Burdur", "Elazığ", 
           "Afyonkarahisar", "Kastamonu", "Van"),
  province = c("İstanbul", "Ankara", "Selanik", "Edirne", "Erzurum", "Trabzon",
               "Erzincan", "İzmir", "Manisa", "Burdur", "Elazığ",
               "Afyonkarahisar", "Kastamonu", "Van"),
  in_turkey = c(TRUE, TRUE, FALSE, TRUE, TRUE, TRUE, 
                TRUE, TRUE, TRUE, TRUE, TRUE, 
                TRUE, TRUE, TRUE)
)

# Add province mapping
chiefs_data <- chiefs_data %>%
  left_join(city_to_province, by = c("birthplace" = "city"))

# Count chiefs per province (only Turkish provinces)
province_counts <- chiefs_data %>%
  filter(in_turkey == TRUE) %>%
  group_by(province) %>%
  summarise(
    n_chiefs = n(),
    chiefs_list = paste(name, collapse = "; "),
    .groups = 'drop'
  ) %>%
  arrange(desc(n_chiefs))

cat("\nProvince-level counts:\n")
print(province_counts)

# Download Turkey GeoJSON (province level)
geojson_file <- "data/turkey_provinces_r.geojson"

if (!file.exists(geojson_file)) {
  cat("\nDownloading Turkey province boundaries...\n")
  
  # Try to download from a reliable source
  tryCatch({
    url <- "https://raw.githubusercontent.com/codefortr/turkeygeo json/master/geo/tr-cities-basic.json"
    download.file(url, geojson_file, method = "curl", quiet = FALSE)
  }, error = function(e) {
    cat("  Download failed, trying alternative source...\n")
    # Create a simple GeoJSON with approximate province locations
    # This is a fallback - ideally we'd have actual boundaries
    cat("  Creating simplified province map...\n")
  })
}

# Read Turkey map data
cat("\nLoading Turkey province map data...\n")

# Try to read the GeoJSON
turkey_sf <- tryCatch({
  st_read(geojson_file, quiet = TRUE)
}, error = function(e) {
  cat("  Could not load GeoJSON, creating from coordinates...\n")
  # Create simple points that we'll buffer to make "provinces"
  coords_data <- read.csv("data/city_coordinates.csv", stringsAsFactors = FALSE, fileEncoding = "UTF-8")
  
  # Convert to sf object with points
  turkey_sf_points <- st_as_sf(coords_data, 
                                 coords = c("longitude", "latitude"),
                                 crs = 4326)
  
  # Buffer points to create circular "provinces" (50km radius)
  turkey_sf_buffered <- st_buffer(turkey_sf_points, dist = 0.5)  # ~50km in degrees
  
  turkey_sf_buffered$name <- turkey_sf_buffered$city
  return(turkey_sf_buffered)
})

cat("  Loaded", nrow(turkey_sf), "province boundaries\n")

# Get the name column (could be different in different GeoJSONs)
name_cols <- names(turkey_sf)
name_col <- name_cols[grep("name|NAME|il|city|province", name_cols, ignore.case = TRUE)][1]

if (is.na(name_col)) {
  cat("Available columns:", paste(names(turkey_sf), collapse = ", "), "\n")
  name_col <- names(turkey_sf)[1]
}

cat("Using column '", name_col, "' as province name\n", sep = "")

# Prepare turkey_sf for merging
turkey_sf <- turkey_sf %>%
  rename(province_name = !!name_col)

# Merge with province counts
turkey_map_data <- turkey_sf %>%
  left_join(province_counts, by = c("province_name" = "province"))

# Fill NA values
turkey_map_data <- turkey_map_data %>%
  mutate(
    n_chiefs = replace_na(n_chiefs, 0),
    chiefs_category = case_when(
      n_chiefs == 0 ~ "0",
      n_chiefs == 1 ~ "1",
      n_chiefs == 2 ~ "2",
      n_chiefs >= 3 & n_chiefs <= 4 ~ "3-4",
      n_chiefs >= 5 & n_chiefs <= 6 ~ "5-6",
      n_chiefs >= 7 ~ "7+",
      TRUE ~ "0"
    ),
    chiefs_category = factor(chiefs_category, 
                            levels = c("0", "1", "2", "3-4", "5-6", "7+"))
  )

# Define military green color palette
military_green_palette <- c(
  "#e8e8e8",  # 0 chiefs - grey
  "#8a9a5b",  # 1 chief
  "#697843",  # 2 chiefs
  "#4b5320",  # 3-4 chiefs - base military green
  "#3d4a2a",  # 5-6 chiefs
  "#2d3a1a"   # 7+ chiefs - darkest
)

cat("\nCreating map visualization...\n")

# Create the choropleth map with geom_sf (polygon-based like ggplot geom_polygon)
map_plot <- ggplot(data = turkey_map_data) +
  geom_sf(aes(fill = chiefs_category), color = "white", size = 0.3) +
  scale_fill_manual(
    values = military_green_palette,
    name = "Number of\nChiefs of Staff",
    drop = FALSE
  ) +
  coord_sf(xlim = c(26, 45), ylim = c(36, 42.5)) +
  theme_void() +
  labs(
    title = "Turkish Chiefs of Staff - Birthplace Distribution by Province",
    subtitle = paste0("Republic Era (1920-Present) • Total: ", sum(turkey_map_data$n_chiefs, na.rm = TRUE), " Chiefs"),
    caption = "Data: Turkish Wikipedia • Visualization: R/ggplot2 geom_sf() [polygon coloring approach]"
  ) +
  theme(
    plot.title = element_text(hjust = 0.5, size = 18, face = "bold", color = "#4b5320"),
    plot.subtitle = element_text(hjust = 0.5, size = 13, color = "#666666", margin = margin(b = 15)),
    plot.caption = element_text(hjust = 1, size = 10, color = "#999999"),
    legend.position = "right",
    legend.title = element_text(size = 12, face = "bold", color = "#4b5320"),
    legend.text = element_text(size = 11),
    legend.key.size = unit(1, "cm"),
    plot.margin = margin(20, 20, 20, 20),
    plot.background = element_rect(fill = "white", color = NA),
    panel.background = element_rect(fill = "white", color = NA)
  )

# Save the map
ggsave("chiefs_birthplace_map_ggplot2.png", 
       plot = map_plot, 
       width = 14, 
       height = 10, 
       dpi = 300,
       bg = "white")

cat("✓ Saved: chiefs_birthplace_map_ggplot2.png\n")

# Print to screen
print(map_plot)

# Create bar chart
cat("\nCreating bar chart...\n")

bar_plot <- ggplot(city_counts, aes(x = reorder(birthplace, count), y = count)) +
  geom_bar(stat = "identity", fill = "#4b5320", color = "white", width = 0.8) +
  geom_text(aes(label = count), hjust = -0.3, size = 4, color = "#4b5320", fontface = "bold") +
  coord_flip() +
  labs(
    title = "Number of Chiefs of Staff by Birthplace",
    subtitle = "Republic Era (1920-Present)",
    x = "",
    y = "Number of Chiefs"
  ) +
  theme_minimal() +
  theme(
    plot.title = element_text(hjust = 0.5, size = 16, face = "bold", color = "#4b5320"),
    plot.subtitle = element_text(hjust = 0.5, size = 12, color = "#666666"),
    axis.text = element_text(size = 11),
    axis.title.x = element_text(size = 12, margin = margin(t = 10)),
    panel.grid.major.y = element_blank(),
    panel.grid.minor = element_blank(),
    plot.background = element_rect(fill = "white", color = NA),
    panel.background = element_rect(fill = "white", color = NA)
  ) +
  scale_y_continuous(expand = expansion(mult = c(0, 0.1)))

ggsave("chiefs_birthplace_barchart_r.png", 
       plot = bar_plot, 
       width = 10, 
       height = 8, 
       dpi = 300,
       bg = "white")

cat("✓ Saved: chiefs_birthplace_barchart_r.png\n")

cat("\n============================================================\n")
cat("Analysis complete!\n")
cat("Generated files:\n")
cat("  - chiefs_birthplace_map_ggplot2.png (province polygon map)\n")
cat("  - chiefs_birthplace_barchart_r.png (bar chart)\n")
cat("============================================================\n")
