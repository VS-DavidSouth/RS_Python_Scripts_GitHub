####################### Automated_Review.py #######################

############################
####### DESCRIPTION ########
############################

#
# Created by David South 7/9/18, updated 11/28/18
#
# Script Description:
#      This script is intended for use with remotely sensed poultry data
#      exported from the Feature Analyst extension in vector point form.
#      It is intended to be used to remove clutter from the input dataset
#      using various methods. It requires a probability surface raster,
#      as well as county polygon files for each county that will be
#      referenced during the course of the script.
#
# This script has untested functionality to be used as a custom ArcGIS Python tool.
# Instructions for setting it up in ArcGIS are included in the "if run_script_as_tool == True:"
# section.  Reference this URL:
# http://desktop.arcgis.com/en/arcmap/10.3/analyze/creating-tools/adding-a-script-tool.htm
#
# The Spatial Analyst ArcGIS extension is required for the prob_surface portion
# of this script.
#


############################
########## SETUP ###########
############################
import os
import sys
import csv
import time
import arcpy
import random
import numpy as np
from Converting_state_names_and_abreviations import *


start_time = time.time()
arcpy.env.OverwriteOutput = True


############################
######## PARAMETERS ########
############################

# The run_script_as_tool variable will overwrite any preset parameters by the
# ArcGIS tool inputs.  Note that this functionality is untested and may require
# some alterations.
run_script_as_tool = False
# Change save_intermediates to false if you don't care about the intermediate files.
save_intermediates = True
# Change track_completed_counties to false if you don't want the script
# to keep track of the completed counties by editing the specified CSV.
track_completed_counties = False

# Specify the location of the CSV file where the script will track which
# counties have been completed.  If no file is present at this location,
#  the script will create a new blank file and begin to fill it.
progress_tracking_file = r'R:\Nat_Hybrid_Poultry\Documents\trackingFileCSV.csv'

# clustersList is a very important parameter. The script will reference this to
# determine which folders to look for Batch files in, which will be used for
# the rest of the process. This parameter will be overwritten if
# run_script_as_tool = True.
cluster_list = [
    r'R:\Nat_Hybrid_Poultry\Results\Automated_Review_Results\Massachusetts.gdb'
    # counties that are having errors: Massachusetts through Mississipii
    ]
    
# Specify the location of probability surface raster and the threshold.
prob_surface_raster = r'N:\FLAPS from Chris Burdett\Data\poultry_prob_surface\poultryMskNrm\poultryMskNrm.tif'
prob_surface_threshold = 0.1   # Points with values < or = threshold will be deleted

# Specify the location of the folder that contains the county outline files.
county_outline_folder = r'N:\Remote Sensing Projects\2016 Cooperative Agreement Poultry Barns\Documents\Deliverables\Library\CountyOutlines'

# Specify the location of the adjusted NASS values CSV.  Make sure to double
# check that the read_adjFLAPS function to ensure it is reading the proper 
# column.
adjFLAPS_CSV = r'R:\Nat_Hybrid_Poultry\FLAPS\adjFLAPS_FINAL.csv'

# MASKING: It is important to define if the masks that will be used. If you
# don't want any masks, set either (or both) of these parameters = []. 
# The parameter neg_masks is where you would put feature classes which
# exclude any farm premises for being there. An example would be water bodies.
# The parameter pos_masks is the opposite; farms cannot be placed outside of
# these areas. An example would be private land polygons.
# Both neg_masks (negative masks) and pos_masks (positive masks) should be
#  formatted like this, with '~' representing the buffer distance in Meters:
#          neg_mask =[
#                     [r'C:\file_path\file', ~],
#                     [r'C:\alt_file_path\file2', ~],
#                    ]
# Note that buffer distance can be 0.
neg_masks = [
    [r'N:\Geo_data\ESRI_Data\ESRI_Base_Data_2014\usa\census\urban.gdb\urban', 0],
    [r'N:\Geo_data\ESRI_Data\ESRI_Base_Data_2012\usa\census\urban.sdc\urban', 0],
    [r'N:\Geo_data\ESRI_Data\ESRI_Base_Data_2012\streetmap_na\data\streets.sdc\streets', 20],
    [r'N:\Geo_data\ESRI_Data\ESRI_Base_Data_2014\usa\hydro\dtl_wat.gdb\dtl_wat', 0],
    [r'N:\Geo_data\ESRI_Data\ESRI_Base_Data_2014\usa\hydro\dtl_riv.gdb\dtl_riv', 10],
    # The following annotation shows the file added to the list for the states
    # WA, OR, or CA.  This can be verified by checking the DO STUFF section.
    # [r'R:\Nat_Hybrid_Poultry\Remote_Sensing\PADUS\PADUS1_4Shapefile\PADUS_WA_OR_CA_FED_STAT_LOC.shp, 0]
    ]
pos_masks = [
        
            ]

# Define the maximum and minimum Length(L) or Aspect Ratio(AR) values.
# Any points outside of these bounds are deleted automatically.
# L values are in meters. If you don't want to include a particular threshold,
# set equal to None.
L_max_threshold = 500
L_min_threshold = 50
AR_max_threshold = None
AR_min_threshold = None

# Define the maximum distance (in Meters) that two barns/points can be apart
# from each other to still be considered one barn. Anything at this distance
# or less will be moved to a centroid and combined into a single point.  The
# number of points collapsed this way will be saved in the ICOUNT field.
clust_tolerance = 100

# The ss_bins_matrix can be specified manually. See the simulated_sampling function
# for more documentation. Make sure this agrees with the prob_surface_threshold.
# If no matrix is specified, set ss_bins_matrix = 'default'.
ss_bins_matrix = 'default'

# Define num_iterations. Any number >1 will result multiple several iterations
# of the simulated_sampling and project functions, with a unique file for each.
# If a decimal is put in here, it will be rounded down.  This can be set to None.
num_iterations = 1

# Use skip_list to specify that certain counties, or steps for specific counties
# can be skipped to make processing faster. This is typically done when changes
# are made to later steps, but the previous steps don't need to be completed
# again. Note that this list is ignored if the output file doesn't exist.
# For example, you could use skip_list=[['MS', 'all_counties', 'all_steps'],]
# to skip over all MS counties that have been completed  but do the counties that
# don't have CollectEvents files or Project files, even though it isn't specified
# in skip_list itself.
skip_list = [
            # 1st column, put the state abbreviation in CAPS as a string,
            # or 'all_states'.
            # 2nd column, put county name as a string, or 'all_counties'.
            # 3rd column, put either 'Clip', 'Masking', 'LAR', 'ProbSurf',
            # 'CollectEvents', 'SimSampling', 'Project', or 'all_steps'.
            # The latter indicates that no geoprocesses should be done
            # for that file since it has already been completed.

            # Note: be sure to include commas after each line. Template:
            #       ['AL', 'all_counties', 'all_steps'],
            ['MA', 'all_counties', 'Clip'],
            ['MA', 'all_counties', 'Masking'],
            ['MA', 'all_counties', 'LAR'],
            ['MA', 'all_counties', 'ProbSurf'],
            ['MA', 'all_counties', 'CollectEvents'],
            ['MA', 'all_counties', 'SimSampling'],
            ]

