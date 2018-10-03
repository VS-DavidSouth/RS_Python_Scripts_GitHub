####################### Automated_Review.py #######################

############################
####### DESCRIPTION ########
############################

##
## Created by David South 7/9/18, updated 8/9/18
##
## Script Description:
##      This script is intended for use with remotely sensed poultry data
##       exported from the Feature Analyst extension in vector point form.
##      It is intended to be used to remove clutter from the input dataset
##       using various methods. It requires a probability surface raster,
##       as well as county polygon files for each county that will be
##       referenced during the course of the script.
##
## This script is designed to be used as a custom ArcGIS tool. Instructions
##  for setting it up in ArcGIS will be included. Reference this URL:
##  http://desktop.arcgis.com/en/arcmap/10.3/analyze/creating-tools/adding-a-script-tool.htm
##
## The Spatial Analyst ArcGIS extension is required for the ProbSurface portion
##  of this script.
##

############################
########## SETUP ###########
############################

import os, sys, csv, random
import numpy as np

import time
start_time = time.time()

import arcpy
arcpy.env.OverwriteOutput = True

## This next import gives us access to two dictionaries for
##  converting state names to abbreviations and vice versa
from Converting_state_names_and_abreviations import *


############################
######## PARAMETERS ########
############################

runScriptAsTool = False ## This will overwrite any preset parameters by the ArcGIS tool inputs
                        ## Note that this is untested and may require some alteraetions.

saveIntermediates = True   # Change to false if you don't care about the intermediate files
trackWhichCountiesAreCompleted = True # Change to false if you don't want the script
                                      #  to keep track of the completed counties by
                                      #  editing a specified CSV.

regional_35_counties = [
    ## Note that these are only saved here for ease of use. The clusters that are
    ##  going to be run are found in the clusterList, so if you want to run the
    ##  clusters for all 35 counties from the Regional remote sensing project,
    ##  then set clusterList = regional_35_counties.
     r'R:\Nat_Hybrid_Poultry\Remote_Sensing\Feature_Analyst\Alabama\BatchGDB_AL_Z16_c1.gdb',
     r'R:\Nat_Hybrid_Poultry\Remote_Sensing\Feature_Analyst\Arkansas\BatchGDB_AR_Z15_c1.gdb',
     r'R:\Nat_Hybrid_Poultry\Remote_Sensing\Feature_Analyst\Georgia\BatchGDB_GA_Z16_c1.gdb',
     r'R:\Nat_Hybrid_Poultry\Remote_Sensing\Feature_Analyst\Georgia\BatchGDB_GA_Z17_c5.gdb',
     r'R:\Nat_Hybrid_Poultry\Remote_Sensing\Feature_Analyst\Louisiana\BatchGDB_LA_Z15_c1.gdb',
     r'R:\Nat_Hybrid_Poultry\Remote_Sensing\Feature_Analyst\Mississippi\BatchGDB_MS_Z16_c2.gdb',
     r'R:\Nat_Hybrid_Poultry\Remote_Sensing\Feature_Analyst\North_Carolina\BatchGDB_NC_Z17_c1.gdb',
     r'R:\Nat_Hybrid_Poultry\Remote_Sensing\Feature_Analyst\North_Carolina\BatchGDB_NC_Z18_c5.gdb',
     r'R:\Nat_Hybrid_Poultry\Remote_Sensing\Feature_Analyst\Tennessee\BatchGDB_TN_Z16_c1.gdb',
    ]

clusterList = regional_35_counties
    #[
     #r'R:\Nat_Hybrid_Poultry\Remote_Sensing\Feature_Analyst\Mississippi\BatchGDB_MS_Z16_c2.gdb',
     #r'R:\Nat_Hybrid_Poultry\Remote_Sensing\Feature_Analyst\North_Carolina\BatchGDB_NC_Z17_c1.gdb',
     #r'R:\Nat_Hybrid_Poultry\Remote_Sensing\Feature_Analyst\North_Carolina\BatchGDB_NC_Z18_c5.gdb',
     #r'R:\Nat_Hybrid_Poultry\Remote_Sensing\Feature_Analyst\Tennessee\BatchGDB_TN_Z16_c1.gdb',
    #] # A list of the file paths to all the relevant cluster GDBs. You can manually
      #  input entries if runScriptAsTool = False

## Location of probability surface raster
prob_surface_raster = r'N:\FLAPS from Chris Burdett\Data\poultry_prob_surface\poultryMskNrm\poultryMskNrm.tif'
prob_surface_threshold = 0.1   # Points with values < or = threshold will be deleted

## Location of the folder that contains the county outline shapefiles
county_outline_folder = r'N:\Remote Sensing Projects\2016 Cooperative Agreement Poultry Barns\Documents\Deliverables\Library\CountyOutlines'

## Location of the adjusted NASS values CSV
adjNASS_CSV = r'R:\Nat_Hybrid_Poultry\Documents\adjNASS_FINAL_CSV.csv'

progress_tracking_file = r'R:\Nat_Hybrid_Poultry\Documents\trackingFileCSV.csv'

## This folder should be the location where all the state folders are, which will each store the GDBs of the state clusters
output_folder = r'R:\Nat_Hybrid_Poultry\Remote_Sensing\Feature_Analyst'



## It is important to define if the masks that will be used.
## If you don't want any, set these parameters = [].
## The parameter neg_masks is where you would put feature classes which
##  exclude any farm premises for being there. An example would be water bodies.
## The parameter pos_masks is the opposite; farms cannot be placed outside of
##  these areas. An example would be public land boundaries.
## Both neg_masks (negative masks) and pos_masks (positive masks) should be
##  formatted like this, with '~' representing the buffer distance in Meters:
##          neg_mask =[
##                     [r'C:\file_path\file', ~],
##                     [r'C:\alt_file_path\file2', ~],
##                    ]
## Note that buffer distance can be 0. Set = [] if no masks.
neg_masks = [
             [r'N:\Geo_data\ESRI_Data\ESRI_Base_Data_2014\usa\census\urban.gdb\urban', 0],
             [r'N:\Geo_data\ESRI_Data\ESRI_Base_Data_2012\usa\census\urban.sdc\urban', 0],
             [r'N:\Geo_data\ESRI_Data\ESRI_Base_Data_2012\streetmap_na\data\streets.sdc\streets', 20],
             [r'N:\Geo_data\ESRI_Data\ESRI_Base_Data_2014\usa\hydro\dtl_wat.gdb\dtl_wat', 0],
             [r'N:\Geo_data\ESRI_Data\ESRI_Base_Data_2014\usa\hydro\dtl_riv.gdb\dtl_riv', 10],
            ]

