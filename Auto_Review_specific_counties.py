####################### Auto_Review_specific_counties.py #######################

############################
####### DESCRIPTION ########
############################

############################
##########  SETUP ##########
############################
import os
from Automated_Review import *

############################
######## PARAMETERS ########
############################

############################
##### DEFINE FUNCTIONS #####
############################
def single_step(func):
    """
    This function allows you to run steps from Automated_Review.py as normal,
    without having to worry about tracking intermed_list, or skip_list.
    Note: This will override existing features, beware!
    Put the full function for func. For example:
    single_step(clip(input_feature=filepath, clip_files=files, output_location=output,
         state_abbrev="DC", county_name="District_of_Colombia"))
    Of course, you can't use DC as a state because DC is not a state and has
    taxation without representation despite a population of 700,000+, greater than
    the entire population of Vermont or Wyoming. But good thing the US split Dakatoa
    into both a North Dakota and a South Dakota, which had populations of 190,983
    and 348,600 respectively when they achieved statehood.
    :param func: the function from Automated_Review, with all of its parameters.
    :return: output file path
    """
    intermed_list = []
    skip_list = []
    path = func
    return path


def single_county(batch_file, iteration_number=None):
    """
    This function runs all the steps for a single county.
    Note that this uses skip_list from the Automated_Review script, so
    if you don't want something to be skipped, change it there and save it.
    :param batch_file: file path to the relevant batch_file
    :param iteration_number: optional iteration number. UNTESTED.
    :return: file path to AutoReview file.
    """
    global neg_masks
    
    cluster_GDB = os.path.dirname(batch_file)
    state_abbrev = os.path.basename(batch_file)[6:8]
    state_name = nameFormat(state_abbrev_to_name[state_abbrev])
    county_name = os.path.basename(batch_file)[9:]
    county_outline = os.path.join(county_outline_folder,
                                          state_name + '.gdb',
                                          county_name + 'Co' + state_abbrev + '_outline')
    FIPS, UTM = find_FIPS_UTM(county_outline)
    
    print "Clipping."
    clipFile = clip(batch_file, county_outline, cluster_GDB, state_abbrev, county_name)
    print "Clip finished for", state_abbrev, county_name
    
    print "Masking."
    # Do some stuff that is unique to WA, OR and CA
    state_land_mask = r'R:\Nat_Hybrid_Poultry\Remote_Sensing\PADUS\PADUS1_4Shapefile\PADUS_WA_OR_CA_FED_STAT_LOC.shp'
    if state_abbrev in ['WA', 'OR', 'CA']:  # REMOVE THIS LATER
        if not [state_land_mask, 0] in neg_masks:
            neg_masks += [[state_land_mask, 0]]
    else:
        if [state_land_mask, 0] in neg_masks:
            neg_masks.remove([state_land_mask, 0])

    if not (neg_masks == [] and pos_masks == []):
        maskFile = masking(clipFile, cluster_GDB, state_abbrev, county_name, county_outline,
                       neg_masks, pos_masks)
    else:
        print "No masking files selected."
        maskFile = clipFile  # This essentially just skips the masking step

    print "Masking finished for", state_abbrev, county_name

    print "LARing."
    larFile = LAR(maskFile, cluster_GDB, LAR_thresholds, state_abbrev, county_name)
    print "LAR finished for", state_abbrev, county_name

    print "ProbSurf."
    probSurfaceFile = prob_surface(larFile, prob_surface_raster, cluster_GDB, state_abbrev, county_name)
    print "ProbSurf finished for", state_abbrev, county_name

    print "Collapsing points."
    collapsePointsFile = collapse_points(probSurfaceFile, cluster_GDB, state_abbrev, county_name)
    print "Points collapsed for", state_abbrev, county_name

    print "Sampling in a simulated sort of way."
    simSamplingFile = simulated_sampling(collapsePointsFile, prob_surface_raster, cluster_GDB,
                                        state_abbrev, county_name, ss_bins='default',
                                        iteration=iteration_number)
    print "Simulated Sampling finished for", state_abbrev, county_name

    print "Projecting."
    autoReviewFile = project(simSamplingFile, cluster_GDB, UTM, state_abbrev, county_name,
                             iteration=iteration_number)
    print "AutoReview finished for", state_abbrev, county_name

    if saveIntermediates == False:
        deleteIntermediates(intermed_list)

    return autoReviewFile

if __name__ == '__main__':
    print "Ready to do some stuff."
    
