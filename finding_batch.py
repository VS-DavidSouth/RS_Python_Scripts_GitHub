

import os, arcpy, numpy

sys.path.insert(0, r'O:\AI Modeling Coop Agreement 2017\David_working\Python')
from Converting_state_names_and_abreviations import *



def findBatchFiles():
    global batchList
    folderLocation = r'A:'
    walk = arcpy.da.Walk(folderLocation, datatype = "FeatureClass", type = "Polygon")

    nopeList = ['Project Documents', 'Copy',]
    batchList = []

    for dirpath, dirnames, filenames in walk:
        for filename in filenames:
            filepath = os.path.join(dirpath, filename)
            if filename[-6:] == '_Batch' and not 'Project Documents' in filepath and not 'Copy' in filepath:
                print dirpath, filename
                batchList.append(filepath)

def batchFile(state_abbrev, county):
    for batch in batchList:
        state_name = state_abbrev_to_name[state_abbrev]
        if state_name in batch and county in batch:
            return batch



def findFinalFiles():
    print "Finding _Batch files..."

    global finalFilesList
    
    folderLocation = r'A:'
    walk = arcpy.da.Walk(folderLocation, datatype = "FeatureClass", type = "Point")

    finalFilesList = []

    for dirpath, dirnames, filenames in walk:
        for filename in filenames:
            filepath = os.path.join(dirpath, filename)
            if filename[-6:] == '_FINAL' or filename[-6:] == '_Final':
                finalFilesList.append(filepath)
    print "A total of", len(finalFilesList), "_FINAL files found."
    print numpy.array(finalFilesList)
    
print "Ready for testing!"
