
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
# This was edited by David South to run for the counties that were added later on.
#       New counties: Kings, California / Stanislaus, California / Sussex, Delaware / Kent, Delaware
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

# This allows us to import relevant functions from existing Python scripts
sys.path.insert(0, r'O:\AI Modeling Coop Agreement 2017\David_working\Remote_Sensing_Procedure\RS_Python_Scripts_GitHub')

from Automated_Review import find_FIPS_UTM
from Converting_state_names_and_abreviations import *
    # This module gives us several tools, such as:
    #   state_name_to_abbrev - dictionary to turn state name "California" to "CA"
    #   state_abbrev_to_name - same but in reverse
    #   nameFormat(name) - function that removes some troublesome characters from names.

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
# The Relevant_Counties list should be a nested list, meaning a list of counties,
# for example:
#       [['California', 'CA', 'Kings'],
#       ['Delaware', 'DE', 'Kent'],
#       ['Minnesota', 'MN', 'Cottonwood']]
Relevant_Counties = [['Minnesota', 'MN', 'Cottonwood'],
                   ['Minnesota', 'MN', 'Kandiyohi'],
                   ['Minnesota', 'MN', 'Redwood']]
# Note that if the following variable 'all_counties' is True, Relevant_Counties will be ignored.
# Instead, the script will just run for each county found in AutoReviewCounties.gdb
all_counties = False

# Use this if you want to skip until a certain entry in the counties list.
# Format it with state abbreviation and county name like so:
#    ["MS", "Wayne"]
# If you don't want to skip, set skip_until = None
skip_until = None

##########Keep these Variables##########
Automated_Review_ResultsPath = r'R:\Nat_Hybrid_Poultry\Results\Automated_Review_Results/'
TP_FN_FPPath = r'O:\AI Modeling Coop Agreement 2017\David_working\Remote_Sensing_Procedure\TP_FN_FP.gdb/' 
CountyOutlinesPath = r'N:\Remote Sensing Projects\2016 Cooperative Agreement Poultry Barns\Documents\Deliverables\Library\CountyOutlines/'

TP_FNPath = r'O:\AI Modeling Coop Agreement 2017\Grace Cap Stone Validation\Validation_Results\TP_FN_Counties/' 
AutoReviewPath = r'O:\AI Modeling Coop Agreement 2017\Grace Cap Stone Validation\Validation_Results\AutoReviewCounties.gdb/' # Don't add counties to this GDB, it is populated automatically.
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

def tableToCSV(Input_Table, Filepath, Print_Results=False):
    Field_List = arcpy.ListFields(Input_Table)
    Field_Names = [Field.name for Field in Field_List]
    # Note that Python will overwrite Filepath if something existed there previously.
    with open(Filepath, 'wb') as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(Field_Names)
        with arcpy.da.SearchCursor(Input_Table, Field_Names) as cursor:
            for row in cursor:
                writer.writerow(row)
        if Print_Results==True:
            print Filepath + " CREATED"
            
    
