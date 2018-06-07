

import os, arcpy, numpy


def findBatchFiles():
        global batchList
        folderLocation = r'A:'
        walk = arcpy.da.Walk(folderLocation, datatype = "FeatureClass", type = "Polygon")

        nopeList = ['Project Documents', 'Copy',]
        batchList = []

        for dirpath, dirnames, filenames in walk:
                for filename in filenames:
                        if filename[-6:] == '_Batch' and 'Project Documents' not in filename and 'Copy' not in filename:
                                print dirpath, filename
                                batchList.append(os.path.join(dirpath, filename))


