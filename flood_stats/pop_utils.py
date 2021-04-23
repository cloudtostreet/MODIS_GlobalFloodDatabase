# Original scripts written by Devin Routh
# This file is a collection of functions that can be applied to outputted map layers from other functions
# within the C2S API

# --------------------------------------------------------
# The function below was written by Devin Routh to compute
# the estimated number of people affected
# by the flood (according to the WorldPop dataset).
# --------------------------------------------------------

def getFloodPopbyCountry_LandScan(flood_img):
    """
    Args:
        floodImage : the standard Earth Engine Image object outputted by the map_DFO_event function
        roiGEO : the region of interest as an Earth Engine Geometry object

    Returns:
    -a feature collection of all countries for each flood events
    -with a pop and area count
        - An ee feature with properties including
              'Index': the event index ID
              'Began': start date of event map
              'Ended': end date of event map
              'Flood_Area': total area of detected flood
              'Pop_Exposed': the number of people in the mapped flood from WorldPop data
    """
    import ee
    ee.Initialize()

    roi_geo = flood_img.geometry()

    # Import the LandScan image collection & permannt water mask
    pop_all = ee.ImageCollection("projects/global-flood-db/landscan")
    perm_water = ee.Image("JRC/GSW1_0/GlobalSurfaceWater").select("transition").eq(1).unmask()

    def maskImages(img):
        non_flood = img.select("flooded")
        water_mask = non_flood.multiply(perm_water.neq(1))
        return img.select("flooded").mask(water_mask)

    # Extract the final flood extent image data as its own variable for analysis
    flood_extent = maskImages(ee.Image(flood_img.select("flooded")))

    # Get event year, match with the population year and clip to study are
    event_year = ee.Date(flood_img.get('began')).get('year')
    pop_img = ee.Image(pop_all.filterMetadata('year', 'equals', event_year)\
                    .first()).clip(roi_geo)
    pop_img = pop_img.updateMask(pop_img.gte(0)) # mask out bad data with negative values

    # Mask the world population dataset using the flood extent layer
    pop_scale = pop_img.projection().nominalScale()
    pop_masked = pop_img.updateMask(flood_extent)

    # Select the countries for which flood touches
    countries = ee.FeatureCollection('ft:1tdSwUL7MVpOauSgRzqVTOwdfy17KDbw-1d9omPw')
    flood_countries = countries.filterBounds(flood_extent.geometry().bounds())

    # Get area of flood in the scale of the flood map
    flood_area_img = flood_extent.multiply(ee.Image.pixelArea())
    map_scale = flood_extent.projection().nominalScale()
    index = ee.Image(flood_img).get("id")
    began_year = ee.Date(flood_img.get("began")).get("year")
    began_month = ee.Date(flood_img.get("began")).get("month")
    began_day = ee.Date(flood_img.get("began")).get("day")

    def getCountriesPop(ft):
        pop_sum = pop_masked.reduceRegion(
        reducer = ee.Reducer.sum(),
        geometry = ft.geometry(),
        scale = pop_scale,
        maxPixels = 1e9)

        pop = pop_sum.get("b1")

        area_sum= flood_area_img.reduceRegion(
        reducer= ee.Reducer.sum(),
        geometry= ft.geometry(),
        scale= map_scale,
        maxPixels= 1e9)

        sys_id = ee.String(flood_img.get('system:index')).getInfo()

        area = area_sum.get("flooded")
        return ee.Feature(None, {"system:index":sys_id,
                            "id": index,
                            "Year": began_year,
                            "Month": began_month,
                            "Day": began_day,
                            "Country":ft.get("Country"),
                            "Exposed":pop,
                            "Area": area})

    country_stats = ee.FeatureCollection(flood_countries).map(getCountriesPop)
    return ee.FeatureCollection(country_stats).set({"id":index})

# --------------------------------------------------------
# The function below was written by Devin Routh to compute
# the estimated number of people affected
# by the flood (according to the WorldPop dataset).
# --------------------------------------------------------

