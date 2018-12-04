# Setting_up_results_GDBs.py
#
# Created by David South 12/4/2018
#
# This script has adapted several parts from Setting_up_counties_database.py.
# It is designed to create a GDB for each state for the HPAI II project, one for each
# state that contains one of the 594 high poultry or otherwise important counties.
#

import os
from Converting_state_names_and_abreviations import *

# PARAMETERS #
#
# You should make sure to check that these parameters are all correct.
arcpy.env.OverwriteOutput = True # Overwrite results

results_folder = r'R:\Nat_Hybrid_Poultry\Results\Automated_Review_Results'

# Specify the folder location for all the batch_files
batch_files_location = r'R:\Nat_Hybrid_Poultry\Remote_Sensing\Feature_Analyst'

states2do = [
    'Alabama',
    'Arkansas',
    'California',
    'Colorado',
    'Delaware',
    'Florida',
    'Georgia',
    'Illinois',
    'Indiana',
    'Iowa',
    'Kentucky',
    'Louisiana',
    'Maryland',
    'Massachusetts',
    'Michigan',
    'Minnesota',
    'Mississippi',
    'Missouri',
    'Montana',
    'Nebraska',
    'New York',
    'North Carolina',
    'Ohio',
    'Oklahoma',
    'Oregon',
    'Pennsylvania',
    'South Carolina',
    'South Dakota',
    'Tennessee',
    'Texas',
    'Virginia',
    'Washington',
    'West Virginia',
    'Wisconsin',
    ]


def create_state_GDBs(outputFolder, state_list):
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
    for state_name in state_list:

        state_name = nameFormat(state_name)

        GDB = state_name  # Note that this should not have '.gdb' as part of it, it will be added later

        print ("Creating geodatabase for %s..." % state_name)

        # Check to see if the gdb already exists
        if not arcpy.Exists(os.path.join(outputFolder, GDB + '.gdb')):  ## See if this geodatabase already exists

            try:
                ## If the gdb doesn't already exist, create new geodatabase for that state
                arcpy.CreateFileGDB_management(out_folder_path=outputFolder, \
                                               out_name=GDB, out_version="CURRENT")
                print "GDB created."

            except:
                print ("Error creating GDB for %s." % state_name)

        else:
            print ("Geodatabase already exists for %s." % state_name)


def walk_folder(folderLocation):
    walk = arcpy.da.Walk(folderLocation, type="Point")

    walkList = []   # This will hold all of the file paths to the files within the folder

    for dirpath, dirnames, filenames in walk:
        for filename in filenames:
            if filename[:7] == 'Batch_' and 'ModelGDB' not in dirpath and 'TestGDB' not in dirpath:
                walkList.append(os.path.join(dirpath, filename))

    return walkList


def transfer_to_GDB(target_file, output_GDB):
    file_name = os.path.basename(target_file)

    if arcpy.Exists(os.path.join(output_GDB, file_name)):
        print file_name, "already exists."
        return
    else:
        arcpy.FeatureClassToFeatureClass_conversion(in_features=batch_file, out_path=output_GDB, out_name=file_name)
        print "Copied:", file_name


if __name__ == '__main__':
    create_state_GDBs(results_folder, states2do)

    all_batch_files = walk_folder(batch_files_location)
    for batch_file in all_batch_files:
        batch_name = os.path.basename(batch_file)
        state_abbrev = batch_name[6:9]
        state_name = state_abbrev_to_name[state_abbrev]
        state_GDB = os.path.join(results_folder, state_name + '.gdb')
        transfer_to_GDB(batch_file, output_GDB)

    print "Total Batch files:", len(all_batch_files)
    print "~~~~~~~~~~~~SCRIPT COMPLETED~~~~~~~~~~~~"
