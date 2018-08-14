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


############################
########## SETUP ###########
############################

import os, sys
import numpy as np

import time
start_time = time.time()

import arcpy
arcpy.env.OverwriteOutput = True

from Creating_TP_FN_FP_files import addRasterInfo, checkTime
from Setting_up_counties_database import centralMeridian

# this next import gives us access to two dictionaries for converting state names to abbreviations and vice versa
sys.path.insert(0, r'O:\AI Modeling Coop Agreement 2017\David_working\Python') # it also gives us the nameFormat function which is very useful for name standardization
from Converting_state_names_and_abreviations import *


############################
######## PARAMETERS ########
############################

runScriptAsTool = False ## This will overwrite any preset parameters by the ArcGIS tool inputs
                        ## Note that this is untested and may require some alteraetions.

saveIntermediates = True   # Change to false if you don't care about the intermediate files

clusterList = [
    r'R:\Nat_Hybrid_Poultry\Remote_Sensing\Feature_Analyst\Alabama\BatchGDB_AL_Z16_c1_mask_test.gdb'
    ] # A list of the file paths to all the relevant cluster GDBs. You can manually
      #  input entries if runScriptAsTool = False

## Location of probability surface raster
probSurfaceRaster = r'N:\FLAPS from Chris Burdett\Data\poultry_prob_surface\poultryMskNrm\poultryMskNrm.tif'

county_outline_folder = r'N:\Remote Sensing Projects\2016 Cooperative Agreement Poultry Barns\Documents\Deliverables\Library\CountyOutlines'

output_folder = r'R:\Nat_Hybrid_Poultry\Remote_Sensing\Feature_Analyst'

prob_surface_threshold = 0.15   # Points with values < 0.15 will be deleted

## Define if any masks will be used. If none, set these parameters = [].
## The parameter neg_masks is where you would put feature classes which
##  exclude any farm premises for being there. An example would be water bodies.
## The parameter pos_masks is the opposite; farms cannot be placed outside of
##  these areas. An example would be public land boundaries.
## Both neg_masks (negative masks) and pos_masks (positive masks) should be
##  formatted like this, with '#' representing the buffer distance in Meters:
##          neg_mask =[[r'C:\file_path\file', #],
##                     [r'C:\alt_file_path\file2', #]]
## Note that buffer distance can be 0. Set = [] if no masks.
neg_masks = [
             [r'N:\Geo_data\ESRI_Data\ESRI_Base_Data_2014\usa\census\urban.gdb\urban', 0],
             [r'N:\Geo_data\ESRI_Data\ESRI_Base_Data_2012\streetmap_na\data\streets.sdc\streets', 20]
            ]
pos_masks = [
        
            ]

## Define the maximum and minimum Length(L) or AspRatio(AR) values
##  (which came from the Batch file). Any points outisde of these bounds
##  are deleted automatically. L values are in meters.
L_max_threshold = 99999   # Fill this with 99999 if you don't want to delete based on max Length
L_min_threshold = 0    # Fill this with 0 if you don't want to delete based on min Length
AR_max_threshold = 99999   # Fill this with 99999 if you don't want to delete based on max AspRatio
AR_min_threshold = 0  # Fill this with 0 if you don't want to delete based on min AspRatio

## Overwrite certain parameters set above, if this tool is run as a custom
##  ArcGIS Python tool. The values will be determined by the user.
if runScriptAsTool == True:
    clusterList = arcpy.GetParameterAsText(0)   # This should be in list format, but can contain a single entry
    prob_surface_threshold = arpy.GetParametersAsText(1) # Set default to 0.15
    negative_masks = arcpy.GetParameterAsText(2)       # Multivalue should be set to Yes and Type should be Optional
    negative_buffer_dist = arcpy.GetParameterAsText(3) # Multivalue should be set to Yes and Type should be Optional
    positive_masks = arcpy.GetParameterAsText(4)       # Multivalue should be set to Yes and Type should be Optional
    positive_buffer_dist = arcpy.GetParameterAsText(5) # Multivalue should be set to Yes and Type should be Optional
    L_max_threshold = arcpy.GetParameterAsText(6)  # Set default to 800
    L_min_threshold = arcpy.GetParameterAsText(7)  # Set default to 35
    AR_max_threshold = arcpy.GetParameterAsText(8) # Set defualt to 10
    AR_min_threshold = arcpy.GetParameterAsText(9) # Set default to 1.3
    saveIntermediates = arcpy.GetparameterAsText(10)# Set default to True

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

        
thresholds = [
              [L_max_threshold, L_min_threshold],   ## This section just makes it so that we don't need
              [AR_max_threshold, AR_min_threshold], ##  so many input parameters for the LAR function
             ]

    