pos_masks = [
        
            ]

## Define the maximum and minimum Length(L) or AspRatio(AR) values
##  (which came from the Batch file). Any points outisde of these bounds
##  are deleted automatically. L values are in meters.
L_max_threshold = 500   # Fill this with 99999 if you don't want to delete based on max Length
L_min_threshold = 50   # Fill this with 0 if you don't want to delete based on min Length
AR_max_threshold = 99999   # Fill this with 99999 if you don't want to delete based on max AspRatio
AR_min_threshold = 0  # Fill this with 0 if you don't want to delete based on min AspRatio

numIterations = 10 # Any number >1 will result in several iterations of simualtedSampling,
                  #  meaining several projected AutoReview files will be created, each with a unique name.

## If steps have been completed before, there may be no need to repeat them because
##  there will simply output the exact same result. If that is the case for all
##  clusters this script will run, those steps to this list.append  They will be skipped. 
skipList = [    ## NOTE TO SELF: It would probably be easiest to simply add in a
                ##  'skip' argument of True or False to each major function. Then
                ##  when skip=True you simply have it return the output file path
                ##  before it actually does any geoprocessing.
            ## 1st column, put the state abbreviation in CAPS as a string.
            ## 2nd column, put county name as a string.
            ## 3rd column, put either 'Clip', 'Mask', 'LAR', 'ProbSurf',
            ##  'CollectEvents', 'SimSampling' or 'all'. The latter indicates
            ##  that no geoprocesses should be done for that file, since it is
            ##  already completed.
    
            ['AL', 'Barbour',  'all'],
            ['AL', 'Blount',   'all'],
            ['AL', 'Bullock',  'all'],
            ['AL', 'Coffee',   'all'],
            ['AL', 'Cullman',  'all'],
            ['AL', 'DeKalb',   'all'],
            ['AL', 'Geneva',   'all'],
            ['AL', 'Madison',  'all'],
            ['AL', 'Marshall', 'all'],
            ]

## Overwrite certain parameters set above, if this tool is run as a custom
##  ArcGIS Python tool. The values will be determined by the user.
if runScriptAsTool == True:
    clusterList = arcpy.GetParameterAsText(0)   # This should be in list format, but can contain a single entry
    prob_surface_threshold = arpy.GetParametersAsText(1) # Set default to 0.1
    negative_masks = arcpy.GetParameterAsText(2)       # Multivalue should be set to Yes and Type should be Optional
    negative_buffer_dist = arcpy.GetParameterAsText(3) # Multivalue should be set to Yes and Type should be Optional
    positive_masks = arcpy.GetParameterAsText(4)       # Multivalue should be set to Yes and Type should be Optional
    positive_buffer_dist = arcpy.GetParameterAsText(5) # Multivalue should be set to Yes and Type should be Optional
    L_max_threshold = arcpy.GetParameterAsText(6)   # Set default to 800
    L_min_threshold = arcpy.GetParameterAsText(7)   # Set default to 35
    AR_max_threshold = arcpy.GetParameterAsText(8)  # Set defualt to 10
    AR_min_threshold = arcpy.GetParameterAsText(9)  # Set default to 1.3
    saveIntermediates = arcpy.GetParameterAsText(10)# Set default to True
    numIterations = arcpy.GetParameterAsText(11)    # Set default to 1

    if not len(negative_masks) == len(negative_buffer_dist) and \
       not len(positive_masks) == len(positive_buffer_dist):
        raise Exception("Error: There must be an equal number of entries in the negative_masks & " \
                        + "negative_buffer_dist parameters. Likewise for positive_masks and positive_buffer_dist.")
    
    else:
        neg_masks, pos_masks = [], []
        for index in range(0, len(negative_masks)):
            neg_masks.append([negative_masks[index], negative_buffer_dist[index]])

        for index in range(0, len(positive_masks)):
            pos_masks.append([positive_masks[index], positive_buffer_dist[index]])

        
LAR_thresholds = [
              [L_max_threshold, L_min_threshold],   ## This section just makes it so that we don't need
              [AR_max_threshold, AR_min_threshold], ##  so many input parameters for the LAR function
             ]

    
############################
#### DEFINE DICTIONARIES ###
############################

## NAMING CONVENTIONS:
## Names for all files created in this script will follow the the same format.
##
##      [prefix]_[ST]_Z[##]_c[#]_[CountyName].[ext]
##
## Some files will not have Z[##], c[#], or [CountyName].
##
##      [prefix] -> a unique identifier for each type of file, below is a dictionary explaining each prefix
##      [ST] -> the 2-letter state abbreviation
##      Z[##] -> the UTM zone number
##      c[#] -> the cluster number
##      [CountyName] -> the specific county name
##      [ext] -> the file extension
##

prefix_dict = {
    'NAIP': 'Downloaded 1m resolution NAIP areal imagery',
    'NAIP2m': '2m resampled NAIP imagery',
    'Model': 'AFE file that is used to create the Batch files for a particular state',
    'ModelGDB': 'The file geodatabase that was used to create the Model for that state',
    'ModelMXD': 'The ArcMap MXD that was used to run Feature Analyst to create the Model',
    'BatchGDB': 'A file geodatabase that contains all the intermediate files for the creation of the Batch file',
    'BatchMXD': 'The ArcMap MXD file that was used to run Feature Analyst to create the Batch file',
    'Clip': 'The Batch file clipped to the county',
    'Mask': 'The Clip file with points removed based on a series of masking layers',
    'LAR': 'The Mask file with points removed based on Length or AspRatio values outside of the thresholds',
    'ProbSurf': 'The LAR file with points removed according to a threshold value for the probablity surface',
    'Integrate': 'The ProbSurf file with points within 100m of each other are moved on top of one another at the centroid; no points are removed',
    'CollectEvents': 'Integrate file with points on top of one another combined to a single point',
    'SimSampling': 'The CollectEvents file with points sorted into bins and many points removed to ensure each bin has the appropriate number of points, according to the Adjusted NASS values',
    'AutoReview': 'The final stage, which is the CollectEvents file but projected into NAD 1983 with coordinate fields added',
    }

