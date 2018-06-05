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

# this next line gives us access to two dictionaries for converting state names to abbreviations and vice versa
sys.path.insert(0, r'O:\AI Modeling Coop Agreement 2017\David_working\Python')
from Converting_state_names_and_abreviations.py import *



import time
start_time = time.time()

############################
####### PARAMETERS #########
############################

# location of CSV with names of all completed counties
countiesCSV = r'O:\AI Modeling Coop Agreement 2017\David_working\Remote_Sensing_Procedure\RS_completed_counties.csv'

# location of CSV with summary satistics, such as Collect Events which is used to tell TP from FN
summaryStatsCSV = r'O:\AI Modeling Coop Agreement 2017\David_working\Remote_Sensing_Procedure\Stats_summary.csv'

# location of probability surface raster
probSurface = r'N:\FLAPS from Chris Burdett\Data\poultry_prob_surface\poultryMskNrm\poultryMskNrm.tif'

############################
###### DEFINE FUNCTIONS ####
############################

def collectCounties():
    ##
    ## This function creates a numpy array from the countiesCSV.csv file.
    ##  This gives the names and states of all counties that need to be run.
    ##
    global counties
    counties = [] # define a blank list that will later be turned into a numpy array
    
    with open(countiesCSV, 'rb') as CSVfile:
        reader = csv.reader(CSVfile)
        for row in reader:
            counties.append(row)

    counties = np.array (counties)

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
            summaryStats.append(row)

    summaryStats = np.array (summaryStats)

def findCollectEventsCount(state_abbrev, county)
    ##
    ## This function seeks through the summaryStats numpy array and returns the
    ##  proper CollectEvents value which is used to determine the line between
    ##  TP and FN.
    ##
    for row in summaryStats:
        if (row[0][:1] == state_abbrev) and (row[1] == county):
            return row[7]

def createTP_FN(state_abbrev, county):
    ##
    ## This function creates a file containing all TP and FN and labels them
    ##  with a 1 for TP and 2 for FN. This file will be turned into TP_FN_FP
    ##  by the addFP function.
    ##
    global Final, TP_FN

    state_name = state_abbrev_to_name[state_abbrev]    # this comes from the Converting_state_names_and_abreviations.py file that we imported from back in the setup

    # define the path to the input file that will be used to determine both TP and FN
    Final = os.path.join(r'N:\Remote Sensing Projects\2016 Cooperative Agreement Poultry Barns\Documents\Deliverables\Library\Poultry_Premises_Results', \
                         state_name + '.gdb', county + 'Co_Prems_FINAL')

    if arcpy.exists(Final) == False:    # check to see if the file exists, and if not add another '_FINAL' to it because some have the suffix twice
        Final = Final + '_FINAL'

    # define the path to the _TP_FN output file, which will later get renamed as _TP_FN_FP
    TP_FN = os.path.join(r'O:\AI Modeling Coop Agreement 2017\David_working\Remote_Sensing_Procedure\TP_FN_FP.gdb', state_abbrev + '_' + county + '_TP_FN')

    # create a copy of the input file, create it as TP_FN, defined above                      
    arcpy.CopyFeatures_management(in_features = Final, \
                                  out_feature_class = TP_FN, \
                                  config_keyword="", spatial_grid_1="0", spatial_grid_2="0", spatial_grid_3="0")

    # add a new field to store whether it is a True Positive (1), a False Negative (2) or a False Positive (3) 
    arcpy.AddField_management(in_table = TP_FN, field_name = "TP_FN_FP", field_type="SHORT", field_precision="", field_scale="", field_length="", field_alias="", field_is_nullable="NULLABLE", field_is_required="NON_REQUIRED", field_domain="")

    # determine the number of points in the corresponding CollectEvents file, which will be used
    #  as the threshold of where points were manually added. If OBJECTID > # entries in CollectEvents,
    #  it was manually added and thus a False Negative.
    CollectEvents = findCollectEventsCount(state_abbrev, county)

    # decide whether each location is a TP or FN
    arcpy.CalculateField_management(in_table = TP_FN, field = "TP_FN_FP", \
                                    expression = "fn(!OBJECTID!)", \
                                    expression_type = "PYTHON_9.3", \
                                    code_block = 'def fn(num):\n  if num <= %s:\n    return (1)\n  elif num > %s:\n    return (2)' %(CollectEvents, CollectEvents))


