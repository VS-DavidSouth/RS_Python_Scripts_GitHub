#################### Creating_TP_FN_FP_files.py ##############################

############################
####### DESCRIPTION ########
############################

## Created by David South 5/30/18, updated 6/20/18
##
## Script description: This script will take the results from the county-level
##  Remote Sensing procedure and export a file with [county] being
##  the name of the county and [ST] being the 2 letter state abbreviation:
##       [ST]_[county]_TP_FN_FP.shp
##
##  TP = True Positives, meaning the poultry premises that the remote sensing
##       procedure correctly recognized
##  FN = False Negatives, meaning the poultry premises that were not picked
##       up by the remote sensing procedure and which needed to be added in
##       manually by a user
##  FP = False Positives, meaning the noise and clutter which the remote sensing
##       procedure incorrectly thought were poultry premises
##
## Beware that this script (mostly) assumes that state names with spaces like
##  North Carolina will be used as NorthCarolina. Other scripts and databases
##  will likely format it as North_Carolina. This can (and will) cause errors.

############################
########## SETUP ###########
############################

import time
start_time = time.time()

import csv, os, sys

import arcpy
arcpy.env.overwriteOutput = True

import numpy as np

# this next import gives us access to two dictionaries for converting state names to abbreviations and vice versa
sys.path.insert(0, r'O:\AI Modeling Coop Agreement 2017\David_working\Python') # it also gives us the nameFormat function which is very useful for name standardization
from Converting_state_names_and_abreviations import *

############################
######## PARAMETERS ########
############################

# location of CSV with summary satistics, such as Collect Events which is used to tell TP from FN
summaryStatsCSV = r'O:\AI Modeling Coop Agreement 2017\David_working\Remote_Sensing_Procedure\Stats_summary.csv'

# location of the CSV file containing file paths of _Final files
finalFileLocations = r'O:\AI Modeling Coop Agreement 2017\David_working\Remote_Sensing_Procedure\FileLocations.csv'

# location of probability surface raster
probSurface = r'N:\FLAPS from Chris Burdett\Data\poultry_prob_surface\poultryMskNrm\poultryMskNrm.tif'

# folder that will hold all the output files
outputFolder = r'O:\AI Modeling Coop Agreement 2017\David_working\Remote_Sensing_Procedure\TP_FN_FP.gdb'

############################
##### DEFINE FUNCTIONS #####
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

def collectSummaryStats():
    ##
    ## This function is similar to the collectCounties function except
    ##  instead it looks at the summary spreadsheet for all counties.
    ##
    global summaryStats
    summaryStats = []


    with open(summaryStatsCSV, 'rb') as CSVfile:
        reader = csv.reader(CSVfile)
        for row in reader:
            if not row[0] == 'State' and not row[0] == '' and not row[0] == 'MS2':     # skip the first row which just contains the column labels, also skip MS2 because it wasn't completed
                summaryStats.append(row)

    summaryStats = np.array (summaryStats)
    return summaryStats

def findCollectEventsCount(state_abbrev, county_name):
    ##
    ## This function seeks through the summaryStats numpy array and returns the
    ##  proper CollectEvents value which is used to determine the line between
    ##  TP and FN.
    ##
    for row in summaryStats:
        if (row[0][:2] == state_abbrev) and (row[1] == county_name):
            return row[7]

def findRowCount(state_abbrev, county_name):
    ##
    ## This function seeks through the summaryStats numpy array and returns the
    ##  proper Fa_ManRev value, meaning the number of rows in that _FINAL file.
    ##
    for row in summaryStats:
        if (row[0][:2] == state_abbrev) and (row[1] == county_name):
            return row[8]
    