centralMeridian = {10:'-123.0' , 11:'-117.0' , 12:'-111.0' , 13:'-105.0', \
                   14:'-99.0'  , 15:'-93.0'  , 16:'-87.0'  , 17:'-81.0' , \
                   18:'-75.0'  , 19:'-69.0',}
    ##
    ## Note: this dictionary is used to store the central meridian value for each UTM zone that
    ## the contiguous USA is within (UTM 10-19). This wil be referenced in the following line.
    ## This library is in the format of [UTM Zone]:[central meridian]. Values were found
    ## at this site: http://www.jaworski.ca/utmzones.htm
    ##


############################
#### DEFINE FUNCTIONS ######
############################

    ##
    ## Note: when a function has several arguments, they should generally
    ##  go in the following order (if a parameter is not needed, skip it):
    ##      (main_input_file, other_inputs, output_location, state_abbrev, \
    ##       county_name, {optional_parameters})
    ##

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

def shouldThisStepBeSkipped(state_abbrev, county_name, step_name):
    ##
    ## This function returns either True or False, based on whether
    ##  the specified county is in skipList.
    ##
    county_name_unformat = nameFormat(county_name)
    for county in skipList:
        if state_abbrev == county[0]:
            if nameFormat(county_name) == nameFormat(county[1]):
                if county[2].lower() == 'all' \
                or step_name.lower() == county[2].lower():
                    return True
    ## If it isn't in the skipList, just return false
    return False


def findBatch(clusterGDB):
    ##
    ## This function finds all the point files in the target GDB
    ##  and returns them in the form of a list.
    ##
    walkList = []   ## This will hold all of the file paths to the files within the folder

    walk = arcpy.da.Walk(clusterGDB, type="Point")

    for dirpath, dirnames, filenames in walk:
        for filename in filenames:
            if filename[:6] == 'Batch_':
                county_name = filename[9:]
                path = os.path.join(dirpath, filename)
                walkList.append([county_name, path])

    ## Look at the first path in walkList and get the state_abbrev from that
    state_abbrev = os.path.basename(walkList[0][1]) [6:8]
    
    return state_abbrev, walkList


def findFIPS_UTM(county_file):
            ##
            ## This determines the appropriate UTM and FIPS code values for the county.
            ##
            with arcpy.da.SearchCursor(county_file, ['FIPS', 'UTM',]) as cursor:
                for row in cursor:
                    return cursor[0], cursor[1]
        

def addFipsInfo(input_feature, state_abbrev, county_name):
        ##
        ## This adds the FIPS value (from the findFIPS_UTM function) to a given shapefile
        ##

        ## The following several lines are to check to see if the FIPS or FIPS2 fields exist
        fieldList = [field.name for field in arcpy.ListFields(input_feature)] # Creates a list of all fields in that feature class

        ## Checks if the fieldName is in the list that was just generated as fieldList
        if "FIPS" in fieldList or "FIPS2" in fieldList:
            print "File already has FIPS fields."
            
        else:
            state_name = nameFormat(state_abbrev_to_name[state_abbrev])
            
            ## Location of county folder:
            county_outline = os.path.join(county_outline_folder,
                                              state_name + '.gdb',
                                              county_name + 'Co' + state_abbrev + '_outline')


            FIPS, UTM = findFIPS_UTM(county_outline)
            
            ## Add a new field to store FIPS information. This field will hold the FIPS but remove leading zeroes
            arcpy.AddField_management(in_table = input_feature, field_name = "FIPS", 
                                      field_type = "LONG", field_precision = "", 
                                      field_scale = "", field_length = "", field_alias = "", 
                                      field_is_nullable = "NULLABLE", 
                                      field_is_required = "NON_REQUIRED", field_domain = "")

            ## Fill FIPS field with UTM info (DOES NOT FUNCTION PROPERLY)
            #arcpy.CalculateField_management(in_table = input_feature, field = "FIPS", \
            #                                expression = FIPS, \
            #                                expression_type = "PYTHON_9.3", )
            #                                #code_block = 'def fn(num):\n  if num <= %s:\n    return (1)\n  elif num > %s:\n    return (2)' %(collectEvents, collectEvents))

            ## Fill newly created UTM field with the proper UTM
            with arcpy.da.UpdateCursor(input_feature, ['FIPS']) as cursor_a:
                for row in cursor_a:
                    row[0] = int(FIPS)
                    cursor_a.updateRow(row)

            ## Add a second field to store FIPS information. This field will hold the
            ##  FIPS as a string and will NOT remove leading zeroes
            arcpy.AddField_management(in_table = input_feature, field_name = "FIPS2", 
                                      field_type = "TEXT", field_precision = "", 
                                      field_scale = "", field_length = "", field_alias = "", 
                                      field_is_nullable = "NULLABLE", 
                                      field_is_required = "NON_REQUIRED", field_domain = "")

            ## Fill FIPS field with UTM info
            #arcpy.CalculateField_management(in_table = input_feature, field = "FIPS2", \
             #                               expression = FIPS, \
              #                              expression_type = "PYTHON_9.3", )
               #                             #code_block = 'def fn(num):\n  if num <= %s:\n    return (1)\n  elif num > %s:\n    return (2)' %(collectEvents, collectEvents))

            ## Fill newly created UTM field with the proper UTM
            with arcpy.da.UpdateCursor(input_feature, ['FIPS2']) as cursor_b:
                for row in cursor_b:
                    row[0] = str(FIPS)
                    cursor_b.updateRow(row)



def clip(input_feature, clip_files, output_location, state_abbrev,
         county_name):
    ##
    ## This function clips the input features and names everything properly,
    ##  as well as adding FIPS information.
    ##


    ## Get rid of any weird characters in the county name
    county_name = nameFormat(county_name)
    
    ## Set up the name and lcation of the output 
    outputName = 'Clip_' + state_abbrev + '_' + county_name
    outputFilePath = os.path.join(output_location, outputName)

    if arcpy.Exists(outputFilePath) == True:
        print "IT EXISTS!"
        if shouldThisStepBeSkipped(state_abbrev, county_name, 'Clip') == True:
            print "Clip skipped."
            return outputFilePath
        else:
            arcpy.Delete_management(outputFilePath)

    ## Do the clip
    arcpy.Clip_analysis(in_features = input_feature, 
                        clip_features = clip_files, 
                        out_feature_class = outputFilePath, 
                        cluster_tolerance = "")

    addFipsInfo(outputFilePath, state_abbrev, county_name)
                                    
    ## Add the old file to the list of intermediate files
    try:
        intermed_list.append(input_feature)
    finally:
        return outputFilePath

    
