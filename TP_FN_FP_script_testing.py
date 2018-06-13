from Creating_TP_FN_FP_files import *
import numpy as np


print "Ready to test."

def TEST():
    global errorList, batchList, filteredFinalFilesList, summaryStats
    errorList = []
    
    summaryStats = collectSummaryStats() # create the 'summaryStats' numpy array

    print "Finding _FINAL files..."
    filteredFinalFilesList = findFinalFiles()   # create a list of the file locaitons of all the _FINAL files (and similar) on the A: drive
    print "_FINAL files found. Script duration so far:", checkTime()

    print "Finding _Batch files..."
    batchList = findBatchFiles()    # create a list of the file locations of all the _Batch files on the A: drive
    print "_Batch files found. Script duration so far:", checkTime()

    for county in summaryStats:
        state_abbrev = county[0][0:2]    # holds the 2-letter abbreviation for the current state
        state_name = state_abbrev_to_name[state_abbrev]     # holds the full name of the state
        state_name = state_name.replace(" ", "")
        county_name = county[1]    # holds the county name
        flag = False

        for finalFile in filteredFinalFilesList:
            if state_name and county_name in finalFile:
                flag = True
        if flag == False:
            errorList.append([state_name, county_name])

    print np.array(errorList)
