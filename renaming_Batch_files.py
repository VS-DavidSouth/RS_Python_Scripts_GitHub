## This script renames the output of the Feature Analyst files.
## For example, 'georgia_NAIP2m_GA_Bulloch' becomes 'Batch_GA_Bulloch'

import arcpy, os
from Automated_Review import checkTime

## Input folder where Feature Analyst exports the shapefiles
#inputFolder = arcpy.GetParameterAsText(0)
inputFolder = r'R:\Nat_Hybrid_Poultry\Remote_Sensing\Feature_Analyst\Georgia\GA_Z17_c8'

## Output geodatabase where this scripe will rename files
#outputGDB = arcpy.GetParameterAsText(1)
outputGDB = r'R:\Nat_Hybrid_Poultry\Remote_Sensing\Feature_Analyst\Georgia\BatchGDB_GA_Z17_c8.gdb'

def walkFolder(folderLocation):
    
    walk = arcpy.da.Walk(folderLocation, type = "Point")

    walkList = []   ## This will hold all of the file paths to the files wuithin the folder

    for dirpath, dirnames, filenames in walk:
        for filename in filenames:
                walkList.append(filename)

    return walkList

def renameFiles(folder):
    ##
    ## This function changes the names of all files in the folder that it
    ##  is pointed at.
    ##
    if not 'GDB' in folder:
        print "'GDB' is not found in the folder to be renamed."
    else:
        batchList = walkFolder(folder)

        for batchFile in batchList:
            if not 'Batch' in batchFile:
            
                ## This script finds the second underscore and only keeps the part after that
                firstUnderscore = batchFile.find('_')
                secondUnderscore = batchFile.find('_', firstUnderscore + 1)
                newName = 'Batch' + batchFile[secondUnderscore:]

                arcpy.Rename_management( os.path.join(folder, batchFile),
                                         os.path.join(folder, newName) )


def transferToGDB(in_folder, out_GDB):

    ## Get a list of all the files in the input folder
    inList = walkFolder(in_folder)
    outList = walkFolder(out_GDB)

    ## Don't add new files if the target GDB is not empty
    if not outList == []:
        return
    
    listString = ''
    for item in inList:

        listString = listString + os.path.join(in_folder, item) + ';'

    if listString[-1] == ';':
        listString = listString[:-1]
    
    ## Transfer all files to the GDB
    arcpy.FeatureClassToGeodatabase_conversion(Input_Features=listString,
                                               Output_Geodatabase=out_GDB)
    
    renameFiles(out_GDB)

transferToGDB(inputFolder, outputGDB)

print "Time to run:", checkTime()
print "Completed!"