# Overwrite certain parameters set above, if this tool is run as a custom
# ArcGIS Python tool. The input values will be determined by the user.
if run_script_as_tool == True:
    cluster_list = arcpy.GetParameterAsText(0)   # This should be in list format, but can contain a single entry
    prob_surface_threshold = arpy.GetParametersAsText(1) # Set default to 0.1
    negative_masks = arcpy.GetParameterAsText(2)       # Multivalue should be set to Yes and Type should be Optional
    negative_buffer_dist = arcpy.GetParameterAsText(3) # Multivalue should be set to Yes and Type should be Optional
    positive_masks = arcpy.GetParameterAsText(4)       # Multivalue should be set to Yes and Type should be Optional
    positive_buffer_dist = arcpy.GetParameterAsText(5) # Multivalue should be set to Yes and Type should be Optional
    L_max_threshold = arcpy.GetParameterAsText(6)   # Set default to None
    L_min_threshold = arcpy.GetParameterAsText(7)   # Set default to None
    AR_max_threshold = arcpy.GetParameterAsText(8)  # Set defualt to None
    AR_min_threshold = arcpy.GetParameterAsText(9)  # Set default to None
    save_intermediates = arcpy.GetParameterAsText(10)# Set default to True
    num_iterations = arcpy.GetParameterAsText(11)    # Set default to 1

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

# This section just makes it so that we don't need so many arguments
# for the LAR function.
LAR_thresholds = [
    [L_max_threshold, L_min_threshold],
    [AR_max_threshold, AR_min_threshold],
    ]


############################
#### DEFINE DICTIONARIES ###
############################

# NAMING CONVENTIONS:
# Names for all files created in this script will follow the the same format.
#
#      [prefix]_[ST]_Z[##]_c[#]_[County_Name].[ext]
#
# Some files will not have Z[##], c[#], or [County_Name].
#
#      [prefix] -> a unique identifier for each type of file, below is a
#                  dictionary explaining each prefix
#      [ST] -> the 2-letter state abbreviation
#      Z[##] -> the UTM zone number
#      c[#] -> the cluster number
#      [County_Name] -> the specific county name
#      [ext] -> the file extension
#

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
    'CollectEvents': 'The ProbSurf file with points within 100m of each other are moved on top of one another at the centroid and combined to a single point',
    'SimSampling': 'The CollectEvents file with points sorted into bins and many points removed to ensure each bin has the appropriate number of points, according to the Adjusted NASS values',
    'AutoReview': 'The final stage, which is the CollectEvents file but projected into NAD 1983 with coordinate fields added',
    }

# This next dictionary is used to store the central meridian value for each UTM
# zone that the contiguous USA is within (UTM 10-19).  This library is in the
# format of [UTM Zone]:[central meridian]. Values were originally found
# at this site: http://www.jaworski.ca/utmzones.htm
centralMeridian = {10: '-123.0', 11: '-117.0', 12: '-111.0', 13: '-105.0',
                   14: '-99.0',  15: '-93.0',  16: '-87.0',  17: '-81.0',
                   18: '-75.0',  19: '-69.0', }


############################
#### DEFINE FUNCTIONS ######
############################

#
# Note: when a function has several arguments, they should generally
# go in the following order (if a parameter is not needed, skip it):
#      (main_input_file, other_inputs, output_location, state_abbrev, \
#       county_name, {optional_parameters})
#

def check_time():
    """
    :return: This function returns a string of how many minutes or hours the script
    has run so far.
    """
    time_so_far = time.time() - start_time
    time_so_far /= 60.     # changes this from seconds to minutes
    
    if time_so_far < 60. :
        return str(int(round(time_so_far))) + " minutes"

    else:
        return str(round( time_so_far / 60. , 1)) + " hours"


def check_parameters():
    """
    This function is somewhat unpythonic, but it serves as a quick and simple
    way of ensuring minor errors like forgetting the [] around an entry in
    cluster_list won't cause strange errors that are confusing for users who
    have little to no experience in Python.  If parameter names change, be sure
    to change them in this function too!

    To disable this function, simply remove or comment out the following line
    in the if __name__=='__main__': section of the ccode:
           check_parameters()

    :return: None
    """
    should_be_files = [
        (prob_surface_raster, 'prob_surface_raster'),
        ]
    should_be_folder = [
        (county_outline_folder, 'county_outline_folder'),
        ]
    should_be_booleans = [
        (run_script_as_tool, 'run_script_as_tool'),
        (save_intermediates, 'save_intermediates'),
        (track_completed_counties, 'track_completed_counties'),
        ]
    should_be_lists = [
        (cluster_list, 'cluster_list'),
        (neg_masks, 'neg_masks'),
        (pos_masks, 'pos_masks'),
        (skip_list, 'skip_list'),
        ]
    should_be_list_of_lists = [
        (neg_masks, 'neg_masks'),
        (pos_masks, 'pos_masks'),
        (skip_list, 'skip_list'),
        ]
    should_be_number_or_None = [
        (prob_surface_threshold, 'prob_surface_threshold'),
        (L_max_threshold, 'L_max_threshold'),
        (L_min_threshold, 'L_min_threshold'),
        (AR_max_threshold, 'AR_max_threshold'),
        (AR_min_threshold, 'AR_min_threshold'),
        (num_iterations, 'num_iterations'),
        (clust_tolerance, 'clust_tolerance'),
        ]
    for thing in should_be_files:
        parameter = thing[0]
        param_name = thing[1]
        try:
            os.path.isfile(parameter)
        except Exception:
            raise TypeError(param_name + ' needs to be a file.')
    for thing in should_be_folder:
        parameter = thing[0]
        param_name = thing[1]
        try:
            os.path.isdir(parameter)
        except Exception:
            raise TypeError(param_name + ' needs to be a folder/directory.')
    for thing in should_be_booleans:
        parameter = thing[0]
        param_name = thing[1]
        if parameter is True or parameter is False:
            ()
        else:
            raise TypeError(param_name + ' needs to be a boolean, True or False.')
    for thing in should_be_lists:
        parameter = thing[0]
        param_name = thing[1]
        if not isinstance(parameter, list):
            raise TypeError(param_name + ' needs to be a list.')
    for thing in should_be_list_of_lists:
        parameter = thing[0]
        param_name = thing[1]
        for item in parameter:
            if not isinstance(item, list):
                raise TypeError(param_name + 'needs to be a list containing lists.')
    for thing in should_be_number_or_None:
        parameter = thing[0]
        param_name = thing[1]
        if parameter is not None:
            try:
                parameter + 1
            except Exception:
                raise TypeError(param_name + ' needs to be a number, either an integer or a float.')
    

def should_step_be_skipped(state_abbrev, county_name, step_name):
    """
    This function returns either True or False, based on whether
    the specified county is in skip_list.

    :param state_abbrev: Two-digit uppercase letter code of the relevant state as a string.
    :param county_name: The name of the relevant county as a string.
    :param step_name: The string key to the step to be skipped. See skip_list for documentation.
    :return: Boolean.
    """
    if skip_list == [] or skip_list == [[]]:
        return False
    else:
        for skip_item in skip_list:
            if skip_item[0].lower() == 'all_states' or skip_item[0] == state_abbrev:
                if skip_item[1] == 'all_counties' or nameFormat(skip_item[1]) == nameFormat(county_name):
                    if skip_item[2].lower() == 'all_steps' or skip_item[2].lower() == step_name.lower():
                        return True
    # If it isn't in the skip_list, just return false
    return False


