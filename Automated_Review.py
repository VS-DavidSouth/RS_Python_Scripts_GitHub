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

import os, sys

import time
start_time = time.time()

import arcpy
arcpy.env.OverwriteOutput = True

from Creating_TP_FN_FP_files import addRasterInfo, checkTime
from Setting_up_counties_database import centralMeridian

# this next import gives us access to two dictionaries for converting state names to abbreviations and vice versa
sys.path.insert(0, r'O:\AI Modeling Coop Agreement 2017\David_working\Python') # it also gives us the nameFormat function which is very useful for name standardization
from Converting_state_names_and_abreviations import *


############################
#### NAMING CONVENTIONS ####
############################

## Names for all files created in this script will follow the the same format.
##
##      [prefix]_[ST]_Z[##]_c[#]_[CountyName].[ext]
##
## Some files will not have Z[##], c[#], or [CountyName].
##
##      [prefix] -> a unique identifier for each type of file
##      [ST] -> the state abbreviation
##      Z[##] -> the UTM zone number
##      c[#] -> the cluster number
##      [CountyName] -> the specific county name
##      [ext] -> the file extension
##

prefix_dict = {
    'NAIP': 'downloaded 1m resolution NAIP areal imagery',
    'NAIP2m': '2m resampled NAIP imagery',
    'Model': 'AFE file that is used to create the Batch files for a particular state',
    'ModelGDB': 'The file geodatabase that was used to create the Model for that state',
    'ModelMXD': 'The ArcMap MXD that was used to run Feature Analyst to create the Model',
    'BatchGDB': 'A file geodatabase that contains all the intermediate files for the creation of the Batch file',
    'BatchMXD': 'The ArcMap MXD file that was used to run Feature Analyst to create the Batch file',
    'Clip': 'Intermediate stage after creating Batch file, this is the Batch file clipped to the county',
    'LAR': 'TO BE DETERMINED',
    'Masked': 'TO BE DETERMINED',
    'ProbSurf': 'TO BE DETERMINED',
    'Integrate': 'TO BE DETERMINED',
    'CollectEvents': 'TO BE DETERMINED',
    'AutoReview': 'TO BE DETERMINED',
    }


############################
######## PARAMETERS ########
############################

save_intermediates = True   # change to false if you don't care about the intermediate files

                   
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
countyList = []
for county in first10counties:
    countyList.append([county, 'AL'])

## Location of probability surface raster
probSurfaceRaster = r'N:\FLAPS from Chris Burdett\Data\poultry_prob_surface\poultryMskNrm\poultryMskNrm.tif'

county_outline_folder = r'N:\Remote Sensing Projects\2016 Cooperative Agreement Poultry Barns\Documents\Deliverables\Library\CountyOutlines'

output_folder = r'R:\Nat_Hybrid_Poultry\Remote_Sensing\Feature_Analyst'

## Define the maximum and minimum Length(L) or AspRatio(AR) values
##  (which came from the Batch file). Any points outisde of these bounds
##  are deleted automatically. L values are in meters.
L_max_threshold = 800   # Fill this with 99999 if you don't want to delete based on max Length
L_min_threshold = 35    # Fill this with 0 if you don't want to delete based on min Length
AR_max_threshold = 10   # Fill this with 99999 if you don't want to delete based on max AspRatio
AR_min_threshold = 1.3  # Fill this with 0 if you don't want to delete based on min AspRatio
thresholds = [
              [L_max_threshold, L_min_threshold],   ## This section just makes it so that we don't need
              [AR_max_threshold, AR_min_threshold], ##  so many input parameters for the LAR function
             ]
############################
#### DEFINE FUNCTIONS #####
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


def FIPS_UTM(county_file):

    with arcpy.da.SearchCursor(county_file, ['FIPS', 'UTM',]) as cursor:
        for row in cursor:
            return cursor[0], cursor[1]