############################
#### NAMING CONVENTIONS ####
############################

## Names for all files created in this script will follow the the same format.
##
##      [prefix]_[ST]_Z[##]_c[#]_[CountyName].[ext]
##
## Some files will not have Z[##], c[#], or [CountyName].
##
##      [prefix] -> a unique identifier for each type of file, below is a dictionary explaining each prefix
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
    'LAR': 'The Clip file but with points with Length or AspRatio values outside of the thresholds removed',
    'Mask': 'The LAR file but with points removed based on masking layers',
    'ProbSurf': 'The Mask file but with values from the probability surface used to remove FPs',
    'Integrate': 'The ProbSurf file but points within 100m of each other are moved on top of one another at the centroid',
    'CollectEvents': 'Integrate file but with points on top of one another combined to a single point',
    'AutoReview': 'The final stage, which is the CollectEvents file but projected into NAD 1983',
    }


############################
#### DEFINE FUNCTIONS ######
############################

    ##
    ## Note: when a function has several arguments, they should generally
    ##  go in the following order (if a parameter is not needed, skip it):
    ##      (input_file, critical_inputs, output_location, state_abbrev, \
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


def findBatch(clusterGDB):
    ##
    ## This function finds all the point files in the target GDB
    ##  and returns them in the form of a list.
    ##
    walkList = []   ## This will hold all of the file paths to the files wuithin the folder

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


def FIPS_UTM(county_file):
    ##
    ## This determines the appropriate UTM and FIPS code values for the county.
    ##
    with arcpy.da.SearchCursor(county_file, ['FIPS', 'UTM',]) as cursor:
        for row in cursor:
            return cursor[0], cursor[1]


def add_FIPS_info(input_feature, state_abbrev, county_name):
    ##
    ## This adds the FIPS value (from the FIPS_UTM function) to a given shapefile
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

        FIPS, UTM = FIPS_UTM(county_outline)
        
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


def clip(input_feature, clip_files, output_location, state_abbrev, county_name):
    ##
    ## This function clips the input features and names everything properly,
    ##  as well as adding FIPS information.
    ##
    
    ## Get rid of any weird characters in the county name
    county_name = nameFormat(county_name)
    
    ## Set up the name and lcation of the output 
    outputName = 'Clip_' + state_abbrev + '_' + county_name
    outputFilePath = os.path.join(output_location, outputName)

    ## Do the clip
    arcpy.Clip_analysis(in_features = input_feature, 
                        clip_features = clip_files, 
                        out_feature_class = outputFilePath, 
                        cluster_tolerance = "")

    add_FIPS_info(outputFilePath, state_abbrev, county_name)
                                    
    ## Add the old file to the list of intermediate files
    if __name__ == '__main__':
        intermed_list.append(input_feature)

    return outputFilePath

    
def LAR(input_feature, thresholds, output_location, state_abbrev, county_name):
    ##
    ## LAR stands for Length(L) and Aspect Ratio(AR). This function
    ##  deletes points that do not conform with L or AR thresholds.
    ##

    L_max_threshold =  thresholds [0][0]
    L_min_threshold =  thresholds [0][1]
    AR_max_threshold = thresholds [1][0]
    AR_min_threshold = thresholds [1][1]

    outputName = 'LAR' + '_' + state_abbrev + '_' + county_name
    outputFilePath = os.path.join(output_location, outputName)

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
    if __name__ == '__main__':
        intermed_list.append(input_feature)
        
    return outputFilePath

    
