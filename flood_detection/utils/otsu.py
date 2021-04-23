
# coding: utf-8

# Otsu thresholding functions for choosing thresholds for DFO flood detection
import ee
ee.Initialize()

# Compute between sum of squares, where each mean partitions the data.
def get_threshold(histogram):
    counts = ee.Array(ee.Dictionary(histogram).get('histogram'))
    means = ee.Array(ee.Dictionary(histogram).get('bucketMeans'))
    size = means.length().get([0])
    total = counts.reduce(ee.Reducer.sum(), [0]).get([0])
    summed = means.multiply(counts).reduce(ee.Reducer.sum(), [0]).get([0])
    mean = summed.divide(total)

    indices = ee.List.sequence(1, size)

    def calc_bss(i):
        aCounts = counts.slice(0, 0, i)
        aCount = aCounts.reduce(ee.Reducer.sum(), [0]).get([0])
        aMeans = means.slice(0, 0, i)
        aMean = aMeans.multiply(aCounts).reduce(ee.Reducer.sum(), [0]).get([0]).divide(aCount)
        bCount = total.subtract(aCount)
        bMean = summed.subtract(aCount.multiply(aMean)).divide(bCount)
        return aCount.multiply(aMean.subtract(mean).pow(2)).add(bCount.multiply(bMean.subtract(mean).pow(2)))

    bss = indices.map(calc_bss)

    # Return the mean value corresponding to the maximum BSS.
    return means.sort(bss).get([-1])
