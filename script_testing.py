from Automated_Review import *
import numpy as np
import arcpy, os

#probSurfaceFile = r'R:\Nat_Hybrid_Poultry\Remote_Sensing\Feature_Analyst\Alabama\BatchGDB_AL_Z16_c1.gdb\ProbSurf_AL_Barbour'
probSurfaceFile = r'R:\Nat_Hybrid_Poultry\Remote_Sensing\Feature_Analyst\Alabama\TestGDB_AL_Z16_c1.gdb\ProbSurf_AL_Barbour'
intermed_list = []
#clusterGDB = r'R:\Nat_Hybrid_Poultry\Remote_Sensing\Feature_Analyst\Alabama\BatchGDB_AL_Z16_c1.gdb'
clusterGDB = r'R:\Nat_Hybrid_Poultry\Remote_Sensing\Feature_Analyst\Alabama\TestGDB_AL_Z16_c1.gdb'
state_abbrev = 'AL'
state_name = 'Alabama'
county_name = 'Barbour'
county_outline_folder = r'N:\Remote Sensing Projects\2016 Cooperative Agreement Poultry Barns\Documents\Deliverables\Library\CountyOutlines'
county_outline = os.path.join(county_outline_folder,
                                          state_name + '.gdb',
                                          county_name + 'Co' + state_abbrev + '_outline')

def run():
    global simSamplingFile
    simSamplingFile = simulatedSampling(probSurfaceFile, clusterGDB, state_abbrev, county_name, ssBins='default' )

output_location = clusterGDB
input_point_data = probSurfaceFile
ssBins = 'default'

## Get rid of any weird characters in the state and county name
county_name = nameFormat(county_name)
state_name = nameFormat(state_abbrev_to_name[state_abbrev])

outputName = 'SimSampling_' + state_abbrev + '_' + county_name
outputFilePath = os.path.join(output_location, outputName)

if arcpy.Exists(outputFilePath):
    arcpy.Delete_management(outputFilePath)

## Create a new file with all points. This function will delete most of the points later on.
arcpy.CopyFeatures_management (input_point_data, outputFilePath)

#                                     #
### SETUP TO READ FROM adjNASS file ###
#                                     #
def readAdjNASS(adjNASS_CSV):
    ##
    ## This funtion reads the adjNASS_CSV file and returns the adjusted NASS value.
    ##
    with open(adjNASS_CSV) as csvfile:
        reader = csv.reader(csvfile, delimiter=',')
        for row in reader:
            ## If the row matches the state and county, save the ptot_ALL field value
            ##  as adjNASS, the total number of poultry in the county.
            if row[1] == state_name.upper() and row[2] == county_name.upper():
                adjNASS = row[16]
                
                return adjNASS
            
            ## If there are no values in the 2nd or 3rd column, check the 12th column.
            elif row[1] == '' and row[2] == '':
                tempIndex = row[11].find('\\') ## Note that \\ is used instead of \, this is because \ has special meaning
                                               ##  in Python so you must use \\ to represent \. In this case, \ is the divider
                                               ##  between the state name and county name in column 12 (index 11) in the CSV.
                tempStateName = row[11][:tempIndex]
                tempCountyName = row[11][tempIndex+1:]  ## These two temp names are basically the value in column 12 (index 11)
                                                        ##  sliced with the \ as the dividing line.
                if tempStateName == state_name and tempCountyName == county_name:
                    adjNASS = row[16]
                    
                    tempIndex, tempStateName, tempCountyName = '' ## Reset the temp variables so you don't get them mixed up.

                    return adjNASS
                
adjNASS = readAdjNASS(adjNASS_CSV)

