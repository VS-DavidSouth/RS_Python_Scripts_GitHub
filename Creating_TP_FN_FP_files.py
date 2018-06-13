#################### Creating_TP_FN_FP_files.py ##############################

############################
####### DESCRIPTION ########
############################

## Created by David South 5/30/18, updated N/A
##
## Script description: This script will take the results from the county-level
##  Remote Sensing procedure and export a file with [county] being
##  the name of the county and [ST] being the 2 letter state abbreviation:
##       [ST]_[county]_TP_FN_FP.shp
##
##  TP = True Positives, meaning the poultry premises that the remote sensing
##       procedure correctly recognized
##  FP = False Positives, meaning the noise and clutter which the remote sensing
##       procedure incorrectly thought were poultry premises
##  FN = False Negatives, meaning the poultry premises that were not picked
##       up by the remote sensing procedure and which needed to be added in
##       manually by a user

############################
####### SETUP ##############
############################
import time
start_time = time.time()

import csv, os, sys

import arcpy
arcpy.env.overwriteOutput = True

import numpy as np

# this next import gives us access to two dictionaries for converting state names to abbreviations and vice versa
sys.path.insert(0, r'O:\AI Modeling Coop Agreement 2017\David_working\Python')
from Converting_state_names_and_abreviations import *

############################
####### PARAMETERS #########
############################

# location of CSV with summary satistics, such as Collect Events which is used to tell TP from FN
summaryStatsCSV = r'O:\AI Modeling Coop Agreement 2017\David_working\Remote_Sensing_Procedure\Stats_summary.csv'

# location of probability surface raster
probSurface = r'N:\FLAPS from Chris Burdett\Data\poultry_prob_surface\poultryMskNrm\poultryMskNrm.tif'

############################
###### DEFINE FUNCTIONS ####
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

def findCollectEventsCount(state_abbrev, county):
    ##
    ## This function seeks through the summaryStats numpy array and returns the
    ##  proper CollectEvents value which is used to determine the line between
    ##  TP and FN.
    ##
    for row in summaryStats:
        if (row[0][:2] == state_abbrev) and (row[1] == county):
            return row[7]


def specificCountyFile(file_list, state_abbrev, county_name):
    ##
    ## This fuction searches through a list of filepaths and finds the one for the
    ##  appropriate state. This can be used for batchList, correctFiles,
    ##  etc.
    ##
            
            
    for file_path in file_list:
        state_name = state_abbrev_to_name[state_abbrev]
        state_name = state_name.replace(' ', '')
        
        if state_abbrev in file_path or state_name in file_path:
            if county_name in file_path:
                return file_path    # it should be noted that this will only choose the first matching file and ignore any further ones. This could introduce errors.

def findBatchFiles():
    ##
    ## This function looks through the A:\ Drive to find all the files with the
    ##  suffix '_Batch' and organizes them (with their file location) in a list.
    ##
    global batchList
    
    folderLocation = r'A:'
    walk = arcpy.da.Walk(folderLocation, datatype = "FeatureClass", type = "Polygon")

    nopeList = ['Project Documents', 'Copy',]   # this is unused so far, if more entries are needed than this will be used to negatively select things
    yepList = ['GilesCo_Results', 'FranklinCo_Results', 'WayneCo_Results2', \
               'SampsonCo_Results2', 'DuplinCo_Results2',]
    batchList = []

    for dirpath, dirnames, filenames in walk:
        for filename in filenames:
            filepath = os.path.join(dirpath, filename)
            if not 'Project Documents' in filepath and not 'Copy' in filepath:
                if filename[-6:] == '_Batch':
                    batchList.append(filepath)
                elif 'tr_Lrn_Rmv_RS_CVM' in filename:
                    batchList.append(filepath)
                elif filename in yepList:
                    batchList.append(filepath)
    
    return batchList

def findFinalFiles():
    ##
    ## This function 'walks' through all files in the A: drive collects the locations
    ##  of all _FINAL files.
    ##
    global correctFiles
    
    folderLocation = r'A:'  # this is the folder that this function will search through
    summaryStats = collectSummaryStats()    # create the summaryStats numpy array that contains important information on the counties
    walk = arcpy.da.Walk(folderLocation, datatype = "FeatureClass", type = "Point")
        ## This walk function systematically goes through all sub-folders/directories
        ##  within the 'folderLocation' folder. It finds things of a certain type.


    filesList = []     # this will hold all files from A: with 'FINAL' in the name
    correctFiles = [] # this will hold all files from filesList that don't
                                #  have anything from the nopeList in it.

    nopeList = ['Project Documents', 'Confidence3', 'Copy', 'Test', 'test', 'SpatialJ']
        ## If any file has one or more of the items in this list within it, it will not
        ##  be selected and will be ignored.

    for dirpath, dirnames, filenames in walk:   # itterate through all directories in folderLocation
        for filename in filenames:
            filepath = os.path.join(dirpath, filename)
            if '_Prem' in filepath:     # this is not '_Prems' because at least one filename doesn't have the 's'
                if '_FINAL_FINAL' in filename or '_Final_FINAL' in filename:
                    filesList.append(filepath) # find _FINAL_FINAL files first
                elif '_FINAL2' in filename:
                    filesList.append(filepath) # next check for a 2 at the end
                elif '_FINAL' in filename or '_Final' in filename:
                    filesList.append(filepath) # now look for just a single 'final'

    correctFiles = [s for s in filesList if not any(xs in s for xs in nopeList)]
            
    return correctFiles