def getFloodPopbyCountry_GHSLTimeConstant(flood_img):
    """
    Args:
        floodImage : the standard Earth Engine Image object outputted by the map_DFO_event function
        roiGEO : the region of interest as an Earth Engine Geometry object

    Returns:
    -a feature collection of all countries for each flood events
    -with a pop and area count
        - An ee feature with properties including
              'Index': the event index ID
              'Began': start date of event map
              'Ended': end date of event map
              'Flood_Area': total area of detected flood
              'Pop_Exposed': the number of people in the mapped flood from WorldPop data
    """
    import ee
    ee.Initialize()

    roi_geo = flood_img.geometry()

    # Import the LandScan image collection & permannt water mask - clip to the study area
    pop_all = ee.ImageCollection("JRC/GHSL/P2016/POP_GPW_GLOBE_V1")
    perm_water = ee.Image("JRC/GSW1_0/GlobalSurfaceWater").select("transition").eq(1).unmask()

    def maskImages(img):
        non_flood = img.select("flooded")
        water_mask = non_flood.multiply(perm_water.neq(1))
        return img.select("flooded").mask(water_mask)

    # Extract the final flood extent image data as its own variable for analysis
    flood_extent = maskImages(ee.Image(flood_img.select("flooded")))

    # Get event year to match with the population year
    pop_2000 = ee.Image(pop_all.filterMetadata('system:index', 'equals', '2000')\
                    .first()).clip(roi_geo)
    pop_2015 = ee.Image(pop_all.filterMetadata('system:index', 'equals', '2015')\
                    .first()).clip(roi_geo)
    # Mask the world population dataset using the flood extent layer
    pop_scale = pop_2000.projection().nominalScale()
    pop_2000_masked = pop_2000.updateMask(flood_extent)
    pop_2015_masked = pop_2015.updateMask(flood_extent)

    # Select the countries for which flood touches
    countries = ee.FeatureCollection('ft:1tdSwUL7MVpOauSgRzqVTOwdfy17KDbw-1d9omPw')
    flood_countries = countries.filterBounds(flood_extent.geometry().bounds())

    # Get area of flood in the scale of the flood map
    flood_area_img = flood_extent.multiply(ee.Image.pixelArea())
    map_scale = flood_extent.projection().nominalScale()

    # Properties to go in export
    index = ee.Image(flood_img).get("id")
    began_year = ee.Date(flood_img.get("began")).get("year")
    began_month = ee.Date(flood_img.get("began")).get("month")
    began_day = ee.Date(flood_img.get("began")).get("day")

    def getCountriesPop(ft):
        pop_2000_sum = pop_2000_masked.reduceRegion(
        reducer = ee.Reducer.sum(),
        geometry = ft.geometry(),
        scale = pop_scale,
        maxPixels = 1e9)

        pop_2015_sum = pop_2015_masked.reduceRegion(
        reducer = ee.Reducer.sum(),
        geometry = ft.geometry(),
        scale = pop_scale,
        maxPixels = 1e9)

        area_sum= flood_area_img.reduceRegion(
        reducer= ee.Reducer.sum(),
        geometry= ft.geometry(),
        scale= map_scale,
        maxPixels= 1e9)

        pop_2000 = pop_2000_sum.get("population_count")
        pop_2015 = pop_2015_sum.get("population_count")
        area = area_sum.get("flooded")
        sys_id = ee.String(flood_img.get('system:index')).getInfo()

        return ee.Feature(None, {"system:index":sys_id,
                            "id": index,
                            "Year": began_year,
                            "Month": began_month,
                            "Day": began_day,
                            "Country":ft.get("Country"),
                            "GHSL_2000":pop_2000,
                            "GHSL_2015":pop_2015,
                            "Area": area})

    country_stats = ee.FeatureCollection(flood_countries).map(getCountriesPop)
    return ee.FeatureCollection(country_stats).set({"id":index})