#                #
### SETUP BINS ###
#                #
## Note that ssBins stands for simulated sampling bins.
if ssBins == 'default' and prob_surface_threshold == 0.1:
    ssBins = ( ## Column 1 is the numeric label for each bin.
               ##  Columns 2 and 3 are the lower and upper values for
               ##  that particular bin, respectively. Column 4 is the
               ##  percentage of points that should be selected from
               ##  that bin. Column 5 will be filled later with the
               ##  number of points that should actually be drawn from that bin.
              (1, 0.1, 0.2, 3.88 ),
              (2, 0.2, 0.3, 7.69 ),
              (3, 0.3, 0.4, 11.95),
              (4, 0.4, 0.5, 19.64),
              (5, 0.5, 0.6, 23.34),
              (6, 0.6, 0.7, 20.09),
              (7, 0.7, 0.8, 11.08),
              (8, 0.8, 0.9, 2.23 ),
              (9, 0.9, 1.0, 0.09 ),
              )
elif ssBins == 'default' and not prob_surface_threshold == 0.1:
    raise Exception("Error: please provide ssBins values that fit with a prob_surface_threshold of %s" %str(prob_surface_threshold) )

## Change ssBins to a numpy array.
ssBins = np.array(ssBins)

## Add column 5 to array, then fill it with
##  the proper number of points to draw from that bin, calculated as
##  column 3 percentage times adjNASS total for that county.
ssBins = np.insert(ssBins, 4, np.zeros(len(ssBins)), axis=1) ## create column 4 (index 3) and fill it with meaningless zeros
for row in ssBins:
    ## Now actually fill column 5 with a rounded number of points to draw from that bin.
    row[4] = round( float(row[3])/100. * float(adjNASS), 0)

if not round(sum(ssBins[:,3]),1) == 100.0:
    ## If the percentages don't total to really close to 100%, raise hell
    raise Exception("Error: please provide ssBins values that total to 100 percent")


## Add a new field to the input data to hold the bin information in
arcpy.AddField_management(in_table = outputFilePath, field_name = "Bin", 
                      field_type = "SHORT", field_precision = "", 
                      field_scale = "", field_length = "", field_alias = "", 
                      field_is_nullable = "NULLABLE", 
                      field_is_required = "NON_REQUIRED", field_domain = "")

with arcpy.da.UpdateCursor(outputFilePath, ['OBJECTID', 'ProbSurf_1', 'Bin',]) as cursor:
    for row in cursor:
        ProbSurf_1 = row[1]
        
        for binThresholds in ssBins:
            ## Classify the point based on which of the bin max and min categories that it fits within
            if ProbSurf_1 > binThresholds[1] and ProbSurf_1 <= binThresholds[2]:
                ## Assign the Bin field based on what range the ProbSurf_1 field fits in.
                row[2] = int(binThresholds[0])
                cursor.updateRow(row)
                break
            
#                           #                      
### DRAW POINTS FROM BINS ###
#                           #
selectedPoints = [] ## This will be used to collect all the points that will be in the output.
            
for specificBin in ssBins:
    ## Create a list that contains the pool of points for that bin that we will draw random points out of
    pointsPool = []

    with arcpy.da.SearchCursor(outputFilePath, ['OBJECTID', 'ProbSurf_1', 'Bin',]) as cursor2:
        for row2 in cursor2:
            ## Check to see if the point matches the current bin label,
            ##  if so, add it to pointsPool so it can be drawn out later.
            if row2[2] == specificBin[0]:
                pointsPool.append(row2)
                
    ## Randomly select (from the pointsPool list) a number of points equal to the value in the
    ##  5th column (index 4) of ssBins.
    try:
        selectedPoints.append(random.sample(pointsPool, specificBin[4]) )
    ## If there are too few points in that pool, select them all instead of taking some random points.
    except ValueError:
        selectedPoints.append(pointsPool)

## Create a list of just the OBJECTID values, which will be used to delete points.
selectedOIDs = []
for bn in selectedPoints:
    for pointInfo in bn:
        OID = pointInfo[0]
        selectedOIDs.append(OID)

with arcpy.da.UpdateCursor(outputFilePath, ['OBJECTID', 'ProbSurf_1', 'Bin',]) as cursor3:
    for row3 in cursor3:
        ## Check to see if the OBJECTID is in the OBJECTID section of the
        ##  selectedPoints list, otherwise it gets deleted.
        if row3[0] not in selectedOIDs:
                cursor3.deleteRow()

print "Ready to test."