def add_FIPS_info(input_feature, state_abbrev, county_name):
    
    ## The following several lines are to check to see if the FIPS or FIPS2 fields exist
    fieldList = [field.name for field in arcpy.ListFields(input_feature)] # Creates a list of all fields in that feature class

    ## Checks if the fieldName is in the list that was just generated as fieldList
    if "FIPS" in fieldList or "FIPS2" in fieldList:
        print "File already has FIPS fields."
        
    else:
        state_name = nameFormat(state_abbrev_to_name[state_abbrev])
        
        ## Location of county folder:
        county_outline = os.path.join(county_outline_folder,
                                          state_name + '.gdb',
                                          county_name + 'Co' + state_abbrev + '_outline')

        FIPS, UTM = FIPS_UTM(county_outline)
        
        ## Add a new field to store FIPS information. This field will hold the FIPS but remove leading zeroes
        arcpy.AddField_management(in_table = input_feature, field_name = "FIPS", \
                                  field_type = "SHORT", field_precision = "", \
                                  field_scale = "", field_length = "", field_alias = "", \
                                  field_is_nullable = "NULLABLE", \
                                  field_is_required = "NON_REQUIRED", field_domain = "")

        ## Fill FIPS field with UTM info (DOES NOT FUNCTION PROPERLY)
        #arcpy.CalculateField_management(in_table = input_feature, field = "FIPS", \
        #                                expression = FIPS, \
        #                                expression_type = "PYTHON_9.3", )
        #                                #code_block = 'def fn(num):\n  if num <= %s:\n    return (1)\n  elif num > %s:\n    return (2)' %(collectEvents, collectEvents))

        ## Fill newly created UTM field with the proper UTM
        with arcpy.da.UpdateCursor(input_feature, ['FIPS']) as cursor_a:
            for row in cursor_a:
                row[0] = int(FIPS)
                cursor_a.updateRow(row)

        ## Add a second field to store FIPS information. This field will hold the
        ##  FIPS as a string and will NOT remove leading zeroes
        arcpy.AddField_management(in_table = input_feature, field_name = "FIPS2", \
                                  field_type = "TEXT", field_precision = "", \
                                  field_scale = "", field_length = "", field_alias = "", \
                                  field_is_nullable = "NULLABLE", \
                                  field_is_required = "NON_REQUIRED", field_domain = "")

        ## Fill FIPS field with UTM info
        #arcpy.CalculateField_management(in_table = input_feature, field = "FIPS2", \
         #                               expression = FIPS, \
          #                              expression_type = "PYTHON_9.3", )
           #                             #code_block = 'def fn(num):\n  if num <= %s:\n    return (1)\n  elif num > %s:\n    return (2)' %(collectEvents, collectEvents))

        ## Fill newly created UTM field with the proper UTM
        with arcpy.da.UpdateCursor(input_feature, ['FIPS2']) as cursor_b:
            for row in cursor_b:
                row[0] = str(FIPS)
                cursor_b.updateRow(row)


def clip(input_feature, clip_files, output_location, state_abbrev, county_name):

    ## Get rid of any weird characters in the county name
    county_name = nameFormat(county_name)
    
    ## Set up the name and lcation of the output 
    outputName = 'Clip_' + state_abbrev + '_' + county_name
    outputFilePath = os.path.join(output_location, outputName)

    ## Do the clip
    arcpy.Clip_analysis(in_features = input_feature, \
                        clip_features = clip_files, \
                        out_feature_class = outputFilePath, \
                        cluster_tolerance = "")

    add_FIPS_info(outputFilePath, state_abbrev, county_name)
                                    
    ## Add the old file to the list of intermediate files
    intermed_list.append(input_feature)

    return outputFilePath

    
