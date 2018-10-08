from Automated_Review import *
import numpy as np
import arcpy, os

#probSurfaceFile = r'R:\Nat_Hybrid_Poultry\Remote_Sensing\Feature_Analyst\Alabama\BatchGDB_AL_Z16_c1.gdb\ProbSurf_AL_Barbour'
#collapsePointsFile = r'R:\Nat_Hybrid_Poultry\Remote_Sensing\Feature_Analyst\Alabama\BatchGDB_AL_Z16_c1.gdb\CollectEvents_AL_Coffee'
clipFile = r'R:\Nat_Hybrid_Poultry\Remote_Sensing\Feature_Analyst\Alabama\BatchGDB_AL_Z16_c1.gdb\Clip_AL_Coffee'
intermed_list = []
#clusterGDB = r'R:\Nat_Hybrid_Poultry\Remote_Sensing\Feature_Analyst\Alabama\BatchGDB_AL_Z16_c1.gdb'
clusterGDB = clusterList[0]
state_abbrev = 'AL'
state_name = 'Alabama'
state_name = nameFormat(state_name)
county_name = 'Coffee'
county_outline_folder = r'N:\Remote Sensing Projects\2016 Cooperative Agreement Poultry Barns\Documents\Deliverables\Library\CountyOutlines'
county_outline = os.path.join(county_outline_folder,
                                          state_name + '.gdb',
                                          county_name + 'Co' + state_abbrev + '_outline')

def run(iterationVal):
    global simSamplingFile
    simSamplingFile = simulatedSampling(collapsePointsFile, prob_surface_raster, clusterGDB,
                                                        state_abbrev, county_name, ssBins='default',
                                                        iteration=iterationVal )

#shouldThisStepBeSkipped(state_abbrev, county_name, 'Clip')
markCountyAsCompleted(clusterGDB, progress_tracking_file, state_abbrev, county_name)

#for num in range(1,3):   
#    run(num)

print "Ready to test."