def addFP(state_abbrev, county):
    global FP, TP_FN_FP
    
    state_name = state_abbrev_to_name[state_abbrev]

    # define the _batch file to be clipped
    batch = os.path.join(r'A:', state_name, state_abbrev + '1cluster.gdb', county + 'Co_Batch'

    # define the location of the county file to clip the batch to
    county_outline = os.path.join(r'N:\Remote Sensing Projects\2016 Cooperative Agreement Poultry Barns\Documents\Deliverables\Library\CountyOutlines', \
                                  state_name + '.gdb', county + 'Co' = county_abbrev + '_outline'

    # define location of FP file and the final TP_FN_FP file
    FP = os.path.join(r'O:\AI Modeling Coop Agreement 2017\David_working\Remote_Sensing_Procedure\TP_FN_FP.gdb', state_abbrev + '_' + county + '_FP'
    TP_FN_FP = os.path.join(r'O:\AI Modeling Coop Agreement 2017\David_working\Remote_Sensing_Procedure\TP_FN_FP.gdb', state_abbrev + '_' + county + 'TP_FN_FP'

    # clip by county border
    arcpy.Clip_analysis(in_features = batch, clip_features = county_outline, \
                        out_feature_class = 'in_memory/temp_clip', cluster_tolerance="")
    
    # convert to point
    arcpy.FeatureToPoint_management(in_features = 'in_memory/temp_clip', out_feature_class = "O:/AI Modeling Coop Agreement 2017/David_working/TEST.gdb/FranklinCo_FP_point", point_location="CENTROID")

    # create temprorary buffer, which will be used to cut out TP & FN from _Batch file
    arcpy.Buffer_analysis(in_features = Final, out_feature_class = 'in_memory/temp_buffer', \
                          buffer_distance_or_field = "200 Meters", line_side="FULL", line_end_type="ROUND", \
                          dissolve_option="NONE", dissolve_field="", method="PLANAR")

    # clip out all points of _Batch that are within 200m of either a TP or a FN so the program can root out all FP
    arcpy.Clip_analysis(in_features = 'in_memory/temp_clip', clip_features = 'in_memory/temp_buffer', \
                        out_feature_class = FP, cluster_tolerance=""))
                      
    # combine the TP_FN file with the FP file
    arcpy.Merge_management(inputs = TP_FN + ';' +  FP, output = TP_FN_FP, field_mappings='ICOUNT "ICOUNT" true true false 4 Long 0 0 ,First,#,GA_Franklin_TP_FN,ICOUNT,-1,-1;Confidence "Confidence" true true false 2 Short 0 0 ,First,#,GA_Franklin_TP_FN,Confidence,-1,-1;POINT_X "POINT_X" true true false 8 Double 0 0 ,First,#,GA_Franklin_TP_FN,POINT_X,-1,-1;POINT_Y "POINT_Y" true true false 8 Double 0 0 ,First,#,GA_Franklin_TP_FN,POINT_Y,-1,-1;TP_FN_FP "TP_FN_FP" true true false 2 Short 0 0 ,First,#,GA_Franklin_TP_FN,TP_FN_FP,-1,-1')

    # delete all the 'in memory' temporary files and the individual TP_FN and FP files
    arcpy.Delete_management(in_data = 'in_memory/temp_clip', data_type = "")
    arcpy.Delete_management(in_data = 'in_memory/temp_buffer', data_type = "")
    arcpy.Delete_management(in_data = TP_FN, data_type = "")
    arcpy.Delete_management(in_data = FP, data_type = "")

    # calculate the TP_FN_FP field, change any blanks to 3 (representing FP)
    arcpy.CalculateField_management(in_table = TP_FN_FP, field = "TP_FN_FP", \
                                    expression = "fn( !TP_FN_FP!)", \
                                    expression_type="PYTHON_9.3", \
                                    code_block="def fn(x):\n  if (x is None):\n    return (3)\n  else:\n    return x")

    # change the Confidence field for all FP to 9, representing 'INCORRECT'
    arcpy.CalculateField_management(in_table = TP_FN_FP, field = "Confidence", \
                                    expression = "fn(!Confidence!)", \
                                    expression_type="PYTHON_9.3", \
                                    code_block = "def fn(y):\n  if (y is None):\n    return (9)\n  else:\n    return y")
        

############################
####### DO STUFF ###########
############################

if __name__ == '__main__':

    collectCounties() # create the 'counties' numpy array
    collectSummaryStats()

    # loop for all relevant counties
    for county in counties:
        state = county[1][0:2]    # holds the 2-letter abbreviation for the current state
        countyName = county[2]    # holds the county name
        if not county[0] == '' or not county[1] == 'MS2':     # skip the first row which just contains the column labels, also skip MS2 because it wasn't completed

            try:
                
                createTP_FN(state, countyName)
                print state, countyName, "county TPs and FNs completed. Script duration so far:", time.time() - start_time / 60, "minutes"
                
                addFP(state, countyName)
                print state, countyName, "county FPs completed. Script duration so far:", time.time() - start_time / 60, "minutes"
                

            except:
                e = sys.exc_info()[0]
                print e


    ############################
    ####### CLEANUP ############
    ############################

    time_to_run = (time.time() - start_time) / 60.

    print "---------------------\nSCRIPT COMPLETE!"

    if time_to_run < 60. :
        
        print "This program took", round(time_to_run), "minutes to run."

    else:
        print "This program took", round( (time_to_run / 60.) , 1) , "hours to run."
        
    print "---------------------"

