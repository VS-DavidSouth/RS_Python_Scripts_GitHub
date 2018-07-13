####################### Automated_Review.py #######################

############################
####### DESCRIPTION ########
############################

##
## Created by David South 7/9/18, updated N/A
##
## Script Description:
##
## This scirpt would be great to make an ArcGIS tool out of.
##
## Note: as the script stands now, save each individual step along the way
##  Have a boolean that allows you to save all steps, or not
##
## This script is designed to be used as a custom ArcGIS tool. Instructions
##  for setting it up in ArcGIS will be included. Reference this URL:
##  http://desktop.arcgis.com/en/arcmap/10.3/analyze/creating-tools/adding-a-script-tool.htm
##

############################
########## SETUP ###########
############################

import time
start_time = time.time()

import arcpy, os
arcpy.env.OverwriteOutput = True

from Creating_TP_FN_FP_files import addRasterInfo, checkTime

# this next import gives us access to two dictionaries for converting state names to abbreviations and vice versa
sys.path.insert(0, r'O:\AI Modeling Coop Agreement 2017\David_working\Python') # it also gives us the nameFormat function which is very useful for name standardization
from Converting_state_names_and_abreviations import *


############################
#### NAMING CONVENTIONS ####
############################

## Names for all files created in this script will follow the the same format.
##
##      [prefix]_[ST]_Z[##]_c[#]_[CountyName].[ext]
##
## Some files will not have Z[##], c[#], or [CountyName].
##
##      [prefix] -> a unique identifier for each type of file
##      [ST] -> the state abbreviation
##      Z[##] -> the UTM zone number
##      c[#] -> the cluster number
##      [CountyName] -> the specific county name
##      [ext] -> the file extension
##

prefix_dict = {
    'NAIP': 'downloaded 1m resolution NAIP areal imagery',
    'NAIP2m': '2m resampled NAIP imagery',
    'Model': 'AFE file that is used to create the Batch files for a particular state',
    'ModelGDB': 'The file geodatabase that was used to create the Model for that state',
    'ModelMXD': 'The ArcMap MXD that was used to run Feature Analyst to create the Model',
    'BatchGDB': 'A file geodatabase that contains all the intermediate files for the creation of the Batch file',
    'BatchMXD': 'The ArcMap MXD file that was used to run Feature Analyst to create the Batch file',
    'Clip': 'Intermediate stage after creating Batch file, this is the Batch file clipped to the county',
    'LAR': 'TO BE DETERMINED',
    'Masked': 'TO BE DETERMINED',
    'ProbSurf': 'TO BE DETERMINED',
    'Integrate': 'TO BE DETERMINED',
    'CollectEvents': 'TO BE DETERMINED',
    'AutoReview': 'TO BE DETERMINED',
    }


############################
######## PARAMETERS ########
############################

save_intermediates = True   # change to false if you don't care about the intermediate files

global intermed_list
intermed_list = []  # this will be filled later with the filepaths to all the intermediate
                    #  files, which may or may not be deleted depending on whether
                    #  save_intermediates is True or False

## list of                     
from resample_NAIP import first10counties
countyList = []
for county in first10counties:
    countyList.append([county, 'AL'])

## location of probability surface raster
probSurfaceRaster = r'N:\FLAPS from Chris Burdett\Data\poultry_prob_surface\poultryMskNrm\poultryMskNrm.tif'

output_folder = r'R:\Nat_Hybrid_Poultry\Remote_Sensing\Feature_Analyst'

############################
#### DEFINE FUNCTIONS #####
############################

def checkTime():
    ##
    ## This function returns a string of how many minutes or hours the
    ##  script has run for so far.
    ##
    timeSoFar = time.time() - start_time
    timeSoFar /= 60     # changes this from seconds to minutes
    
    if timeSoFar < 60. :
        return str(int(round(timeSoFar))) + " minutes"

    else:
        return str(round( timeSoFar / 60. , 1)) + " hours"