#            #             #           #
#############Get Source Data############
#            #             #           #
def do_stuff(State_Name, State_Abbrev, County_Name, setup_input_data=True, autoreview=True, flaps=True, grid_density=True, ellipse=True,
             distance=True, buffer_analysis=True):
    # Pull ground truth points, hybrid model points, and county outlines from their sources.

    County_Outline = County_Name + 'Co' + State_Abbrev + '_outline'
    TP_FN_FP = State_Abbrev + '_' + County_Name + '_TP_FN_FP'
    TP_FN = State_Abbrev + '_' + County_Name + '_TP_FN'
    FLAPS = State_Abbrev + '_' + County_Name + '_FLAPS'
    AutoReviewSource = 'AutoReview_' + State_Abbrev + '_' + County_Name
    AutoReview = State_Abbrev + '_' + County_Name + '_AutoReview'
    Fishnet = State_Abbrev + '_' + County_Name + '_Fishnet_'
    source_data_list = {CountyOutlinesPath + State_Name + '.gdb/' + County_Outline: County_Outline, \
                        TP_FN_FPPath + TP_FN_FP: TP_FN_FP,
                        Automated_Review_ResultsPath + State_Name + '.gdb/' + AutoReviewSource: AutoReviewSource}
    Input_List = {AutoReviewPath+AutoReview:AutoReview,TP_FNPath+TP_FN+".shp":TP_FN,FLAPSPath+FLAPS:FLAPS}
    Model_List = {AutoReviewPath + AutoReview:AutoReview,FLAPSPath + FLAPS:FLAPS}
    
    if setup_input_data==True:
        for source_data in source_data_list:
            if arcpy.Exists(source_data):
                arcpy.MakeFeatureLayer_management(source_data,source_data_list[source_data])
            else:
                print ("Error: source layer does not exist.", source_data)

        print("source layers created")
        

    if autoreview==True:
        # Change the projection of the hybrid model layer to match that of the ground truth layer and save it
        # as a new layer in the "AutoReviewCounties" geodatabase in the "Validation_Results" folder.
       

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
           
    if flaps==True:    
        # Create FLAPS dataset for county from national model using select by location and the county
        # outline layer.

        if arcpy.Exists(FLAPSPath + FLAPS) == True:
           print ("new FLAPS layer already exists")
        else:
            poultry_list = ["Layers","Pullets","Turkeys","Broilers"]
            for poultry_type in poultry_list:
                arcpy.MakeFeatureLayer_management(FLAPSPath + poultry_type, poultry_type)
                arcpy.SelectLayerByLocation_management(poultry_type,"COMPLETELY_WITHIN",County_Outline,"","NEW_SELECTION","")
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

    if grid_density==True:
        fishnet_coord = arcpy.Describe(County_Outline)

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
        
        for Data_Type in Input_List:
           for Grid_Size in Grid_Size_List:
              if arcpy.Exists(Grid_DensityPath + Input_List[Data_Type] + '_Grid_' + Grid_Size) == True:
                 print ("grid density analysis for " + Grid_Size + " meters already complete")
              else:
                 arcpy.SpatialJoin_analysis(FishnetsPath + Fishnet + Grid_Size,Data_Type,Grid_DensityPath + Input_List[Data_Type] + '_Grid_' + Grid_Size,\
                                   "JOIN_ONE_TO_ONE","KEEP_ALL","","COMPLETELY_CONTAINS","","")
                 print("grid density calculated for " + Grid_Size + " meters")
              Grid_Densities.append(Input_List[Data_Type] + '_Grid_' + Grid_Size)

        # Export spatial join outputs (from calculating grid density with fishnet layer)
        Grid_Density_CSVPath = r'O:\AI Modeling Coop Agreement 2017\Grace Cap Stone Validation\Validation_Results\Grid_Density/'

        for Grid_Density in Grid_Densities:
           if arcpy.Exists(Grid_Density_CSVPath + Grid_Density)== False:
              tableToCSV(Grid_DensityPath + Grid_Density,Grid_Density_CSVPath + Grid_Density)

    ########################################
    #############ELLIPSE OVERLAP############
    ########################################

    def findField(fc, fi): # David South added this function so that the script
                           # can check to see if a field exists in the data.
        fieldnames = [field.name for field in arcpy.ListFields(fc)]
        if fi in fieldnames:
            return True
        else:
            return False

    if ellipse==True:

        ### WARNING:
        ###     This section is having some issues, it wasn't creating the csv files but everything else
        ###     was working fine. So if there is an issue, check to see that the "Ellipses" folder
        ###     has the proper files, and if not just use the tableToCSV function to create the csv files
        ###     manually

        # Construct standard deviational ellipses within grid sizes of 3, 10, and 20km. First spatial join layers
        # to fishnet polygons to assign cell ID to points for hybrid and FLAPS models and ground truth layer.
        Ellipse_Size_List = ['3000','10000','20000']

        Ellipses = []
        for Data_Type in Input_List:
           arcpy.MakeFeatureLayer_management(Data_Type,Input_List[Data_Type])
           for Ellipse_Size in Ellipse_Size_List:
              if arcpy.Exists(Cell_AssignmentsPath + Input_List[Data_Type] + '_Cell_' + Ellipse_Size) == True:
                 Ellipses.append(Input_List[Data_Type] + '_Ellipse_' + Ellipse_Size)
                 print ("ellipse of " + Ellipse_Size + " size for " + Input_List[Data_Type] + " in " + County_Name + " county already exists")
              else:
                 arcpy.MakeFeatureLayer_management(Grid_DensityPath + Input_List[Data_Type] + '_Grid_' + Ellipse_Size,Input_List[Data_Type] + '_Grid_' + Ellipse_Size)
                 arcpy.AddField_management(FishnetsPath + Fishnet + Ellipse_Size, "Cell_ID","LONG","","","","","NULLABLE","NON_REQUIRED","")
                 if findField(FishnetsPath + Fishnet + Ellipse_Size, "OID") is True:  # This section added to allow for inputs with OBJECTID instead of just OID
                     arcpy.CalculateField_management(FishnetsPath + Fishnet + Ellipse_Size, "Cell_ID", "sum([!OID!],0)","PYTHON","")
                 elif findField(FishnetsPath + Fishnet + Ellipse_Size, "OBJECTID") is True:
                     print "File for", Fishnet + Ellipse_Size, "had OBJECTID field instead of OID, but no matter it works fine."
                     arcpy.CalculateField_management(FishnetsPath + Fishnet + Ellipse_Size, "Cell_ID", "sum([!OBJECTID!],0)","PYTHON","")
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
         
        # Export ellipse and intersection output files.
        Ellipse_CSVPath = r'O:\AI Modeling Coop Agreement 2017\Grace Cap Stone Validation\Validation_Results\Ellipses/'

        for Ellipse in Ellipses:
           if arcpy.Exists(EllipsePath + Ellipse)== True:
              tableToCSV(EllipsePath + Ellipse,Ellipse_CSVPath + Ellipse)
      

    ########################################
    ############DISTANCE ANALYSIS###########
    ########################################

    if distance==True:
        # Create two tables in the "Dist_Between_Tables" geodatabase with distances between all points in the
        # hybrid model and distances between all points in the ground truth layer.

        Distances = []
        for Data_Type in Input_List:  ## DS: This loop was modified to check for existing files.
            dist_file_path = NearTablePath + Input_List[Data_Type] + '_Distance'
            if arcpy.Exists(dist_file_path):
                print "File already exists:", dist_file_path
            else:
                arcpy.GenerateNearTable_analysis(Data_Type, Data_Type, dist_file_path, "", "LOCATION", "NO_ANGLE", "ALL", "", "PLANAR")
                Distances.append(Input_List[Data_Type] + '_Distance')

        print ("distances between farms calculated")   
        #########################################################################################################
        # Export distance between farms tables to .csv files.

        Distance_CSVPath = r'O:\AI Modeling Coop Agreement 2017\Grace Cap Stone Validation\Validation_Results\Distances/'

        for Distance in Distances:
           tableToCSV(NearTablePath + Distance,Distance_CSVPath + Distance)
      
    ########################################
    ############BUFFER   ANALYSIS###########
    ########################################
    # Generate buffers around ground truth points of 100, 500, 1000, 2000, and 5000 meters. Then use the
    # "Spatial Join" tool to count the number of hybrid model points that fall within each buffer, for each
    # radius size. Save the spatial join outputs to the "Buffer_Capture" geodatabase.

    if buffer_analysis==True:
        Captures = []
        Buffer_Size_List = ['100','500','1000','2000','5000']
        for Buffer_Size in Buffer_Size_List:    ## DS: this loop was modified to check to see if the files already existed.
            buf_file_path = BuffersPath + State_Abbrev + '_' + County_Name + '_Buffer_' + Buffer_Size
            if arcpy.Exists(buf_file_path):
                print "File already exists:", buf_file_path
            else:
                arcpy.Buffer_analysis(TP_FNPath + TP_FN + ".shp", buf_file_path,\
                                 Buffer_Size,"FULL","","NONE","","PLANAR")
            for Model_Type in Model_List:
                join_buf_file_path = Buffer_CapturePath + Model_List[Model_Type] + '_Capture_' + Buffer_Size
                Captures.append(Model_List[Model_Type] + '_Capture_' + Buffer_Size)
                if arcpy.Exists(join_buf_file_path):
                    print "File already exists:", join_buf_file_path
                else:
                    ## DS: if you are getting an error around this part, it might be because you added data to the
                    ##     TP_FN GDB, and it wasn't projected. It might create a buf_file_path shapefile with
                    ##     buffers larger than the earth. Double check that.
                    arcpy.SpatialJoin_analysis(buf_file_path,\
                                             Model_Type,join_buf_file_path,\
                                             "JOIN_ONE_TO_ONE", "KEEP_ALL", "", "COMPLETELY_CONTAINS", "", "")
                    


        Buffer_Capture_CSVPath = r'O:\AI Modeling Coop Agreement 2017\Grace Cap Stone Validation\Validation_Results\Buffer_Capture/'

        for Capture in Captures:
            tableToCSV(Buffer_CapturePath + Capture,Buffer_Capture_CSVPath + Capture)

        print ("buffer captures finished")

        
    #########################################################################################################
    # Export distance between farms tables to .csv files.

    print "\n\n\nAll analysis completed for", State_Abbrev, County_Name