def LAR(input_feature, thresholds, output_location, state_abbrev, county_name):
    ##
    ## LAR stands for Length(L) and Aspect Ratio(AR). This function
    ##  deletes points that do not conform with L or AR thresholds.
    ##

    L_max_threshold =  thresholds [0][0]
    L_min_threshold =  thresholds [0][1]
    AR_max_threshold = thresholds [1][0]
    AR_min_threshold = thresholds [1][1]

    #outputName = 'LAR' + '_' + state_abbrev + '_' + county_name
    outputName = 'LAR' + '_' + state_abbrev + '_' + county_name + '_LAR' # DELETE THIS WHEN NO LONGER TESTING LENGTH
    outputFilePath = os.path.join(output_location, outputName)

    arcpy.CopyFeatures_management (input_feature, outputFilePath)

    ## Add the AspRatio field
    arcpy.AddField_management(in_table = outputFilePath, \
                              field_name = "AspRatio", field_type = "FLOAT", \
                              field_precision = "", field_scale = "", field_length = "", \
                              field_alias = "", field_is_nullable = "NULLABLE", \
                              field_is_required = "NON_REQUIRED", field_domain = "")

    ## Fill the AspRatio field that was just created
    arcpy.CalculateField_management(in_table = outputFilePath, \
                                    field = "AspRatio", \
                                    expression = "!Length!/!Width!", \
                                    expression_type = "PYTHON_9.3", code_block = "")

    ## Delete features based on the Length and AspRatio fields
    with arcpy.da.UpdateCursor(outputFilePath, ["Length", "AspRatio",]) as deleteCursor:
        for row in deleteCursor:
            if row[0] > L_max_threshold or row[0] < L_min_threshold:
                deleteCursor.deleteRow()
            elif row[1] > AR_max_threshold or row[1] < AR_min_threshold:
                deleteCursor.deleteRow()

    ## Add the old file to the list of intermediate files
    intermed_list.append(input_feature)

    return outputFilePath

    
def masking(variable1, variable2, state_abbrev, county_name):
    
    county_name = nameFormat(county_name)
    ()

def probSurface(input_point_data, raster_dataset, output_location, state_abbrev, county_name):
    ##
    ## This function exists to replace the Manual Review step of the regional
    ##  remote sensing procedure. It uses the FLAPS probability surface to
    ##  determine which points are True Positives (TP) or False Positives (FP).
    ##

    county_name = nameFormat(county_name)

    threshold = 0.15

    #outputName = 'ProbSurf_' + state_abbrev + '_' + county_name
    outputName = 'ProbSurf_' + state_abbrev + '_' + county_name + '_LAR' # DELETE THIS WHEN NO LONGER TESTING LENGTH
    outputFilePath = os.path.join(output_location, outputName)

    arcpy.CopyFeatures_management (input_point_data, outputFilePath)

    ## This next funciton comes from the creating_TF_FN_FP_files.py script
    addRasterInfo(outputFilePath, raster_dataset)

    ## Apply threshold - NOTE THIS WILL LIKELY BE CHANGED LATER
    with arcpy.da.UpdateCursor(outputFilePath, "ProbSurf_1") as cursor:
        for row in cursor:
            if row[0] < threshold:
                cursor.deleteRow()

    ## Add the old file to the list of intermediate files
    intermed_list.append(input_point_data)

    return outputFilePath

        
def collapsePoints(input_point_data, output_location, state_abbrev, county_name):
    ##
    ## Note: This function changes the input data with the Integrate tool.
    ##  input_point_data MUST HAVE NO SPACES OR SPECIAL CHARACTERS IN IT!
    ##

    county_name = nameFormat(county_name)
    state_name = nameFormat(state_abbrev_to_name[state_abbrev])

    ## Set up names and FilePaths for the Ingetrate and CollectEvents files
    #integrateOutputName = 'Integrate_' + state_abbrev + '_' + county_name
    integrateOutputName = 'Integrate_' + state_abbrev + '_' + county_name + '_LAR' # DELETE THIS WHEN NO LONGER TESTING LENGTH

    integrateOutputFilePath = os.path.join(output_location, integrateOutputName)
    #collectEventsOutputName = 'CollectEvents' + '_' + state_abbrev + '_' + county_name
    collectEventsOutputName = 'CollectEvents' + '_' + state_abbrev + '_' + county_name + '_LAR' # DELETE THIS WHEN NO LONGER TESTING LENGTH
    collectEventsOutputFilePath = os.path.join(output_location, collectEventsOutputName)

    if arcpy.Exists(integrateOutputFilePath):
        arcpy.Delete_management(integrateOutputFilePath)
        
    arcpy.CopyFeatures_management (input_point_data, integrateOutputFilePath)

    ## The input file path to the Integrate tool NEEDS to have no spaces in it, otherwise it will cause errors
    arcpy.Integrate_management(in_features = integrateOutputFilePath, cluster_tolerance = "100 Meters")

    ## Collapse points that are on top of eachother to single points
    arcpy.CollectEvents_stats(Input_Incident_Features = integrateOutputFilePath, \
                              Output_Weighted_Point_Feature_Class = collectEventsOutputFilePath)

    add_FIPS_info(collectEventsOutputFilePath, state_abbrev, county_name)

    ## Add the old file to the list of intermediate files
    intermed_list.append(input_point_data)
    intermed_list.append(integrateOutputFilePath)

    return collectEventsOutputFilePath


