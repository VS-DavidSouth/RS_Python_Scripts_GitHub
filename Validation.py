
####################### Validation.py #######################

############################
####### DESCRIPTION ########
############################

#
# Created by Grace Kuiper, 1/15/19
#
# Script Description:
#      This script will generate the layers and tables necessary for the hybrid model validation. There are
#      three primary methods for the validation: Buffer Capture, Grid Density, and Ellipse Overlap. 
#


########################################
##################SETUP#################
########################################

#            #             #           #
############Import Libraries############
#            #             #           #

import os
import sys
import csv
import arcpy

sys.path.insert(0, r'O:\AI Modeling Coop Agreement 2017\David_working\Remote_Sensing_Procedure\RS_Python_Scripts_GitHub')

from Automated_Review import find_FIPS_UTM

arcpy.env.OverwriteOutput = True

#            #             #           #
############Define Variables############
#            #             #           #

# Results will be saved to a folder titled "Validation_Results", which contains geodatabases called "AutoReviewCounties",
# "Dist_Between_Tables", "Buffers", "Buffer_Capture","Fishnets",and "Grid_Density" to hold layers with hybrid model points,
# near tables with distances between barns, ground truth buffers, spatial join outputs for hybrid model points in ground
# truth buffer zones, fishnet grids, and spatial join outputs for hybrid model points in fishnet grids, respectively. Also
# create a folder called "TP_FN_Counties" for shape files for ground truth points.

# Set up variables for file paths to the geodatabases and files in the "Validation_Results" folder, as well as the
# pathways to source data (hybrid model results, ground truth results, and the county outlines).

#########Change these Variables#########
State_Name = 'Louisiana'
State_Abbrev = 'LA'
County_Name = 'Claiborne'

##########Keep these Variables##########
Automated_Review_ResultsPath = r'R:\Nat_Hybrid_Poultry\Results\Automated_Review_Results/'
TP_FN_FPPath = r'O:\AI Modeling Coop Agreement 2017\David_working\Remote_Sensing_Procedure\TP_FN_FP.gdb/'
CountyOutlinesPath = r'N:\Remote Sensing Projects\2016 Cooperative Agreement Poultry Barns\Documents\Deliverables\Library\CountyOutlines/'

TP_FNPath = r'O:\AI Modeling Coop Agreement 2017\Grace Cap Stone Validation\Validation_Results\TP_FN_Counties/'
AutoReviewPath = r'O:\AI Modeling Coop Agreement 2017\Grace Cap Stone Validation\Validation_Results\AutoReviewCounties.gdb/'
NearTablePath = r'O:\AI Modeling Coop Agreement 2017\Grace Cap Stone Validation\Validation_Results\Dist_Between_Tables.gdb/'
BuffersPath = r'O:\AI Modeling Coop Agreement 2017\Grace Cap Stone Validation\Validation_Results\Buffers.gdb/'
Buffer_CapturePath = r'O:\AI Modeling Coop Agreement 2017\Grace Cap Stone Validation\Validation_Results\Buffer_Capture.gdb/'
FishnetsPath = r'O:\AI Modeling Coop Agreement 2017\Grace Cap Stone Validation\Validation_Results\Fishnets.gdb/'
Grid_DensityPath = r'O:\AI Modeling Coop Agreement 2017\Grace Cap Stone Validation\Validation_Results\Grid_Density.gdb/'
FLAPSPath = r'O:\AI Modeling Coop Agreement 2017\Grace Cap Stone Validation\Validation_Results\FLAPS.gdb/'
Cell_AssignmentsPath = r'O:\AI Modeling Coop Agreement 2017\Grace Cap Stone Validation\Validation_Results\Cell_Assignments.gdb/'
EllipsePath = r'O:\AI Modeling Coop Agreement 2017\Grace Cap Stone Validation\Validation_Results\Ellipse.gdb/'

#            #             #           #
#############Define Functions###########
#            #             #           #