def masking(input_feature, output_location, state_abbrev, county_name, county_outline, neg_masks=[], pos_masks=[] ):
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

    ## Both neg_masks and pos_masks are default (empty), then simply pass the input_feature out of the function
    if neg_masks == [] and pos_masks == []:
        return input_feature
    
    county_name = nameFormat(county_name)
    outputName = 'Masking' + '_' + state_abbrev + '_' + county_name
    outputFilePath = os.path.join(output_location, outputName)
    neg_masks = neg_masks
    pos_masks = pos_masks

    if arcpy.Exists(outputFilePath):
        arcpy.Delete_management(outputFilePath)

    def clip_buffer(mask):
        ##
        ## This function is a small thing to clip the mask file to the county
        ##  to chop it into a manageable size. The file is buffered if required.
        ##  This function is used for each mask. This mini-function is not for
        ##  clipping or erasing the point file input data.
        ##
        clip_temp = os.path.join(output_location,'clipped_mask_temp') # Where the temporary clipped file will be stored

        ## Create a temporary clipped file of the mask
        arcpy.Clip_analysis(in_features = mask[0], 
                        clip_features = county_outline, 
                        out_feature_class = clip_temp, 
                        cluster_tolerance = "")
        
        buff_temp = os.path.join(output_location, 'buffer_mask_temp') # Where the temporary buffer file will be stored

        if mask[1] > 0: # If there is a buffer value specified:
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
    ##  be the cumulative result of all the masks at once.
    fileToRemovePointsFrom = input_feature

    for maskType in ('neg', 'pos'): # Do this whole thing for both positive and negative masks
        count = 0 # Start the count, this will be used to name temporary files
        currentFile = ''

        if maskType == 'neg':
            masksList = neg_masks
            tempMaskFilePath = 'in_memory/neg_mask'
        elif maskType == 'pos':
            masksList = pos_masks
            tempMaskFilePath = 'in_memory/pos_mask'

        if not masksList == []:
            for mask in masksList:
                count +=1
                tempMaskFile = clip_buffer(mask)

                if ( pos_masks == [] and count == len(neg_masks) ) \
                   or count == len(pos_masks):
                    currentFile = outputFilePath
                    ## This is basically saying that if this is the final mask that needs
                    ##  to be applied, then don't make a temporary file, use the actual
                    ##  output file name.
                    
                else:
                    currentFile = tempMaskFilePath + str(count)

                if maskType == 'neg' and not neg_masks == []:
                    arcpy.Erase_analysis(in_features = fileToRemovePointsFrom, \
                                         erase_features = tempMaskFile, \
                                         out_feature_class = currentFile)
                    
                elif maskType == 'pos' and not pos_masks == []:
                    arcpy.Clip_analysis(in_features = fileToRemovePointsFrom, 
                                        clip_features = tempMaskFile, 
                                        out_feature_class = currentFile)

                arcpy.Delete_management(tempMaskFile) # Get rid of the masking file, we don't need it

                if arcpy.Exists(currentFile[:-1] + str(count - 1)):
                    arcpy.Delete_management(currentFile[:-1] + str(count - 1))
                    ## Does the previous version of 'currentFile' still exist?
                    ## If so, delete that piece of junk, it's outdated.
                                   
                fileToRemovePointsFrom = currentFile
                    ## Set the loop to preform all further changes to the
                    ##  temporary file that was used prevously, so that all
                    ##  the changes are present in a single file.

    ## Add the old file to the list of intermediate files
    if __name__ == '__main__':
        intermed_list.append(input_feature)
        
    return outputFilePath

def probSurface(input_point_data, raster_dataset, output_location, state_abbrev, county_name):
    ##
    ## This function exists to replace the Manual Review step of the regional
    ##  remote sensing procedure. It uses the FLAPS probability surface to
    ##  determine which points are True Positives (TP) or False Positives (FP).
    ##

    county_name = nameFormat(county_name)

    outputName = 'ProbSurf_' + state_abbrev + '_' + county_name
    outputFilePath = os.path.join(output_location, outputName)

    arcpy.CopyFeatures_management (input_point_data, outputFilePath)

    ## This next funciton comes from the creating_TF_FN_FP_files.py script
    addRasterInfo(outputFilePath, raster_dataset)

    ## Apply threshold - NOTE THIS WILL LIKELY BE CHANGED LATER
    with arcpy.da.UpdateCursor(outputFilePath, "ProbSurf_1") as cursor:
        for row in cursor:
            if row[0] < prob_surface_threshold:
                cursor.deleteRow()

    ## Add the old file to the list of intermediate files
    intermed_list.append(input_point_data)

    return outputFilePath

        
def collapsePoints(input_point_data, output_location, state_abbrev, county_name):
    ##
    ## This function creates a new file and uses the Integrate and CollectEvents
    ##  ArcGIS tools to collapse input points within 100m of each other to
    ##  single points. Note: The Integrate tool is really finiky about the
    ##  file paths having spaces in them. It will cause vague errors if there
    ##  are spaces or special characters in the filepaths. Don't do it.
    ##

    county_name = nameFormat(county_name)
    state_name = nameFormat(state_abbrev_to_name[state_abbrev])

    ## Set up names and FilePaths for the Ingetrate and CollectEvents files
    integrateOutputName = 'Integrate_' + state_abbrev + '_' + county_name

    integrateOutputFilePath = os.path.join(output_location, integrateOutputName)
    collectEventsOutputName = 'CollectEvents' + '_' + state_abbrev + '_' + county_name
    collectEventsOutputFilePath = os.path.join(output_location, collectEventsOutputName)

    if arcpy.Exists(integrateOutputFilePath):
        arcpy.Delete_management(integrateOutputFilePath)
        
    arcpy.CopyFeatures_management (input_point_data, integrateOutputFilePath)

    ## The input file path to the Integrate tool NEEDS to have no spaces in it, otherwise it will cause errors
    arcpy.Integrate_management(in_features = integrateOutputFilePath, cluster_tolerance = "100 Meters")

    ## Collapse points that are on top of eachother to single points
    arcpy.CollectEvents_stats(Input_Incident_Features = integrateOutputFilePath, \
                              Output_Weighted_Point_Feature_Class = collectEventsOutputFilePath)

    add_FIPS_info(collectEventsOutputFilePath, state_abbrev, county_name)

    ## Add the old file to the list of intermediate files
    intermed_list.append(input_point_data)
    intermed_list.append(integrateOutputFilePath)

    return collectEventsOutputFilePath


