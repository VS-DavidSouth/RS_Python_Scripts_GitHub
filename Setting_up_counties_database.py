##
## Current Version: 4/9/18
##
## Setting_up_counties_database.py
##
## Authors: David South and Susan Maroney
##
## Code based on Python v2.7, the version that is installed with ArcGIS 10.5
##
## Purpose:
##
##          This program is designed to set up a county database for Susan's remote sensing procedure
##          to detect large commercial poultry farms using resampled 2m resolution NAIP imagery.
##          This database is intended to contain a file geodatabase for the 48 contiguous US States.
##          Inside each geodatabase should be a polygon shapefile for each county, projected into the
##          appropriate UTM projection.
##
##          The files will be exported in the following format:
##          County Outlines Folder
##              Alabama.gdb
##                  AutaugaCoAL_outline.shp     # [county name]Co[State]_outline.shp
##                  BaldwinCoAL_outline.shp
##
##          In theory, this script should be able to be run independent of ArcGIS, but it should still
##          be run on a computer that has ArcGIS installed with an active license so that Arcpy will work.
##
## Inputs:
##
##          1. Shapefile containing all contiguous US counties, in US_Albers_Equal_Area_Conic projection
##          2. Shapefile with USA NAD regions
##
## Requirements:
##
##          ArcGIS 10.5 or later installed on the computer running the script (it may work with previous
##          versions but this is untested and a file location to store the database.
##


import arcpy, os, sys

# this next import gives us access to two dictionaries for converting state names to abbreviations and vice versa
sys.path.insert(0, r'O:\AI Modeling Coop Agreement 2017\David_working\Python') # it also gives us the nameFormat function which is very useful for name standardization
from Converting_state_names_and_abreviations import *

## SETUP:
##
##          If running this as a standalone script without ArcGIS open, ensure the following locations are
##          correct. If running this as a custom tool in ArcGIS, comment out these parameters and uncomment
##          all the lines with "arcpy.GetParametersAsText".
##

arcpy.env.OverwriteOutput = True # Overwrite results

databaseFolder = r'N:\Remote Sensing Projects\2016 Cooperative Agreement Poultry Barns\Documents\Deliverables\Library\CountyOutlines' # where you want the database to be placed
#databaseFolder = arcpy.GetParametersAsText(0)

UTM_file = r'O:\AI Modeling Coop Agreement 2017\David_working\Source Files\Source_files.gdb\World_UTM_Grid' # just to be safe, please copy the original dataset and move it to a new location and use that for the script
#UTM_file = arcpy.GetParameterAsText(1)

countiesFile = r'O:\AI Modeling Coop Agreement 2017\David_working\Source Files\Source_files.gdb\dtl_cnty' # just to be safe, please copy the original dataset and move it to a new location and use that for the script
#countiesFile = arcpy.GetParameterAsText(2)

centroidsFile = countiesFile + '_centroids' # By default the centroids version of the counties will be placed in the same folder as the countiesFile, change this if you want it in some other location

totalCounties = 3221 # This number is how many counties there are in the contiguous US

###########################################################################################
########### First, we have to define a dictionary for later use ###########################
###########################################################################################

centralMeridian = {10:'-123.0' , 11:'-117.0' , 12:'-111.0' , 13:'-105.0', \
                   14:'-99.0'  , 15:'-93.0'  , 16:'-87.0'  , 17:'-81.0' , \
                   18:'-75.0'  , 19:'-69.0',}
    ##
    ## Note: this dictionary is used to store the central meridian value for each UTM zone that
    ## the contiguous USA is within (UTM 10-19). This wil be referenced in the following line.
    ## This library is in the format of [UTM Zone]:[central meridian]. Values were found
    ## at this site: http://www.jaworski.ca/utmzones.htm
    ##

############################################################################################
####### Now that the dictionaries are out of the way, we can get to the actual code ########
############################################################################################

def nameFormat (name):
    ##
    ## Function description:
    ##      This function removes symbols that cause problems with file names.
    ##
    ## Input Variables:
    ##      name: the county name that you want to format
    ##
    ## Returns:
    ##      The name, with all the annoying symbols removed, as a string.
    ##
    
    output = name.replace(" ", "_").replace("'","").replace(".","").replace("-","_")

    return output
    
