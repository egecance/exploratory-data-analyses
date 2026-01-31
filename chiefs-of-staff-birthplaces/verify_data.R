#!/usr/bin/env Rscript
library(dplyr)
library(sf)

chiefs <- read.csv('data/chiefs_of_staff.csv')
army <- read.csv('data/army_commanders.csv')
geojson <- st_read('data/turkey_greece_provinces_with_chiefs.geojson', quiet=TRUE)

transliterate <- function(text) {
  text %>%
    gsub('İ', 'I', .) %>%
    gsub('ı', 'i', .) %>%
    gsub('Ğ', 'G', .) %>%
    gsub('ğ', 'g', .) %>%
    gsub('Ü', 'U', .) %>%
    gsub('ü', 'u', .) %>%
    gsub('Ş', 'S', .) %>%
    gsub('ş', 's', .) %>%
    gsub('Ö', 'O', .) %>%
    gsub('ö', 'o', .) %>%
    gsub('Ç', 'C', .) %>%
    gsub('ç', 'c', .)
}

chiefs$birthplace_clean <- transliterate(chiefs$birthplace)
army$birthplace_clean <- transliterate(army$birthplace)
geojson_names <- unique(transliterate(geojson$name_en))

special <- c('Selanik', 'Rahova', 'Manastır')

message("\n=== CHIEFS OF STAFF ===")
unmatched_chiefs <- chiefs %>%
  filter(!(birthplace %in% special) & !(birthplace_clean %in% geojson_names)) %>%
  select(name, birthplace)

if (nrow(unmatched_chiefs) > 0) {
  message("Birthplaces not matching any province:")
  print(unmatched_chiefs, row.names=FALSE)
} else {
  message("All chiefs birthplaces match province names!")
}

message("\n=== ARMY COMMANDERS ===")
unmatched_army <- army %>%
  filter(!(birthplace %in% special) & !(birthplace_clean %in% geojson_names)) %>%
  select(name, birthplace)

if (nrow(unmatched_army) > 0) {
  message("Birthplaces not matching any province:")
  print(unmatched_army, row.names=FALSE)
} else {
  message("All army commanders birthplaces match province names!")
}

message("\n=== SUMMARY ===")
message("Total chiefs: ", nrow(chiefs))
message("Total army commanders: ", nrow(army))
message("Unmatched chiefs: ", nrow(unmatched_chiefs))
message("Unmatched army: ", nrow(unmatched_army))
