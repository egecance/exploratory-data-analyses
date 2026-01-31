#!/usr/bin/env Rscript
# Turkish Army Commanders - Proper Choropleth Map with Province Boundaries

options(repos = c(CRAN = 'https://cloud.r-project.org'))

# Install and load packages
packages <- c("tidyverse", "sf", "rnaturalearth")
for (pkg in packages) {
  if (!require(pkg, character.only = TRUE, quietly = TRUE)) {
    install.packages(pkg)
    library(pkg, character.only = TRUE)
  }
}

library(tidyverse)
library(sf)
library(rnaturalearth)

cat("============================================================\n")
cat("Turkish Army Commanders - Choropleth Map with Province Boundaries\n")
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

cat("Province Distribution:\n")
print(province_counts %>% arrange(desc(count)), n = Inf)
cat("\n")

# Download provinces for Turkey, Greece, Bulgaria, North Macedonia, and Romania
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
cat("Total provinces/regions:", nrow(all_provinces), "\n")

# Clean province names for matching
all_provinces <- all_provinces %>%
  mutate(
    province_match = case_when(
      # Turkey provinces - ASCII matching
      name == "İstanbul" ~ "Istanbul",
      name == "İzmir" ~ "Izmir",
      name == "Çanakkale" ~ "Canakkale",
      name == "Çankırı" ~ "Cankiri",
      name == "Kütahya" ~ "Kutahya",
      name == "Gümüşhane" ~ "Gumushane",
      # Greece provinces
      name == "Kentrikí Makedonía" ~ "Thessaloniki",
      name == "Kentriki Makedonia" ~ "Thessaloniki",
      # North Macedonia provinces
      name == "Pelagoniski" ~ "Pelagonia",
      # Romania provinces
      name == "Olt" ~ "Olt",
      # Default: use name as is
      TRUE ~ name
    )
  )

# Join with commander counts
provinces_with_commanders <- all_provinces %>%
  left_join(province_counts, by = c("province_match" = "province")) %>%
  mutate(
    count = replace_na(count, 0),
    count_category = case_when(
      count == 0 ~ "0",
      count == 1 ~ "1",
      count == 2 ~ "2",
      count >= 3 & count <= 4 ~ "3-4",
      count >= 5 & count <= 6 ~ "5-6",
      count >= 7 ~ "7+"
    ),
    count_category = factor(count_category, levels = c("0", "1", "2", "3-4", "5-6", "7+"))
  )

# Filter to provinces with commanders
provinces_with_data <- provinces_with_commanders %>%
  filter(count > 0)

cat("Provinces with commanders:", nrow(provinces_with_data), "\n")
cat("Total commanders mapped:", sum(provinces_with_data$count, na.rm = TRUE), "\n\n")

# Count by country
country_summary <- province_counts %>%
  group_by(country) %>%
  summarise(total_commanders = sum(count), .groups = "drop")
cat("Country Summary:\n")
print(country_summary)
cat("\n")

# Show commanders by province
cat("Commanders by Province:\n")
commanders_summary <- provinces_with_data %>% 
  select(province_match, country, count, commanders) %>% 
  st_drop_geometry() %>%
  arrange(desc(count))
print(as.data.frame(commanders_summary))
cat("\n")

# Define military green color palette (6 categories)
military_colors <- c(
  "0" = "#e8e8e8",      # Light grey for 0
  "1" = "#a8b88f",      # Light military green
  "2" = "#8a9e6f",      # Medium-light green
  "3-4" = "#6c8450",    # Medium green
  "5-6" = "#4d6a30",    # Dark green
  "7+" = "#2d3a1a"      # Very dark military green
)

# Create the choropleth map
cat("Creating choropleth map...\n")
p <- ggplot() +
  # Base layer: all provinces with commander counts
  geom_sf(data = provinces_with_commanders, 
          aes(fill = count_category),
          color = "white", 
          size = 0.2) +
  scale_fill_manual(
    values = military_colors,
    name = "Number of\nArmy\nCommanders",
    drop = FALSE
  ) +
  coord_sf(xlim = c(20, 45), ylim = c(35, 47)) +
  theme_minimal() +
  labs(
    title = "Turkish Army Commanders - Birthplace Distribution",
    subtitle = "Republic Era (1949-Present) • Total: 52 Commanders (2 from Thessaloniki/Greece, 1 from Rahova/Romania, 1 from Manastır/N. Macedonia)",
    caption = "Data: Turkish Wikipedia • Visualization: Natural Earth Province Boundaries"
  ) +
  theme(
    plot.title = element_text(size = 18, face = "bold", hjust = 0.5),
    plot.subtitle = element_text(size = 11, hjust = 0.5, color = "gray30"),
    plot.caption = element_text(size = 9, color = "gray50", hjust = 1),
    legend.position = "right",
    legend.title = element_text(size = 11, face = "bold"),
    legend.text = element_text(size = 10),
    panel.grid = element_line(color = "gray90", size = 0.2),
    plot.background = element_rect(fill = "white", color = NA),
    panel.background = element_rect(fill = "white", color = NA)
  )

# Save the map
output_file <- "army_commanders_birthplace_choropleth.png"
ggsave(output_file, p, width = 14, height = 10, dpi = 300, bg = "white")
cat("✓ Saved:", output_file, "\n")

cat("\n============================================================\n")
cat("Map generation complete!\n")
cat("============================================================\n")