def find_batch(cluster_GDB):
    """
    This function finds all the point files in the target GDB
    and returns them in the form of a list.

    :param cluster_GDB: A file path to a GDB or folder with point feature classes or shapefiles within.
    :return: A list of file paths of all point files within cluster_GDB.
    """
    # walk_list will hold the file paths to the Batch files within the folder.
    walk_list = []

    walk = arcpy.da.Walk(cluster_GDB, type="Point")

    for dirpath, dirnames, filenames in walk:
        for filename in filenames:
            if filename[:6] == 'Batch_':
                county_name = filename[9:]
                path = os.path.join(dirpath, filename)
                walk_list.append([county_name, path,os.path.basename(path)[6:8]])
    
    return walk_list


def find_FIPS_UTM(county_file):
    """
    This determines the appropriate UTM and FIPS code values for the county.
    WARNING: This script will return unicode, because some counties have FIPS
    codes starting with zero. Convert to int to remove the starting zero! Remember,
    in Python numbers starting with zero are converted, so:
        >>> 01031 == 537
        True

    :param county_file: File path to a feature class (or similar) ArcGIS file that contains all
    relevant counties and their UTM and FIPS information.
    :return: FIPS code as a string, UTM code as a string
    """
    with arcpy.da.SearchCursor(county_file, ['FIPS', 'UTM',]) as cursor:
        for row in cursor:
            return cursor[0], cursor[1]
        

def add_FIPS_info(input_feature, state_abbrev, county_name):
    """
    This function adds the FIPS value (from the find_FIPS_UTM function) to a given
    shapefile.

    :param input_feature: The file path to a feature class or shapefile.
    :param state_abbrev: Two-digit uppercase letter code of the relevant state as a string.
    :param county_name: The name of the relevant county as a string.
    :return: None
    """
    # The following several lines are to check to see if the FIPS or FIPS2
    # fields exist. First, creates a list of all fields in that feature class:
    field_list = [field.name for field in arcpy.ListFields(input_feature)]
    # Then check if the fieldName is in the list that was just created.
    if "FIPS" in field_list or "FIPS2" in field_list:
        print "File already has FIPS fields."

    else:
        state_name = nameFormat(state_abbrev_to_name[state_abbrev])

        # Location of county folder:
        county_outline = os.path.join(county_outline_folder,
                                          state_name + '.gdb',
                                          county_name + 'Co' + state_abbrev + '_outline')

        FIPS, UTM = find_FIPS_UTM(county_outline)

        # Add a new field to store FIPS information. This field will hold
        # the FIPS but remove leading zeroes.
        arcpy.AddField_management(in_table=input_feature, field_name="FIPS",
                                  field_type="LONG", field_precision="",
                                  field_scale="", field_length="", field_alias="",
                                  field_is_nullable="NULLABLE",
                                  field_is_required="NON_REQUIRED", field_domain="")

        # Fill FIPS field with UTM info (DOES NOT FUNCTION PROPERLY)
        #arcpy.CalculateField_management(in_table = input_feature, field = "FIPS", \
        #                                expression = FIPS, \
        #                                expression_type = "PYTHON_9.3", )
        #                                #code_block = 'def fn(num):\n  if num <= %s:\n    return (1)\n  elif num > %s:\n    return (2)' %(collectEvents, collectEvents))

        # Fill newly created FIPS field with the proper FIPS code.
        with arcpy.da.UpdateCursor(input_feature, ['FIPS']) as cursor_a:
            for row in cursor_a:
                row[0] = int(FIPS)
                cursor_a.updateRow(row)

        # Add a second field to store FIPS information. This field will hold the
        # FIPS as a string and will NOT remove leading zeroes.
        arcpy.AddField_management(in_table = input_feature, field_name = "FIPS2",
                                  field_type = "TEXT", field_precision = "",
                                  field_scale = "", field_length = "", field_alias = "",
                                  field_is_nullable = "NULLABLE",
                                  field_is_required = "NON_REQUIRED", field_domain = "")

        # Fill newly created FIPS2 field with the proper FIPS code.
        with arcpy.da.UpdateCursor(input_feature, ['FIPS2']) as cursor_b:
            for row in cursor_b:
                row[0] = str(FIPS)
                cursor_b.updateRow(row)


def clip(input_feature, clip_files, output_location, 
         state_abbrev, county_name):
    """
    This function clips the Batch file to the county outline. It also adds FIPS
    information.

    :param input_feature: The Batch point feature class.
    :param clip_files: A file path or list of file paths of feature classes to use
    to clip the Batch file. This should probably be the county outlien feature class.
    :param output_location: File path where the clipped file will be saved.
    :param state_abbrev: Two-digit uppercase letter code of the relevant state as a string.
    :param county_name: The name of the relevant county as a string.
    :return: The file path to the newly created clipped file.
    """
    # Get rid of any weird characters in the county name.
    county_name = nameFormat(county_name)
    
    # Set up the name and location of the output.
    output_name = 'Clip_' + state_abbrev + '_' + county_name
    output_file_path = os.path.join(output_location, output_name)

    if arcpy.Exists(output_file_path) == True:
        if should_step_be_skipped(state_abbrev, county_name, 'Clip') == True:
            print "Clip skipped."
            return output_file_path
        else:
            arcpy.Delete_management(output_file_path)

    # Do the clip.
    arcpy.Clip_analysis(in_features=input_feature,
                        clip_features=clip_files,
                        out_feature_class=output_file_path,
                        cluster_tolerance="")

    add_FIPS_info(output_file_path, state_abbrev, county_name)
                                    
    # Add the old file to the list of intermediate files.
    try:
        intermed_list.append(input_feature)
    finally:
        return output_file_path

    