def tableToCSV(Input_Table, Filepath):
    Field_List = arcpy.ListFields(Input_Table)
    Field_Names = [Field.name for Field in Field_List]
    with open(Filepath, 'wb') as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(Field_Names)
        with arcpy.da.SearchCursor(Input_Table, Field_Names) as cursor:
            for row in cursor:
                writer.writerow(row)
        print Filepath + " CREATED"
    csv_file.close()
    
#            #             #           #
#############Get Source Data############
#            #             #           #

# Pull ground truth points, hybrid model points, and county outlines from their sources.

County_Outline = County_Name + 'Co' + State_Abbrev + '_outline'
TP_FN_FP = State_Abbrev + '_' + County_Name + '_TP_FN_FP'
AutoReviewSource = 'AutoReview_' + State_Abbrev + '_' + County_Name
source_data_list = {CountyOutlinesPath + State_Name + '.gdb/' + County_Outline : County_Outline,\
                    TP_FN_FPPath + TP_FN_FP : TP_FN_FP,\
                    Automated_Review_ResultsPath + State_Name + '.gdb/' + AutoReviewSource : AutoReviewSource}

for source_data in source_data_list:
   arcpy.MakeFeatureLayer_management(source_data,source_data_list[source_data])

print("source layers created")

# Change the projection of the hybrid model layer to match that of the ground truth layer and save it
# as a new layer in the "AutoReviewCounties" geodatabase in the "Validation_Results" folder.
AutoReview = State_Abbrev + '_' + County_Name + '_AutoReview'

centralMeridian = {'10' : '-123.0', '11' : '-117.0', '12' : '-111.0', '13' : '-105.0',
                   '14' : '-99.0',  '15' : '-93.0',  '16' : '-87.0',  '17' : '-81.0',
                   '18' : '-75.0',  '19' : '-69.0', }
if arcpy.Exists(AutoReviewPath + AutoReview) == True:
   print ("projected AutoReview already exists")
else:
   FIPS, UTM = find_FIPS_UTM(CountyOutlinesPath + State_Name + '.gdb/' + County_Outline)
   arcpy.Project_management(AutoReviewSource,AutoReviewPath + AutoReview,\
                "PROJCS['NAD_1983_UTM_Zone_" + UTM + "N',\
                GEOGCS['GCS_North_American_1983',DATUM['D_North_American_1983',\
                SPHEROID['GRS_1980',6378137.0,298.257222101]],PRIMEM['Greenwich',0.0],\
                UNIT['Degree',0.0174532925199433]],PROJECTION['Transverse_Mercator'],\
                PARAMETER['False_Easting',500000.0],PARAMETER['False_Northing',0.0],\
                PARAMETER['Central_Meridian'," + centralMeridian[UTM] + "],PARAMETER['Scale_Factor',0.9996],\
                PARAMETER['Latitude_Of_Origin',0.0],UNIT['Meter',1.0]];17410.045707 4262033.695016 3906.249996;\
                0.000000 100000.000000;0.000000 100000.000000")
   print ("new AutoReview projection complete")
      
# Create FLAPS dataset for county from national model using select by location and the county
# outline layer.
FLAPS = State_Abbrev + '_' + County_Name + '_FLAPS'

poultry_list = ["Layers","Pullets","Turkeys","Broilers"]
for poultry_type in poultry_list:
   arcpy.MakeFeatureLayer_management(FLAPSPath + poultry_type, poultry_type)
   arcpy.SelectLayerByLocation_management(poultry_type,"COMPLETELY_WITHIN",County_Outline,"","NEW_SELECTION","")

if arcpy.Exists(FLAPSPath + FLAPS) == True:
   print ("new FLAPS layer already exists")
