##################### Feature_Analyst_Setup.py #########################

############################
####### DESCRIPTION ########
############################

## Created by David South 6/25/18, updated N/A
##
## Script description: This script is designed to create and set up the
##  MXD documents that will be used for the national remote sensing model.
##  It will create the needed GDBs and fill the MXDs the needed files.
##
##  Files to be added (not created for this script) are as follows:
##
##      2m resolution resampled NAIP imagery
##      county outline file
##

############################
####### SETUP ##############
############################

import numpy as np
from resample_NAIP import resample

sys.path.insert(0, r'O:\AI Modeling Coop Agreement 2017\David_working\Python') # Gives us access to nameFormat function which is very useful for name standardization
from Converting_state_names_and_abreviations import *                          #  as well as state_abbrev_to_name and state_name_to_abbrev dictionaries

# this gives us access to two dictionaries for converting state names to abbreviations and vice versa
#  it also gives us the nameFormat function which is very useful for name standardization
sys.path.insert(0, r'O:\AI Modeling Coop Agreement 2017\David_working\Python') 
from Converting_state_names_and_abreviations import *

############################
####### PARAMETERS #########
############################
clusterList = ['CO_cluster1', 'CO_cluster2']

#             state    cluster      county
countyList = [
              ['CO', 'CO_cluster1', 'Jefferson'],
              ['CO', 'CO_cluster1', 'Lairmer'],
              ['CO', 'CO_cluster2', 'Broomfield'],
             ]
countyList = np.array(countyList)

folderLocation = 

############################
####### DEFINE FUNCTIONS ###
############################

def createGDB(folderLocation, state_abbrev, clusterName):
    # check to see if GDB exits
    if not arcpy.Exists( os.path.join(folderLocation, clusterName) ):
        # create GDB
        arcpy.CreateFileGDB_management(out_folder_path = folderLocation, out_name = clusterName, out_version = "CURRENT")
            
    # check if MXD exists
    if not arcpy.Exists(os.path.join(folderLocation, clusterName + '.mxd')):
        # create MXD    ## this may not actually be possible in arcMap
        

    # check if county outline is in MXD:
        # add county outline to MXD

    # check to see if the 2m NAIP imagery exists (if yes):
        # check if 2m NAIP imagery is in MXD
            # add 2m NAIP to MXD

############################
####### DO STUFF ###########
############################

if __name__ = '__main__':

    missingNAIP = []    # will hold all the county names that are missing the resampled 2m NAIP imagery
    errorCounty = []    # will hold all counties that had errors during this process
    
    for cluster in clusterList:
        # name conventions for the county outline shapefiles:
        #   nameFormat(countyName) + "Co" + us_state_abbrev[state] + "_outline"
    
        state_abbrev = row[0]
        state_name = state_abbrev_to_name[state_abbrev]    # this comes from the Converting_state_names_and_abreviations.py file that we imported from back in the setup
        state_name = nameFormat(state_name)

        clusterName = row[1]

        for county in countyList:
            countyName = nameFormat(row[2])

            createGDB(folderLocation, state_abbrev, clusterName)

        
