#!/usr/bin/env Rscript
# Turkish Chiefs of Staff - Proper Choropleth Map with Province Boundaries
# Following the approach from https://milospopovic.net/how-to-make-choropleth-map-in-r/

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
cat("Turkish Chiefs of Staff - Choropleth Map with Province Boundaries\n")
cat("============================================================\n\n")

# Read the chiefs data
chiefs_data <- read.csv("data/chiefs_of_staff.csv", stringsAsFactors = FALSE, fileEncoding = "UTF-8")

cat("Total Chiefs of Staff:", nrow(chiefs_data), "\n")
cat("Unique Birthplaces:", length(unique(chiefs_data$birthplace)), "\n\n")

# Map cities to provinces
city_to_province <- tibble(
  city = c("İstanbul", "Ankara", "Selanik", "Edirne", "Erzurum", "Trabzon", 
           "Erzincan", "İzmir", "Alaşehir", "Burdur", "Elazığ", 
           "Afyonkarahisar", "Kastamonu", "Van"),
  province = c("Istanbul", "Ankara", "Thessaloniki", "Edirne", "Erzurum", "Trabzon",
               "Erzincan", "Izmir", "Manisa", "Burdur", "Elazig",
               "Afyonkarahisar", "Kastamonu", "Van"),
  country = c("Turkey", "Turkey", "Greece", "Turkey", "Turkey", "Turkey",
              "Turkey", "Turkey", "Turkey", "Turkey", "Turkey",
              "Turkey", "Turkey", "Turkey"),
  in_turkey = c(TRUE, TRUE, FALSE, TRUE, TRUE, TRUE, 
                TRUE, TRUE, TRUE, TRUE, TRUE, 
                TRUE, TRUE, TRUE)
)

# Add province mapping and count (including all chiefs now)
province_counts <- chiefs_data %>%
  left_join(city_to_province, by = c("birthplace" = "city")) %>%
  group_by(province, country) %>%
  summarise(
    n_chiefs = n(),
    chiefs_names = paste(name, collapse = "; "),
    .groups = 'drop'
  )

cat("Province counts (including Greece):\n")
print(province_counts)

# Download Turkey provinces from Natural Earth (admin level 1)
cat("\nDownloading Turkey province boundaries from Natural Earth...\n")

turkey_provinces <- ne_states(country = "turkey", returnclass = "sf")

if (is.null(turkey_provinces) || nrow(turkey_provinces) == 0) {
  cat("Natural Earth data not available, trying alternative...\n")
  world_states <- ne_states(returnclass = "sf")
  turkey_provinces <- world_states[world_states$admin == "Turkey", ]
}

turkey_provinces$country <- "Turkey"

cat("Loaded", nrow(turkey_provinces), "Turkish provinces\n")

# Download Greece provinces (for Thessaloniki/Selanik)
cat("Downloading Greece province boundaries...\n")
greece_provinces <- ne_states(country = "greece", returnclass = "sf")
greece_provinces$country <- "Greece"
cat("Loaded", nrow(greece_provinces), "Greek provinces\n")

# Download neighboring countries (for context)
cat("Downloading neighboring countries...\n")
neighbors <- c("Bulgaria", "Georgia", "Armenia", "Azerbaijan", "Iran", "Iraq", "Syria")
neighbor_countries <- ne_countries(country = neighbors, scale = "medium", returnclass = "sf")
neighbor_countries$country <- neighbor_countries$admin
cat("Loaded", nrow(neighbor_countries), "neighboring countries\n")