else:
   arcpy.Merge_management(poultry_list,FLAPSPath+FLAPS+'_pre_project',"")
   arcpy.Project_management(FLAPSPath + FLAPS + '_pre_project',FLAPSPath + FLAPS,\
                "PROJCS['NAD_1983_UTM_Zone_" + UTM + "N',\
                GEOGCS['GCS_North_American_1983',DATUM['D_North_American_1983',\
                SPHEROID['GRS_1980',6378137.0,298.257222101]],PRIMEM['Greenwich',0.0],\
                UNIT['Degree',0.0174532925199433]],PROJECTION['Transverse_Mercator'],\
                PARAMETER['False_Easting',500000.0],PARAMETER['False_Northing',0.0],\
                PARAMETER['Central_Meridian'," + centralMeridian[UTM] + "],PARAMETER['Scale_Factor',0.9996],\
                PARAMETER['Latitude_Of_Origin',0.0],UNIT['Meter',1.0]];17410.045707 4262033.695016 3906.249996;\
                0.000000 100000.000000;0.000000 100000.000000")
   print ("new FLAPS layer created")
      
# Select points from ground truth layer that are true positives or false negatives, then export them
# as a shape file into the "TP_FN_Counties" folder in the "Validation_Results" folder.
TP_FN = State_Abbrev + '_' + County_Name + '_TP_FN'

if arcpy.Exists(TP_FNPath+TP_FN+'.shp') == True:
   print ("new TP_FN layer already exists")
else:
   arcpy.SelectLayerByAttribute_management (TP_FN_FP, "NEW_SELECTION", "TP_FN_FP <>3")
   arcpy.FeatureClassToFeatureClass_conversion(TP_FN_FP,TP_FNPath,TP_FN + '.shp')
   print ("new TP_FN layer made")
      
########################################
##############GRID DENSITY##############
########################################
 
# Generate a grid to fit the county outline with cell sizes of listed in Grid_Size_List variable. Then
# use "Spatial Join" tool to count the number of hybrid model and ground truth points within each grid
# cell, for each cell size. Save the spatial join outputs to the "Grid_Density" geodatabase.
fishnet_coord = arcpy.Describe(County_Outline)

Fishnet = State_Abbrev + '_' + County_Name + '_Fishnet_'
Grid_Size_List = ['500','1000','1500','2000','2500','3000','4000','5000','6000','7000','8000','9000','10000','11000','12000','13000','14000','15000',\
                  '16000','17000','18000','19000','20000','22000','25000','30000','35000','40000','45000','50000','55000','60000']
for Grid_Size in Grid_Size_List:
   if arcpy.Exists(FishnetsPath + Fishnet + Grid_Size) == True:
      print ("fishnet of " + Grid_Size + " meters for " + County_Name + " county already exists")
   else:
      arcpy.CreateFishnet_management(FishnetsPath + Fishnet + Grid_Size,str(fishnet_coord.extent.lowerLeft),\
                                     str(fishnet_coord.extent.XMin) + " " + str(fishnet_coord.extent.YMax),\
                                     Grid_Size, Grid_Size, "", "", str(fishnet_coord.extent.upperRight), "NO_LABELS",County_Outline,"POLYGON")
      print(Grid_Size + "-meter fishnet created for " + County_Name + " county")            

Grid_Densities = [] 
Input_List = {AutoReviewPath+AutoReview:AutoReview,TP_FNPath+TP_FN+".shp":TP_FN,FLAPSPath+FLAPS:FLAPS}
for Data_Type in Input_List:
   for Grid_Size in Grid_Size_List:
      if arcpy.Exists(Grid_DensityPath + Input_List[Data_Type] + '_Grid_' + Grid_Size) == True:
         print ("grid density analysis for " + Grid_Size + " meters already complete")
      else:
         arcpy.SpatialJoin_analysis(FishnetsPath + Fishnet + Grid_Size,Data_Type,Grid_DensityPath + Input_List[Data_Type] + '_Grid_' + Grid_Size,\
                           "JOIN_ONE_TO_ONE","KEEP_ALL","","COMPLETELY_CONTAINS","","")
         print("grid density calculated for " + Grid_Size + " meters")
      Grid_Densities.append(Input_List[Data_Type] + '_Grid_' + Grid_Size)

# Export spatial join outputs (from calculating grid density with fishnet layer), to .csv geodatabase.
Grid_Density_CSVPath = r'O:\AI Modeling Coop Agreement 2017\Grace Cap Stone Validation\Validation_Results\Grid_Density/'