def clip(input_feature, clip_files, output_location, state_abbrev, county_name):

    ## Get rid of any weird characters in the county name
    county_name = nameFormat(county_name)
    
    ## Set up the name and lcation of the output 
    outputName = 'Clip_' + state_abbrev + '_' + county_name
    outputFilepath = os.path.join(output_location, outputName)

    ## Do the clip
    arcpy.Clip_analysis(in_features = input_feature, \
                        clip_features = clip_files, \
                        out_feature_class = outputFilepath, \
                        cluster_tolerance = "")
    
    ## Add the old file to the list of intermediate files
    intermed_list.append(input_feature)

    return outputFilepath
    
def LAR(input_feature, L_threshold, AR_threshold, state_abbrev, county_name):
    ##
    ## LAR stands for Length(L) and Aspect Ratio(AR)
    ##

    county_name = nameFormat(county_name)

    ## Add the AspRatio field
    arcpy.AddField_management(in_table = input_feature, \
                              field_name = "AspRatio", field_type = "SHORT", \
                              field_precision = "", field_scale = "", field_length = "", \
                              field_alias = "", field_is_nullable = "NULLABLE", \
                              field_is_required = "NON_REQUIRED", field_domain = "")

    ## Fill the AspRatio field that was just created
    arcpy.CalculateField_management(in_table = input_feature, \
                                    field = "AspRatio", \
                                    expression = "[Length]/[Width]", \
                                    expression_type = "VB", code_block = "")

    ## Delete features based on the Length and AspRatio fields

    ## Add the old file to the list of intermediate files
    intermed_list.append(input_feature)
    
def masking(variable1, variable2, state_abbrev, county_name):
    
    county_name = nameFormat(county_name)
    ()

def probSurface(input_point_data, raster_dataset, output_location, state_abbrev, county_name):
    ##
    ## This function exists to replace the Manual Review step of the regional
    ##  remote sensing procedure. It uses the FLAPS probability surface to
    ##  determine which points are True Positives (TP) or False Positives (FP).
    ##

    county_name = nameFormat(county_name)

    threshold = 0.15

    outputName = 'ProbSurf_' + state_abbrev + '_' + county_name
    outputFilepath = os.path.join(output_location, outputName)

    arcpy.CopyFeatures_management (input_point_data, outputFilepath)

    ## This next funciton comes from the creating_TF_FN_FP_files.py script
    addRasterInfo(outputFilepath, raster_dataset)

    ## Apply threshold - NOTE THIS WILL LIKELY BE CHANGED LATER
    with arcpy.da.UpdateCursor(outputFilepath, "ProbSurf_1") as cursor:
        for row in cursor:
            if row[0] < threshold:
                cursor.deleteRow()

    ## Add the old file to the list of intermediate files
    intermed_list.append(input_point_data)

    return outputFilepath
        
def collapsePoints(input_point_data, output_location, state_abbrev, county_name):
    ##
    ## Note: This function changes the input data with the Integrate tool.
    ##

    county_name = nameFormat(county_name)

    ## Set up names and filepaths for the Ingetrate and CollectEvents files 
    integrateOutputName = 'Integrate_' + state_abbrev + '_' + county_name
    integrateOutputFilepath = os.path.join(output_location, integrateOutputName)
    collectEventsOutputName = 'CollectEvents' + '_' + state_abbrev + '_' + county_name
    collectEventsOutputFilepath = os.path.join(output_location, collectEventsOutputName)

    arcpy.CopyFeatures_management (input_point_data, integrateOutputFilepath)

    ## Move points within 100m of each other all on top of each other at the centroid
    #arcpy.Integrate_management(in_features = integrateOutputFilepath, 
    #                           cluster_tolerance = "100 Meters")
    ## NOTE: YOU MUST REPLACE THIS WITH THE ACTUAL LOCATION, TYPE IT IN WITH / INSTEAD OF \, NO r'. IT MUST HAVE THE "'R:/...' #"
    #arcpy.Integrate_management(in_features = "'N:/Remote Sensing Projects/2016 Cooperative Agreement Poultry Barns/Documents/Poultry Population Modeling Project/Rdrive/Remote_Sensing/Feature_Analyst/Alabama/BatchGDB_AL_Z16_c1.gdb/ProbSurf_AL_Barbour' #",
    #                           cluster_tolerance = "100 Meters")
    arcpy.Integrate_management(in_features = integrateOutputFilepath,cluster_tolerance = "100 Meters")


    
    ## Collapse points that are on top of eachother to single points
    arcpy.CollectEvents_stats(Input_Incident_Features = integrateOutputFilepath, \
                              Output_Weighted_Point_Feature_Class = collectEventsOutputFilepath)

    ## Add the old file to the list of intermediate files
    intermed_list.append(input_point_data)
    intermed_list.append(integrateOutputFilepath)

    return collectEventsOutputFilepath