def specificCountyFile(file_list, state_abbrev, county_name):
    ##
    ## This fuction searches through a list of filepaths and finds the one for the
    ##  appropriate state. This can be used for batchList, finalFiles, etc.
    ##
    ##          file_list:  the list of filepaths that this function will sort through
    ##          state_abbrev & county_name: state abbreviation and county name
    ##          final:      boolean (True or False) signifying whether or not
    ##                       the function is searching for '_FINAL' files
    ##
            
    #yepList = ['_FINAL_FINAL', '_Final_FINAL', '_FINAL2', '_FINAL', '_Final']
    state_name = state_abbrev_to_name[state_abbrev]
    state_name = state_name.replace(' ', '')

    ## Note the following several lines of code were from before the FileLocations
    ##  CSV was created. It is saved here for posterity, even though it isn't
    ##  relevant anymore. It may be able to be reused.

    #if final == True:
    #    row_count = summaryStats[8]
    #    for yep in yepList:    
    #        for file_path in file_list:
    #            if yep in file_path and state_name in file_path and county_name in file_path:
    #                return file_path
                        ## This loop goes through yepList and checks to see
                        ##  if each file_path has a version of _FINAL as
                        ##  well as the correct state name and county name.
                        ##  It chooses based on the order of yepList, and
                        ##  thus chooses _FINAL_FINAL prerentially to the rest.
                        ##  It returns the chosen file_path from the list.

    
            
    #if final == False:
    for file_path in file_list:    
        if state_name in file_path and county_name in file_path:  
            return file_path              
                    ## This loop only checks for the proper state and
                    ## county names before returning the first one.
        
def findBatchFiles():
    ##
    ## This function looks through the A:\ Drive to find all the files with the
    ##  suffix '_Batch' and organizes them (with their file location) in a list.
    ##
    global batchList
    
    folderLocation = r'A:'
    walk = arcpy.da.Walk(folderLocation, datatype = "FeatureClass", type = "Polygon")

    nopeList = ['Project Documents', 'Copy',]   # this is unused so far, if more entries are
                                                #  needed, this will be used to negatively select things

    yepList = ['GilesCo_Results', 'FranklinCo_Results', 'WayneCo_Results2', \
               'SampsonCo_Results2', 'DuplinCo_Results2', 'UnionCo_barns_tr4_Lrn_Rmv_RS', \
               'YellCo_barns_tr_Lrn_Rmv_RS3', 'LincolnCo_barns_tr2_Lrn_Rmv_RS_CVM', \
               'CullmanCo_barns_tr_Lrn2_Rmv_RS', 'WayneCo_barns_Lrn_Rmv_RS_CVM',
               ]## This is a list of things that didn't fit in with the naming conventions
                ##  of the rest of the results. These were manually collected and will be
                ##  included in batchList. Some files had 'tr_Lrn_Rmv_RS_CVM', which was
                ##  also added.
    
    batchList = []  # this will be filled here in a bit with all the _Batch files or equivalents

    for dirpath, dirnames, filenames in walk:   # go through each folder and subfolder within the folderLocation looking for feature class polygons (see walk)
        for filename in filenames:
            filepath = os.path.join(dirpath, filename)
            if not 'Project Documents' in filepath and not 'Copy' in filepath:
                if filename[-6:] == '_Batch':
                    batchList.append(filepath)        ## Basically, all this stuff is just looking
                elif 'tr_Lrn_Rmv_RS_CVM' in filename: ##  through all folders in 'walk' and saving 
                    batchList.append(filepath)        ##  the locations of the files that include either
                elif filename in yepList:             ##  '_Batch', 'tr_Lrn_Rmv_RS_CVM', or are found
                    batchList.append(filepath)        ##  in yepList.
    
    return batchList