def LAR(input_feature, output_location, LAR_thresholds,
        state_abbrev, county_name):
    """
    This function applies strict LAR thresholds, removing points from the
    input point feature class. LAR stands for Length(L) and Aspect Ratio(AR).
    This function deletes points that do not conform with L or AR thresholds.

    :param input_feature: Point feature class that was derived from the Batch file.
    :param output_location: File path where the LAR file will be saved.
    :param LAR_thresholds: A list of 4 parameters, likely given in the LAR_thresolds
    global variable.
    :param state_abbrev: Two-digit uppercase letter code of the relevant state as a string.
    :param county_name: The name of the relevant county as a string.
    :return: The file path to the newly created LAR file.
    """
    L_max_threshold =  LAR_thresholds [0][0]
    L_min_threshold =  LAR_thresholds [0][1]
    AR_max_threshold = LAR_thresholds [1][0]
    AR_min_threshold = LAR_thresholds [1][1]

    # Skip the LAR step if none of the thresholds are set to anything.
    if all((L_max_threshold is None, L_min_threshold is None,
             AR_max_threshold is None, AR_min_threshold is None,)):
        return input_feature

    # Get rid of any weird characters in the county name.
    county_name = nameFormat(county_name)

    output_name = 'LAR' + '_' + state_abbrev + '_' + county_name
    output_file_path = os.path.join(output_location, output_name)

    if arcpy.Exists(output_file_path) == True:
        if should_step_be_skipped(state_abbrev, county_name, 'LAR') == True:
            print "LAR skipped."
            return output_file_path
        else:
            arcpy.Delete_management(output_file_path)

    arcpy.CopyFeatures_management (input_feature, output_file_path)

    # Add the AspRatio field.
    arcpy.AddField_management(in_table=output_file_path,
                              field_name="AspRatio", field_type="FLOAT",
                              field_precision="", field_scale="", field_length="",
                              field_alias="", field_is_nullable="NULLABLE",
                              field_is_required="NON_REQUIRED", field_domain="")

    # Fill the AspRatio field that was just created.
    arcpy.CalculateField_management(in_table = output_file_path, 
                                    field = "AspRatio", 
                                    expression = "!Length!/!Width!", 
                                    expression_type = "PYTHON_9.3", code_block = "")

    # Delete features based on the Length and AspRatio fields.
    with arcpy.da.UpdateCursor(output_file_path, ["Length", "AspRatio",]) as delete_cursor:
        for row in delete_cursor:
            if L_max_threshold is not None:
                if row[0] > L_max_threshold:
                    delete_cursor.deleteRow()
            elif L_min_threshold is not None:
                if row[0] < L_min_threshold:
                    delete_cursor.deleteRow()
            if AR_max_threshold is not None:
                if row[1] > L_max_threshold:
                    delete_cursor.deleteRow()
            elif AR_min_threshold is not None:
                if row[1] < L_min_threshold:
                    delete_cursor.deleteRow()

    # Add the old file to the list of intermediate files.
    try:
        intermed_list.append(input_feature)
    finally:
        return output_file_path

    
def masking(input_feature, output_location, state_abbrev, county_name,
            county_outline, neg_masks=[], pos_masks=[]):
    """
    This function uses the Erase tool to remove any points with a set
    distance of the files in the neg_masks list.  It also uses the Clip
    ArcGIS tool (NOT the same as the clip(...) function in this script)
    to remove any points that are NOT within a set distance of files in
    the pos_masks list.

    Both neg_masks (negative masks) and pos_masks (positive masks) should
    look similar to this, with # representing the buffer distance in Meters:
          [[r'C:\file_path\file', #],
           [r'C:\alt_file_path\file2', #]]

    :param input_feature: Point feature class that was derived from the Batch file.
    :param output_location: The file path where the masking output will be saved.
    :param state_abbrev: Two-digit uppercase letter code of the relevant state as a string.
    :param county_name: The relevant county name as a string.
    :param county_outline: The file path to the county outline feature class, used to clip the masks.
    :param neg_masks: The file path and buffer distance in Meters for that mask. See above for formatting.
    :param pos_masks: The file path and buffer distance in Meters for that mask. See above for formatting.
    :return: The file path to the newly created masked point feature class.
    """
    # If both neg_masks and pos_masks are default (empty), then simply pass
    # the input_feature out of the function.
    if neg_masks == [] and pos_masks == []:
        return input_feature
    
    county_name = nameFormat(county_name)
    output_name = 'Masking' + '_' + state_abbrev + '_' + county_name
    output_file_path = os.path.join(output_location, output_name)

    if arcpy.Exists(output_file_path) == True:
        if should_step_be_skipped(state_abbrev, county_name, 'Masking') == True:
            print "Masking skipped."
            return output_file_path
        else:
            arcpy.Delete_management(output_file_path)

    def clip_buffer(mask, temp_location, county_outline):
        """
        This function is a small thing to clip the mask file to the county
        to chop it into a manageable size. The file is buffered if required.
        This function is used for each mask. This mini-function is NOT for
        clipping or erasing the point file input data and only deals with
        mask files themselves.

        :param mask: A single element from either neg_masks or pos_masks, in the form of a list with a
        file path and a integer (or similar number) buffer distance.
        :param temp_location: File path to place the temprorary clipped mask file.
        :param county_outline: The file path to the relevant county feature class file.
        :return: The file path to the newly created clipped and buffered mask file.
        """
        # This is where the temporary clipped file will be stored.
        clip_temp = os.path.join(temp_location, 'clipped_mask_temp')

        if arcpy.Exists(clip_temp):
            arcpy.Delete_management(clip_temp)

        # Create a temporary clipped file of the mask.
        arcpy.Clip_analysis(in_features=mask[0],
                            clip_features=county_outline,
                            out_feature_class=clip_temp,
                            cluster_tolerance="")

        # This is where the temporary buffer file will be stored.
        buff_temp = os.path.join(temp_location, 'buffer_mask_temp')

        if mask[1] > 0:
            # If there is a buffer value specified:
            # Create a temporary buffer around the clipped file, but only if the buffer distance is >0
            arcpy.Buffer_analysis(in_features=clip_temp,
                                  out_feature_class=buff_temp,
                                  buffer_distance_or_field='%s Meters' % mask[1],
                                  )
            arcpy.Delete_management(clip_temp)
            
        else:
            # Otherwise just use the un-buffered file.
            buff_temp = clip_temp

        return buff_temp

    # This 'file_to_remove_points_from' variable is going to be changed throughout
    # this function. It starts as the input feature, then will changed to
    # be set as the current temporary file that is created during the process.
    # This ensures that each time that points are removed, they are removed
    # from the most recent version of the file so that the end result will
    # be the cumulative result of all the masks at once. Note the original file
    # will not be modified, new temporary files will be made every step.
    file_to_remove_points_from = input_feature

    for mask_type in ('neg', 'pos'):  # Do this whole thing for both positive and negative masks
        count = 0  # Start the count, this will be used to name temporary files
        current_file = ''

        if mask_type == 'neg':
            mask_list = neg_masks
        elif mask_type == 'pos':
            mask_list = pos_masks
        
        if not mask_list == []:
            for mask in mask_list:
                count += 1
                temp_mask_file = clip_buffer(mask, 'in_memory', county_outline)

                if count == len(neg_masks) + len(pos_masks):
                    # This is basically saying that if this is the final mask
                    # that needs to be applied, then don't make a temporary
                    # file, use the actual output file name.
                    current_file = output_file_path

                else:
                    current_file = os.path.join('in_memory',
                                               'temp_applied_mask_' + str(count))

                if arcpy.Exists(current_file):
                    # Sometimes when errors happen previous versions are
                    # left over and need to be deleted before the next time around.
                    arcpy.Delete_management(current_file)
                
                if mask_type == 'neg' and not neg_masks == []:
                    arcpy.Erase_analysis(in_features=file_to_remove_points_from,
                                         erase_features=temp_mask_file,
                                         out_feature_class=current_file)
                    
                elif mask_type == 'pos' and not pos_masks == []:
                    arcpy.Clip_analysis(in_features=file_to_remove_points_from,
                                        clip_features=temp_mask_file,
                                        out_feature_class=current_file)

                # Get rid of the temporary masking file, we don't need it.
                arcpy.Delete_management(temp_mask_file)

                if arcpy.Exists(current_file[:-1] + str(count - 1)):
                    # Does the previous version of 'current_file' still exist?
                    # If so, delete that piece of junk, it's outdated.
                    arcpy.Delete_management(current_file[:-1] + str(count - 1))

                # Set the loop to preform all further changes to the
                # temporary file that was used previously, so that all
                # the changes are present in a single file.
                file_to_remove_points_from = current_file

    # Add the old file to the list of intermediate files.
    try:
        intermed_list.append(input_feature)
    finally:
        return output_file_path


