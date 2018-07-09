#################### resample_NAIP.py ##############################

############################
####### DESCRIPTION ########
############################

## Created by David South 5/30/18, updated 6/20/18
##
## This script is intended to be able to resample any 1m NAIP imagery that
##  it is directed to, and output them in a neat little organized folder.
##

############################
####### SETUP ##############
############################

import time
start_time = time.time()

import arcpy, os

# this next line gives us access to the nameFormat function
sys.path.insert(0, r'O:\AI Modeling Coop Agreement 2017\David_working\Python') 
from Converting_state_names_and_abreviations import *
    ## The above lines give us acccess to 3 useful things:
    ##      nameFormat(x)
    ##      state_abbrev_to_name[x]
    ##      state_name_to_abbrev[x]

############################
####### PARAMETERS #########
############################

first10counties = [     ## This list holds the first 10 counties in Alabama
    'Barbour',          ##  alphabetically. We are running these first to 
    'Blount',           ##  get a full batch complete.
    'Bullock',
    'Butler',
    'Calhoun',
    'Cherokee',
    'Clay',
    'Cleburne',
    'Coffee',
    'Colbert',
    ]

NAIP_folder = r'N:\Remote Sensing Projects\2016 Cooperative Agreement Poultry Barns\Documents\Poultry Population Modeling Project\Rdrive\Imagery\NAIP'
NAIP2m_folder = r'N:\Remote Sensing Projects\2016 Cooperative Agreement Poultry Barns\Documents\Poultry Population Modeling Project\Rdrive\Imagery\NAIP2m'

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

def create_state_GDBs (outputFolder, state_list):
    ##
    ## Input Variables:
    ##      outputFolder: the file location to put all the GDBs into
    ##      state_list: a list object containing abbreviations for all
    ##                   the states that need GDBs created
    ##
    ## Returns:
    ##      none
    ##
        
    ## Loop for each state
    for state_abbrev in state_list:

        state_name = nameFormat(state_abbrev_to_name[state_abbrev])

        GDB = 'NAIP2m_' + state_abbrev

        print ("Creating geodatabase for %s..." %state_name)

            # Check to see if the gdb already exists                
        if not arcpy.Exists(os.path.join(outputFolder, GDB + '.gdb')): ## See if this geodatabase already exists

            try:
                ## If the gdb doesn't already exist, create new geodatabase for that state
                arcpy.CreateFileGDB_management(out_folder_path = outputFolder, \
                                               out_name = GDB, out_version = "CURRENT")
                print "GDB created."
                
            except:
                print ("Error creating GDB for %s." %state_name)

        else:
            print ("Geodatabase already exists for %s." %state_name)

def findSID(state_abbrev, county_name):
    state_name = nameFormat(state_abbrev_to_name[state_abbrev])
    county_name = nameFormat(county_name)
    
    for File in os.listdir(
                os.path.join(
                             NAIP_folder, state_name, \
                             county_name + 'Co' + state_abbrev
                             )
                           ):
        if File.endswith('.sid'):
            return File
    
def resample(input_raster, output_location, state_abbrev, county_name):
    ##
    ## This function reprojects the selected raster to 2m resolution.
    ##
    ## Input Variables:
    ##      input_raster:   The file location of the native NAIP imagery.
    ##                       This is likely in 1m resolution, but may be
    ##                       as small as .3m in some states like California.
    ##
    ##      output_location:    The path to the folder where the reprojected file should
    ##                           be placed in. This does not include the filename.
    ##
    ##      state_abbrev & county_name: The respective state abbreviation, 'NC' for
    ##                                   example, and the respective county name,
    ##                                   such as 'Union'.
    ##
    state_name = nameFormat(state_abbrev_to_name[state_abbrev])
    county_name = nameFormat(county_name)

    outputName = 'NAIP2m_' + state_abbrev + '_' + county_name
    if not arcpy.Exists(os.path.join(output_location, outputName)):
        if arcpy.Exists(input_raster):
            print "Resampling", state_abbrev, county_name, "..."
            arcpy.Resample_management (input_raster, os.path.join(output_location, outputName), \
                                        cell_size="2 2", resampling_type="NEAREST")
            
            print state_abbrev, county_name, "resampled. Script duration so far:", checkTime()
        else:
            print "--", state_abbrev, county_name, "input NAIP imagery not found."
    else:
        print "-- Resampled raster for", state_abbrev, county_name, "already exists!"
            # may want to remove the above line in case it gets annoying for users
    
############################
####### DO STUFF ###########
############################

if __name__ == '__main__':
#if __name__ == 'LEEEEERRRRROOOYYYYY JJJJJEEENNNKKKKIINNNSSSSSSSSSS':

    print "Creating GDBs..."
    create_state_GDBs(NAIP2m_folder, ['AL'])
    print "GDBs created. Script duration so far:", checkTime(), '\n\n'

    print "Starting resampling process ...\n\n"

    for county_name in first10counties:

        
                
        county_name = nameFormat(county_name)
        state_abbrev = 'AL' ## CHANGE THIS LATER ##
        state_name = nameFormat(state_abbrev_to_name[state_abbrev])

        SID = findSID(state_abbrev, county_name)
        
        input_raster = os.path.join(NAIP_folder, \
                                    state_name, \
                                    county_name + 'Co' + state_abbrev,\
                                    SID)
                
        output_location = os.path.join(NAIP2m_folder, 'NAIP2m_' + state_abbrev + '.gdb')

        resample(input_raster, output_location, state_abbrev, county_name)
    
    ############################
    ####### CLEANUP ############
    ############################
                
    print "\n\n---------------------\nSCRIPT COMPLETE!"
    print "The script took a total of", checkTime(), "."
    print "---------------------"
