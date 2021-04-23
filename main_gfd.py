# Wrapper function for running modis_dfo algorithm over DFO database.

import ee
ee.Initialize()

from flood_detection import modis
from flood_detection.utils import export, misc

import time, os, csv

# INPUTS
# Enter the ID of the GEE Asset that contains the list of events to be mapped
# and cast as ee.FeatureCollection(). GEE Asset must have at least 3 columns
# titled: "ID", "Began", "Ended". In this version of the script, the GEE
# Asset also needs to have polygons associated with each event that will be used
# to select watersheds from global HydroSheds data to use as the area to map the
# event over.

# This GEE Asset is the QC database from August 1, 2019
event_db = ee.FeatureCollection("projects/global-flood-db/dfo-polygons/qc-aug-01-2019").sort("ID")

# This GEE Asset is the DFO Polygon database from Dec 3rd, 2019
# event_db = ee.FeatureCollection("projects/global-flood-db/dfo-polygons/dec-03-2019")

# GEE Asset folder and Google Cloud Storage for image collection
gcs_folder = "gfd_v3"
asset_path = "projects/global-flood-db/gfd_v3"

#-------------------------------------------------------------------------------
# PROCESSING STARTS HERE

# Create Error Log file
log_file = "error_logs/gfd_v3/error_log_{0}.csv".format(time.strftime("%d_%m_%Y"))

with open(log_file,"ab") as out_file:
    wr = csv.writer(out_file)
    wr.writerow(["error_type", "dfo_id", "error_message"])

# Create list of events from input gee asset
event_ids = ee.List(event_db.filterMetadata("ID", "greater_than", 4603).aggregate_array('ID')).sort()
id_list = event_ids.getInfo()
id_list = [int(i) for i in id_list]

# NOTE: Code snippet for when you are re-running floods in error log
# errors = "error_logs\\gfd_v3\\3Day_otsu_error_log_23_07_2019_1.csv"
# with open(errors) as f:
#     id_list = sorted([int(float(row["dfo_id"])) for row in csv.DictReader(f)])

# NOTE: ID List for Validation Floods
# id_list = [1641,1810,1818,1910,1925,1931,1971,2024,2035,2045,2075,2076,2099,
#            2104,2119,2143,2167,2177,2180,2183,2191,2206,2214,2216,2261,2269,
#            2296,2303,2332,2345,2366,2395,2443,2444,2458,2461,2463,2473,2507,
#            2543,2570,2584,2586,2597,2599,2629,2640,2650,2688,2711,2780,2821,
#            2829,2832,2940,2947,2948,3070,3075,3076,3094,3123,3132,3162,3166,
#            3179,3198,3205,3218,3267,3274,3282,3285,3306,3345,3365,3366,3464,
#            3476,3544,3567,3572,3625,3657,3658,3667,3673,3678,3692,3696,3754,
#            3786,3801,3846,3850,3856,3871,3894,3916,3931,3977,4019,4022,4024,
#            4083,4098,4115,4159,4163,4171,4179,4188,4211,4218,4226,4241,4258,
#            4272,4314,4315,4325,4339,4340,4346,4357,4364,4427,4428,4435,4444,
#            4464,4507,4516]

snooze_button = 1
for event in id_list:

    # Check if we have worn out GEE
    if snooze_button%50==0: #if true - hit the snooze button
        print "---------------------Giving GEE a breather for 15 mins--------------------"
        time.sleep(900)

    # Get event date range
    flood_event = ee.Feature(event_db.filterMetadata('ID', 'equals', event).first())
    began = str(ee.Date(flood_event.get('Began')).format('yyyy-MM-dd').getInfo())
    ended = str(ee.Date(flood_event.get('Ended')).format('yyyy-MM-dd').getInfo())
    thresh_type = str(flood_event.get('ThreshType').getInfo())

    if thresh_type == 'std':
        thresh_type = 'standard'
    else:
        pass

    # Use polygon from event GEE Asset to select watersheds from global
    # HydroSheds data choose level3, level4, or level5
    watershed = misc.get_watersheds_level4(flood_event.geometry()).union().geometry()
    # watershed = misc.get_islands(flood_event.geometry()).union().geometry()

    try:
        # Map the event. Returns 4 band image: 'flooded', 'duration',
        # 'clearViews', 'clearPerc'
        print "Mapping Event {0} - {1} threshold".format(event, thresh_type)
        flood_map = modis.dfo(watershed, began, ended, thresh_type, "3Day")

        # Apply slope mask to remove false detections from terrain
        # shadow. Input your image and choose a slope (in degrees) as a threshold
        flood_map_slope_mask = misc.apply_slope_mask(flood_map, thresh=5)

        # Get permanent water from JRC dataset at MODIS resolution
        perm_water = misc.get_jrc_perm(watershed)

        # Get countries within the watershed boundary
        country_info = misc.get_countries(watershed)

        # Add permanent and seasonal water as bands to image
        # Format the final DFO algorithm image for export
        dfo_final = ee.Image(flood_map_slope_mask).addBands(perm_water)\
                            .set({'id': event,
                                  'gfd_country_code': str(country_info[0]),
                                  'gfd_country_name': str(country_info[1])})

    except Exception as e:
        s = str(e)
        with open(log_file,"ab") as out_file:
            wr = csv.writer(out_file)
            wr.writerow(["DFO Algorithm Error", event, s])
        print "DFO Algorithm Error {0} - Cataloguing and moving onto next event".format(event)
        print "-------------------------------------------------"
        snooze_button+=1
        continue

    try:
    #     Export to an asset. This function needs the ee.Image of the flood map
    #     from map_DFO_event, the roi that is returned from the
    #     map_floodEvent_MODIS, the path to where the asset will be saved, and
    #     the resolution (in meters) to save it (default = 250m)

        export.to_asset(dfo_final, watershed.bounds(), asset_path, 250)
        export.to_gcs(dfo_final, watershed.bounds(), gcs_folder, 'DFO', 250)

        print "Uploading DFO {0} to GEE Assets & GCS".format(event)
        print "-------------------------------------------------"

    except Exception as e:
        s = str(e)
        with open(log_file,"ab") as out_file:
            wr = csv.writer(out_file)
            wr.writerow(["Export Error", event, s])
        print "Export Error DFO {0} - Cataloguing and moving onto next event".format(event)
        print "-------------------------------------------------"

    # Add to the snooze_button so we don't make Noel angry.
    snooze_button+=1