def getFloodPopbyCountry_GHSLTimeSeries(floodImage):
    """
    Args:
        floodImage : the standard Earth Engine Image object outputted by the map_DFO_event function
        roiGEO : the region of interest as an Earth Engine Geometry object

    Returns:
    -a feature collection of all countries for each flood events
    -with a pop and area count
        - An ee feature with properties including
              'Index': the event index ID
              'Began': start date of event map
              'Ended': end date of event map
              'Flood_Area': total area of detected flood
              'Pop_Exposed': the number of people in the mapped flood from WorldPop data
    """
    import ee
    ee.Initialize()

    roiGEO = floodImage.geometry()

    permWater = ee.Image("JRC/GSW1_0/GlobalSurfaceWater").select("transition").eq(1).unmask()
    def maskImages(image):
        nonFlood = image.select("flooded")
        waterMask = nonFlood.multiply(permWater.neq(1))
        return image.select("flooded").mask(waterMask)


    # Extract the final flood extent image data as its own variable for analysis
    floodExtent = maskImages(ee.Image(floodImage.select("flooded")))

    # check to make sure there are actually flooded pixels, some images are only 0 and masked, which will make this function fail.
    # if there is not, then you just return a feature with 0 for pop and area effected.
    #  maxVal = floodExtent.reduceRegion(reducer=ee.Reducer.max(), maxPixels=1e9)

    # Import the World Pop image collection, clip it to the study area, and get the UN adjusted data
    popAll = ee.ImageCollection("JRC/GHSL/P2016/POP_GPW_GLOBE_V1").filterBounds(roiGEO)

    # get event year and available population years to figure out the population dataset closest to the event
    eventYear = ee.Date(floodImage.get('began')).get('year')

    def year_diff(popImg):
        popYear = ee.Date(popImg.get('system:index')).get('year')
        diff = ee.Number(eventYear).subtract(ee.Number(popYear)).abs()
        return popImg.set({"year_diff": diff})

    withYearDiffs = popAll.map(year_diff).sort('year_diff')
    closestYear = withYearDiffs.first().get('system:index')

    popImg = ee.Image(popAll.filterMetadata('system:index', 'equals', closestYear).first())

    # Mask the world population dataset using the flood extent layer
    popScale = popImg.projection().nominalScale()
    popImageMasked = popImg.updateMask(floodExtent)

    #now only select the countries for which flood touches
    #countries = ee.FeatureCollection('USDOS/LSIB_SIMPLE/2017')
    #getcountries = countries.filterBounds(roiGEO.bounds())
    countries = ee.FeatureCollection('projects/global-flood-db/fpu')
    #countries = ee.FeatureCollection('ft:1tdSwUL7MVpOauSgRzqVTOwdfy17KDbw-1d9omPw')
    getcountries = countries.filterBounds(floodExtent.geometry().bounds())

    # Get area of flood in the scale of the flood map
    floodAreaImg = floodExtent.multiply(ee.Image.pixelArea())
    map_scale = floodExtent.projection().nominalScale()
    index= ee.Image(floodImage).get("id")
    began_year = ee.Date(floodImage.get("began")).get("year")
    began_month = ee.Date(floodImage.get("began")).get("month")
    began_day = ee.Date(floodImage.get("began")).get("day")

    def countrieswithpop(feature):
        popsum= popImageMasked.reduceRegion(
        reducer= ee.Reducer.sum(),
        geometry= feature.geometry(),
        scale= popScale,
        maxPixels= 1e9)

        pop = popsum.get("population_count")

        areasum= floodAreaImg.reduceRegion(
        reducer= ee.Reducer.sum(),
        geometry= feature.geometry(),
        scale= map_scale,
        maxPixels= 1e9)

        si = ee.String(floodImage.get('system:index')).getInfo()

        area = areasum.get("flooded")
        return ee.Feature(None, {"system:index":si,
                            "id": index,
                            "Year": began_year,
                            "Month": began_month,
                            "Day": began_day,
                            "FPU": feature.get("id"),
                            #"Country":feature.get("Country"),
                            "Exposed":pop,
                            "Area": area})

    stat= ee.FeatureCollection(getcountries).map(countrieswithpop)
    return ee.FeatureCollection(stat).set({"id":index})