def create_state_GDBs (outputFolder):
    ##
    ## Function description: This function creates the file structure for storage of the individtual county files.
    ##      One geodatabase(GDB) is created for each contiguous state (and Washington D.C. which isn't technically a state).
    ##
    ## Input Variables:
    ##      outputFolder: the file location to put all the GDBs into
    ##
    ## Returns:
    ##      none
    ##
    
    GDBcount = 0
    
    ## Loop for each contiguous US state
    for state in state_name_to_abbrev:
        
            stateF = nameFormat(state) # The 'F' stands for Formatted
            
            ## Only run for the contiguous US
            if not (state == 'Hawaii') and not (state == 'Alaska'):

                print ("Creating geodatabase for %s..." %state)

                # Check to see if the gdb already exists                
                if (arcpy.Exists(os.path.join(outputFolder, stateF +'.gdb')) == False): ## See if this geodatabase already exists

                    try:
                        ## If the gdb doesn't already exist, create new geodatabase for that state
                        arcpy.CreateFileGDB_management(out_folder_path = outputFolder, out_name = stateF, out_version = "CURRENT")
                        
                    except:
                        print ("Error creating GDB for %s." %state)

                    print ("file structure " + str(int(round(float(GDBcount)/49*100))) + " percent complete.")

                else:
                    print ("Geodatabase already exists for %s." %state)

                GDBcount +=1 # Keep track of how many times this process was completed
                

def setupUTM ():
    ##
    ## Function Description:
    ##      Sets up the file which will be used in the decideUTM function. This file will be a
    ##      point shapefile containing all US counties centroids. They will have UTM information
    ##      attached which can be used later. Note: this may need to be done manually in ArcMap.
    ##
    ##  Input Variables:
    ##      None
    ##
    ##  Returns:
    ##      None
    ##

    ## Check if the centroids file already exists
    if arcpy.Exists(centroidsFile):
        arcpy.Delete_management(in_data = centriodsFile, data_type = "") #For some reason, sometimes the 'OverwriteOutput = True' setting doesn't work here, so this part of the code exists to delete any previously existing versions

    ## Convert the polygon shapefile containing the counties to points, which are placed at the centoid of each polygon
    arcpy.FeatureToPoint_management(in_features = countiesFile, out_feature_class = 'in_memory/temp_centroids', \
                                    point_location = "CENTROID") # This intermediate is saved in memory to make the program run quicker and because this file is updated in the next step and is no longer needed

    ## Add the UTM information to the point version of the counties by using the spatial join tool with the temporary centroids file
    arcpy.SpatialJoin_analysis(target_features = 'in_memory/temp_centroids', join_features = UTM_file, \
                               out_feature_class = centroidsFile, join_operation = "JOIN_ONE_TO_ONE", \
                               join_type="KEEP_ALL", field_mapping='NAME "NAME" true true false 32 Text 0 0 ,First,#,dtl_cnty_centroids,NAME,-1,-1;STATE_NAME "STATE_NAME" true true false 35 Text 0 0 ,First,#,dtl_cnty_centroids,STATE_NAME,-1,-1;STATE_FIPS "STATE_FIPS" true true false 2 Text 0 0 ,First,#,dtl_cnty_centroids,STATE_FIPS,-1,-1;CNTY_FIPS "CNTY_FIPS" true true false 3 Text 0 0 ,First,#,dtl_cnty_centroids,CNTY_FIPS,-1,-1;FIPS "FIPS" true true false 5 Text 0 0 ,First,#,dtl_cnty_centroids,FIPS,-1,-1;ZONE "ZONE" true true false 8 Double 0 0 ,First,#,World_UTM_Grid,ZONE,-1,-1;ROW_ "ROW_" true true false 1 Text 0 0 ,First,#,World_UTM_Grid,ROW_,-1,-1;WEST_VALUE "WEST_VALUE" true true false 4 Text 0 0 ,First,#,World_UTM_Grid,WEST_VALUE,-1,-1;CM_VALUE "CM_VALUE" true true false 5 Text 0 0 ,First,#,World_UTM_Grid,CM_VALUE,-1,-1;EAST_VALUE "EAST_VALUE" true true false 4 Text 0 0 ,First,#,World_UTM_Grid,EAST_VALUE,-1,-1;Shape_Length "Shape_Length" false true true 8 Double 0 0 ,First,#,World_UTM_Grid,Shape_Length,-1,-1;Shape_Area "Shape_Area" false true true 8 Double 0 0 ,First,#,World_UTM_Grid,Shape_Area,-1,-1', \
                               match_option = "INTERSECT", search_radius = "", distance_field_name = "")
                                    ## The long, confusing line of text for 'field_mapping'  basically just removes a bunch of fields in the counties file that aren't necessary or needed
    
    ## Delete the 'in_memory' temporary file because it is no longer needed
    arcpy.Delete_management(in_data = 'in_memory/temp_centroids', data_type = "")
        