def project(input_data, output_location, state_abbrev, county_name, UTM_code):
    ##
    ## This function projects the input from the UTM county projection into
    ##  WGS 1984 Geographic Coordinate System
    ##

    county_name = nameFormat(county_name)

    #outputName = 'AutoReview_' + state_abbrev + '_' + county_name
    outputName = 'AutoReview_' + state_abbrev + '_' + county_name + '_LAR' # DELETE THIS WHEN NO LONGER TESTING LENGTH

    outputFilePath = os.path.join(output_location, outputName)

    meridian = centralMeridian[int(UTM_code)] ## centralMeridian is a dictionary found in Setting_up_counties_database.py
                                              ##  and specifies the central meridian for the projection
    
    ## Project file into WGS 1984 Geographic Coordinate System
    arcpy.Project_management(in_dataset = input_data, \
                             out_dataset = outputFilePath, \
                             out_coor_system = "GEOGCS['GCS_WGS_1984',DATUM['D_WGS_1984',SPHEROID['WGS_1984',6378137.0,298.257223563]],PRIMEM['Greenwich',0.0],UNIT['Degree',0.0174532925199433]]", \
                             transform_method = "WGS_1984_(ITRF00)_To_NAD_1983", \
                             in_coor_system = "PROJCS['NAD_1983_UTM_Zone_%sN',GEOGCS['GCS_North_American_1983',DATUM['D_North_American_1983',SPHEROID['GRS_1980',6378137.0,298.257222101]],PRIMEM['Greenwich',0.0],UNIT['Degree',0.0174532925199433]],PROJECTION['Transverse_Mercator'],PARAMETER['False_Easting',500000.0],PARAMETER['False_Northing',0.0],PARAMETER['Central_Meridian',%s],PARAMETER['Scale_Factor',0.9996],PARAMETER['Latitude_Of_Origin',0.0],UNIT['Meter',1.0]]" %(UTM, meridian), \
                             preserve_shape = "NO_PRESERVE_SHAPE", max_deviation="", \
                             vertical="NO_VERTICAL")
                        
    ## Add coordinates
    arcpy.AddXY_management(outputFilePath)

    ## Add the old file to the list of intermediate files
    intermed_list.append(input_data)

    return outputFilePath


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
        except:
            print "error deleting the following file:\n" + intermed_file


###########TESTING ---- REMOVE THIS LATER############
def testing():
    global county_name, state_abbrev, state_name, cluster, county_outline, FIPS, UTM, batchGDB, batchFile, batchLocation, errors, intermed_list
    county_name = 'Barbour'
    state_abbrev = 'AL'
    state_name = nameFormat(state_abbrev_to_name[state_abbrev])
    cluster = 1
    county_outline = os.path.join(county_outline_folder,
                                      state_name + '.gdb',
                                      county_name + 'Co' + state_abbrev + '_outline')
    FIPS, UTM = FIPS_UTM(county_outline)
    #batchGDB = 'BatchGDB_' + state_abbrev + '_Z' + str(UTM) + '_c' + str(cluster) + '.gdb'
    batchGDB = 'BatchGDB_' + state_abbrev + '_Z' + str(UTM) + '_c' + str(cluster) + '_test' + '.gdb' # DELETE THIS WHEN NO LONGER TESTING LENGTH
    batchGDB = os.path.join(output_folder, state_name, batchGDB)
    batchFile = 'Batch' + '_' + state_abbrev + '_' + county_name
    batchLocation = os.path.join(batchGDB, batchFile)
    errors = []
    intermed_list = []
    