def add_raster_info(point_data_to_alter, raster_dataset,
                    field_name_1='ProbSurf_1', field_name_2='ProbSurf_2'):
    """
    This function extracts the values from the input raster
    raster and creates two new fields in the input feature class,
    called ProbSurf_1 and ProbSurf_2 respectively. ProbSurf_1 has
    no interpolation, ProbSurf_2 has bilinear interpolation.
    Note: THIS FUNCTION CHANGES THE INPUT FEATURE CLASS BY ADDING FIELDS.

    :param point_data_to_alter: File path to a feature class file.
    :param raster_dataset:  File path for the raster file in an ArcGIS format.
    :param field_name_1: Name of the field in the raster that data will be taken from, as a string.
    :param field_name_2: Name of the second field in the raster that data will be taken from, as a string.
    :return: None.
    """
    # Allow the script to access the Spatial Analyst ArcGIS extension.
    arcpy.CheckOutExtension("Spatial")
    
    arcpy.sa.ExtractMultiValuesToPoints(point_data_to_alter,
                                        [[raster_dataset, field_name_1]], "NONE")
    arcpy.sa.ExtractMultiValuesToPoints(point_data_to_alter,
                                        [[raster_dataset, field_name_2]], "BILINEAR")
    
    arcpy.CheckInExtension("Spatial") 


def prob_surface(input_point_data, raster_dataset, output_location,
                state_abbrev, county_name):
    """
    This function reduces false positives in the Batch file ("clutter") by
    removing points that exist at locations that are below the specified threshold
    on the probability surface raster from FLAPS.

    :param input_point_data: Point feature class that was derived from the Batch file.
    :param raster_dataset: File path to the probability surface raster from FLAPS.
    :param output_location: File path where output feature class will be saved.
    :param state_abbrev: Two-digit uppercase letter code of the relevant state as a string.
    :param county_name: The name of the relevant county as a string.
    :return: The file path to the newly created feature class.
    """
    county_name = nameFormat(county_name)

    output_name = 'ProbSurf_' + state_abbrev + '_' + county_name
    output_file_path = os.path.join(output_location, output_name)

    if arcpy.Exists(output_file_path) == True:
        if should_step_be_skipped(state_abbrev, county_name, 'ProbSurf') == True:
            print "ProbSurf skipped."
            return output_file_path
        else:
            arcpy.Delete_management(output_file_path)

    arcpy.CopyFeatures_management (input_point_data, output_file_path)

    # Call add_raster_info to add the probability surface information to the
    # input file.
    add_raster_info(output_file_path, raster_dataset)

    # Apply threshold.
    with arcpy.da.UpdateCursor(output_file_path, "ProbSurf_1") as cursor:
        for row in cursor:
            if row[0] <= prob_surface_threshold:
                cursor.deleteRow()

    # Add the old file to the list of intermediate files.
    try:
        intermed_list.append(input_point_data)
    finally:
        return output_file_path


def collapse_points(input_point_data, output_location, state_abbrev,
                   county_name):
    """
    This function creates a new file and uses the Integrate and CollectEvents
    ArcGIS tools to collapse input points within 100m of each other to
    single points.

    BEWARE - The Integrate tool is really finicky about the
    file paths having spaces in them. It will cause vague errors if there
    are spaces or special characters in the file paths. Don't put blank
    spaces in your file paths. Don't do it. Like that creepy child you keep
    seeing in your basement, it will come back to haunt you.
    If you get the error
        "ERROR 999999: Error executing function.
        Invalid Topology [Maximum tolerance exceeded.]"
    then be wary. Sometimes you can close programs, restart and try again and it works.

    :param input_point_data: Point feature class that was derived from the Batch file.
    :param output_location: The file path where the shiny new feature class will be saved.
    :param state_abbrev: Two-digit uppercase letter code of the relevant state as a string.
    :param county_name: The name of the relevant county as a string.
    :return:
    """
    # Get rid of any weird characters in the county name.
    county_name = nameFormat(county_name)
    state_name = nameFormat(state_abbrev_to_name[state_abbrev])

    # Set up name and FilePath for CollectEvents file.
    collectEventsOutputName = 'CollectEvents' + '_' + state_abbrev + '_' + county_name
    collectEventsOutputFilePath = os.path.join(output_location, collectEventsOutputName)

    # Check to see if it should skip. Otherwise delete existing files.
    if arcpy.Exists(collectEventsOutputFilePath) == True:
        if should_step_be_skipped(state_abbrev, county_name,
                               'CollectEvents') == True:
            print "collapse_points skipped."
            return collectEventsOutputFilePath
        else:
            arcpy.Delete_management(collectEventsOutputFilePath)

    tempIntegrateFile = os.path.join('in_memory', 'temp_integrate')
        
    arcpy.CopyFeatures_management (input_point_data, tempIntegrateFile)

    # The input file path to the Integrate tool NEEDS to have no spaces in it,
    # otherwise it will cause frustratingly vague errors.
    arcpy.Integrate_management(in_features=tempIntegrateFile, cluster_tolerance="%s Meters" %str(clust_tolerance) )

    # Collapse points that are on top of each other to single points.
    arcpy.CollectEvents_stats(Input_Incident_Features=tempIntegrateFile,
                              Output_Weighted_Point_Feature_Class=collectEventsOutputFilePath)

    arcpy.Delete_management(tempIntegrateFile)

    add_FIPS_info(collectEventsOutputFilePath, state_abbrev, county_name)

    # Add the old file to the list of intermediate files.
    try:
        intermed_list.append(input_point_data)
    finally:
        return collectEventsOutputFilePath


