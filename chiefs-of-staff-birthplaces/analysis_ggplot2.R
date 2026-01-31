#!/usr/bin/env Rscript
# Turkish Military Chiefs of Staff - Birthplace Analysis with ggplot2
# Using geom_polygon to color actual province boundaries

# Set CRAN mirror
options(repos = c(CRAN = "https://cloud.r-project.org"))

# Install and load required packages
if (!require("tidyverse")) install.packages("tidyverse")
if (!require("sf")) install.packages("sf")
if (!require("rnaturalearth")) install.packages("rnaturalearth")
if (!require("rnaturalearthdata")) install.packages("rnaturalearthdata")
if (!require("rgeos")) install.packages("rgeos", type = "source")

library(tidyverse)
library(sf)
library(rnaturalearth)
library(ggplot2)

# Read the chiefs of staff data
chiefs_data <- read.csv("data/chiefs_of_staff.csv", stringsAsFactors = FALSE, fileEncoding = "UTF-8")
city_coords <- read.csv("data/city_coordinates.csv", stringsAsFactors = FALSE, fileEncoding = "UTF-8")

# Print summary
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

# Map city names to province names (some cities are district centers)
# In Turkey, the main distinction is at province level
city_to_province <- data.frame(
  city = c("İstanbul", "Ankara", "Selanik", "Edirne", "Erzurum", "Trabzon", 
           "Erzincan", "İzmir", "Alaşehir", "Burdur", "Elazığ", 
           "Afyonkarahisar", "Kastamonu", "Van"),
  province = c("Istanbul", "Ankara", "Thessaloniki", "Edirne", "Erzurum", "Trabzon",
               "Erzincan", "Izmir", "Manisa", "Burdur", "Elazig",
               "Afyonkarahisar", "Kastamonu", "Van"),
  in_turkey = c(TRUE, TRUE, FALSE, TRUE, TRUE, TRUE, 
                TRUE, TRUE, TRUE, TRUE, TRUE, 
                TRUE, TRUE, TRUE),
  stringsAsFactors = FALSE
)

# Add province mapping to chiefs data
chiefs_data <- chiefs_data %>%
  left_join(city_to_province, by = c("birthplace" = "city"))

# Count chiefs per province
province_counts <- chiefs_data %>%
  filter(in_turkey == TRUE) %>%
  group_by(province) %>%
  summarise(
    n_chiefs = n(),
    chiefs_list = paste(name, collapse = ", "),
    .groups = 'drop'
  )

cat("\nProvince-level counts:\n")
print(province_counts)

# Get Turkey map data from Natural Earth
# Download Turkey administrative boundaries
turkey_provinces <- ne_states(country = "Turkey", returnclass = "sf")

# Check what we got
cat("\nMap data columns:\n")
print(names(turkey_provinces))
cat("\nFirst few province names:\n")
print(head(turkey_provinces$name))

# Normalize province names for matching
turkey_provinces <- turkey_provinces %>%
  mutate(
    province_normalized = name,
    province_latin = iconv(name, to = "ASCII//TRANSLIT")
  )

# Merge the chiefs count data with map data
# We need to handle Turkish character conversion
turkey_map_data <- turkey_provinces %>%
  left_join(province_counts, by = c("name" = "province"))

# Fill NA values with 0 for provinces without chiefs
turkey_map_data <- turkey_map_data %>%
  mutate(
    n_chiefs = ifelse(is.na(n_chiefs), 0, n_chiefs),
    chiefs_list = ifelse(is.na(chiefs_list), "None", chiefs_list)
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

# Create discrete breaks for the color scale
turkey_map_data <- turkey_map_data %>%
  mutate(
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

# Create the map with ggplot2
map_plot <- ggplot(data = turkey_map_data) +
  geom_sf(aes(fill = chiefs_category), color = "white", size = 0.3) +
  scale_fill_manual(
    values = military_green_palette,
    name = "Number of\nChiefs of Staff",
    drop = FALSE
  ) +
  coord_sf(xlim = c(26, 45), ylim = c(36, 42)) +
  theme_void() +
  labs(
    title = "Turkish Chiefs of Staff - Birthplace Distribution by Province",
    subtitle = paste0("Republic Era (1920-Present) • Total: ", nrow(chiefs_data), " Chiefs"),
    caption = "Data: Turkish Wikipedia • Visualization: R/ggplot2"
  ) +
  theme(
    plot.title = element_text(hjust = 0.5, size = 16, face = "bold", color = "#4b5320"),
    plot.subtitle = element_text(hjust = 0.5, size = 12, color = "#666666"),
    plot.caption = element_text(hjust = 1, size = 9, color = "#999999"),
    legend.position = "right",
    legend.title = element_text(size = 11, face = "bold", color = "#4b5320"),
    legend.text = element_text(size = 10),
    plot.margin = margin(20, 20, 20, 20)
  )

# Save the map
ggsave("chiefs_birthplace_map_ggplot2.png", 
       plot = map_plot, 
       width = 14, 
       height = 10, 
       dpi = 300,
       bg = "white")

cat("\n✓ Saved: chiefs_birthplace_map_ggplot2.png\n")

# Print the plot to screen
print(map_plot)

# Create a detailed province table
province_table <- turkey_map_data %>%
  st_drop_geometry() %>%
  select(name, n_chiefs, chiefs_category) %>%
  filter(n_chiefs > 0) %>%
  arrange(desc(n_chiefs))

cat("\n============================================================\n")
cat("Provinces with Chiefs of Staff:\n")
cat("============================================================\n")
print(province_table, n = 50)

# Additional visualization: Bar chart
bar_plot <- ggplot(city_counts, aes(x = reorder(birthplace, count), y = count)) +
  geom_bar(stat = "identity", fill = "#4b5320", color = "white") +
  coord_flip() +
  labs(
    title = "Number of Chiefs of Staff by Birthplace",
    subtitle = "Republic Era (1920-Present)",
    x = "",
    y = "Number of Chiefs"
  ) +
  theme_minimal() +
  theme(
    plot.title = element_text(hjust = 0.5, size = 14, face = "bold", color = "#4b5320"),
    plot.subtitle = element_text(hjust = 0.5, size = 11, color = "#666666"),
    axis.text = element_text(size = 10),
    axis.title = element_text(size = 11),
    panel.grid.major.y = element_blank()
  )

ggsave("chiefs_birthplace_barchart_r.png", 
       plot = bar_plot, 
       width = 10, 
       height = 8, 
       dpi = 300,
       bg = "white")

cat("✓ Saved: chiefs_birthplace_barchart_r.png\n")

cat("\n============================================================\n")
cat("Analysis complete!\n")
cat("============================================================\n")