def decideUTM (FIPScode):
    ##
    ## Function description:
    ##      This function decides what UTM zone the specified county is within. UTM is decided based
    ##      on which zone the centroid of the polygon is within.
    ##
    ## Input Variables:
    ##      FIPScode: The unique FIPS code of the county, as a STRING. This is
    ##                 because some of the FIPS codes start with a 0, which
    ##                 results in the number being interpreted as an octal number.
    ##                 This can be avoided by formatting it as a string.
    ##
    ## Returns:
    ##      UTM Zone for that county in the form of an integer    
    ##

    ## search through the centroid-UTM reference file until you find the correct county (based on the FIPS), then return the associated UTM code
    with arcpy.da.SearchCursor(centroidsFile, ['FIPS', 'ZONE',]) as counties_centroids:
        for county in counties_centroids:
            if str(county[0]) == str(FIPScode):
                return int(county[1]) # This will return the UTM zone in the form of an integer

def findField (featureClass, fieldName):
    ##
    ## Function description:
    ##      Decides if the field exists or not
    ##
    ## Input Variables:
    ##      featureClass: the feature class that you want to check the field from
    ##      fieldName: the field that you want to check whether it exists or not
    ##
    ## Returns:
    ##      boolean (True or False)
    ##

    fieldList = [field.name for field in arcpy.ListFields(featureClass)] # Creates a list of all fields in that feature class

    ## Checks if the fieldName is in the list that was just generated as fieldList
    if fieldName in fieldList:
        return True
    else:
        return False

def exportCounty (inputFile, outputLocation, countyName, stateName, FIPS):
    ##
    ## Function description:
    ##      This function will create one single-county file, derived from the inputFile.
    ##      They will be formatted as follows:
    ##          County Outlines Folder
    ##              Alabama.gdb
    ##                  AutaugaCoAL_outline.shp     # The general format is [county name]Co[State]_outline.shp
    ##                  BaldwinCoAL_outline.shp
    ##
    ##
    ## Input Variables:
    ##      inputFile: the shapefile that the county is exported from
    ##      outputLocation: the folder or geodatabase that the county is exported to
    ##      countyName: a string containing the name of the county
    ##      state: the name of the state that the county is within (Alabama, etc.)
    ##      FIPS: the unique FIPS code of the county, saved as a string
    ##
    ## Returns:
    ##      none
    ##

    OVERWRITE = True  ## CHANGE THIS TO 'False' IF YOU DON'T WANT FILES OVERWRITTEN
    
    ## Create SQL statement to isolate only that county
    FIPS_SQL = "FIPS = '%s'" %FIPS

    ## Decide UTM zone
    UTM = int(decideUTM(str(FIPS)))

    ## Decide the name for the output file
    countyFileName = nameFormat(countyName) + "Co" + nameFormat(state_name_to_abbrev[stateName]) + "_outline"
    countyFileNameUnprojected = countyFileName + '_unprojected'
    countyFileFull = os.path.join(outputLocation, countyFileName)

    if OVERWRITE == True:

        ## Set ArcGIS to overwrite geoprocessing outputs
        arcpy.env.OverwriteOutputs = True

        if arcpy.Exists(countyFileFull):
            arcpy.Delete_management(countyFileFull)
    
    ## Determine if the file already exists
    if not arcpy.Exists(countyFileFull):   
        
        ## If the file doesn't exist, export a single county from reference counties file.
        ## This line saves the intermediate in memory to make the program quicker
        arcpy.FeatureClassToFeatureClass_conversion(in_features = inputFile, out_path = 'in_memory', \
                                                    out_name = countyFileNameUnprojected, where_clause = FIPS_SQL, \
                                                    field_mapping = 'NAME "NAME" true true false 32 Text 0 0 ,First,#,dtl_cnty,NAME,-1,-1;STATE_NAME "STATE_NAME" true true false 35 Text 0 0 ,First,#,dtl_cnty,STATE_NAME,-1,-1;STATE_FIPS "STATE_FIPS" true true false 2 Text 0 0 ,First,#,dtl_cnty,STATE_FIPS,-1,-1;CNTY_FIPS "CNTY_FIPS" true true false 3 Text 0 0 ,First,#,dtl_cnty,CNTY_FIPS,-1,-1;FIPS "FIPS" true true false 5 Text 0 0 ,First,#,dtl_cnty,FIPS,-1,-1;SQMI "SQMI" true true false 8 Double 0 0 ,First,#,dtl_cnty,SQMI,-1,-1;Shape_Length "Shape_Length" false true true 8 Double 0 0 ,First,#,dtl_cnty,Shape_Length,-1,-1;Shape_Area "Shape_Area" false true true 8 Double 0 0 ,First,#,dtl_cnty,Shape_Area,-1,-1', config_keyword="")
                                                    # The above line for field_mapping is basically just to get rid of extra fields in the attribute table

        ## Project the newly created county shapefile to the appropriate UTM zone
        arcpy.Project_management(in_dataset = os.path.join('in_memory', countyFileNameUnprojected), \
                                 out_dataset = countyFileFull, \
                                 out_coor_system = "PROJCS['NAD_1983_UTM_Zone_%sN',GEOGCS['GCS_North_American_1983',DATUM['D_North_American_1983',SPHEROID['GRS_1980',6378137.0,298.257222101]],PRIMEM['Greenwich',0.0],UNIT['Degree',0.0174532925199433]],PROJECTION['Transverse_Mercator'],PARAMETER['False_Easting',500000.0],PARAMETER['False_Northing',0.0],PARAMETER['Central_Meridian',%s],PARAMETER['Scale_Factor',0.9996],PARAMETER['Latitude_Of_Origin',0.0],UNIT['Meter',1.0]]" %(UTM, centralMeridian[UTM]), \
                                 transform_method = "WGS_1984_(ITRF00)_To_NAD_1983", in_coor_system = "GEOGCS['GCS_WGS_1984',DATUM['D_WGS_1984',SPHEROID['WGS_1984',6378137.0,298.257223563]],PRIMEM['Greenwich',0.0],UNIT['Degree',0.0174532925199433]]", \
                                 preserve_shape = "NO_PRESERVE_SHAPE", max_deviation = "", vertical = "NO_VERTICAL")

        ## Delete the '_unprojected' file that is stored in memory because it is no longer needed
        arcpy.Delete_management(in_data = os.path.join('in_memory', countyFileNameUnprojected + '.shp'), data_type = "")

        ## Add UTM field
        arcpy.AddField_management(countyFileFull, 'UTM', 'TEXT')

        ## Fill newly created UTM field with the proper UTM
        with arcpy.da.UpdateCursor(countyFileFull, ['UTM']) as UTM_field:
            for row in UTM_field:
                row[0] = decideUTM(FIPS)
                UTM_field.updateRow(row)

        print (stateName + " " + countyName + " county shapefile exported to geodatabase.")

    else:
        print (stateName + " " + countyName + " county shapefile already exists.")

