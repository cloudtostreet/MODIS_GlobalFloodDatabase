library(tidyverse)
library(countrycode)

# --- POP SENSITIVITY ANALYSIS ---
# Set working directory
pop_base = "data/pop_sensitivity_analysis"

# List csv files
files = list.files(pop_base, pattern = "*.csv")
hrsl_file = files[1]
pop_files = files[2:length(files)]

# Load metadata for HRSL dataset
hrsl_metadata = read.csv(paste(pop_base, hrsl_file, sep='/')) %>%
  mutate(iso3 = toupper(iso3))

# Load pop analysis data and bind files together
drop_cols = c('country_abbrev', 'id','.geo')
pop_sensitivity <- pop_files %>% 
  map_df(~read.csv(paste(pop_base, ., sep='/'))) %>% # reading all csvs and bindind
  select(-drop_cols) %>% # removing columns in drop_cols()
  mutate(world_region = if_else(country_name=='United States', "North America", world_region)) %>% # fixing Hawaii that is in region Oceania
  rename('iso2c' = 'countrycode') # renaming column

# Add code with 3-digit iso-code
iso3c = countrycode(pop_sensitivity$country_name, origin = 'country.name', destination = 'iso3c')
pop_sensitivity$iso3c = iso3c

# Remove some small islands that are creating duplicates
country_rm = c('Portugal (Azores)', 'Portugal (Madeira Is)', 'Spain (Canary Is)', 
               'Spain (Africa)', 'Korean Is. (UN Jurisdiction)', 
               'US Minor Pacific Is. Refuges')

# Filter pop sensitivity to those with HRSL data
`%notin%` = Negate(`%in%`)
bias_factor = pop_sensitivity %>%
  filter(iso3c %in% hrsl_metadata$iso3) %>% # filter pop_sensitivity to countries with HRSL data
  filter(country_name %notin% country_rm) %>% # removing some odd island 
  group_by(country_name, iso3c, iso2c, world_region) %>% # grouping for later aggregation stats
  summarise_if(is.numeric, sum, na.rm = TRUE) %>% # summing all numeric columns (e.g. different geometries for Italy or now just one record)
  mutate(floodpop_ghsl_tot = floodpop_ghsl_1+floodpop_ghsl_2+floodpop_ghsl_3,
         floodpop_gridpop3_tot = floodpop_gridpop3_1+floodpop_gridpop3_2+floodpop_ghsl_3,
         floodpop_hrsl_tot = floodpop_hrsl_1+floodpop_hrsl_2+floodpop_hrsl_3,
         bias_factor = floodpop_hrsl_tot/floodpop_ghsl_tot) # creating new columns


continent = countrycode(bias_factor$country_name, origin='country.name', destination = 'continent')
bias_factor$continent = continent

# Plot
ggplot(data=bias_factor, aes(x=continent, y=bias_factor))+
  geom_boxplot(fill='#377eb8', alpha=0.5) +
  geom_hline(yintercept=1, size=1, linetype='dashed') +
  labs(x="Continent", y="Correction Factor") +
  theme_minimal() +
  theme(axis.title.x = element_text(size=18),
        axis.title.y = element_text(size=18),
        axis.text.x = element_text(size=14),
        axis.text.y = element_text(size=14))

# Write CSV
#write.csv(bias_factor, "data/bias_factor.csv")

# --- FLOOD PROPORTION --- #
# Main results from Beth
gfd_main = read.csv("data/GFDabove.13.csv")

# Add 3-digit country code
iso3c = countrycode(gfd_main$country, origin = 'country.name', destination = 'iso3c')
gfd_main$iso3c = iso3c

# Join main analysis to bias factor by 3-digit country code
bias2join = bias_factor %>%
  ungroup() %>%
  select(iso3c, 
         floodpop_hrsl_1, floodpop_hrsl_2, floodpop_hrsl_3, 
         bias_factor)

# Join main analysis and bias together
gfd_main_bias = gfd_main %>%
  left_join(bias2join, by='iso3c') 

# Calculation bias by region
main_region_bias = gfd_main_bias %>% 
  group_by(region) %>% 
  summarize(region_mean_bias = mean(bias_factor, na.rm=T),
            region_sd_bias = sd(bias_factor, na.rm=T))

# Final dataset!
gfd_main_bias_final = gfd_main_bias %>%
  left_join(main_region_bias, by='region') %>%
  mutate(hrsl_data = if_else(is.na(bias_factor), "No", "Yes"),
         bias_factor = if_else(is.na(bias_factor), region_mean_bias, bias_factor))

# Annnnnnddd...write to disk
#write.csv(gfd_main_bias_final, "data/GFDabove_13_wBias.csv")


#--- EVENT STATS ---#
ghsl_events = read.csv("data/compiled_pop_ghsl_ts_2019_08_04.csv")

# Clean up some country names
ghsl_events$country[ghsl_events$country=="Byelarus"] = "Belarus"
ghsl_events$country[ghsl_events$country=="Korea, Peoples Republic of"] = "North Korea"
ghsl_events$country[ghsl_events$country=="Iraq-Saudi Arabia Neutral Zone"] = "Iraq"
ghsl_events$country[ghsl_events$country=="Yugoslavia"] = "Serbia"

