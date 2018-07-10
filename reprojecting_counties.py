##
## reprojecting_counties.py
##
## Code based on python v2.7, the version that is installed with ArcGIS 10.5
##
## Purpose:
##
##          This program is designed to reproject the files that were outputted from the file
##          'Setting_up_counties_database.py' into the correct projection. This is because
##          the original script (which has now been fixed) outputted the counties into the
##          'NAD_1983_UTM_Zone_[UTM]' Projected Coordinate System, when they should have been
##          in the 'NAD_1983_UTM_Zone_[UTM]N' Projected Coordinate System (note the 'N' suffix).
##

from Setting_up_counties_database import *

contigUS = "NOT STATE_NAME = 'Alaska' AND NOT STATE_NAME = 'Hawaii' AND NOT STATE_NAME = 'Puerto Rico'"

## Determine if you want to skip past some that have already been completed so that the code is faster
skip = False
startValue = 1815 # The OBJECTID value of the county that you want to start at, in the form of an integer


## To save time, if skip is specified, skip to the OBJECTID value indicated by startValue
if (skip == True):
    contigUS += " AND OBJECTID >= %s" %startValue   

with arcpy.da.SearchCursor(centroidsFile, ['NAME', 'STATE_NAME', 'FIPS', 'OBJECTID', 'ZONE'], where_clause = contigUS) as allCounties:
    for county in allCounties:

        print("Starting %s county in %s..." %(county[0], county[1]))
        
        abbrev = us_state_abbrev[county[1]]

        UTM = int(county[4])

        originalFile = os.path.join(databaseFolder,county[1] + '.gdb', \
                                    nameFormat(county[0]) + 'Co' + abbrev + '_outline')

        reprojectedFile = originalFile + '_reproj'

        ## reproject the file
        if not arcpy.Exists(reprojectedFile):
            arcpy.Project_management(in_dataset = originalFile, \
                                     out_dataset = reprojectedFile, \
                                     out_coor_system = "PROJCS['NAD_1983_UTM_Zone_%sN',GEOGCS['GCS_North_American_1983',DATUM['D_North_American_1983',SPHEROID['GRS_1980',6378137.0,298.257222101]],PRIMEM['Greenwich',0.0],UNIT['Degree',0.0174532925199433]],PROJECTION['Transverse_Mercator'],PARAMETER['False_Easting',500000.0],PARAMETER['False_Northing',0.0],PARAMETER['Central_Meridian',%s],PARAMETER['Scale_Factor',0.9996],PARAMETER['Latitude_Of_Origin',0.0],UNIT['Meter',1.0]]" %(UTM, centralMeridian[float(UTM)]), \
                                     transform_method = "", in_coor_system = "PROJCS['NAD_1983_UTM_Zone_%s',GEOGCS['GCS_North_American_1983',DATUM['D_North_American_1983',SPHEROID['GRS_1980',6378137.0,298.257222101]],PRIMEM['Greenwich',0.0],UNIT['Degree',0.0174532925199433]],PROJECTION['Transverse_Mercator'],PARAMETER['False_Easting',500000.0],PARAMETER['False_Northing',0.0],PARAMETER['Central_Meridian',%s],PARAMETER['Scale_Factor',0.9996],PARAMETER['Latitude_Of_Origin',0.0],UNIT['Meter',1.0]]" %(UTM, centralMeridian[float(UTM)]), \
                                     preserve_shape = "NO_PRESERVE_SHAPE", max_deviation = "", vertical = "NO_VERTICAL")
        else:
            print("Reprojected file for %s already exists, skipping." %county[0])
            
        ## delete the original file
        arcpy.Delete_management(originalFile)
        
        ## rename the file to what it should be
        arcpy.Rename_management(in_data = reprojectedFile, out_data = originalFile, data_type = "FeatureClass")

        print(county[0] + " reprojected.")


        ### NOTE: The line below is only used if things were projected incorrectly.
        ###  The line below simply renames the projection, it does not reproject anyhting.
        #arcpy.DefineProjection_management(in_dataset = originalFile, \
        #                                  coor_system = "PROJCS['NAD_1983_UTM_Zone_%sN',GEOGCS['GCS_North_American_1983',DATUM['D_North_American_1983',SPHEROID['GRS_1980',6378137.0,298.257222101]],PRIMEM['Greenwich',0.0],UNIT['Degree',0.0174532925199433]],PROJECTION['Transverse_Mercator'],PARAMETER['False_Easting',500000.0],PARAMETER['False_Northing',0.0],PARAMETER['Central_Meridian',%s],PARAMETER['Scale_Factor',0.9996],PARAMETER['Latitude_Of_Origin',0.0],UNIT['Meter',1.0]]" %(UTM, centralMeridian[float(UTM)]))

print("****************************************************************")
print("                            COMPLETED!")
print("****************************************************************")