def simulated_sampling(input_point_data, raster_dataset, output_location, state_abbrev,
                      county_name, ss_bins='default', iteration=None, random_seed=None):
    """
    This function randomly forces the data into a probability distribution
    curve similar to the probability distribution found in the 'truth' data.
    It constructs several 'bins' which are based on the probSurf_1 fields
    of the input_point_data file, then deletes all but the specified number
    points from that bin. It is generally assumed that 'raster_dataset' used
    here is the same as was used for the prob_surface function.

    Note that this function assumes that prob_surface_threshold = 0.1 as default.
    If this isn't the case, be sure to specify a custom ss_bins matrix.
    
    :param input_point_data: Point feature class that was derived from the Batch file.
    :param raster_dataset: File path to a raster dataset in ArcGIS format.
    :param output_location: The file path that dictates where to save this marvelous output file.
    :param state_abbrev: Two-digit uppercase letter code of the relevant state as a string.
    :param county_name: The name of the relevant county as a string.
    :param ss_bins: An optional parameter that can be used to specify the probability matrix.
    See the `if ss_bins == 'default':` section below for more details and formatting.
    :param iteration: Optional parameter, either None or a number like a float or integer.
    This will be put in the file name.
    :param random_seed: Optional parameter, can be used to specify a random seed for repeatablility. Integer.
    :return: The output file path of the file that was recently outputed to that output file path.
    """
    # Get rid of any weird characters in the state and county name
    county_name = nameFormat(county_name)
    state_name = nameFormat(state_abbrev_to_name[state_abbrev])

    # This next part gets a little hairy. Basically it is just deleting
    # any previously run SimSampling outputs, for all iterations and for
    # runs that were done without iterations. It also deletes all
    # AutoReview iterations as well, while it's at it. It starts by
    # naming the output, then it might add on the iteration suffix if
    # the file is part of a series of iterations.

    output_name = 'SimSampling_' + state_abbrev + '_' + county_name
    output_file_path = os.path.join(output_location, output_name)

    if iteration is not None:
        # If an iteration is specified, put a label showing that in the name.
        # The 'i' stands for 'iteration'.
        output_name = 'SimSampling_' + state_abbrev + '_' + county_name + '_i' + str(iteration)
        output_file_path = os.path.join(output_location, output_name)

    if arcpy.Exists(output_file_path):
        if should_step_be_skipped(state_abbrev, county_name, 'SimSampling') == True:
            print "SimSampling skipped."
            return output_file_path
        else:
            arcpy.Delete_management(output_file_path)

    # Before doing the first iteration, delete all old SimSampling files for that county.
    # This is included to avoid errors of old versions floating around, for example
    # if you ran a county with num_iterations=10, changed parameters and ran it with
    # num_iterations=5, you would have i6-i10 still in the folder, which could be
    # confusing and cause mistakes.
    if iteration <= 1 or iteration == None:
        walk = arcpy.da.Walk(output_location, type="Point")
        for dirpath, dirnames, filenames in walk:
            for filename in filenames:
                if 'AutoReview' in filename or 'SimSampling' in filename:
                    if '_'+state_abbrev+'_' in filename and county_name in filename:
                        arcpy.Delete_management(os.path.join(dirpath, filename))
                        print 'deleted older file:', os.path.join(dirpath, filename)

    # Okay, now that we have either skipped this whole function or deleted
    # outdated iterations, now we can continue.
        
    # Create a new file with all points. This function will delete most of the
    # points later on.
    arcpy.CopyFeatures_management (input_point_data, output_file_path)

    # Since the collapse_points function has erased existing fields, we need to
    # re-add the ProbSurf_1 and ProbSurf_2 fields.
    add_raster_info(output_file_path, raster_dataset,
                  field_name_1='ProbSurf_1', field_name_2='ProbSurf_2')

    #                                      #
    ### SETUP TO READ FROM adjFLAPS FILE ###
    #                                      #
    def read_adjFLAPS(adjFLAPS_CSV):
        """
        This function reads the adjFLAPS_CSV file and returns the adjusted
        FLAPS value. This is used to determine how many total points should be
        selected during Simulated Sampling.
        :param adjFLAPS_CSV: File path to the csv file containing the adjFLAPS values.
        :return: The value from the CSV of the appropriate county as a string.
        """
        with open(adjFLAPS_CSV) as csv_file:
            reader = csv.reader(csv_file, delimiter=',')
            for row in reader:
                # If the row matches the state and county (once they have been
                # formatted and capitalized properly), save the adjFLAPS field
                # value as the adjFLAPS variable, which is returned out of the
                # function.
                #
                # BE SURE TO DOUBLE CHECK THAT IT IS READING THE RIGHT COLUMN!
                # This could cause many errors.

                # This finds the state name of the row, which is something like
                # 'Alabama\Barbour', but slices it so that we only get the 'Alabama'
                # part. Likewise for temp_county_name, but we get 'Barbour'.
                temp_state_name = row[1][:row[1].find('\\')]
                temp_county_name = row[1][row[1].find('\\')+1:]
                if nameFormat(temp_state_name).title() == state_name.title() \
                  and nameFormat(temp_county_name).title() == county_name.title():
                    adjFLAPS_value = row[6]
                    
                    return adjFLAPS_value

                # Devel note: In the future, it would be good to switch this so that
                # it uses FIPS codes throughout the script, not the county and
                # state (or state abbreviation) combo that the script uses currently.
                

    adjFLAPS = read_adjFLAPS(adjFLAPS_CSV)
    print "----Total number of points to select:", adjFLAPS

        
    #                #
    ### SETUP BINS ###
    #                #
    # Note that ss_bins stands for simulated sampling bins.
    if ss_bins == 'default' and prob_surface_threshold == 0.1:
        # Column 1 is the numeric label for each bin.
        # Columns 2 and 3 are the lower and upper values for that
        # particular bin, respectively.
        # Column 4 is the percentage of points that should be selected from
        # that bin.
        # Column 5 will be filled later with the number of points that should
        # actually be drawn from that bin.
        ss_bins = (
                  (1, 0.1, 0.2, 3.88),
                  (2, 0.2, 0.3, 7.69),
                  (3, 0.3, 0.4, 11.95),
                  (4, 0.4, 0.5, 19.64),
                  (5, 0.5, 0.6, 23.34),
                  (6, 0.6, 0.7, 20.09),
                  (7, 0.7, 0.8, 11.08),
                  (8, 0.8, 0.9, 2.23),
                  (9, 0.9, 1.0, 0.09),
                  )
    elif ss_bins == 'default' and not prob_surface_threshold == 0.1:
        raise Exception("Error: please provide ss_bins values that fit with a prob_surface_threshold of %s" %str(prob_surface_threshold) )

    # Change ss_bins to a numpy array.
    ss_bins = np.array(ss_bins)
    
    # Add column 5 to array, then fill it with the proper number of points to
    # draw from that bin, calculated as the column 3 percentage times adjFLAPS
    # total for that county. Start by filling it with meaningless zeros:
    ss_bins = np.insert(ss_bins, 4, np.zeros(len(ss_bins)), axis=1)
    for row in ss_bins:
        # Now actually fill column 5 with a rounded number of points to
        # draw from that bin.
        row[4] = round( float(row[3])/100. * float(adjFLAPS), 0)
        print '----' + str(int(row[0])),'points:', str(row[4])

    if not round(sum(ss_bins[:,3]),1) == 100.0:
        # If the percentages don't total to really close to 100%, raise hell.
        raise Exception("Error: please provide ss_bins values that total to 100 percent")

    # Add a new field to the input data to hold the bin information in.
    arcpy.AddField_management(in_table=output_file_path, field_name="Bin",
                              field_type="SHORT", field_precision="",
                              field_scale="", field_length="", field_alias="",
                              field_is_nullable="NULLABLE",
                              field_is_required="NON_REQUIRED", field_domain="")
    
    with arcpy.da.UpdateCursor(output_file_path, ['OBJECTID', 'ProbSurf_1', 'Bin',]) \
      as cursor:
        for row in cursor:
            ProbSurf_1 = row[1]
            
            for bin_thresholds in ss_bins:
                # Classify the point based on which of the bin max and min
                # categories that it fits within.
                if ProbSurf_1 > bin_thresholds[1] and ProbSurf_1 <= bin_thresholds[2]:
                    # Assign the Bin field based on what range the ProbSurf_1 field fits in.
                    row[2] = int(bin_thresholds[0])
                    cursor.updateRow(row)
                    break
                
    # If adjFLAPS is too low, don't do any deleting.
    if adjFLAPS <= int(arcpy.GetCount_management(input_point_data)[0]):
        print "Too few points to do Simulated Sampling. All points taken."
        
    # If adjFLAPS is greater than the number of points in the input data,
    # draw out points and the rest will be deleted without mercy!
    else:  
        #                           #                      
        ### DRAW POINTS FROM BINS ###
        #                           #
        # selected_points will be used to collect all the points that will be in
        # the output.
        selected_points = []
                    
        for specific_bin in ss_bins:
            # Create a list that contains the pool of points for that bin that we
            # will draw random points out of.
            pointsPool = []

            with arcpy.da.SearchCursor(output_file_path, ['OBJECTID', 'ProbSurf_1', 'Bin', ]) as cursor2:
                for row2 in cursor2:
                    # Check to see if the point matches the current bin label,
                    # if so, add it to pointsPool so it can be drawn out later.
                    if row2[2] == specific_bin[0]:
                        pointsPool.append(row2)
                        
            # Randomly select (from the pointsPool list) a number of points equal
            # to the value in the 5th column (index 4) of ss_bins.
            try:
                if random_seed is not None:
                    random.seed(random_seed)  # Note that random seed is untested in this script..
                # Draw out a bunch of points. Note that random.sample is sampling
                # without replacement, meaning that once a point is drawn, it
                # cannot be drawn out again. You will never get duplicates of the
                # same point.
                selected_points.append(random.sample(pointsPool, int(specific_bin[4])) )

            # If there are too few points in that pool, select them all instead of
            # taking some random points.
            except ValueError:
                print "Welp, guess we gotta take all the points for category", \
                    int(specific_bin[0])
                selected_points.append(pointsPool)

        # Create a list of just the OBJECTID values, which will be used to delete points.
        selected_OIDs = []
        for bn in selected_points:
            for pointInfo in bn:
                OID = pointInfo[0]
                selected_OIDs.append(OID)

        with arcpy.da.UpdateCursor(output_file_path,
                                   ['OBJECTID', 'ProbSurf_1', 'Bin', ] ) as cursor3:
            for row3 in cursor3:
                # Check to see if the OBJECTID is in the OBJECTID section of the
                # selected_points list, otherwise it gets deleted.
                if row3[0] not in selected_OIDs:
                        cursor3.deleteRow()
                
    #             #
    ### CLEANUP ###
    #             #
    try:
        intermed_list.append(input_point_data)
    finally:
        return output_file_path
    