# Add ISO3
iso3c = countrycode(ghsl_events$country, origin = 'country.name', destination = 'iso3c')
ghsl_events$iso3c = iso3c

# World region2join
region2join = pop_sensitivity %>%
  filter(country_name %notin% country_rm) %>%
  select(iso3c, world_region) %>%
  filter(!is.na(iso3c)) %>%
  unique()

# Reduce bias2join further
bias2join = bias_factor %>%
  ungroup() %>%
  select(iso3c, bias_factor)

ghsl_events_bias = ghsl_events %>%
  rename(exposed_ghsl=exposed) %>%
  left_join(region2join, by="iso3c") %>%
  left_join(bias2join, by="iso3c") %>%
  mutate(bias_factor = if_else(is.infinite(bias_factor), as.numeric(NA), bias_factor),
         bias_factor = if_else(is.nan(bias_factor), as.numeric(NA), bias_factor))

# Bermuda, Turks and Caicos, and Bahamas missing a world region
ghsl_events_bias$world_region[is.na(ghsl_events_bias$world_region)] = "Caribbean" 

# Calculate regional bias based in the LSIB classification
lsib_region_bias = bias_factor %>%
  mutate(bias_factor = if_else(is.infinite(bias_factor), as.numeric(NA), bias_factor),
         bias_factor = if_else(is.nan(bias_factor), as.numeric(NA), bias_factor)) %>%
  group_by(world_region) %>%
  summarize(region_mean_bias = mean(bias_factor, na.rm=T))

ghsl_events_out = ghsl_events_bias %>%
  left_join(lsib_region_bias, by="world_region") %>%
  mutate(bias_factor = if_else(is.na(bias_factor), region_mean_bias, bias_factor),
         exposed_adjusted = exposed_ghsl * bias_factor)

# And....write to csv
#write.csv(ghsl_events_out, "data/compiled_pop_ghsl_ts_wbias_2019_08_04.csv")


# ------- FLOOD MECHANISMS ---------- #
fmech_base = 'data/flood_mechanism'
surge = read.csv(paste(fmech_base, 'hotspot_countries_jrc_20210112_Surge.csv', sep='/'))
snowicerain = read.csv(paste(fmech_base, 'hotspot_countries_jrc_20210112_SnowIceRain.csv', sep='/'))
heavyrain = read.csv(paste(fmech_base, 'hotspot_countries_jrc_20210112_HeavyRain.csv', sep='/'))
dam = read.csv(paste(fmech_base, 'hotspot_countries_jrc_20210112_Dam.csv', sep='/'))

# removing these classification from LSIB
no_country = c("Abyei Area", "Akrotiri", "Aksai Chin", "Demchok Area", "Dhekelia", 
               "Dragonja River Mouth", "Dramana-Shakatoe Area", "Halaib Triangle", 
               "IN-CH Small Disputed Areas", "Invernada Area", "Jan Mayen", "Kalapani Area", 
               "Kosovo", "No Man's Land", "Paracel Is", "Siachen-Saltoro Area", 
               "St Martin", "US Virgin Is", "Christmas I", "Cocos (Keeling) Is")


drop_cols = c("system.index", ".geo")
flood_mechanism = rbind(surge, snowicerain, heavyrain, dam) %>%
  select(-drop_cols) %>%
  rename('iso2c' = 'cc') %>% # renaming column
  mutate(country = if_else(iso2c=='US', "United States", country), # Hawaii and Alaska have weird names and regions
         region = if_else(iso2c=='US', "North America", region)) %>% 
  mutate(sum=rowSums(.[,3:25])) %>%# Remove rows where no flood exposure was detected (e.g. equal to 0)
  filter(sum>0 & country %notin% no_country)

# Add code with 3-digit iso-code
iso3c = countrycode(flood_mechanism$country, origin = 'country.name', destination = 'iso3c')
region = countrycode(flood_mechanism$country, origin = 'country.name', destination = 'region23')

flood_mechanism$iso3c = iso3c
flood_mechanism$region = region


# Join main analysis and bias together
oceania = c("Polynesia", "Micronesia", "Melanesia") # these regions have no floods so grouping together

flood_mechanism_bias = flood_mechanism %>%
  left_join(bias2join, by='iso3c') %>%
  mutate(bias_factor = na_if(bias_factor, Inf),
         bias_factor = na_if(bias_factor, "NaN"),
         bias_factor = na_if(bias_factor, NaN),
         hrsl_data = if_else(is.na(bias_factor), "N", "Y"),
         region = if_else(region %in% oceania, "Australia and New Zealand", region))
  
# Calculation bias by region
wb_region_bias = flood_mechanism_bias %>% 
  group_by(region) %>% 
  summarize(region_mean_bias = mean(bias_factor, na.rm=T),
            region_sd_bias = sd(bias_factor, na.rm=T))

# Join region bias estimates
flood_mechanism_out = flood_mechanism_bias %>%
  left_join(wb_region_bias, by = 'region') %>%
  mutate(bias_factor = if_else(is.na(bias_factor), region_mean_bias, bias_factor))

# And DONE DONE DONE!
# write.csv(flood_mechanism_out, "data/flood_mechanism_wbias.csv")