def get_flood_PopbyCountryCIESEN(floodImage):
    """
    Args:
        floodImage : the standard Earth Engine Image object outputted by the map_DFO_event function
        roiGEO : the region of interest as an Earth Engine Geometry object

    Returns:
    -a feature collection of all countries for each flood events
    -with a pop and area count
        - An ee feature with properties including
              'Index': the event index ID
              'Began': start date of event map
              'Ended': end date of event map
              'Flood_Area': total area of detected flood
              'Pop_Exposed': the number of people in the mapped flood from WorldPop data
    """
    import ee
    ee.Initialize()

    roiGEO = floodImage.geometry()

    permWater = ee.Image("JRC/GSW1_0/GlobalSurfaceWater").select("transition").eq(1)
    def maskImages(image):
        nonFlood = image.select("flooded")
        waterMask = nonFlood.multiply(permWater.neq(1))
        return image.select("flooded").mask(waterMask)


    # Extract the final flood extent image data as its own variable for analysis
    floodExtent = maskImages(ee.Image(floodImage.select("flooded")))

    # check to make sure there are actually flooded pixels, some images are only 0 and masked, which will make this function fail.
    # if there is not, then you just return a feature with 0 for pop and area effected.
  #  maxVal = floodExtent.reduceRegion(reducer=ee.Reducer.max(), maxPixels=1e9)

    # Import the World Pop image collection, clip it to the study area, and get the UN adjusted data
    popAll = ee.ImageCollection("CIESIN/GPWv4/unwpp-adjusted-population-count").filterBounds(roiGEO)

    # get event year and available population years to figure out the population dataset closest to the event
    eventYear = ee.Date(floodImage.get('Began')).get('year')

    def year_diff(popImg):
        popYear = ee.Date(popImg.get('system:index')).get('year')
        diff = ee.Number(eventYear).subtract(ee.Number(popYear)).abs()
        return popImg.set({"year_diff": diff})

    withYearDiffs = popAll.map(year_diff).sort('year_diff')
    closestYear = withYearDiffs.first().get('system:index')

    popImg = ee.Image(popAll.filterMetadata('system:index', 'equals', closestYear).first())


    # Mask the world population dataset using the flood extent layer
    popScale = popImg.projection().nominalScale()
    popImageMasked = popImg.updateMask(floodExtent)

    #now only select the countries for which flood touches
    countries = ee.FeatureCollection('ft:1tdSwUL7MVpOauSgRzqVTOwdfy17KDbw-1d9omPw')
    getcountries = countries.filterBounds(floodExtent.geometry().bounds())

    # Get area of flood in the scale of the flood map
    floodAreaImg = floodExtent.multiply(ee.Image.pixelArea())
    map_scale = floodExtent.projection().nominalScale()
    index= ee.Image(floodImage).get("Index")
    began = ee.Date(floodImage.get("Began")).get("year")

    def countrieswithpop(feature):
        popsum= popImageMasked.reduceRegion(
        reducer= ee.Reducer.sum(),
        geometry= feature.geometry(),
        scale= popScale,
        maxPixels= 1e9)

        pop = popsum.get("population-count")

        areasum= floodAreaImg.reduceRegion(
        reducer= ee.Reducer.sum(),
        geometry= feature.geometry(),
        scale= map_scale,
        maxPixels= 1e9)

        area = areasum.get("flooded")
        return ee.Feature(None, {"Index": index,
                            "Year": began_year,
                            "Country":feature.get("Country"),
                            "Exposed":pop,
                            "Area": area})

    stat= ee.FeatureCollection(getcountries).map(countrieswithpop)
    return ee.FeatureCollection(stat).set({"Index":index})