def findFinalFiles_outdated():
    ##
    ## This function 'walks' through all files in the A: drive collects the locations
    ##  of all _FINAL files.
    ##
    global finalFiles
    
    folderLocation = r'A:'  # this is the folder that this function will search through
    summaryStats = collectSummaryStats()    # create the summaryStats numpy array that contains important information on the counties
    walk = arcpy.da.Walk(folderLocation, datatype = "FeatureClass", type = "Point")
        ## This walk function systematically goes through all sub-folders/directories
        ##  within the 'folderLocation' folder. It finds things of a certain type.


    filesList = []     # this will hold all files from A: with 'FINAL' in the name
    finalFiles = []    # this will hold the filtered filesList, not containing anything in nopeList

    nopeList = ['Project Documents', 'Confidence3', 'Copy', 'Test', 'test', 'SpatialJ']
        ## If any file has one or more of the items in this list within it, it will not
        ##  be selected and will be ignored.

    for dirpath, dirnames, filenames in walk:   # itterate through all directories in folderLocation
        for filename in filenames:
            filepath = os.path.join(dirpath, filename)
            if '_Prem' in filename:     # this is not '_Prems' because at least one filename doesn't have the 's'
                filesList.append(filepath)

    finalFiles = [filepath for filepath in filesList if not any(nope in filepath for nope in nopeList)]
        ## Check to see if any of the phrases from nopeList are in the filepath, if
        ##  they aren't present then include them in the finalFiles.

    return finalFiles

def findFinalFiles():
    ##
    ## 
    finalFiles = []  # this will be filled with the _FINAL file paths
    
    with open(finalFileLocations, 'rb') as CSVfile:
        reader = csv.reader(CSVfile)
        for row in reader:
            if not row[0] == '':         
                finalFiles.append(row[8].replace('D:', 'A:'))

    finalFiles = np.array (finalFiles)
    return finalFiles
    
def createTP_FN(state_abbrev, county_name):
    ##
    ## This function creates a file containing all TP and FN and labels them
    ##  with a 1 for TP and 2 for FN. This file will be turned into TP_FN_FP
    ##  by the addFP function.
    ##
    global Final, TP_FN

    # define the path to the input file that will be used to determine both TP and FN
    Final = specificCountyFile(finalFiles, state_abbrev, county_name)

    # define the path to the _TP_FN output file, which will later get renamed as _TP_FN_FP
    TP_FN = os.path.join(outputFolder, state_abbrev + '_' + county_name + '_TP_FN')

    collectEvents = findCollectEventsCount(state_abbrev, county_name)
        ## determine the number of points in the corresponding CollectEvents file, which will be used
        ##  as the threshold of where points were manually added. If OBJECTID > # entries in CollectEvents,
        ##  it was manually added and thus a False Negative.
    
    # delete the files if they exist
    if arcpy.Exists(TP_FN):
        arcpy.Delete_management(TP_FN)

    # create a copy of the input file, create it as TP_FN, defined above                      
    arcpy.CopyFeatures_management(in_features = Final, \
                                  out_feature_class = TP_FN, \
                                  config_keyword="", spatial_grid_1="0", spatial_grid_2="0", spatial_grid_3="0")

    # add a new field to store whether it is a True Positive (1), a False Negative (2) or a False Positive (3) 
    arcpy.AddField_management(in_table = TP_FN, field_name = "TP_FN_FP", field_type="SHORT", field_precision="", field_scale="", field_length="", field_alias="", field_is_nullable="NULLABLE", field_is_required="NON_REQUIRED", field_domain="")

    # decide whether each location is a TP or FN
    arcpy.CalculateField_management(in_table = TP_FN, field = "TP_FN_FP", \
                                    expression = "fn(!OID_Copy!)", \
                                    expression_type = "PYTHON_9.3", \
                                    code_block = 'def fn(num):\n  if num <= %s:\n    return (1)\n  elif num > %s:\n    return (2)' %(collectEvents, collectEvents))
                                    