if __name__=='__main__':
    if all_counties == True:
        counties = []
        walk = arcpy.da.Walk(AutoReviewPath[0:-1], datatype="FeatureClass") # The [0:-1] part is because it doesn't like the \ at the end of the file path.
        for dirpath, dirnames, filenames in walk:
            for filename in filenames:
                # Slice up the file name to get at the juicy information contained within.
                abbrev = filename[0:2] # First two letters are state abbreviation.
                state = state_abbrev_to_name[abbrev] # Get full state name.
                county_name = filename[3:-11] # The county name is between the abbreviation and '_AutoReview'
                if county_name == "Cluster":
                    continue # Don't add files that have cluster in the name, not relevant.
                else:
                    counties.append([state, abbrev, county_name])       
    else:
        # Use only the manually specified counties.
        counties = Relevant_Counties
        
    for county in counties:
        # If skip_until is set, the script will skip counties in the list
        # until the loop reaches the specified county.
        if skip_until is not None:
            if county[1] == skip_until[0] and county[2] == skip_until[1]:
                skip_until = None
            else:
                print "Skipping", county[1], county[2], "\n"
                continue  # This does not trigger the do_stuff function, it ends
                          # the current iteration of the loop and goes to the
                          # next county.
            
        do_stuff(State_Name=nameFormat(county[0]), # nameFormat replaces spaces with _
                 State_Abbrev=county[1],
                 County_Name=nameFormat(county[2]),
                 setup_input_data=False, autoreview=False, flaps=False, grid_density=False, ellipse=True,
                 distance=False, buffer_analysis=False)
    print "\n\n\n###########\n###########\n\nSCRIPT COMPLETE!"