def get_flood_PopArea_CIESIN(floodImage):
    """
    Function to compute the estimated affected population and area (in square meters) of a flood event
    given a computed flood image

    Args:
        floodImage : the standard Earth Engine Image object outputted by the map_DFO_event function
        roiGEO : the region of interest as an Earth Engine Geometry object

    Returns:
        - An ee feature with properties including
              'Index': the event index ID
              'Began': start date of event map
              'Ended': end date of event map
              'Flood_Area': total area of detected flood
              'Pop_Exposed': the number of people in the mapped flood from WorldPop data
    """
    import ee
    ee.Initialize()

    roiGEO = floodImage.geometry()

    # Extract the final flood extent image data as its own variable for analysis
    floodExtent = ee.Image(floodImage.select("flooded"))

    # check to make sure there are actually flooded pixels, some images are only 0 and masked, which will make this function fail.
    # if there is not, then you just return a feature with 0 for pop and area effected.
  #  maxVal = floodExtent.reduceRegion(reducer=ee.Reducer.max(), maxPixels=1e9)

    # Import the World Pop image collection, clip it to the study area, and get the UN adjusted data
    popAll = ee.ImageCollection("CIESIN/GPWv4/unwpp-adjusted-population-count").filterBounds(roiGEO)

    # get event year and available population years to figure out the population dataset closest to the event
    eventYear = ee.Date(floodImage.get('Began')).get('year')

    def year_diff(popImg):
        popYear = ee.Date(popImg.get('system:index')).get('year')
        diff = ee.Number(eventYear).subtract(ee.Number(popYear)).abs()
        return popImg.set({"year_diff": diff})

    withYearDiffs = popAll.map(year_diff).sort('year_diff')
    closestYear = withYearDiffs.first().get('system:index')

    popImg = ee.Image(popAll.filterMetadata('system:index', 'equals', closestYear).first())


    # Mask the world population dataset using the flood extent layer
    popScale = popImg.projection().nominalScale()
    popImageMasked = popImg.updateMask(floodExtent)

    # Calculate the population affected and area maintain as a dictionary
    popAffected = popImageMasked.reduceRegion(reducer=ee.Reducer.sum(),
                                        geometry=roiGEO,
                                        scale=popScale,
                                        maxPixels=1e9,
                                        bestEffort=True);

    # Get area of flood in the scale of the flood map
    floodAreaImg = floodExtent.multiply(ee.Image.pixelArea())

    # map scale
    map_scale = floodExtent.projection().nominalScale()

    floodArea = floodAreaImg.reduceRegion(reducer=ee.Reducer.sum(),
                                         geometry=roiGEO,
                                         scale=map_scale,
                                         maxPixels=1e9,
                                         bestEffort=True);

    results = {'Area_flooded_(km2)': ee.Number(floodArea.get('flooded')).divide(1e6),
               'Pop_Exposed': ee.Number(popAffected.get('population-count')).round()}

    return ee.Feature(ee.Geometry.Point([100,100]),results).copyProperties(floodImage)