def LAR(input_feature, output_location, LAR_thresholds, state_abbrev,
        county_name):
    ##
    ## LAR stands for Length(L) and Aspect Ratio(AR). This function
    ##  deletes points that do not conform with L or AR thresholds.
    ##

    L_max_threshold =  LAR_thresholds [0][0]
    L_min_threshold =  LAR_thresholds [0][1]
    AR_max_threshold = LAR_thresholds [1][0]
    AR_min_threshold = LAR_thresholds [1][1]

    ## Get rid of any weird characters in the county name
    county_name = nameFormat(county_name)

    outputName = 'LAR' + '_' + state_abbrev + '_' + county_name
    outputFilePath = os.path.join(output_location, outputName)

    if arcpy.Exists(outputFilePath) == True:
        if shouldThisStepBeSkipped(state_abbrev, county_name, 'LAR') == True:
            print "LAR skipped."
            return outputFilePath
        else:
            arcpy.Delete_management(outputFilePath)

    arcpy.CopyFeatures_management (input_feature, outputFilePath)

    ## Add the AspRatio field
    arcpy.AddField_management(in_table = outputFilePath, 
                              field_name = "AspRatio", field_type = "FLOAT", 
                              field_precision = "", field_scale = "", field_length = "", 
                              field_alias = "", field_is_nullable = "NULLABLE", 
                              field_is_required = "NON_REQUIRED", field_domain = "")

    ## Fill the AspRatio field that was just created
    arcpy.CalculateField_management(in_table = outputFilePath, 
                                    field = "AspRatio", 
                                    expression = "!Length!/!Width!", 
                                    expression_type = "PYTHON_9.3", code_block = "")

    ## Delete features based on the Length and AspRatio fields
    with arcpy.da.UpdateCursor(outputFilePath, ["Length", "AspRatio",]) as deleteCursor:
        for row in deleteCursor:
            if row[0] > L_max_threshold or row[0] < L_min_threshold:
                deleteCursor.deleteRow()
            elif row[1] > AR_max_threshold or row[1] < AR_min_threshold:
                deleteCursor.deleteRow()

    ## Add the old file to the list of intermediate files
    try:
        intermed_list.append(input_feature)
    finally:
        return outputFilePath

    
def masking(input_feature, output_location, state_abbrev, county_name,
            county_outline, neg_masks=[], pos_masks=[]):
    ##
    ## This function uses the Erase tool to remove any points with a set distance
    ##  of the files in the neg_masks list. It also uses the Clip tool to
    ##  remove any points that are NOT within a set distance of files in the
    ##  pos_masks list.
    ##
    ## Both neg_masks (negative masks) and pos_masks (positive masks) should
    ##  look similar to this, with # representing the buffer distance in Meters:
    ##      [[r'C:\file_path\file', #],
    ##       [r'C:\alt_file_path\file2', #]]
    ##

    ## If both neg_masks and pos_masks are default (empty), then simply pass the input_feature out of the function
    if neg_masks == [] and pos_masks == []:
        return input_feature
    
    county_name = nameFormat(county_name)
    outputName = 'Masking' + '_' + state_abbrev + '_' + county_name
    outputFilePath = os.path.join(output_location, outputName)

    if arcpy.Exists(outputFilePath) == True:
        if shouldThisStepBeSkipped(state_abbrev, county_name, 'Masking') == True:
            print "Masking skipped."
            return outputFilePath
        else:
            arcpy.Delete_management(outputFilePath)

    def clip_buffer(mask, temp_location, county_outline):
        ##
        ## This function is a small thing to clip the mask file to the county
        ##  to chop it into a manageable size. The file is buffered if required.
        ##  This function is used for each mask. This mini-function is not for
        ##  clipping or erasing the point file input data.
        ##
        clip_temp = os.path.join(temp_location,'clipped_mask_temp') ## Where the temporary clipped file will be stored

        if arcpy.Exists(clip_temp):
            arcpy.Delete_management(clip_temp)

        ## Create a temporary clipped file of the mask
        arcpy.Clip_analysis(in_features = mask[0], 
                        clip_features = county_outline, 
                        out_feature_class = clip_temp, 
                        cluster_tolerance = "")
        
        buff_temp = os.path.join(temp_location, 'buffer_mask_temp') ## Where the temporary buffer file will be stored

        if mask[1] > 0:
            ## If there is a buffer value specified:
            ## Create a temporary buffer around the clipped file, but only if the buffer distance is >0
            arcpy.Buffer_analysis(in_features = clip_temp, 
                            out_feature_class = buff_temp, 
                            buffer_distance_or_field = '%s Meters' %mask[1], 
                        )
            arcpy.Delete_management(clip_temp)
            
        else:
            ## Otherwise just use the un-buffered file
            buff_temp = clip_temp

        return buff_temp

    ## This 'fileToRemovePointsFrom' variable is going to be changed throughout
    ##  this function. It starts as the input feature, then will changed to
    ##  be set as the current temporary file that is created during the process.
    ##  This ensures that each time that points are removed, they are removed
    ##  from the most recent version of the file so that the end result will
    ##  be the cumulative result of all the masks at once. Note the original file
    ##  will not be modified, new temporary files will be made every step.
    fileToRemovePointsFrom = input_feature

    for maskType in ('neg', 'pos'): # Do this whole thing for both positive and negative masks
        count = 0 ## Start the count, this will be used to name temporary files
        currentFile = ''

        if maskType == 'neg':
            masksList = neg_masks
        elif maskType == 'pos':
            masksList = pos_masks
        
        if not masksList == []:
            for mask in masksList:
                count +=1
                tempMaskFile = clip_buffer(mask, 'in_memory', county_outline)

                if count == len(neg_masks) + len(pos_masks):
                    currentFile = outputFilePath
                    ## This is basically saying that if this is the final mask that needs
                    ##  to be applied, then don't make a temporary file, use the actual
                    ##  output file name.
                    
                else:
                    currentFile = os.path.join('in_memory', 'temp_applied_mask_' + str(count))

                if arcpy.Exists(currentFile):
                    arcpy.Delete_management(currentFile) ## Sometimes when errors happen previous versions are
                                                         ##  left over and need to be deleted before the next time 'round.
                
                if maskType == 'neg' and not neg_masks == []:
                    arcpy.Erase_analysis(in_features = fileToRemovePointsFrom, \
                                         erase_features = tempMaskFile, \
                                         out_feature_class = currentFile)
                    
                elif maskType == 'pos' and not pos_masks == []:
                    arcpy.Clip_analysis(in_features = fileToRemovePointsFrom, 
                                        clip_features = tempMaskFile, 
                                        out_feature_class = currentFile)

                arcpy.Delete_management(tempMaskFile) ## Get rid of the masking file, we don't need it

                if arcpy.Exists(currentFile[:-1] + str(count - 1)):
                    arcpy.Delete_management(currentFile[:-1] + str(count - 1))
                    ## Does the previous version of 'currentFile' still exist?
                    ## If so, delete that piece of junk, it's outdated.
                                   
                fileToRemovePointsFrom = currentFile
                    ## Set the loop to preform all further changes to the
                    ##  temporary file that was used prevously, so that all
                    ##  the changes are present in a single file.

    ## Add the old file to the list of intermediate files
    try:
        intermed_list.append(input_feature)
    finally:
        return outputFilePath