for Grid_Density in Grid_Densities:
   if arcpy.Exists(Grid_Density_CSVPath + Grid_Density)== False:
      tableToCSV(Grid_DensityPath + Grid_Density,Grid_Density_CSVPath + Grid_Density)

########################################
#############ELLIPSE OVERLAP############
########################################

# Construct standard deviational ellipses within grid sizes of 3, 10, and 20km. First spatial join layers
# to fishnet polygons to assign cell ID to points for hybrid and FLAPS models and ground truth layer.
Ellipse_Size_List = ['3000','10000','20000']

Ellipses = []
for Data_Type in Input_List:
   #arcpy.MakeFeatureLayer_management(Data_Type,Input_List[Data_Type])
   for Ellipse_Size in Ellipse_Size_List:
      if arcpy.Exists(Cell_AssignmentsPath + Input_List[Data_Type] + '_Cell_' + Ellipse_Size) == True:
         Ellipses.append(Input_List[Data_Type] + '_Ellipse_' + Ellipse_Size)
         print ("ellipse of " + Ellipse_Size + " size for " + Input_List[Data_Type] + " in " + County_Name + " county already exists")
      else:
         arcpy.MakeFeatureLayer_management(Grid_DensityPath + Input_List[Data_Type] + '_Grid_' + Ellipse_Size,Input_List[Data_Type] + '_Grid_' + Ellipse_Size)
         arcpy.AddField_management(FishnetsPath + Fishnet + Ellipse_Size, "Cell_ID","LONG","","","","","NULLABLE","NON_REQUIRED","")
         arcpy.CalculateField_management(FishnetsPath + Fishnet + Ellipse_Size, "Cell_ID", "sum([!OID!],0)","PYTHON","")
         arcpy.SelectLayerByAttribute_management(Input_List[Data_Type] + '_Grid_' + Ellipse_Size,"NEW_SELECTION","Join_Count > 2")
         arcpy.SelectLayerByLocation_management(Input_List[Data_Type],"COMPLETELY_WITHIN",Input_List[Data_Type] + '_Grid_' + Ellipse_Size,"","NEW_SELECTION")
         count = int(arcpy.GetCount_management(Input_List[Data_Type]).getOutput(0))
         if count < 1:
            print("too few points for ellipse of " + Ellipse_Size + " size for " + Input_List[Data_Type] + " in " + County_Name + " county")
         else:
            arcpy.SpatialJoin_analysis(Input_List[Data_Type],FishnetsPath + Fishnet + Ellipse_Size,Cell_AssignmentsPath + Input_List[Data_Type] + '_Cell_' + Ellipse_Size,\
                                 "JOIN_ONE_TO_ONE","KEEP_ALL","", "COMPLETELY_WITHIN", "","")
            arcpy.DirectionalDistribution_stats(Cell_AssignmentsPath + Input_List[Data_Type] + '_Cell_' + Ellipse_Size, EllipsePath + Input_List[Data_Type] + '_Ellipse_' + Ellipse_Size,\
                                          "1_STANDARD_DEVIATION", "", "Cell_ID")
            print ("ellipse of " + Ellipse_Size + "size for " + Input_List[Data_Type] + " in " + County_Name + "county created")
            Ellipses.append(Input_List[Data_Type] + '_Ellipse_' + Ellipse_Size)