if __name__ == '__main__':

    errors = []

    for county in countyList:

        ## Reset the file parameters, so that if there are errors they are not used again
        clipFile = larFile = maskFile = collapsePointsFile = autoReviewFile = ''

        intermed_list = []  # this will be filled later with the FilePaths to all the intermediate
                            #  files, which may or may not be deleted depending on whether
                            #  save_intermediates is True or False

        county_name = county[0]
        state_abbrev = county[1]
        state_name = nameFormat(state_abbrev_to_name[state_abbrev])
        cluster = 1 ##CHANGE THIS LATER
        county_outline = os.path.join(county_outline_folder,
                                      state_name + '.gdb',
                                      county_name + 'Co' + state_abbrev + '_outline')
        FIPS, UTM = FIPS_UTM(county_outline)
                
        #batchGDBname = 'BatchGDB_' + state_abbrev + '_Z' + str(UTM) + '_c' + str(cluster) + '.gdb'
        batchGDBname = 'BatchGDB_' + state_abbrev + '_Z' + str(UTM) + '_c' + str(cluster) + '_test' + '.gdb' # DELETE THIS WHEN NO LONGER TESTING LENGTH
        batchGDB = os.path.join(output_folder, state_name, batchGDBname)
    
        batchFile = 'Batch' + '_' + state_abbrev + '_' + county_name
        batchLocation = os.path.join(batchGDB, batchFile)

        print "Clipping", state_name, county_name + "..."
        try:
            clipFile = clip(batchLocation, county_outline, batchGDB, state_abbrev, county_name)
            print "Clipped. Script duration so far:", checkTime()
        except:
            e = sys.exc_info()[1]
            print(e.args[0])
            errors.append(['Clip', state_abbrev, county_name, e.args[0] ])

        print "Applying Length/AspRatio thresholds for", state_name, county_name + "..."              
        try:
            larFile = LAR(clipFile, thresholds, batchGDB, state_abbrev, county_name)
            print "LAR thresholds applied. Script duration so far:", checkTime()
        except:
            e = sys.exc_info()[1]
            print(e.args[0])
            errors.append(['LAR', state_abbrev, county_name, e.args[0] ])
            
        #masking()

        print "Applying probability surface for", state_name, county_name
        try:
            probSurfaceFile = probSurface(larFile, probSurfaceRaster, batchGDB, state_abbrev, county_name)
            print "Probability surface applied. Script duration so far:", checkTime()
        except:
            e = sys.exc_info()[1]
            print(e.args[0])
            errors.append(['ProbSurf', state_abbrev, county_name, e.args[0] ])

        print "Collapsing points for", state_name, county_name
        try:
            collapsePointsFile = collapsePoints(probSurfaceFile, batchGDB, state_abbrev, county_name)
            print "Points collapsed. Script duration so far:", checkTime()
        except:
            e = sys.exc_info()[1]
            print(e.args[0])
            errors.append(['Integrate or CollectEvents', state_abbrev, county_name, e.args[0] ])
                          
        print "Projecting Automated Review for", state_name, county_name
        try:
            autoReviewFile = project(collapsePointsFile, batchGDB, state_abbrev, county_name, UTM)
            print "Projected. Script duration so far:", checkTime()
        except:
            e = sys.exc_info()[1]
            print(e.args[0])
            errors.append(['AutoReview', state_abbrev, county_name, e.args[0] ])
            
        if save_intermediates == False:
            deleteIntermediates(intermed_list)

    if errors == []:
        print "\n\nNo counties had any errors!"
    else:
        print "\n\nThe following counties had errors:"
        for row in errors:
            print row[0], row[1], row[2]

    ############################
    ######### CLEANUP ##########
    ############################
    
    print "---------------------\nSCRIPT COMPLETE!"
    print "The script took a total of", checkTime() + "."
    print "---------------------"

