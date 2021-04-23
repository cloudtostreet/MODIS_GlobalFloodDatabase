
# coding: utf-8

# C2S MODIS FUNCTIONS

# COLIN DOYLE - based off of Jon Sullivan's javascript functions
# MARCH 12, 2017
# THESE ARE FUNCTIONS WE MAY COMMONLY USE FOR MODIS
# NEED TO LOAD THESE TO RUN DFO AND OTSU SCRIPTS
# NOTE: SOME OF THESE ARE SET UP SPECIFICALLY FOR THE DFO AND OTSU SCRIPTS

import ee
ee.Initialize()
import math

# Function that renames the bands in MODIS GQ (250-m) collections to
# readable band names
def dfo_bands_gq(collection):
    return collection.select(["sur_refl_b01", "sur_refl_b02"],
                             ["red_250m", "nir_250m"]);

# Function that renames the bands in MODIS GA (500-m) collections to
# readable band names
def dfo_bands_ga(collection):
    return collection.select(["sur_refl_b01", "sur_refl_b03",
                              "sur_refl_b04", "sur_refl_b07",
                              "state_1km"],
                             ["red_500m", "blue", "green", "swir",
                              "state_1km"]);

# join_collections joins the GQ & GA products base on similar timefields.  The bands
# of the each image are concatenated together.  The results is several bands with
# different resolutions!
def join_collections(img_coll1, img_coll2):
    filter_time_eq = ee.Filter.equals(leftField="system:time_start", rightField="system:time_start")
    joined = ee.Join.inner().apply(img_coll1, img_coll2, filter_time_eq)
    def image_cat(image): return ee.Image.cat(image.get("primary"), image.get("secondary"))
    return joined.map(image_cat)

# Function the collects both the GA/GQ data products of MODIS Aqua, renames
# the bands to readable versions, and joins the two collections into one.
def get_aqua(roi, date_range):
    aqua_gq = ee.ImageCollection("MODIS/006/MYD09GQ").filterDate(date_range)\
                                                .filterBounds(roi)
    aqua_ga = ee.ImageCollection("MODIS/006/MYD09GA").filterDate(date_range)\
                                                .filterBounds(roi)
    return ee.ImageCollection(join_collections(dfo_bands_gq(aqua_gq),
                                              dfo_bands_ga(aqua_ga)))

# Function the collects both the GA/GQ data products of MODIS Terra, renames
# the bands to readable versions, and joins the two collections into one.
def get_terra(roi, date_range):
    terra_gq = ee.ImageCollection("MODIS/006/MOD09GQ").filterDate(date_range)\
                                                .filterBounds(roi)
    terra_ga = ee.ImageCollection("MODIS/006/MOD09GA").filterDate(date_range)\
                                                .filterBounds(roi)
    return ee.ImageCollection(join_collections(dfo_bands_gq(terra_gq),
                                              dfo_bands_ga(terra_ga)))

# The panSharpen fucntion pan-sharpens the SWIR band 500-m bands using a Corrected Reflectance technique
# Pay careful attention to the band names in the function.  These need to be present in the
# image passed to the function
def pan_sharpen(image):
    ratio = image.select("red_500m").divide(image.select("red_250m"))
    blue_ps = image.select("blue").divide(ratio)
    swir_ps = image.select("swir").divide(ratio)
    green_ps = image.select("green").divide(ratio)
    return image.select("red_250m", "nir_250m", "state_1km")\
                .addBands([blue_ps, green_ps, swir_ps])\
                .set({"ratio_scale": ratio.projection().nominalScale()})

# Function that calculates a ratio between b1 and b2.  Used principally for
# with the Otsu functions to optimize the thresholds used later in the DFO
# algorithm
def b1b2_ratio (img):
    exp = "float(b('nir_250m') + 13.5) / float(b('red_250m') + 1081.1)"
    dfo_ratio = img.expression(exp) # Band 1/Band 2 Ratio Threshold
    return img.addBands(dfo_ratio.select([0], ["b1b2_ratio"]))\
                .copyProperties(img)


# The get_qa_bits function extracts unpacks the QA band that is in bit format
# Extract QA Bits Returns an image containing just the specified QA bits.
# Args:
#     image - The QA Image to get bits from.
#     start - The first bit position, 0-based.
#     end   - The last bit position, inclusive.
#     name  - A name for the output image.u
def get_qa_bits (image, start, end, new_name):
    # Compute the bits we need to extract.
    pattern = 0
    for i in range(start, end+1):
        pattern += pow(2, i)
    return image.select([0], [new_name]).bitwiseAnd(pattern).rightShift(start)

# add_qa_bands creates an image based on MODIS QA information
# from the "state_1km" QA band.  This function has several bands
# including cloudy areas, cloud shadow, and snow/ice.

# QA Band information is available at:
# http://modis-sr.ltdri.org/guide/MOD09_UserGuide_v1_3.pdf
# Table 16: 1-kilometer State QA Descriptions (16-bit)

# cloud_state ==> 0: "clear", 1: "cloudy", 2: "mixed", 3: "not set"
# cloud_shadow ==> 0: "no", 1: "yes"
# ice_flag ==> 0: "no", 1: "yes"
# snow_flag ==> 0: "no snow", 1: "snow"
def add_qa_bands(img):
    cloud_state = get_qa_bits(img.select("state_1km"), 0, 1, "cloud_state")
    cloud_shadow = get_qa_bits(img.select("state_1km"), 2, 2, "cloud_shadow")
    ice_flag = get_qa_bits(img.select("state_1km"), 12, 12, "ice_flag")
    snow_flag = get_qa_bits(img.select("state_1km"), 15, 15, "snow_flag")
    return img.addBands([cloud_state, cloud_shadow, ice_flag, snow_flag])

# The qaMask function takes an image as an input with bands defined from the
# add_qa_bands function.  This then creates a mask from these bands to mask out
# cloudy areas, shadow, and ice/snow.  This mask is then applied to an image which
# is returned.
def qa_mask(image):
    cloud_mask = image.expression("b('cloud_state') == 1 || b('cloud_state') == 2")
    shadow_mask = image.expression("b('cloud_shadow') == 1")
    ice_mask = image.expression("b('ice_flag') == 1")
    snow_mask = image.expression("b('snow_flag') == 1")
    mask = cloud_mask.add(shadow_mask).add(ice_mask).add(snow_mask)
    return image.updateMask(mask.eq(0))

# cloud_calc calculates the cloud cover over the ROI in each image
def cloud_calc(img):
    roi_pixels = ee.Number(img.select("state_1km").reduceRegion(reducer = ee.Reducer.count(), maxPixels = 1e9)\
                                                    .get("state_1km"))
    cloud_pixels = ee.Number(img.select('cloud_state')
                            .expression("b('cloud_state') == 1 || b('cloud_state') == 2")
                            .reduceRegion(reducer = ee.Reducer.sum(), maxPixels = 1e9)
                            .get("cloud_state"))
    return img.set({'cloud_cover_perc': cloud_pixels.divide(roi_pixels).multiply(100)})

# The least_cloudy fucntion takes an image collection that has already been
# passed to cloud_calc and has a "cloud_cover_perc" property added.  The image
# with the minimum cloud cover is returned
def least_cloudy(img_coll):
    non_null_images = img_coll.filterMetadata("cloud_cover_perc", "greater_than", 0)
    min_cloud = non_null_images.aggregate_min("cloud_cover_perc")
    return ee.Image(non_null_images.filterMetadata("cloud_cover_perc", "equals", min_cloud).first())