def project(input_data, UTM_code, output_location, state_abbrev, county_name):
    ##
    ## This function projects the input from the UTM county projection into
    ##  WGS 1984 Geographic Coordinate System.
    ##

    county_name = nameFormat(county_name)

    outputName = 'AutoReview_' + state_abbrev + '_' + county_name
    outputFilePath = os.path.join(output_location, outputName)

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
    intermed_list.append(input_data)

    return outputFilePath


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
            clipFile = larFile = maskFile = collapsePointsFile = autoReviewFile = ''

            intermed_list = []  # this will be filled later with the FilePaths to all the intermediate
                                #  files, which may or may not be deleted depending on whether
                                #  saveIntermediates is True or False

            county_name = countyBatch[0]
            batch_location = countyBatch[1]
            
            county_outline = os.path.join(county_outline_folder,
                                          state_name + '.gdb',
                                          county_name + 'Co' + state_abbrev + '_outline')
            FIPS, UTM = FIPS_UTM(county_outline)

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
            #   LAR    #
            #          # 
            print "Applying Length/AspRatio thresholds for", state_name, county_name + "..."              
            try:
                larFile = LAR(clipFile, thresholds, clusterGDB, state_abbrev, county_name)
                print "LAR thresholds applied. Script duration so far:", checkTime()
            except:
                e = sys.exc_info()[1]
                print(e.args[0])
                errors.append(['LAR', state_abbrev, county_name, e.args[0] ])
                
            #          #
            #  MASKING #
            #          #
            print "Applying Masks for", state_name, county_name + "..."
            if not neg_masks == [] and not pos_masks == []:
                try:
                    maskFile = masking(larFile, clusterGDB, state_abbrev, county_name, county_outline, neg_masks, pos_masks)
                    print "Mask applied. Script duration so far:", checkTime()
                except:
                    e = sys.exc_info()[1]
                    print(e.args[0])
                    errors.append(['Masking', state_abbrev, county_name, e.args[0] ])
            else:
                print "No masking files selected."
                maskFile = larFile  # This essentially just skips the masking step

            #           #
            #PROBSURFACE#
            #           # 
            print "Applying probability surface for", state_name, county_name
            try:
                probSurfaceFile = probSurface(maskFile, probSurfaceRaster, clusterGDB, state_abbrev, county_name)
                print "Probability surface applied. Script duration so far:", checkTime()
            except:
                e = sys.exc_info()[1]
                print(e.args[0])
                errors.append(['ProbSurf', state_abbrev, county_name, e.args[0] ])

            #          #
            #   C2P    #
            #          # 
            print "Collapsing points for", state_name, county_name
            try:
                collapsePointsFile = collapsePoints(probSurfaceFile, clusterGDB, state_abbrev, county_name)
                print "Points collapsed. Script duration so far:", checkTime()
            except:
                e = sys.exc_info()[1]
                print(e.args[0])
                errors.append(['Integrate or CollectEvents', state_abbrev, county_name, e.args[0] ])

            #          #
            #PROJECTING#
            #          #                               
            print "Projecting Automated Review for", state_name, county_name
            try:
                autoReviewFile = project(collapsePointsFile, UTM, clusterGDB, state_abbrev, county_name)
                print "Projected. Script duration so far:", checkTime()
            except:
                e = sys.exc_info()[1]
                print(e.args[0])
                errors.append(['AutoReview', state_abbrev, county_name, e.args[0] ])
                
            if saveIntermediates == False:
                deleteIntermediates(intermed_list)

    if errors == []:
        print "\n\nNo counties had any errors!"
    else:
        print "\n\nThe following counties had errors:"
        for row in errors:
            print row[0], row[1], row[2]

    ############################
    ######### CLEANUP ##########
    ############################
    
    print "---------------------\nSCRIPT COMPLETE!"
    print "The script took a total of", checkTime() + "."
    print "---------------------"