def project(input_data, output_location, UTM_code, state_abbrev,
            county_name, custom_file_name=None, iteration=None):
    """
    This function projects the input from the UTM county projection into
    WGS 1984 Geographic Coordinate System.

    :param input_data: Point feature class that was derived from the Batch file.
    :param output_location: The file path  where the final output of this script will be saved.
    :param UTM_code: The UTM code, in string form, from the input coordinate system.
    :param state_abbrev: Two-digit uppercase letter code of the relevant state as a string.
    :param county_name: The name of the county as a string.
    :param iteration: None, or the iteration value, either as an integer or string.
    :param custom_file_name: None, or a custom file name. This should not include file path.
    :return: The output file path for the final resting place of this script, projected and pretty.
    """
    # Get rid of any weird characters in the county name.
    county_name = nameFormat(county_name)

    if iteration is None:
        output_name = 'AutoReview_' + state_abbrev + '_' + county_name
    elif custom_file_name is not None:
        output_name = custom_file_name
    else:
        output_name = 'AutoReview_' + state_abbrev + '_' + county_name + '_i' \
                     + str(iteration)
    output_file_path = os.path.join(output_location, output_name)

    if arcpy.Exists(output_file_path) == True:
        if should_step_be_skipped(state_abbrev, county_name, 'Project') == True:
            print "Project skipped."
            return output_file_path
        else:
            arcpy.Delete_management(output_file_path)
        
    meridian = centralMeridian[int(UTM_code)]

    # Project file into WGS 1984 Geographic Coordinate System. I know, this
    # looks terrible, especially out_coor_system and in_coor_system. But that
    # is just he way it's gotta be. Notice that at the end of in_coor_system's
    # ungodly long strings that a bit of code that switches out a number based
    # on the proper meridian value.
    arcpy.Project_management(in_dataset=input_data,
                             out_dataset=output_file_path,
                             out_coor_system="GEOGCS['GCS_WGS_1984',DATUM['D_WGS_1984',SPHEROID['WGS_1984',6378137.0,298.257223563]],PRIMEM['Greenwich',0.0],UNIT['Degree',0.0174532925199433]]",
                             transform_method="WGS_1984_(ITRF00)_To_NAD_1983",
                             in_coor_system="PROJCS['NAD_1983_UTM_Zone_%sN',GEOGCS['GCS_North_American_1983',DATUM['D_North_American_1983',SPHEROID['GRS_1980',6378137.0,298.257222101]],PRIMEM['Greenwich',0.0],UNIT['Degree',0.0174532925199433]],PROJECTION['Transverse_Mercator'],PARAMETER['False_Easting',500000.0],PARAMETER['False_Northing',0.0],PARAMETER['Central_Meridian',%s],PARAMETER['Scale_Factor',0.9996],PARAMETER['Latitude_Of_Origin',0.0],UNIT['Meter',1.0]]" %(UTM, meridian),
                             preserve_shape="NO_PRESERVE_SHAPE", max_deviation="",
                             vertical="NO_VERTICAL")
                        
    # Add coordinates to the file.
    arcpy.AddXY_management(output_file_path)

    # Add the old file to the list of intermediate files.
    try:
        intermed_list.append(input_data)
    finally:
        return output_file_path


def mark_county_as_completed(progress_tracking_file, state_abbrev,
                             county_name, iteration=None):
    """
    This function edits a CSV and can be used to keep track of which counties have been
    completed so far. It will create a new CSV if there isn't one at the
    progress_tracking_file location. This function is entirely optional.

    :param progress_tracking_file: File path to the csv file where the infomration will be stored.
    :param state_abbrev: Same as the last 400 state_abbrev arguments in other functions.
    :param county_name: This should be pretty self-explanatory at this point.
    :param iteration: Iteration number. Not super important.
    :return: None.
    """
    state_name = nameFormat(state_abbrev_to_name[state_abbrev])
    county_name = nameFormat(county_name)

    # time_value saved in case it is required in the future.
    time_value = str( int( round(time.time(), 0) ) )

    if iteration is None:
            iteration_value = None
    else:
            iteration_value = 'i' + str(iteration)
    
    with open(progress_tracking_file, 'ab') as g:
        writer = csv.writer(g, dialect='excel')
        writer.writerow([state_name, county_name, iteration_value])


def delete_intermediates(intermed_list):
    """
    This function is designed to be used in the other functions
    whenever they have any intermediate files. It will delete
    all files that are in list format in the intermed_list
    input. `intermed` is short for intermediate.

    :param intermed_list: A list of file paths which are doomed to be deleted and to android hell.
    :return: None.
    """
    for intermed_file in intermed_list:
        try:
            arcpy.Delete_management(intermed_file)
        except Exception:
            print "error deleting the following file:\n" + intermed_file


def clear_GDB(folder):
    """
    This function clears out all files with items in nope_list
    in their name. Do not use this function unless you are positive
    of what it is going to delete. Once you delete something, its gone.
    Or you have to pay thousands of dollars for data recovery, and it
    might not even work. Remember that. This function will not delete
    any `Batch` files.

    :param folder: The folder that you want to clear the outdated clutter from.
    :return: None.
    """
    print "\nClearing GDBs. This does not affect Batch files."

    # Any files with an item from this list in the name gets deleted.
    nope_list = ['AutoReview_', 'Clip_', 'CollectEvents_', 'Integrate_',
                 'Masking_', 'LAR_', 'ProbSurf_', 'SimSampling_',]
    walk = arcpy.da.Walk(folder, type="Point")
    for dirpath, dirnames, filenames in walk:
            for file_name in filenames:
                if any(nope_word in file_name for nope_word in nope_list):
                    print "Deleting:", file_name
                    arcpy.Delete_management(os.path.join(dirpath, file_name))