def addRasterInfo(point_data_to_alter, raster_dataset, field_name_1='ProbSurf_1',
                  field_name_2='ProbSurf_2'):
    ##
    ## This function extracts the values from the input raster
    ##  raster and creates two new fields in the input feature class,
    ##  called ProbSurf_1 and ProbSurf_2 respectively. ProbSurf_1 has
    ##  no interpolation, ProbSurf_2 has bilinear interpolation.
    ## Note: THIS FUNCTION CHANGES THE INPUT FEATURE CLASS BY ADDING FIELDS.
    ##
    arcpy.CheckOutExtension("Spatial")  ## This just allows the script to access the Spatial Analyst ArcGIS extension
    
    arcpy.sa.ExtractMultiValuesToPoints (point_data_to_alter, [[raster_dataset, field_name_1]], "NONE")
    arcpy.sa.ExtractMultiValuesToPoints (point_data_to_alter, [[raster_dataset, field_name_2]], "BILINEAR")
    
    arcpy.CheckInExtension("Spatial") 

def probSurface(input_point_data, raster_dataset, output_location,
                state_abbrev, county_name):
    ##
    ## This function exists to replace the Manual Review step of the regional
    ##  remote sensing procedure. It uses the FLAPS probability surface to
    ##  determine which points are True Positives (TP) or False Positives (FP).
    ##

    county_name = nameFormat(county_name)

    outputName = 'ProbSurf_' + state_abbrev + '_' + county_name
    outputFilePath = os.path.join(output_location, outputName)

    if arcpy.Exists(outputFilePath) == True:
        if shouldThisStepBeSkipped(state_abbrev, county_name, 'ProbSurf') == True:
            print "ProbSurf skipped."
            return outputFilePath
        else:
            arcpy.Delete_management(outputFilePath)

    arcpy.CopyFeatures_management (input_point_data, outputFilePath)

    ## Call addRasterInfo over to do some stuff for us
    addRasterInfo(outputFilePath, raster_dataset)

    ## Apply threshold
    with arcpy.da.UpdateCursor(outputFilePath, "ProbSurf_1") as cursor:
        for row in cursor:
            if row[0] <= prob_surface_threshold:
                cursor.deleteRow()

    ## Add the old file to the list of intermediate files
    try:
        intermed_list.append(input_point_data)
    finally:
        return outputFilePath


def collapsePoints(input_point_data, output_location, state_abbrev,
                   county_name):
    ##
    ## This function creates a new file and uses the Integrate and CollectEvents
    ##  ArcGIS tools to collapse input points within 100m of each other to
    ##  single points. Note: The Integrate tool is really finiky about the
    ##  file paths having spaces in them. It will cause vague errors if there
    ##  are spaces or special characters in the filepaths. Don't do it.
    ##
    
    ## Get rid of any weird characters in the county name
    county_name = nameFormat(county_name)
    state_name = nameFormat(state_abbrev_to_name[state_abbrev])

    ## Set up names and FilePaths for the Ingetrate and CollectEvents files
    integrateOutputName = 'Integrate_' + state_abbrev + '_' + county_name
    integrateOutputFilePath = os.path.join(output_location, integrateOutputName)
    collectEventsOutputName = 'CollectEvents' + '_' + state_abbrev + '_' + county_name
    collectEventsOutputFilePath = os.path.join(output_location, collectEventsOutputName)

    ## Check to see if it should skip. Otherwise delete existing files.
    if arcpy.Exists(collectEventsOutputFilePath) == True:
        if shouldThisStepBeSkipped(state_abbrev, county_name,
                                   'CollectEvents') == True:
            print "Integrate and CollectEvents skipped."
            return collectEventsOutputFilePath
        else:
            arcpy.Delete_management(collectEventsOutputFilePath)
            if arcpy.Exists(integrateOutputFilePath) == True:
                arcpy.Delete_management(integrateOutputFilePath)
        
    arcpy.CopyFeatures_management (input_point_data, integrateOutputFilePath)

    ## The input file path to the Integrate tool NEEDS to have no spaces in it, otherwise it will cause errors
    arcpy.Integrate_management(in_features = integrateOutputFilePath, cluster_tolerance = "100 Meters")

    ## Collapse points that are on top of eachother to single points
    arcpy.CollectEvents_stats(Input_Incident_Features = integrateOutputFilePath, \
                              Output_Weighted_Point_Feature_Class = collectEventsOutputFilePath)

    addFipsInfo(collectEventsOutputFilePath, state_abbrev, county_name)

    ## Add the old file to the list of intermediate files
    try:
        intermed_list.append(input_point_data)
        intermed_list.append(integrateOutputFilePath)
    finally:
        return collectEventsOutputFilePath