def get_flood_PopArea_CIESINdensity(floodImage):
    """
    Function to compute the estimated affected population and area (in square meters) of a flood event
    given a computed flood image

    Args:
        floodImage : the standard Earth Engine Image object outputted by the map_DFO_event function
        roiGEO : the region of interest as an Earth Engine Geometry object

    Returns:
        - An ee feature with properties including
              'Index': the event index ID
              'Began': start date of event map
              'Ended': end date of event map
              'Flood_Area': total area of detected flood
              'Pop_Exposed': the number of people in the mapped flood from WorldPop data
    """
    import ee
    ee.Initialize()

    roiGEO = floodImage.geometry()

    permWater = ee.Image("JRC/GSW1_0/GlobalSurfaceWater").select("transition").eq(1)
    def maskImages(image):
        nonFlood = image.select("flooded")
        waterMask = nonFlood.multiply(permWater.neq(1))
        return image.select("flooded").mask(waterMask)


    # Extract the final flood extent image data as its own variable for analysis
    floodExtent = maskImages(ee.Image(floodImage.select("flooded")))


    # check to make sure there are actually flooded pixels, some images are only 0 and masked, which will make this function fail.
    # if there is not, then you just return a feature with 0 for pop and area effected.
  #  maxVal = floodExtent.reduceRegion(reducer=ee.Reducer.max(), maxPixels=1e9)

    # Import the World Pop image collection, clip it to the study area, and get the UN adjusted data
    popAll = ee.ImageCollection("CIESIN/GPWv4/unwpp-adjusted-population-density").filterBounds(roiGEO)

    # get event year and available population years to figure out the population dataset closest to the event
    eventYear = ee.Date(floodImage.get('Began')).get('year')

    def year_diff(popImg):
        popYear = ee.Date(popImg.get('system:index')).get('year')
        diff = ee.Number(eventYear).subtract(ee.Number(popYear)).abs()
        return popImg.set({"year_diff": diff})

    withYearDiffs = popAll.map(year_diff).sort('year_diff')
    closestYear = withYearDiffs.first().get('system:index')

    popImg = ee.Image(popAll.filterMetadata('system:index', 'equals', closestYear).first())


    # Mask the world population dataset using the flood extent layer
    popScale = ee.Image(popAll.first()).projection().nominalScale()
    popPerPixel = popImg.multiply(ee.Image.pixelArea().divide(1e6))
    popImageMasked = popPerPixel.updateMask(floodExtent)


    # Calculate the population affected and area maintain as a dictionary
    popAffected = popImageMasked.reduceRegion(reducer=ee.Reducer.sum(),
                                        geometry=roiGEO,
                                        scale=popScale,
                                        maxPixels=1e9,
                                        bestEffort=True);

    # Get area of flood in the scale of the flood map
    floodAreaImg = floodExtent.multiply(ee.Image.pixelArea())

    # map scale
    map_scale = floodExtent.projection().nominalScale()

    floodArea = floodAreaImg.reduceRegion(reducer=ee.Reducer.sum(),
                                         geometry=roiGEO,
                                         scale=map_scale,
                                         maxPixels=1e9,
                                         bestEffort=True);

    results = {'Area_flooded_(km2)': ee.Number(floodArea.get('flooded')).divide(1e6),
               'Pop_Exposed': ee.Number(popAffected.get('population-density')).round()}

    return ee.Feature(ee.Geometry.Point([100,100]),results).copyProperties(floodImage)

def get_flood_PopArea_WP(floodImage):
    """
    Function to compute the estimated affected population and area (in square meters) of a flood event
    given a computed flood image

    Args:
        floodImage : the standard Earth Engine Image object outputted by the map_DFO_event function
        roiGEO : the region of interest as an Earth Engine Geometry object

    Returns:
        - An ee feature with properties including
              'Index': the event index ID
              'Began': start date of event map
              'Ended': end date of event map
              'Flood_Area': total area of detected flood
              'Pop_Exposed': the number of people in the mapped flood from WorldPop data
    """
    import ee
    ee.Initialize()

    roiGEO = floodImage.geometry()

    # Extract the final flood extent image data as its own variable for analysis
    floodExtent = ee.Image(floodImage.select("flooded"))

    # check to make sure there are actually flooded pixels, some images are only 0 and masked, which will make this function fail.
    # if there is not, then you just return a feature with 0 for pop and area effected.
  #  maxVal = floodExtent.reduceRegion(reducer=ee.Reducer.max(), maxPixels=1e9)

    # Import the World Pop image collection, clip it to the study area, and get the UN adjusted data
    worldPopAll = ee.ImageCollection("WorldPop/POP").filterBounds(roiGEO).filterMetadata('UNadj','equals','yes')

    valid = ee.Algorithms.If(worldPopAll.first(), True, False)


    # get event year and available population years to figure out the population dataset closest to the event
    eventYear = ee.Date(floodImage.get('Began')).get('year')

    def year_diff(popImg):
        diff = ee.Number(eventYear).subtract(ee.Number(popImg.get('year'))).abs()
        return popImg.set({"year_diff": diff})

    withYearDiffs = worldPopAll.map(year_diff).sort('year_diff')
    closestYear = withYearDiffs.first().get('year')

    worldPop = worldPopAll.filterMetadata('year', 'equals', closestYear).mosaic()


    # Mask the world population dataset using the flood extent layer
    popImageColl = worldPop.updateMask(floodExtent)
    wpScale = ee.Image(worldPopAll.first()).projection().nominalScale()


    # Calculate the population affected and area maintain as a dictionary
    popAffected = popImageColl.reduceRegion(reducer=ee.Reducer.sum(),
                                        geometry=roiGEO,
                                        scale=wpScale,
                                        maxPixels=1e9,
                                        bestEffort=True);

    # Get area of flood in the scale of the flood map
    floodAreaImg = floodExtent.multiply(ee.Image.pixelArea())

    # map scale
    map_scale = floodExtent.projection().nominalScale()

    floodArea = floodAreaImg.reduceRegion(reducer=ee.Reducer.sum(),
                                         geometry=roiGEO,
                                         scale=map_scale,
                                         maxPixels=1e9,
                                         bestEffort=True);

    results = {'Area_flooded_(km2)': ee.Number(floodArea.get('flooded')).divide(1e6),
               'Pop_Exposed': ee.Number(popAffected.get('population')).round()}

    return ee.Feature(ee.Geometry.Point([100,100]),results).copyProperties(floodImage)