# Create new layer of intersection between FLAPS and hybrid model ellipses at 3, 19, and 20 km and ground
# ground truth ellipses.
Model_List = {AutoReviewPath + AutoReview:AutoReview,FLAPSPath + FLAPS:FLAPS}
for Model_Type in Model_List:
   for Ellipse_Size in Ellipse_Size_List:
      if arcpy.Exists(EllipsePath + TP_FN + '_Ellipse_' + Ellipse_Size)== False:
         print ("no ground truth ellipses exist for " + County_Name + " county at " + Ellipse_Size + " size")
      else:
         if arcpy.Exists(EllipsePath + Model_List[Model_Type] + '_Ellipse_' + Ellipse_Size)== False:
            print ("there is no " +Model_List[Model_Type] + " ellipse at " + Ellipse_Size + " size")
         else:
            if arcpy.Exists(EllipsePath + Model_List[Model_Type] + '_Intersection_' + Ellipse_Size)==True:
               print ("intersection between " + Model_List[Model_Type]+ " and ground truth at " + Ellipse_Size + " size already exists")
               Ellipses.append(Model_List[Model_Type] + '_Intersection_' + Ellipse_Size)
            else:
               arcpy.Intersect_analysis ([EllipsePath + Model_List[Model_Type] + '_Ellipse_' + Ellipse_Size,EllipsePath + TP_FN + '_Ellipse_' + Ellipse_Size],\
                                  EllipsePath + Model_List[Model_Type] + '_Intersection_' + Ellipse_Size,"ALL","","INPUT")
               Ellipses.append(Model_List[Model_Type] + '_Intersection_' + Ellipse_Size)
               print("intersection at " + Ellipse_Size + " size made between " + Model_List[Model_Type] + " ellipse and ground truth ellipse")
 
# Export ellipse and intersection outputs to .csv files.
Ellipse_CSVPath = r'O:\AI Modeling Coop Agreement 2017\Grace Cap Stone Validation\Validation_Results\Ellipses/'

for Ellipse in Ellipses:
   if arcpy.Exists(EllipsePath + Ellipse)== False:
      tableToCSV(EllipsePath + Ellipse,Ellipse_CSVPath + Ellipse)
  

########################################
############DISTANCE ANALYSIS###########
########################################

# Create two tables in the "Dist_Between_Tables" geodatabase with distances between all points in the
# hybrid model and distances between all points in the ground truth layer.

Distances = []
for Data_Type in Input_List:
   arcpy.GenerateNearTable_analysis(Data_Type,Data_Type,NearTablePath + Input_List[Data_Type] + '_Distance',"","LOCATION","NO_ANGLE","ALL","","PLANAR")
   Distances.append(Input_List[Data_Type] + '_Distance')

print ("distances between farms calculated")   
#########################################################################################################
# Export distance between farms tables to .csv files.

Distance_CSVPath = r'O:\AI Modeling Coop Agreement 2017\Grace Cap Stone Validation\Validation_Results\Distances/'

for Distance in Distances:
   tableToCSV(NearTablePath + Distance,Distance_CSVPath + Distance)
  
#########################################################################################################
#########################################################################################################
# Generate buffers around ground truth points of 100, 500, 1000, 2000, and 5000 meters. Then use the
# "Spatial Join" tool to count the number of hybrid model points that fall within each buffer, for each
# radius size. Save the spatial join outputs to the "Buffer_Capture" geodatabase.

Captures = []
Buffer_Size_List = ['100','500','1000','2000','5000']
for Buffer_Size in Buffer_Size_List:
   arcpy.Buffer_analysis(TP_FNPath + TP_FN + ".shp",BuffersPath + State_Abbrev + '_' + County_Name + '_Buffer_' + Buffer_Size,\
                         Buffer_Size,"FULL","","NONE","","PLANAR")
   for Model_Type in Model_List:
      arcpy.SpatialJoin_analysis(BuffersPath + State_Abbrev + '_' + County_Name + '_Buffer_' + Buffer_Size,\
                                 Model_Type,Buffer_CapturePath + Model_List[Model_Type] + '_Capture_' + Buffer_Size,\
                                 "JOIN_ONE_TO_ONE","KEEP_ALL","","COMPLETELY_CONTAINS","","")
      Captures.append(Model_List[Model_Type] + '_Capture_' + Buffer_Size)

print ("buffer captures finished")
#########################################################################################################
# Export distance between farms tables to .csv files.

Buffer_Capture_CSVPath = r'O:\AI Modeling Coop Agreement 2017\Grace Cap Stone Validation\Validation_Results\Buffer_Capture/'

for Capture in Captures:
   tableToCSV(Buffer_CapturePath + Capture,Buffer_Capture_CSVPath + Capture)
  