def simulatedSampling(input_point_data, raster_dataset, output_location, state_abbrev,
                      county_name, ssBins='default', iteration=None, random_seed=None):
    ##
    ## This function randomly forces the data into a probability distribution
    ##  curve similar to the probabilty distribution found in the 'truth' data.
    ##  It constructs several 'bins' which are based on the probSurf_1 fields
    ##  of the input_point_data file, then deletes all but the specified number
    ##  points from that bin. Ensure that the 'raster_dataset' used here
    ##  is the same as was used for the probSurface function.
    ## Note that this function assumes that prob_surface_threshold = 0.1 as default.
    ## This function requires county_name to be UNFORMATTED, otherwise it will return
    ##  'None' for those counties.

    ## Get rid of any weird characters in the state and county name
    #county_name_unformatted = county_name
    county_name = nameFormat(county_name)
    #state_name_unformatted = state_abbrev_to_name[state_abbrev]
    state_name = nameFormat(state_abbrev_to_name[state_abbrev])

    ## This next part gets a little hairy. Basically it is just deleting
    ##  any previously run SimSampling outputs, for all iterations and for
    ##  runs that were done without iterations. It also deletes all
    ##  AutoReview iterations as well, while it's at it. It starts by
    ##  naming the output, then it might add on the iteration suffix if
    ##  the file is part of a series of iterations.
    outputName = 'SimSampling_' + state_abbrev + '_' + county_name
    outputFilePath = os.path.join(output_location, outputName)
    if arcpy.Exists(outputFilePath):
        if shouldThisBeSkipped(state_abbrev, county_name, 'SimSampling') == True:
            print "SimSampling skipped."
            return outputFilePath
        else:
            arcpy.Delete_management(outputFilePath) ## Delete any files without '_i#'
    if not iteration == None:
        ## If an iteration is specified, put that in the name. The 'i' stands for 'iteration'.
        outputName = 'SimSampling_' + state_abbrev + '_' + county_name + '_i' + str(iteration)
        outputFilePath = os.path.join(output_location, outputName)
        if shouldThisStepBeSkipped(state_abbrev, county_name,
                               'SimSampling') == True:
            print "SimSampling skipped."
            return outputFilePath
    ## Before doing the first iteration, delete all files with the '_i' suffix.
    if iteration <= 1 or iteration == None:
        walk = arcpy.da.Walk(output_location, type="Point")
        for dirpath, dirnames, filenames in walk:
            for filename in filenames:
                if 'AutoReview' in filename or 'SimSampling' in filename:
                    if '_i' in filename and state_abbrev in filename \
                    and county_name in filename:
                        arcpy.Delete_management(os.path.join(dirpath, filename))
                        print 'deleted:', os.path.join(dirpath, filename) ## REMOVE THIS LATER
                                

    ## Okay, now that we have either skipped this whole function or deleted outdated
    ##  iterations, now we can continue.
        
    ## Create a new file with all points. This function will delete most of the points later on.
    arcpy.CopyFeatures_management (input_point_data, outputFilePath)

    ## Since the collapsePoints function has eraised existing fields, we need to re-add
    ##  the ProbSurf_1 and ProbSurf_2 fields. 
    addRasterInfo(outputFilePath, raster_dataset, field_name_1='ProbSurf_1', field_name_2='ProbSurf_2')

    #                                     #
    ### SETUP TO READ FROM adjNASS FILE ###
    #                                     #
    def readAdjNASS(adjNASS_CSV):
        ##
        ## This funtion reads the adjNASS_CSV file and returns the adjusted NASS value.
        ##
        with open(adjNASS_CSV) as csvfile:
            reader = csv.reader(csvfile, delimiter=',')
            for row in reader:
                ## If the row matches the state and county (once they have been
                ##  formatted and capitalized properly), save the adjNASS field
                ##  value as the adjNASS variable, which is returned out of the
                ##  function.
                if nameFormat(row[1]).title() == state_name.title() \
                and nameFormat(row[2]).title() == county_name.title():
                    adjNASS = row[8] ## BE SURE TO DOUBLE CHECK THAT IT IS READING
                                     ##  THE RIGHT COLUMN! This could cause many errors.
                    
                    return adjNASS
                
                ## If there are no values in the 2nd or 3rd column, check the 12th column.
                elif row[1] == '' and row[2] == '':
                    tempIndex = row[11].find('\\') ## Note that \\ is used instead of \, this is because \ has special meaning
                                                   ##  in Python so you must use \\ to represent \. In this case, \ is the divider
                                                   ##  between the state name and county name in column 12 (index 11) in the CSV.
                    tempStateName = nameFormat(row[11][:tempIndex]).title()
                    tempCountyName = nameFormat(row[11][tempIndex+1:]).title()
                        ## These two temp names are basically the value in column 12 (index 11)
                        ##  sliced with the \ as the dividing line.
                    
                    if tempStateName == state_name.title() and tempCountyName == county_name.title():
                        adjNASS = row[16]
                        
                        del tempIndex, tempStateName, tempCountyName ## Reset the temp variables so you don't get them mixed up.

                        return adjNASS
                    
    adjNASS = readAdjNASS(adjNASS_CSV)
    print "----Total number of points to select:", adjNASS ## REMOVE THIS LATER

    #                #
    ### SETUP BINS ###
    #                #
    ## Note that ssBins stands for simulated sampling bins.
    if ssBins == 'default' and prob_surface_threshold == 0.1:
        ssBins = ( ## Column 1 is the numeric label for each bin.
                   ##  Columns 2 and 3 are the lower and upper values for
                   ##  that particular bin, respectively. Column 4 is the
                   ##  percentage of points that should be selected from
                   ##  that bin. Column 5 will be filled later with the
                   ##  number of points that should actually be drawn from that bin.
                  (1, 0.1, 0.2, 3.88 ),
                  (2, 0.2, 0.3, 7.69 ),
                  (3, 0.3, 0.4, 11.95),
                  (4, 0.4, 0.5, 19.64),
                  (5, 0.5, 0.6, 23.34),
                  (6, 0.6, 0.7, 20.09),
                  (7, 0.7, 0.8, 11.08),
                  (8, 0.8, 0.9, 2.23 ),
                  (9, 0.9, 1.0, 0.09 ),
                  )
    elif ssBins == 'default' and not prob_surface_threshold == 0.1:
        raise Exception("Error: please provide ssBins values that fit with a prob_surface_threshold of %s" %str(prob_surface_threshold) )

    ## Change ssBins to a numpy array.
    ssBins = np.array(ssBins)
    
    ## Add column 5 to array, then fill it with
    ##  the proper number of points to draw from that bin, calculated as
    ##  column 3 percentage times adjNASS total for that county.
    ssBins = np.insert(ssBins, 4, np.zeros(len(ssBins)), axis=1) ## create column 4 (index 3) and fill it with meaningless zeros
    for row in ssBins:
        ## Now actually fill column 5 with a rounded number of points to draw from that bin.
        row[4] = round( float(row[3])/100. * float(adjNASS), 0)
        print '----' + str(int(row[0])),'points:', str(row[4])

    if not round(sum(ssBins[:,3]),1) == 100.0:
        ## If the percentages don't total to really close to 100%, raise hell
        raise Exception("Error: please provide ssBins values that total to 100 percent")


    ## Add a new field to the input data to hold the bin information in
    arcpy.AddField_management(in_table = outputFilePath, field_name = "Bin", 
                          field_type = "SHORT", field_precision = "", 
                          field_scale = "", field_length = "", field_alias = "", 
                          field_is_nullable = "NULLABLE", 
                          field_is_required = "NON_REQUIRED", field_domain = "")
    
    with arcpy.da.UpdateCursor(outputFilePath, ['OBJECTID', 'ProbSurf_1', 'Bin',]) as cursor:
        for row in cursor:
            ProbSurf_1 = row[1]
            
            for binThresholds in ssBins:
                ## Classify the point based on which of the bin max and min categories that it fits within
                if ProbSurf_1 > binThresholds[1] and ProbSurf_1 <= binThresholds[2]:
                    ## Assign the Bin field based on what range the ProbSurf_1 field fits in.
                    row[2] = int(binThresholds[0])
                    cursor.updateRow(row)
                    break
                
    #                           #                      
    ### DRAW POINTS FROM BINS ###
    #                           #
    selectedPoints = [] ## This will be used to collect all the points that will be in the output.
                
    for specificBin in ssBins:
        ## Create a list that contains the pool of points for that bin that we will draw random points out of
        pointsPool = []

        with arcpy.da.SearchCursor(outputFilePath, ['OBJECTID', 'ProbSurf_1', 'Bin',]) as cursor2:
            for row2 in cursor2:
                ## Check to see if the point matches the current bin label,
                ##  if so, add it to pointsPool so it can be drawn out later.
                if row2[2] == specificBin[0]:
                    pointsPool.append(row2)
                    
        ## Randomly select (from the pointsPool list) a number of points equal to the value in the
        ##  5th column (index 4) of ssBins.
        try:
            if not random_seed == None:
                random.seed(random_seed)
            selectedPoints.append(random.sample(pointsPool, int(specificBin[4])) )
        ## If there are too few points in that pool, select them all instead of taking some random points.
        except ValueError:
            print "Welp, guess we gotta take all the points for category", int(specificBin[0]) ## REMOVE THIS LATER
            selectedPoints.append(pointsPool)

    ## Create a list of just the OBJECTID values, which will be used to delete points.
    selectedOIDs = []
    for bn in selectedPoints:
        for pointInfo in bn:
            OID = pointInfo[0]
            selectedOIDs.append(OID)
    
    with arcpy.da.UpdateCursor(outputFilePath, ['OBJECTID', 'ProbSurf_1', 'Bin',]) as cursor3:
        for row3 in cursor3:
            ## Check to see if the OBJECTID is in the OBJECTID section of the
            ##  selectedPoints list, otherwise it gets deleted.
            if row3[0] not in selectedOIDs:
                    cursor3.deleteRow()
                
    #             #
    ### CLEANUP ###
    #             #
    try:
        intermed_list.append(input_point_data)
    finally:
        return outputFilePath
    

