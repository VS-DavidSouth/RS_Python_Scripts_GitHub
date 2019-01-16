# Auto_Review_to_CSV.py

###########################
#    Description
###########################
# Created 1/16/2019 by David South
#
# This script is designed to take the output files from the Automated_Review
# script and combine them together into a single complete CSV file.
# If more information is required, try checking the documentation for and in the
# Automated_Review script itself.
#
# Inputs:
#       1. A series of ArcGIS point shapefiles or Feature Class files.
#           - These files should be named like:
#                AutoReview_[ST]_[County_Name], with [ST] = State Abbreviation and
#                [County_Name] = the name of the relevant county, formatted by  the
#                nameFormat() function (which can be found in the
#                `Converting_state_names_and_abreviations.py` script).
#           - The relevant fields that should be on each of the files are:
#             a. ICOUNT - The number of 'barns' that were collapsed to become that
#                particular premise point. This field is not high accuracy, but
#                could potentially still be useful.
#             b. FIPS / FIPS2 - FIPS codes without and with any leading
#                zeroes, respectively.
#             c. ProbSurf_1 / ProbSurf_2 - See documentation in `Automated_Review.py`.
#             d. Bin - The Bin number that this point was placed in, based on
#                the ProbSurf_1 value.
#             e. POINT_X / POINT_Y - NAD 1984 Coordinates.
#           - The files should be within folders or geodatabases whose names are
#             the corresponding State. It is assumed that there will be one state
#             godatabase per state (not multiple Californias, etc).
#
# Outputs:


###########################
#         SETUP
###########################
import os
import csv
import time
import arcpy
from Automated_Review import check_time
from Converting_state_names_and_abreviations import *

start_time = time.time()
arcpy.env.OverwriteOutput = True

###########################
#       PARAMETERS
###########################
auto_review_folder = ''

CSV_output_file_path = r''

###########################
#    DEFINE FUNCTIONS
###########################

def find_files(folder):
    """
    This function finds all the Auto_Review files in the target Geodatabase (GDB)
    and returns them in the form of a list. Each item in the list contains a sublist,
    made of [State abbreviation, county name, file path].
    """
    # walk_list will hold the file paths to the Batch files within the folder.
    walk_list = []

    walk = arcpy.da.Walk(folder, type="Point")

    for dirpath, dirnames, filenames in walk:
        for filename in filenames:
            if filename[:11] == 'AutoReview_':

                # Here, think about adding a section that selects for files with iterations

                county_name = filename[14:]
                path = os.path.join(dirpath, filename)
                walk_list.append([os.path.basename(path)[11:14]], county_name, path, )

    return walk_list

def write_row_to_CSV(CSV_file, row, overwrite=False):
    '''
    This function adds a single row to the specified CSV. It can also overwrite.
    :param CSV_file: The file path to the relevant CSV.
    :param row: The row that will be added to the CSV.
    :param overwrite: Boolean indicating whether the function should overwrite the existing
           data in the CSV or not.
    :return: None.
    '''

    if overwrite:
        # This just sets it so that it erases any data that was in the data previously.
        overwrite_code = 'wb'
    else:
        # This is set so that it doesn't change existing data, just adds rows.
        overwrite_code = 'ab'

    with open(CSV_file, overwrite_code) as g:
        writer = csv.writer(g, dialect='excel')
        writer.writerow(row)

    return

###########################
#       RUN CODE
###########################

# Set unique_ID to 0. This will go up with each new point.
unique_ID = 0

# Lets get this party started. Collect all the AutoReview file locations into a list.
# Each item contains a small list. To get state abbreviation - [0], county name - [1],
# and file path - [2].
auto_review_files = find_files(auto_review_folder)

# Overwrite the output CSV and write the first line.
write_row_to_CSV(CSV_output_file_path,
                 ['Unique_ID', 'State', 'County', 'FIPS',
                  'FIPS2',  'ICOUNT', 'ProbSurf_1', 'ProbSurf_2', 'Bin',
                  'POINT_X', 'POINT_Y'],
                 overwrite=True)

# Loop for each individual file.
for auto_review_file in auto_review_files:
    state_abbrev = auto_review_file[0]
    state_name = state_abbrev_to_name(state_abbrev)
    county_name = auto_review_file[1]

    # Loop for each individual row in each file
    with arcpy.da.SearchCursor(auto_review_file[2],
                               ['FIPS', 'FIPS2',  'ICOUNT', 'ProbSurf_1', 'ProbSurf_2', 'Bin',
                               'POINT_X', 'POINT_Y']) as cursor:
        for premise in cursor:
            new_row = [unique_ID, state_name, county_name] + premise
            write_row_to_CSV(CSV_output_file_path, row)