def addFP(state_abbrev, county_name):
    ##
    ## This function takes the existing TP_FN file and adds the FP based on the polygon
    ##  _Batch files. It creates (or overwrites) a new TP_FN_FP file for the specific
    ##  county. It also calcualtes the TP_FN_FP field for the new points with 3s.
    ##
    global TP_FN, TP_FN_FP
    
    state_name = state_abbrev_to_name[state_abbrev]    # this comes from the Converting_state_names_and_abreviations.py file that we imported from back in the setup
    state_name_county_outline = nameFormat(state_name)  # this replaces the ' ' space in the name with an '_', which is what the CountyOutlines database uses
    state_name = state_name.replace(' ', '')

    # define the _batch file to be clipped
    batch = specificCountyFile(batchList, state_abbrev, county_name)

    # define the location of the county file to clip the batch to
    county_outline = os.path.join(r'N:\Remote Sensing Projects\2016 Cooperative Agreement Poultry Barns\Documents\Deliverables\Library\CountyOutlines', \
                                  state_name_county_outline + '.gdb', county_name + 'Co' + state_abbrev + '_outline')

    # define location of TP_FN file and the final TP_FN_FP file
    TP_FN = os.path.join(outputFolder, state_abbrev + '_' + county_name + '_TP_FN')
    TP_FN_FP = os.path.join(outputFolder, state_abbrev + '_' + county_name + '_TP_FN_FP')

    # delete the files if they exist
    if arcpy.Exists(TP_FN_FP):
        arcpy.Delete_management(TP_FN_FP)

    # clip by county border
    arcpy.Clip_analysis(in_features = batch, clip_features = county_outline, \
                        out_feature_class = 'in_memory/temp_clip', cluster_tolerance="")
    
    # convert to point
    arcpy.FeatureToPoint_management(in_features = 'in_memory/temp_clip', out_feature_class = 'in_memory/temp_point', point_location="CENTROID")

    # create temprorary buffer, which will be used to cut out TP & FN from _Batch file
    arcpy.Buffer_analysis(in_features = Final, out_feature_class = 'in_memory/temp_buffer', \
                          buffer_distance_or_field = "200 Meters", line_side = "FULL", line_end_type = "ROUND", \
                          dissolve_option = "NONE", dissolve_field = "", method = "PLANAR")

    # use the erase tool to remove all features within the buffer created in the last step
    arcpy.Erase_analysis(in_features = 'in_memory/temp_point', \
                         erase_features = 'in_memory/temp_buffer', \
                         out_feature_class = 'in_memory/temp_FP', \
                         cluster_tolerance = "")
                     
    # combine the TP_FN file with the FP file
    arcpy.Merge_management(inputs = TP_FN + ';' + 'in_memory/temp_FP', output = TP_FN_FP, field_mappings='ICOUNT "ICOUNT" true true false 4 Long 0 0 ,First,#,GA_Franklin_TP_FN,ICOUNT,-1,-1;Confidence "Confidence" true true false 2 Short 0 0 ,First,#,GA_Franklin_TP_FN,Confidence,-1,-1;POINT_X "POINT_X" true true false 8 Double 0 0 ,First,#,GA_Franklin_TP_FN,POINT_X,-1,-1;POINT_Y "POINT_Y" true true false 8 Double 0 0 ,First,#,GA_Franklin_TP_FN,POINT_Y,-1,-1;TP_FN_FP "TP_FN_FP" true true false 2 Short 0 0 ,First,#,GA_Franklin_TP_FN,TP_FN_FP,-1,-1')

    # delete all the 'in memory' temporary files and the individual TP_FN and FP files
    arcpy.Delete_management(in_data = 'in_memory/temp_clip', data_type = "")
    arcpy.Delete_management(in_data = 'in_memory/temp_buffer', data_type = "")
    arcpy.Delete_management(in_data = 'in_memory/temp_FP', data_type = "")
    arcpy.Delete_management(in_data = TP_FN, data_type = "")

    # calculate the TP_FN_FP field, change any blanks to 3 (representing FP)
    arcpy.CalculateField_management(in_table = TP_FN_FP, field = "TP_FN_FP", \
                                    expression = "fn( !TP_FN_FP!)", \
                                    expression_type = "PYTHON_9.3", \
                                    code_block = "def fn(x):\n  if (x is None):\n    return (3)\n  else:\n    return x")

    # change the Confidence field for all FP to 9, representing 'INCORRECT'
    arcpy.CalculateField_management(in_table = TP_FN_FP, field = "Confidence", \
                                    expression = "fn(!Confidence!)", \
                                    expression_type = "PYTHON_9.3", \
                                    code_block = "def fn(y):\n  if (y is None):\n    return (9)\n  else:\n    return y")
        