def project(input_data, output_location, UTM_code, state_abbrev,
            county_name, iteration=None):
    ##
    ## This function projects the input from the UTM county projection into
    ##  WGS 1984 Geographic Coordinate System.
    ##

    ## Get rid of any weird characters in the county name
    county_name = nameFormat(county_name)

    if iteration == None:
        outputName = 'AutoReview_' + state_abbrev + '_' + county_name
    else:
        outputName = 'AutoReview_' + state_abbrev + '_' + county_name + '_i' + str(iteration) 
    outputFilePath = os.path.join(output_location, outputName)

    if arcpy.Exists(outputFilePath) == True:
        if shouldThisStepBeSkipped(state_abbrev, county_name, 'ProbSurf') == True:
            print "ProbSurf skipped."
            return outputFilePath
        else:
            arcpy.Delete_management(outputFilePath)
        
    meridian = centralMeridian[int(UTM_code)] ## centralMeridian is a dictionary found in Setting_up_counties_database.py
                                              ##  and specifies the central meridian for the projection
    
    ## Project file into WGS 1984 Geographic Coordinate System
    arcpy.Project_management(in_dataset = input_data, \
                             out_dataset = outputFilePath, \
                             out_coor_system = "GEOGCS['GCS_WGS_1984',DATUM['D_WGS_1984',SPHEROID['WGS_1984',6378137.0,298.257223563]],PRIMEM['Greenwich',0.0],UNIT['Degree',0.0174532925199433]]", \
                             transform_method = "WGS_1984_(ITRF00)_To_NAD_1983", \
                             in_coor_system = "PROJCS['NAD_1983_UTM_Zone_%sN',GEOGCS['GCS_North_American_1983',DATUM['D_North_American_1983',SPHEROID['GRS_1980',6378137.0,298.257222101]],PRIMEM['Greenwich',0.0],UNIT['Degree',0.0174532925199433]],PROJECTION['Transverse_Mercator'],PARAMETER['False_Easting',500000.0],PARAMETER['False_Northing',0.0],PARAMETER['Central_Meridian',%s],PARAMETER['Scale_Factor',0.9996],PARAMETER['Latitude_Of_Origin',0.0],UNIT['Meter',1.0]]" %(UTM, meridian), \
                             preserve_shape = "NO_PRESERVE_SHAPE", max_deviation="", \
                             vertical="NO_VERTICAL")
                        
    ## Add coordinates
    arcpy.AddXY_management(outputFilePath)

    ## Add the old file to the list of intermediate files
    try:
        intermed_list.append(input_data)
    finally:
        return outputFilePath


def markCountyAsCompleted(clusterGDB, progress_tracking_file, state_abbrev, county_name, iteration=None):
##
## This function edits a CSV and fills in which counties have been
##  completed so far.
##
    
    state_name = nameFormat(state_abbrev_to_name[state_abbrev])
    county_name = nameFormat(county_name)
    
    timeValue = str( int( round(time.time(), 0) ) )

    if iteration == None:
            iterationValue = None
    else:
            iterationValue = 'i' + str(iteration)
    
    #if not os.path.exists(filePath):
     #   code = 'wb'
    #else:
     #   code = 'ab'

    with open(progress_tracking_file, 'ab') as g:
        writer = csv.writer(g, dialect = 'excel') 
        writer.writerow([state_name, county_name], iterationValue)
        