# --------------------------------------------------------
# The function below was written by Devin Routh to output
# precipitation data for each event in order to compute
# the maximum precipitation date for the event as well as
# a hyetograph.
# --------------------------------------------------------

def create_Flood_Precip_Series(dateRangeOI, roiGEO):
    """
    Function to compute the daily precipitation series for the event

    Args:
        floodImage : the standard Earth Engine Image object outputted by the map_DFO_event function
        roiGEO : the region of interest as an Earth Engine Geometry object

    Returns:
        - The daily precipitation value (averaged across the ROI) for each day  within the DateRange
        corresponding to the inputted floodImage
    """
    import ee
    ee.Initialize()
    import pandas as pd

    # Load the Persiann precipitation dataset, filter it, and prep it
    persiannPrecip = ee.ImageCollection('NOAA/PERSIANN-CDR').filterBounds(roiGEO).filterDate(dateRangeOI.start(), dateRangeOI.end());

    # Compute the scale of the Persiann dataset
    persiannScale = ee.Image(persiannPrecip.first()).projection().nominalScale()

    # Clip the collection to the ROI
    def clipCollection(collection, geometry):
        def clipimage(image): return image.clip(ee.Geometry(geometry));
        return collection.map(clipimage);
    clippedPrecipColl = clipCollection(persiannPrecip, roiGEO);

    # Find the mean precipitation values of all images in the collection
    def meanPrecip(image):
        meanDict = image.reduceRegion(ee.Reducer.mean(), None, persiannScale);
        finalDict = meanDict.set('Date', ee.Date.parse('yyyyMMdd', image.get('system:index')));
        return ee.Feature(None, finalDict);

    fcPrecip = clippedPrecipColl.map(meanPrecip);

    # Reformat the precipitation data into a EE dictionary
    precipList = fcPrecip.toList(999)
    def returnFeatID(element): return ee.Feature(element).id()
    def returnFeatPrecip(element): return ee.Feature(element).get('precipitation')
    precipDict = ee.Dictionary.fromLists(precipList.map(returnFeatID),precipList.map(returnFeatPrecip))

    # Dump this EE dictionary into JSON then convert it to a Pandas Series (while formatting it
    # to have the dates as the index of the series and the precipitation values in mm as the data)
    pdJSONDumps = pd.json.loads(pd.json.dumps(precipDict.getInfo()))
    precipPDF = pd.DataFrame(pdJSONDumps.items(), columns=['Date', 'Precipication_mm'])
    precipPDF['Date'] = pd.to_datetime(precipPDF['Date'], format='%Y%m%d') # precipPDF['Date']
    precipPDF.set_index(precipPDF['Date'], inplace=True)
    precipPDF = precipPDF.drop('Date',1)
    precipPDF.sort_index(inplace=True)
    precipPTS = pd.Series(precipPDF['Precipication_mm'],index=precipPDF.index.values)

    return precipPTS