# Combine all provinces
all_provinces <- bind_rows(
  turkey_provinces,
  greece_provinces
)
# Prepare all provinces for merging
# The name column might have different encoding
all_provinces <- all_provinces %>%
  mutate(
    province_clean = name,
    # Try to match with our data
    province_match = case_when(
      grepl("Istanbul|İstanbul", name, ignore.case = TRUE) ~ "Istanbul",
      grepl("Ankara", name, ignore.case = TRUE) ~ "Ankara",
      grepl("Izmir|İzmir", name, ignore.case = TRUE) ~ "Izmir",
      grepl("Edirne", name, ignore.case = TRUE) ~ "Edirne",
      grepl("Erzurum", name, ignore.case = TRUE) ~ "Erzurum",
      grepl("Trabzon", name, ignore.case = TRUE) ~ "Trabzon",
      grepl("Erzincan", name, ignore.case = TRUE) ~ "Erzincan",
      grepl("Manisa", name, ignore.case = TRUE) ~ "Manisa",
      grepl("Burdur", name, ignore.case = TRUE) ~ "Burdur",
      grepl("Elaz", name, ignore.case = TRUE) ~ "Elazig",
      grepl("Afyon", name, ignore.case = TRUE) ~ "Afyonkarahisar",
      grepl("Kastamonu", name, ignore.case = TRUE) ~ "Kastamonu",
      grepl("Van", name, ignore.case = TRUE) ~ "Van",
      # Thessaloniki is in Central Macedonia (Kentriki Makedonia)
      grepl("Kentriki Makedonia|Central Macedonia", name, ignore.case = TRUE) ~ "Thessaloniki",
      TRUE ~ name
    )
  )

# Merge with chief counts
map_data <- all_provinces %>%
  left_join(province_counts, by = c("province_match" = "province", "country" = "country"))

# Fill NA with 0
map_data <- map_data %>%
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

cat("\nMerge results:\n")
cat("Total provinces/regions:", nrow(map_data), "\n")
cat("Provinces with chiefs:", sum(map_data$n_chiefs > 0), "\n")
cat("Total chiefs mapped:", sum(map_data$n_chiefs, na.rm = TRUE), "\n")
cat("Turkey:", sum(map_data$n_chiefs[map_data$country == "Turkey"], na.rm = TRUE), "chiefs\n")
cat("Greece:", sum(map_data$n_chiefs[map_data$country == "Greece"], na.rm = TRUE), "chiefs\n")

# Military green palette
military_green_palette <- c(
  "#e8e8e8",  # 0 chiefs - grey
  "#8a9a5b",  # 1 chief
  "#697843",  # 2 chiefs
  "#4b5320",  # 3-4 chiefs - base military green
  "#3d4a2a",  # 5-6 chiefs
  "#2d3a1a"   # 7+ chiefs - darkest
)

# Create choropleth map
cat("\nCreating choropleth map with neighboring countries...\n")

map_plot <- ggplot() +
  # Base layer: neighboring countries (light grey)
  geom_sf(data = neighbor_countries, fill = "#f0f0f0", color = "#cccccc", size = 0.3) +
  # Province layer: colored by number of chiefs
  geom_sf(data = map_data, aes(fill = chiefs_category), color = "white", size = 0.3) +
  scale_fill_manual(
    values = military_green_palette,
    name = "Number of\nChiefs of Staff",
    drop = FALSE
  ) +
  coord_sf(xlim = c(19, 45), ylim = c(35, 43), expand = FALSE) +
  theme_void() +
  labs(
    title = "Turkish Chiefs of Staff - Birthplace Distribution",
    subtitle = paste0("Republic Era (1920-Present) • Total: ", sum(map_data$n_chiefs, na.rm = TRUE), " Chiefs (incl. 3 from Thessaloniki, Greece)"),
    caption = "Data: Turkish Wikipedia • Map: Natural Earth • Visualization: R/ggplot2 choropleth"
  ) +
  theme(
    plot.title = element_text(hjust = 0.5, size = 18, face = "bold", color = "#4b5320"),
    plot.subtitle = element_text(hjust = 0.5, size = 12, color = "#666666", margin = margin(b = 15)),
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
ggsave("chiefs_birthplace_choropleth.png", 
       plot = map_plot, 
       width = 14, 
       height = 10, 
       dpi = 300,
       bg = "white")

cat("✓ Saved: chiefs_birthplace_choropleth.png\n")

# Print to screen
print(map_plot)

# Save the spatial data for inspection
st_write(map_data, "data/turkey_greece_provinces_with_chiefs.geojson", 
         delete_dsn = TRUE, quiet = TRUE)
cat("✓ Saved: data/turkey_greece_provinces_with_chiefs.geojson\n")

cat("\n============================================================\n")
cat("Choropleth map complete!\n")
cat("============================================================\n")
