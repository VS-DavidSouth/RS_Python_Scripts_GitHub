## Number Clusters ##
## NOTE: THIS SCRIPT DOESN'T WORK AS IT SHOULD AND REQUIRES MANUAL CLEANUP

import arcpy, csv
import numpy as np

ClustersCSV = r'N:\Remote Sensing Projects\2016 Cooperative Agreement Poultry Barns\Documents\Poultry Population Modeling Project\Rdrive\Remote_Sensing\ClustersCSV.csv'

thing = [] ## This will store the CSV in memory so we can mess with it

o = open(ClustersCSV)
r = csv.reader(o)

data = list(r)



    
        
def checkStateUTM(currentState, currentUTM):
    global previousState, previousUTM, cluster, count

    if not currentState == previousState:
        previousState = currentState
        previousUTM = currentUTM
        count = 0
        cluster = 1

    elif not currentUTM == previousUTM:
        previousState = currentState
        previousUTM = currentUTM
        count = 0
        cluster += 1

def countFN():
    global count, cluster
    count += 1
    if count > 10:
        count = 0
        cluster += 1
    return cluster

def testCount(start, stop):
	global count, cluster
	count = 0
	cluster = 1
	for blurb in range (start,stop):
		print countFN()

def writeCSV(data, CSV_location):
    a = open(CSV_location, 'wb')
    writer = csv.writer(a, dialect = 'excel')
    writer.writerows(data)
    a.close()

count = 0
cluster = 1
previousState = ''
previousUTM = ''

def run():
    global count, cluster, previousState, previousUTM, data
    count = 0
    cluster = 0
    previousState = ''
    previousUTM = ''
    
    for row in data:
        if row[8] == '':
            
            currentState = row[2]
            currentUTM = row[6]
            
            checkStateUTM(currentState, currentUTM)
            
            row[8] = countFN()

    writeCSV(data, ClustersCSV)

if __name__ == '__main__':
    run()

o.close()

print "ready"


