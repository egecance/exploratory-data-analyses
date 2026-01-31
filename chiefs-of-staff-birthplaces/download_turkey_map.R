#!/usr/bin/env Rscript
options(repos = c(CRAN = 'https://cloud.r-project.org'))

# Load packages
suppressPackageStartupMessages({
  library(rnaturalearth)
  library(sf)
})

# Get Turkey country boundary
cat("Downloading Turkey map data...\n")
world <- ne_countries(scale = 'medium', returnclass = 'sf')
turkey <- world[world$name == 'Turkey', ]

# Save as GeoJSON
st_write(turkey, 'data/turkey_country.geojson', delete_dsn = TRUE, quiet = TRUE)
cat("✓ Saved Turkey country boundary\n")
cat("  Bounding box:", paste(round(st_bbox(turkey), 2), collapse = ", "), "\n")

# Try to get provinces
tryCatch({
  turkey_states <- ne_states(country = 'turkey', returnclass = 'sf')
  st_write(turkey_states, 'data/turkey_provinces_ne.geojson', delete_dsn = TRUE, quiet = TRUE)
  cat("✓ Saved", nrow(turkey_states), "Turkey provinces\n")
}, error = function(e) {
  cat("  Note: Province data not available in Natural Earth\n")
})

cat("\nMap data ready!\n")
