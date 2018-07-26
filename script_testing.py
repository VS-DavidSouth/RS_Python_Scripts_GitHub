from Automated_Review import *
import numpy as np
import arcpy, os

print "Ready to test."


def testing():
    global county_name, state_abbrev, state_name, cluster, county_outline, FIPS, UTM, batchGDB, batchFile, batchLocation, errors, intermed_list
    county_name = 'Barbour'
    state_abbrev = 'AL'
    state_name = nameFormat(state_abbrev_to_name[state_abbrev])
    cluster = 1
    county_outline = os.path.join(county_outline_folder,
                                      state_name + '.gdb',
                                      county_name + 'Co' + state_abbrev + '_outline')
    FIPS, UTM = FIPS_UTM(county_outline)
    #batchGDB = 'BatchGDB_' + state_abbrev + '_Z' + str(UTM) + '_c' + str(cluster) + '.gdb'
    batchGDB = 'BatchGDB_' + state_abbrev + '_Z' + str(UTM) + '_c' + str(cluster) + '_test' + '.gdb' # DELETE THIS WHEN NO LONGER TESTING LENGTH
    batchGDB = os.path.join(output_folder, state_name, batchGDB)
    batchFile = 'Batch' + '_' + state_abbrev + '_' + county_name
    batchLocation = os.path.join(batchGDB, batchFile)
    errors = []
    intermed_list = []
