# Colin Doyle
# October 10, 2017

# use this template to run the flood stats functions (area, population, etc.)
# on an image collection and export results as a csv

import ee
ee.Initialize()

from flood_stats import pop_utils
import time, csv

# Image Collection of flood maps, each needs layer called "flooded" that
# is 1 = flooded, 0 = not flooded
gfd = ee.ImageCollection('projects/global-flood-db/gfd_v3').filterMetadata('id','greater_than',4335)

# Create Error Log file
log_file = "error_logs/event_stats/pop_error_log_{0}.csv".format(time.strftime("%d_%m_%Y"))
with open(log_file,"w", newline='') as out_file:
    wr = csv.writer(out_file)
    wr.writerow(["error_type", "dfo_id", "error_message"])

# Create list of events from input fusion table
event_ids = ee.List(gfd.aggregate_array('id')).sort()
id_list = event_ids.getInfo()
id_list = [int(i) for i in id_list]

for event_id in id_list:
    # Get event date range, they can be passed as Strings
    flood_event = ee.Image(gfd.filterMetadata('id', 'equals', event_id).first())

    try:
        # Calculate flood stats
        flood_stats = pop_utils.getFloodPopbyCountry_GHSLTimeSeries(flood_event)
        index = flood_stats.get("id").getInfo()
        print("calculated results, exporting results for DFO {0}...".format(int(index)))

    except Exception as e:
        s = str(e)
        with open(log_file,"w", newline='') as out_file:
            wr = csv.writer(out_file)
            wr.writerow(["Calculation Error", event_id, s])
        print("Calculation Error {0} - Cataloguing and moving onto next event".format(event_id))
        print("-------------------------------------------------")

    # Export results
    try:
        task = ee.batch.Export.table.toCloudStorage(
            collection = flood_stats,
            description = 'GFD_bycountryEstimates_GHSL_TS_{0}'.format(str(int(index))),
            bucket = 'event_stats',
            fileNamePrefix = 'ghsl_fpu/GFD_{0}_Pop_Area_GHSL_TS_2019_07_29'.format(str(int(index))),
            fileFormat = 'CSV')

        task.start()

    except Exception as e:
        s = str(e)
        with open(log_file,"ab") as out_file:
            wr = csv.writer(out_file)
            wr.writerow(["Export Error", event_id, s])
        print("Export Error DFO {0} - Cataloguing and moving onto next event".format(event_id))
        print("-------------------------------------------------")

print('Done!')