def addRasterInfo(input_point_data, raster_dataset):
    ##
    ## This function extracts the values from the input raster
    ##  raster and creates two new fields in the TP_FN_FP file,
    ##  called ProbSurf_1 and ProbSurf_2 respectively. 
    ##  ProbSurf_1 has no interpolation, ProbSurf_2 has
    ##  bilinear interpolation.
    ##
    arcpy.CheckOutExtension("Spatial")  # this just allows the script to access the Spatial Analyst ArcGIS extension
    
    arcpy.sa.ExtractMultiValuesToPoints (input_point_data, [[raster_dataset, 'ProbSurf_1']], "NONE")
    arcpy.sa.ExtractMultiValuesToPoints (input_point_data, [[raster_dataset, 'ProbSurf_2']], "BILINEAR")
    
    arcpy.CheckInExtension("Spatial")   # this makes sure that a license does not remain in use for the Spatial Analyst extension
    
############################
######### DO STUFF #########
############################

if __name__ == '__main__':

    print "Script started! This will probably take 20 minutes to an hour to complete.\n\n"

    errorCounties = [] # this will be filled with the counties that have had errors so far

    summaryStats = collectSummaryStats() # create the 'summaryStats' numpy array

    print "Finding _FINAL files..."
    finalFiles = findFinalFiles()   # create a list of the file locaitons of all the _FINAL files (and similar) on the A: drive
    print "_FINAL files found. Script duration so far:", checkTime()

    print "Finding _Batch files..."
    batchList = findBatchFiles()    # create a list of the file locations of all the _Batch files on the A: drive
    print "_Batch files found. Script duration so far:", checkTime()
    
    # loop for all relevant counties
    for county in summaryStats:
        state_abbrev = county[0][0:2]    # holds the 2-letter abbreviation for the current state
        state_name = state_abbrev_to_name[state_abbrev]     # holds the full name of the state
        state_name = state_name.replace(" ", "")
        county_name = county[1]    # holds the county name

        errorFlag = []
        
        try:
            createTP_FN(state_abbrev, county_name)
            print state_name, county_name, "county TPs and FNs completed. Script duration so far:", checkTime()

        except:
            errorFlag += [1]
            print "ERROR with TP & FN for", state_name, county_name
            errorCounties += [[state_name, county_name, 'createTP_FN']]

        try:  
            addFP(state_abbrev, county_name)
            print state_name, county_name, "county FPs completed. Script duration so far:", checkTime()
            
        except:
            errorFlag += [2]
            print "ERROR with FP for", state_name, county_name
            errorCounties += [[state_name, county_name, 'addFP']]

        try:
            addRasterInfo( os.path.join(outputFolder, state_abbrev + '_' + county_name + '_TP_FN_FP'), \
                           probSurface )            
        except:
            errorFlag += [3]
            print "ERROR with Raster for", state_name, county_name
            errorCounties += [[state_name, county_name, 'addRasterInfo']]
                
    if errorCounties = []:
        print "\nThere were no counties that had errors.\n"

    else:
        errorCounties = np.array(errorCounties)
        print "\nCounties that had errors:\n", errorCounties

    ############################
    ######### CLEANUP ##########
    ############################

    print "---------------------\nSCRIPT COMPLETE!"
    print "The script took a total of", checkTime() + "."
    print "---------------------"