######### Running the script ###################

if __name__ == '__main__':

    ## Determine if you want to skip past some that have already been completed so that the code is faster
    skip = True
    startValue = 171 ## The OBJECTID value of the county that you want to start at, in the form of an integer
                     ##  Simply type county[3] into the shell after an error to determine hte correct startValue
                      
    #create_state_GDBs(databaseFolder) ## Uncomment to create the GDB file structure

    ## In case the UTM reference file is not created, this will create it
    #setupUTM() # Only use this if needed. It may need to be done manually in arcGIS, the function seems to be outputting empty fields or throwing up errors

    ## Count how many times this loop has run
    count = 0.

    ## This SQL statement will be used to only search through counties that exist within the contiguous US
    contigUS = "NOT STATE_NAME = 'Alaska' AND NOT STATE_NAME = 'Hawaii' AND NOT STATE_NAME = 'Puerto Rico'"

    ## To save time, if skip is specified, skip to the OBJECTID value indicated by startValue
    if (skip == True):
        contigUS += " AND OBJECTID >= %s" %startValue
        count = startValue - 1 # Note this doesn't take into account the fact that the counties not in the contiguous US are skipped already.
                               # This will result in the percentage complete value to be a bit over-estimated, and time left to be innacurate. 
        
    ## Loop for each county in the counties file
    with arcpy.da.SearchCursor(countiesFile, ['NAME', 'STATE_NAME', 'FIPS', 'OBJECTID'], where_clause = contigUS) as allCounties:
        for county in allCounties:
            
            countyName = county[0]
            stateName = county[1]
            GDB_name = stateName + '.gdb'
            GDB_location = os.path.join(databaseFolder,GDB_name)
            FIPS = str(county[2])
            
            exportCounty(countiesFile, GDB_location, \
                         countyName, stateName, FIPS)     # This is saying that it will use countiesFile as the source of the county files, it will place the new files in the state database folders,
                                                          # and will use the county name, state name, and FIPS code of each county.

            ## Keep track of how much time is remaining    
            try:
                count +=1
                percent = str(int(round(float(count)/totalCounties*100))) 
                remainingTime = str(round(float(totalCounties - count) * 13./3600. , 1)) 
                print ("    Program is " + percent + "% complete. ~" + remainingTime + " hours remaining.") # Using the 'skip' option, this will make these estimates somewhat innacurate
            except:
                ()

    print("****************************************************************")
    print("                            COMPLETED!")
    print("****************************************************************")