def createTP_FN(state_abbrev, county_name):
    ##
    ## This function creates a file containing all TP and FN and labels them
    ##  with a 1 for TP and 2 for FN. This file will be turned into TP_FN_FP
    ##  by the addFP function.
    ##
    global Final, TP_FN

    state_name = state_abbrev_to_name[state_abbrev]    # this comes from the Converting_state_names_and_abreviations.py file that we imported from back in the setup
    state_name = state_name.replace(' ', '')

    # define the path to the input file that will be used to determine both TP and FN
    Final = specificCountyFile(filteredFilesList, state_abbrev, county_name)

    # define the path to the _TP_FN output file, which will later get renamed as _TP_FN_FP
    TP_FN = os.path.join(r'O:\AI Modeling Coop Agreement 2017\David_working\Remote_Sensing_Procedure\TP_FN_FP.gdb', \
                         state_abbrev + '_' + county_name + '_TP_FN')

    # delete the files if they exist
    if arcpy.Exists(TP_FN):
        arcpy.Delete_management(TP_FN)

    # create a copy of the input file, create it as TP_FN, defined above                      
    arcpy.CopyFeatures_management(in_features = Final, \
                                  out_feature_class = TP_FN, \
                                  config_keyword="", spatial_grid_1="0", spatial_grid_2="0", spatial_grid_3="0")

    # add a new field to store whether it is a True Positive (1), a False Negative (2) or a False Positive (3) 
    arcpy.AddField_management(in_table = TP_FN, field_name = "TP_FN_FP", field_type="SHORT", field_precision="", field_scale="", field_length="", field_alias="", field_is_nullable="NULLABLE", field_is_required="NON_REQUIRED", field_domain="")

    # determine the number of points in the corresponding CollectEvents file, which will be used
    #  as the threshold of where points were manually added. If OBJECTID > # entries in CollectEvents,
    #  it was manually added and thus a False Negative.
    collectEvents = findCollectEventsCount(state_abbrev, county_name)

    # decide whether each location is a TP or FN
    arcpy.CalculateField_management(in_table = TP_FN, field = "TP_FN_FP", \
                                    expression = "fn(!OBJECTID!)", \
                                    expression_type = "PYTHON_9.3", \
                                    ##code_block = 'def fn(num):\n  if num <= %s:\n    return (1)\n  elif num > %s:\n    return (2)' %(collectEvents, collectEvents))
                                    code_block = 'def fn(num):\n  return (1)')   # if the issue with the OBJECTID field gets resolved, uncomment the above line and delete this line
                                            ## As of now, this section is pretty pointless. Since efforts so far to copy the OBJECTID field from the original '_FINAL' files resulted
                                            ##  in the original OBJECTID field to overwrite itself, it has made it impossible to judge the line between TP and FN. Originally FN
                                            ##  were determined as the points that have an OBJECTID field value higher than the _CollectEvents point count, meaning they were
                                            ##  added manually. Since the OBJECTID field has been overwritten, this is moot. It may be possible to go back to the previous files later on.

def addFP(state_abbrev, county_name):
    ##
    ## This function takes the existing TP_FN file and adds the FP based on the polygon
    ##  _Batch files. It creates (or overwrites) a new TP_FN_FP file for the specific
    ##  county. It also calcualtes the TP_FN_FP field for the new points with 3s.
    ##
    global TP_FN, TP_FN_FP
    
    state_name = state_abbrev_to_name[state_abbrev]
    state_name = state_name.replace(' ', '')

    # define the _batch file to be clipped
    batch = specificCountyFile(batchList, state_abbrev, county)

    # define the location of the county file to clip the batch to
    county_outline = os.path.join(r'N:\Remote Sensing Projects\2016 Cooperative Agreement Poultry Barns\Documents\Deliverables\Library\CountyOutlines', \
                                  state_name + '.gdb', county + 'Co' + state_abbrev + '_outline')

    # define location of TP_FN file and the final TP_FN_FP file
    TP_FN = os.path.join(r'O:\AI Modeling Coop Agreement 2017\David_working\Remote_Sensing_Procedure\TP_FN_FP.gdb', state_abbrev + '_' + county + '_TP_FN')
    TP_FN_FP = os.path.join(r'O:\AI Modeling Coop Agreement 2017\David_working\Remote_Sensing_Procedure\TP_FN_FP.gdb', state_abbrev + '_' + county + '_TP_FN_FP')

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
        

############################
####### DO STUFF ###########
############################

if __name__ == '__main__':

    print "Script started! This will probably take 20-30 minutes.\n\n"

    errorCounties = [] # this will be filled with the counties that have had errors so far

    summaryStats = collectSummaryStats() # create the 'summaryStats' numpy array

    print "Finding _FINAL files..."
    correctFiles = findFinalFiles()   # create a list of the file locaitons of all the _FINAL files (and similar) on the A: drive
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
        #if state_abbrev == 'GA' and county_name == 'Franklin':
            createTP_FN(state_abbrev, county_name)
            print state_name, county_name, "county TPs and FNs completed. Script duration so far:", checkTime()

        except:
            errorFlag += [1]
            print "ERROR with TP & FN for", state_name, county_name
            errorCounties += [[state_name, county_name, 'TP_FN']]

        try:
        #if state_abbrev == 'GA' and county_name == 'Franklin':   
            addFP(state_abbrev, county_name)
            print state_name, county_name, "county FPs completed. Script duration so far:", checkTime()
            
        except:
            errorFlag = [2]
            print "ERROR with FP for", state_name, county_name
            errorCounties += [[state_name, county_name, 'FP']]
                
    errorCounties = np.array(errorCounties)
    print "Counties that had errors:\n", errorCounties

    ############################
    ####### CLEANUP ############
    ############################

    print "---------------------\nSCRIPT COMPLETE!"
    print "The script took a total of", checkTime(), "."
    print "---------------------"