def project(input_point_data, output_location, state_abbrev, county_name):

    county_name = nameFormat(county_name)
    
    outputName = ''
    outputFilepath = os.path.join(output_location, outputName)
    
    ## Project file into WGS 1984 Geographic Coordinate System
    
    ## Add coordinates
    arcpy.AddXY_management(in_features)

    ## Add the old file to the list of intermediate files
    intermed_list.append(input_point_data)

    return outputFilepath

def deleteIntermediates(intermed_list):
    ##
    ## This function is designed to be used in the other functions
    ##  whenever they have any intermediate files. It will delete
    ##  all files that are in list format in the intermed_list
    ##  input. (intermed is short for intermediate)
    ##

    for intermed_file in intermed_list:
        try:
            arcpy.Delete_management(intermed_file)
        except:
            print "error deleting the following file:\n" + intermed_file

if __name__ == '__main__':

    #for county in countyList:
    for county in [['Barbour', 'AL']]:
        county_name = county[0]
        state_abbrev = county[1]
        state_name = nameFormat(state_abbrev_to_name[state_abbrev])
        zone = 16 ##CHANGE THIS LATER
        cluster = 1 ##CHANGE THIS LATER
        batchGDB = 'BatchGDB_' + state_abbrev + '_Z' + str(zone) + '_c' + str(cluster) + '.gdb'
        batchGDB = os.path.join(output_folder, state_name, batchGDB)
        batchFile = 'Batch' + '_' + state_abbrev + '_' + county_name
        batchLocation = os.path.join(batchGDB, batchFile)

        county_outline_folder = r'N:\Remote Sensing Projects\2016 Cooperative Agreement Poultry Barns\Documents\Deliverables\Library\CountyOutlines'
        county_outline = os.path.join(county_outline_folder,
                                      state_name + '.gdb', county_name + 'Co' + state_abbrev + '_outline')

        print "Clipping", state_name, county_name + "..."
        #clipFile = clip(batchLocation, county_outline, batchGDB, state_abbrev, county_name)
        print "Clipped. Script duration so far:", checkTime()

        #LAR(input_feature, L_threshold, AR_threshold)
        #masking()

        print "Applying probability surface for", state_name, county_name
        #probSurfaceFile = probSurface(clipFile, probSurfaceRaster, batchGDB, state_abbrev, county_name)
        print "Probability surface applied. Script duration so far:", checkTime()

        print "Collapsing points for", state_name, county_name
        collapsePointsFile = collapsePoints(probSurfaceFile, batchGDB, state_abbrev, county_name)
        print "Points collapsed. Script duration so far:", checkTime()

        print "Projecting Automated Review for", state_name, county_name
        automatedReviewFile = project(collapsePointsFile, batchGDB, state_abbrev, county_name)
        print "Projected. Script duration so far:", checkTime()

        if save_intermediates == False:
            deleteIntermediates(intermed_list)