############################
######### DO STUFF #########
############################

if __name__ == '__main__':

    check_parameters()

    errors = []

    for cluster_GDB in cluster_list:

        batch_list = find_batch(cluster_GDB)

        for county_batch in batch_list:

            # Reset the file parameters, so that if there are errors they
            # are not used again.
            try:
                del clip_file, LAR_file, mask_file, collapse_points_file, sim_sampling_file, auto_review_file
            except Exception:()

            # This blank list will be filled with the FilePaths to all the
            # intermediate files, which may or may not be deleted depending on
            # whether save_intermediates is True or False.
            intermed_list = []

            state_abbrev = county_batch[2]
            state_name = nameFormat(state_abbrev_to_name[state_abbrev])

            county_name = county_batch[0]
            batch_location = county_batch[1]
            
            county_outline = os.path.join(county_outline_folder,
                                          state_name + '.gdb',
                                          county_name + 'Co' + state_abbrev + '_outline')
            FIPS, UTM = find_FIPS_UTM(county_outline)

            # Do some stuff that is unique to WA, OR and CA.
            state_land_mask = r'R:\Nat_Hybrid_Poultry\Remote_Sensing\PADUS\PADUS1_4Shapefile\PADUS_WA_OR_CA_FED_STAT_LOC.shp'
            if state_abbrev in ['WA', 'OR', 'CA']:
                if not [state_land_mask, 0] in neg_masks:
                    neg_masks += [[state_land_mask, 0]]
            else:
                if [state_land_mask, 0] in neg_masks:
                    neg_masks.remove([state_land_mask, 0])

            #          #
            # CLIPPING #
            #          #
            print "Clipping", state_name, county_name + "..."
            try:
                clip_file = clip(batch_location, county_outline, cluster_GDB,
                                 state_abbrev, county_name)
                print "Clipped. Script duration so far:", check_time()
            except Exception:
                e = sys.exc_info()[1]
                print(e.args[0])
                errors.append(['Clip', state_abbrev,
                               county_name, e.args[0]])
 
            #          #
            #  MASKING #
            #          #
            print "Applying Masks for", state_name, county_name + "..."
            if not (neg_masks == [] and pos_masks == []):
                try:
                    mask_file = masking(clip_file, cluster_GDB, state_abbrev,
                                        county_name, county_outline,
                                        neg_masks, pos_masks)
                    print "Mask applied. Script duration so far:", check_time()
                except Exception:
                    e = sys.exc_info()[1]
                    print(e.args[0])
                    errors.append(['Masking', state_abbrev,
                                   county_name, e.args[0]])
            else:
                print "No masking files selected."
                mask_file = clip_file  # This essentially just skips the masking step

            #          #
            #   LAR    #
            #          # 
            print "Applying Length/AspRatio thresholds for", \
                state_name, county_name + "..."
            try:
                LAR_file = LAR(mask_file, cluster_GDB, LAR_thresholds,
                               state_abbrev, county_name)
                print "LAR thresholds applied. Script duration so far:", check_time()
            except Exception:
                e = sys.exc_info()[1]
                print(e.args[0])
                errors.append(['LAR', state_abbrev,
                               county_name, e.args[0]])

            #           #
            #PROBSURFACE#
            #           #
            print "Applying probability surface threshold for", state_name, \
                county_name + "..."
            try:
                prob_surface_file = prob_surface(LAR_file, prob_surface_raster,
                                                cluster_GDB, state_abbrev,
                                                county_name)
                print "Probability surface threshold applied. " \
                      "Script duration so far:", check_time()
            except Exception:
                e = sys.exc_info()[1]
                print(e.args[0])
                errors.append(['ProbSurf', state_abbrev,
                               county_name, e.args[0]])

            #               #
            #COLLAPSE POINTS#
            #               #
            print "Collapsing points for", state_name, county_name + "..."
            try:
                collapse_points_file = collapse_points(prob_surface_file,
                                                       cluster_GDB, state_abbrev,
                                                       county_name)
                print "Points collapsed. Script duration so far:", check_time()
            except Exception:
                e = sys.exc_info()[1]
                print(e.args[0])
                errors.append(['Collapse Points', state_abbrev,
                               county_name, e.args[0]])

            # Note: this sets up a loop, running for each iteration.
            if num_iterations <=1 or num_iterations is None:
                # Set num_iterations to 1 to show that simulated sampling should be done
                # only once.
                num_iterations = 1

            for each_iteration in range(1, int(num_iterations)+1):
                # If we only are doing simulated sampling once, we should specify to the
                # function that it doesn't need to label things with '_i3', etc.
                if num_iterations == 1:
                    iteration_number = None
                else:
                    # If we are doing multiple iterations, label each one.
                    iteration_number = each_iteration

                #          #
                #SIMULATED #
                # SAMPLING #    
                #          #
                print "Preforming Simulated Sampling protocol for", state_name, \
                    county_name + "..."
                try:
                    sim_sampling_file = simulated_sampling(collapse_points_file,
                                                           prob_surface_raster,
                                                           cluster_GDB,
                                                           state_abbrev,
                                                           county_name,
                                                           ss_bins=ss_bins_matrix,
                                                           iteration=iteration_number)
                    print "Simulated Sampling completed. " \
                          "Script duration so far:", check_time()
                except Exception:
                    e = sys.exc_info()[1]
                    print(e.args[0])
                    errors.append(['SimSampling', state_abbrev,
                                   county_name, e.args[0]])
                    sim_sampling_file = ''

                #          #
                #PROJECTING#
                #          #                               
                print "Projecting Automated Review for", state_name, \
                      county_name + "..."
                try:
                    auto_review_file = project(sim_sampling_file, cluster_GDB,
                                               UTM, state_abbrev, county_name,
                                               iteration=iteration_number)
                    if track_completed_counties == True:
                        mark_county_as_completed(cluster_GDB,
                                                 progress_tracking_file,
                                                 state_abbrev,
                                                 county_name,
                                                 iteration=iteration_number)
                    print "Projected. Script duration so far:", check_time()
                except Exception:
                    e = sys.exc_info()[1]
                    print(e.args[0])
                    errors.append(['AutoReview', state_abbrev,
                                   county_name, e.args[0]])

            # Just before you go on to the next county, now is the time
            # to delete unwanted intermediate files.
            if save_intermediates == False:
                delete_intermediates(intermed_list)
                
            print ''  # This just prints a blank line between each county.


    ############################
    ######### CLEANUP ##########
    ############################
            
    # Once all clusters are done, print a readout:
    if errors == []:
        print "\n\nNo counties had any errors!"
    else:
        print "\n\nThe following counties had errors:"
        for row in errors:
            print row[0], row[1], row[2]
    
    print "---------------------\nSCRIPT COMPLETE!"
    print "The script took a total of", check_time() + "."
    print "---------------------"

