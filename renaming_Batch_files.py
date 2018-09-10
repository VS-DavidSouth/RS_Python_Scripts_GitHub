## This script renames the output of the Feature Analyst files.
## For example, 'georgia_NAIP2m_GA_Bulloch' becomes 'Batch_GA_Bulloch'

import arcpy, os
from Automated_Review import checkTime

## Input folder where Feature Analyst exports the shapefiles
inputFolder = arcpy.GetParameterAsText(0)
#inputFolder = r'R:\Nat_Hybrid_Poultry\Remote_Sensing\Feature_Analyst\Georgia\GA_Z17_c8'

def walkFolder(folderLocation):
    
    walk = arcpy.da.Walk(folderLocation, type = "Point")

    walkList = []   ## This will hold all of the file paths to the files wuithin the folder

    for dirpath, dirnames, filenames in walk:
        for filename in filenames:
                walkList.append(os.path.join(dirpath,filename))

    return walkList


def findNewName(batch_file):
    ##
    ## This function decides what the new name of the batch_file should be.
    ## It does not actually rename the file, it simply returns the name.
    ##
    if 'Batch' in batch_file:
        return batch_file

    batchName = os.path.basename(batch_file)
    num_ = batchName.count('_')

    new_name = '' # Set this as default

    startingIndex = 0 # Set this to start searching for '_' at the first character
    previousUnderscoreIndex = -999 # Not a real number
    for underscore in range(0, num_):
        underscoreIndex = batchName.find('_', startingIndex)
        startingIndex = underscoreIndex + 1

        if underscoreIndex - previousUnderscoreIndex == 3: ## This means that there is a gap of two characters 
                                                           ##  between the underscores, such as '_KY_'
            stateAbbrevIndex = previousUnderscoreIndex
            new_name = 'Batch' + batchName[stateAbbrevIndex:]
                ## Name the file starting with 'Batch' and add on
                ##  everything from the state abbreviation onward.
                ## 'kentucky_NAIP2m_KY_Adair' becomes 'Batch_KY_Adair'.
            break
        else:
            previousUnderscoreIndex = underscoreIndex

    if new_name[-4:] == '.shp':
        new_name = new_name[:-4]
        
    return new_name
                                                        
            

def renameBatchFile(batch_file, new_name):
    ##
    ## As of now, this is unused.
    ##
    if 'Batch' in batch_file:
        print "Error: File already contains 'Batch' in the name."
    else:
        folder = os.path.dirname(batch_file)
        arcpy.Rename_management(batch_file,
                                os.path.join(folder, new_name) )

def transferToGDB_old(in_folder):
    ##
    ## This is incomplete. Beware.
    ##
    listString = '' # This will save a string containing all the files to be transfered to GDB, used in the arcpy function
    for batch_file in inList:
        
        new_name = findNewName(batch_file)
        listString = listString + os.path.join(in_folder, item) + ';'

    if listString[-1] == ';':
        listString = listString[:-1]
    
    ## Transfer specified files to the GDB
    arcpy.FeatureClassToGeodatabase_conversion(Input_Features=listString,
                                               Output_Geodatabase=out_GDB)

def transferToGDB(in_folder):

    ## Get a list of all the files in the input folder
    inputList = walkFolder(in_folder)
    folderName = os.path.basename(in_folder) # This is the folder that contains the raw Feature Analyst outputs
    pathToFolder = os.path.dirname(in_folder) # This is the folder that both the folderName and output GDB will be in
    gdbName = 'BatchGDB_' + folderName + '.gdb'
    out_GDB = os.path.join(pathToFolder, gdbName) # This is where the Batch files will be placed

    if not arcpy.Exists(out_GDB):
        arcpy.CreateFileGDB_management(pathToFolder, gdbName)
    
    for batch_file in inputList:
        new_name = findNewName(batch_file)
        arcpy.FeatureClassToFeatureClass_conversion(in_features=batch_file, out_path=out_GDB, out_name=new_name)


transferToGDB(inputFolder)

print "Time to run:", checkTime()
print "Completed!"



