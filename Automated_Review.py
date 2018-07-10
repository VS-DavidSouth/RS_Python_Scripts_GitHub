####################### Automated_Review.py #######################

############################
####### DESCRIPTION ########
############################

##
## Created by David South 7/9/18, updated N/A
##
## Script Description:
##
## This scirpt would be great to make an ArcGIS tool out of.
##
## Note: as the script stands now, save each individual step along the way
##  Have a boolean that allows you to save all steps, or not
##
## This script is designed to be used as a custom ArcGIS tool. Instructions
##  for setting it up in ArcGIS will be included. Reference this URL:
##  http://desktop.arcgis.com/en/arcmap/10.3/analyze/creating-tools/adding-a-script-tool.htm
##

############################
########## SETUP ###########
############################

import arcpy, os
arcpy.env.OverwriteOutput = True

from creating_TP_FN_FP_files import addRasterInfo, checkTime

# this next import gives us access to two dictionaries for converting state names to abbreviations and vice versa
sys.path.insert(0, r'O:\AI Modeling Coop Agreement 2017\David_working\Python') # it also gives us the nameFormat function which is very useful for name standardization
from Converting_state_names_and_abreviations import *

############################
######## PARAMETERS ########
############################

save_intermediates = True   # change to false if you don't care about the intermediate files

global intermed_list
intermed_list = []  # this will be filled later with the filepaths to all the intermediate
                    #  files, which may or may not be deleted depending on whether
                    #  save_intermediates is True or False
from resample_NAIP import first10counties
countyList = []
for county in first10counties:
    countyList.append([county, 'AL'])

############################
##### DEFINE FUNCTIONS #####
############################

def clip(input_feature, clip_files, output_location):
    outputName = "NAME"
    outputFilepath = os.path.join(output_location, outputName)
    arcpy.Clip_analysis(in_features = input_feature, \
                        clip_features = clip_files , \
                        out_feature_class = outputFilepath \
                        cluster_tolerance = "")
    intermed_list.append(input_feature)
    
def LAR(input_feature, L_threshold, AR_threshold):
    ##
    ## LAR stands for Length(L) and Aspect Ratio(AR)
    ##

    ## Add the AspRatio field
    arcpy.AddField_management(in_table = input_feature, \
                              field_name = "AspRatio", field_type = "SHORT", \
                              field_precision = "", field_scale = "", field_length = "", \
                              field_alias = "", field_is_nullable = "NULLABLE", \
                              field_is_required = "NON_REQUIRED", field_domain = "")

    ## Fill the AspRatio field that was just created
    arcpy.CalculateField_management(in_table = input_feature, \
                                    field = "AspRatio", \
                                    expression = "[Length]/[Width]", \
                                    expression_type = "VB", code_block = "")

    ## Delete features based on the Length and AspRatio fields

    ## Add the old file to the list of intermediate files
    intermed_list.append(input_feature)
    
def masking(variable1, variable2):
    ()

def probSurface(input_point_data, raster_dataset):
    ##
    ## This function exists to replace the Manual Review step of the regional
    ##  remote sensing procedure. It uses the FLAPS probability surface to
    ##  determine which points are True Positives (TP) or False Positives (FP).
    ##

    addRasterInfo(input_point_data, raster_dataset)
    
def collapsePoints(input_point_data, output_location):
    ##
    ## Note: This function changes the input data with the Integrate tool.
    ##
    
    ## Move points within 100m of each other all on top of each other at the centroid
    arcpy.Integrate_management(in_features = input_point_data, \
                               cluster_tolerance = "100 Meters")
    
    ## Collapse points that are on top of eachother to single points
    arcpy.CollectEvents_stats(Input_Incident_Features = input_point_data, \
                              Output_Weighted_Point_Feature_Class = output_locatoin)

    ## Add the old file to the list of intermediate files
    intermed_list.append(input_feature)

def project(input_feature, output_location):
    
    outputName = ''
    outputFilepath = os.path.join(output_location, outputName)
    
    ## Project file into WGS 1984 Geographic Coordinate System

    ## Add the old file to the list of intermediate files
    intermed_list.append(input_feature)
    
    ## Add coordinates
    arcpy.AddXY_management(in_features)


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
        else:
            print "error deleting the following file:\n" + intermed_file

if __name__ == '__main__':

    for county in countyList:
        countyName = county[0]
        stateAbbrev = county[1]
        stateName = state_abbrev_to_name[stateAbbrev]
        clip(input_feature, clip_files, output_location)
        #LAR(input_feature, L_threshold, AR_threshold)
        #masking()
        probSurface(input_point_data, raster_dataset)
        collapsePoints(input_point_data, output_location)
        project(input_feature)

        if save_intermediates == False:
            deleteIntermediates(intermed_list)
