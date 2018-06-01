#################### Creating_TP_FN_FP_files.py ##############################

############################
####### DESCRIPTION ########
############################

## Created by David South 5/30/18, updated N/A
##
## Script description: This script will take the results from the county-level
##  Remote Sensing procedure and export 3 files per county with [county] being
##  the name of the county and [ST] being the 2 letter state abbreviation:
##        [county]Co[ST]_TP.shp
##        [coutny]Co[ST]_FP.shp
##        [coutny]Co[ST]_FN.shp
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
import arcpy
from arcpy import env
arcpy.env.overwriteOutput = True
import numpy as np
import csv
import time
start_time = time.time()

############################
####### PARAMETERS #########
############################

# location of CSV with names of all completed counties
countiesCSV = r'O:\AI Modeling Coop Agreement 2017\David_working\Remote_Sensing_Procedure\RS_completed_counties.csv'

# location of probability surface raster
probSurface = r'N:\FLAPS from Chris Burdett\Data\poultry_prob_surface\poultryMskNrm\poultryMskNrm.tif'

############################
####### DEFINE FUNCTIONS ####
############################

def collectCounties():
    global counties
    counties = [] # define a blank list that will later be turned into a numpy array
    
    with open(countiesCSV, 'rb') as CSVfile:
        reader = csv.reader(CSVfile)
        for row in reader:
            counties.append(row)

    counties = np.array (counties)

def createTP(state, county):
    ()

def createFN(state, county):
    ()

def createFP(state, county):
    ()

############################
####### DO STUFF ###########
############################

collectCounties() # create the 'counties' numpy array

# loop for all relevant counties
for county in counties:
    state = county[1][0:2]    # holds the 2-letter abbreviation for the current state
    countyName = county[2]    # holds the county name
    if not county[0] == '':     # skip the first row which just contains the column labels
        createTP(state, countyName)
        print state, countyName, "county TP completed. Script duration so far:", time.time() - start_time / 60, "minutes"
        
        createFN(state, countyName)
        print state, countyName, "county FN completed. Script duration so far:", time.time() - start_time / 60, "minutes"

        createFP(state, countyName)
        print state, countyName, "county FP completed. Script duration so far:", time.time() - start_time / 60, "minutes"
        

    


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

