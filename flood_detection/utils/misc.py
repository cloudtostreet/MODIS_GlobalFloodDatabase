# Import packages
import ee

ee.Initialize()

# Series of functions to extract overlapping watersheds from roi region. We use
# HydroSheds database provided a different levels. Also - functions for islands
# shapefiles are provided as HydroSheds does not cover some small islands.
def get_watersheds_level5(dfo_feature):
    basins = ee.FeatureCollection('ft:1IHRHUiWkgPXOzwNweeM89CzPYSfokjLlz7_0OTQl')
    return basins.filterBounds(dfo_feature)

def get_watersheds_level4(dfo_feature):
    basins = ee.FeatureCollection('ft:1JRW4YKfVTZKLAH4x4JRsggsHZoXRRUQKTIOYgJOW')
    return basins.filterBounds(dfo_feature)

def get_watersheds_level3(dfo_feature):
    basins = ee.FeatureCollection('ft:1asIZ7d9NqNIubAp2dNMvnAfRMd-9ih7kjcLnIzv6')
    return basins.filterBounds(dfo_feature)

def get_islands(dfo_feature):
    islands = ee.FeatureCollection('ft:14BijFeJ0MiV1CeP7FBst8P4Kf1Se0HK5Sfh78hJB')
    return islands.filterBounds(dfo_feature)

def get_american_somoa(dfo_feature):
    asm = ee.FeatureCollection('ft:1C79v82bd1QfIsdGfDFOo2sz2XIHJCiVnXWXBeX0_')
    return asm.filterBounds(dfo_feature)

# applySlopeMask() applies a mask to remove pixels that are greater than a
# certain slope based on SRTM 90-m DEM V4 the only parameter is the slope
# threshold, which is default to 5%
def apply_slope_mask(img, thresh=5):
    srtm = ee.Image("USGS/GMTED2010")
    slope = ee.Terrain.slope(srtm)
    masked = img.updateMask(slope.lte(thresh))
    return masked.set({'slope_threshold': thresh})

# this returns the permanent water mask from the JRC Global Surface Water
# dataset. It gets the permanent water from the transistions layer
def get_jrc_perm(roi_bounds):
    jrc_perm_water = ee.Image("JRC/GSW1_0/GlobalSurfaceWater")\
                    .select("transition").eq(1).unmask()
    return jrc_perm_water.select(['transition'],['jrc_perm_water']).clip(roi_bounds)

def get_jrc_yearly_perm(began, roi):
    ee_began = ee.Date(began)
    jrc_year = ee.Algorithms.If(ee_began.get('year')\
                    .gt(2018), 2018, ee_began.get('year'))
    jrc_perm = ee.Image(ee.ImageCollection('JRC/GSW1_1/YearlyHistory')\
                    .filterBounds(roi)
                    .filterMetadata('year', "equals", jrc_year).first())\
                    .remap([0, 1, 2, 3], [0, 0, 0, 1]).unmask()\
                    .select(['remapped'],['jrc_perm_yearly'])
    return jrc_perm.updateMask(jrc_perm)

def get_countries (roi):
    countries = ee.FeatureCollection("USDOS/LSIB/2013");
    img_country = countries.filterBounds(roi)

    cc_list = img_country.distinct('cc').aggregate_array('cc').getInfo()
    cc_list = [str(c) for c in cc_list]

    country_list = img_country.distinct('name').aggregate_array('name').getInfo()
    country_list = [str(c) for c in country_list]

    return cc_list, country_list
