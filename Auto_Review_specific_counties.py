####################### Autom_Review_specific_counties.py #######################

############################
####### DESCRIPTION ########
############################

import Automated_Review

def singleCounty(batch_file, clusterGDB, state_abbrev, county_name, iterationNumber=None):
    ##
    ##
    ##
    clipFile = clip(batch_file, county_outline, clusterGDB, state_abbrev, county_name)

    ## Do some stuff that is unique to WA, OR and CA
    state_land_mask = r'R:\Nat_Hybrid_Poultry\Remote_Sensing\PADUS\PADUS1_4Shapefile\PADUS_WA_OR_CA_FED_STAT_LOC.shp'
    if state_abbrev in ['WA', 'OR', 'CA']:  ## REMOVE THIS LATER
        if not [state_land_mask, 0] in neg_masks:
            neg_masks += [[state_land_mask, 0]]
    else:
        if [state_land_mask, 0] in neg_masks:
            neg_masks.remove([state_land_mask, 0])

    if not (neg_masks == [] and pos_masks == []):
        maskFile = masking(clipFile, clusterGDB, state_abbrev, county_name, county_outline,
                       neg_masks, pos_masks)
    else:
        print "No masking files selected."
        maskFile = clipFile  # This essentially just skips the masking step

    larFile = LAR(maskFile, clusterGDB, LAR_thresholds, state_abbrev, county_name)

    probSurfaceFile = probSurface(larFile, prob_surface_raster, clusterGDB, state_abbrev, county_name)

    collapsePointsFile = collapsePoints(probSurfaceFile, clusterGDB, state_abbrev, county_name)

    if numIterations <= 1 or numIterations is None:
        iterationNumber = None
    else:
        for eachIteration in range(1, numIterations + 1):
            iterationNumber = eachIteration

            simSamplingFile = simulatedSampling(collapsePointsFile, prob_surface_raster, clusterGDB,
                                                state_abbrev, county_name, ssBins='default',
                                                iteration=iterationNumber)
            autoReviewFile = project(simSamplingFile, clusterGDB, UTM, state_abbrev, county_name,
                                     iteration=iterationNumber)

    if saveIntermediates == False:
        deleteIntermediates(intermed_list)

    return autoReviewFile