def deleteIntermediates(intermed_list):
    ##
    ##e This function is designed to be used in the other functions
    ##  whenever they have any intermediate files. It will delete
    ##  all files that are in list format in the intermed_list
    ##  input. (intermed is short for intermediate)
    ##

    for intermed_file in intermed_list:
        try:
            arcpy.Delete_management(intermed_file)
        except:
            print "error deleting the following file:\n" + intermed_file


############################
######### DO STUFF #########
############################

if __name__ == '__main__':

    errors = []

    for clusterGDB in clusterList:
        
        state_abbrev, batchList = findBatch(clusterGDB)
        state_name = nameFormat(state_abbrev_to_name[state_abbrev])

        for countyBatch in batchList:

            ## Reset the file parameters, so that if there are errors they are not used again
            try:
                del clipFile, larFile, maskFile, collapsePointsFile, simSamplingFile, autoReviewFile
            except: ()
            
            intermed_list = []  # this will be filled later with the FilePaths to all the intermediate
                                #  files, which may or may not be deleted depending on whether
                                #  saveIntermediates is True or False

            county_name = countyBatch[0]
            batch_location = countyBatch[1]
            
            county_outline = os.path.join(county_outline_folder,
                                          state_name + '.gdb',
                                          county_name + 'Co' + state_abbrev + '_outline')
            FIPS, UTM = findFIPS_UTM(county_outline)

            #          #
            # CLIPPING #
            #          #
            print "Clipping", state_name, county_name + "..."
            try:
                clipFile = clip(batch_location, county_outline, clusterGDB, state_abbrev, county_name)
                print "Clipped. Script duration so far:", checkTime()
            except:
                e = sys.exc_info()[1]
                print(e.args[0])
                errors.append(['Clip', state_abbrev, county_name, e.args[0] ])

                
            #          #
            #  MASKING #
            #          #
            print "Applying Masks for", state_name, county_name + "..."
            if not (neg_masks == [] and pos_masks == []):
                try:
                    maskFile = masking(clipFile, clusterGDB, state_abbrev, county_name, county_outline,
                                       neg_masks, pos_masks)
                    print "Mask applied. Script duration so far:", checkTime()
                except:
                    e = sys.exc_info()[1]
                    print(e.args[0])
                    errors.append(['Masking', state_abbrev, county_name, e.args[0] ])
            else:
                print "No masking files selected."
                maskFile = larFile  # This essentially just skips the masking step
                

            #          #
            #   LAR    #
            #          # 
            print "Applying Length/AspRatio thresholds for", state_name, county_name + "..."              
            try:
                larFile = LAR(maskFile, clusterGDB, LAR_thresholds, state_abbrev, county_name)
                print "LAR thresholds applied. Script duration so far:", checkTime()
            except:
                e = sys.exc_info()[1]
                print(e.args[0])
                errors.append(['LAR', state_abbrev, county_name, e.args[0] ])
                

            #           #
            #PROBSURFACE#
            #           # 
            print "Applying probability surface threshold for", state_name, county_name + "..."
            try:
                probSurfaceFile = probSurface(larFile, prob_surface_raster, clusterGDB, state_abbrev, county_name)
                print "Probability surface threshold applied. Script duration so far:", checkTime()
            except:
                e = sys.exc_info()[1]
                print(e.args[0])
                errors.append(['ProbSurf', state_abbrev, county_name, e.args[0] ])

            
            #               #
            #COLLAPSE POINTS#
            #               #
            ## Note: This creates two intermediate files, Integrate and CollectEvents
            print "Collapsing points for", state_name, county_name + "..."
            try:
                collapsePointsFile = collapsePoints(probSurfaceFile, clusterGDB, state_abbrev, county_name)
                print "Points collapsed. Script duration so far:", checkTime()
            except:
                e = sys.exc_info()[1]
                print(e.args[0])
                errors.append(['Integrate or CollectEvents', state_abbrev, county_name, e.args[0] ])
                
            ## Note: this sets up a loop, running for each iteration
            for eachIteration in range(1, numIterations+1):
                if numIterations <=1:
                    iterationNumber = None
                else:
                    iterationNumber = eachIteration

                #          #
                #SIMULATED #
                # SAMPLING #    
                #          #
                print "Preforming Simulated Sampling protocol for", state_name, county_name + "..."
                try:
                    simSamplingFile = simulatedSampling(collapsePointsFile, prob_surface_raster, clusterGDB,
                                                        state_abbrev, county_name, ssBins='default',
                                                        iteration=iterationNumber)
                    print "Simulated Sampling completed. Script duration so far:", checkTime()
                except:
                    e = sys.exc_info()[1]
                    print(e.args[0])
                    errors.append(['SimSampling', state_abbrev, county_name, e.args[0] ])
                    simSamplingFile = ''
                    
                               
                #          #
                #PROJECTING#
                #          #                               
                print "Projecting Automated Review for", state_name, county_name + "..."
                try:
                    autoReviewFile = project(simSamplingFile, clusterGDB,  UTM, state_abbrev, county_name,
                                             iteration=iterationNumber)
                    if trackWhichCountiesAreCompleted == True:
                        markCountyAsCompleted(clusterGDB, progress_tracking_file, state_abbrev,
                                              county_name, iteration=iterationNumber)
                    print "Projected. Script duration so far:", checkTime()
                except:
                    e = sys.exc_info()[1]
                    print(e.args[0])
                    errors.append(['AutoReview', state_abbrev, county_name, e.args[0] ])

            ## Just before you go on to the next county, now is the time to delete unwanted intermediate files.        
            if saveIntermediates == False:
                deleteIntermediates(intermed_list)
                

            print '' # This just puts a blank line between each county

            
    ############################
    ######### CLEANUP ##########
    ############################
            
    ## Once all clusters are done, print a readout:
    if errors == []:
        print "\n\nNo counties had any errors!"
    else:
        print "\n\nThe following counties had errors:"
        for row in errors:
            print row[0], row[1], row[2]
    
    print "---------------------\nSCRIPT COMPLETE!"
    print "The script took a total of", checkTime() + "."
    print "---------------------"

