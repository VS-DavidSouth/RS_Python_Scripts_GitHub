from Automated_Review import *
import numpy as np
import arcpy, os

#probSurfaceFile = r'R:\Nat_Hybrid_Poultry\Remote_Sensing\Feature_Analyst\Alabama\BatchGDB_AL_Z16_c1.gdb\ProbSurf_AL_Barbour'
collapsePointsFile = r'R:\Nat_Hybrid_Poultry\Remote_Sensing\Feature_Analyst\Alabama\TestGDB_AL_Z16_c1.gdb\CollectEvents_AL_Geneva'
intermed_list = []
#clusterGDB = r'R:\Nat_Hybrid_Poultry\Remote_Sensing\Feature_Analyst\Alabama\BatchGDB_AL_Z16_c1.gdb'
clusterGDB = r'R:\Nat_Hybrid_Poultry\Remote_Sensing\Feature_Analyst\Alabama\TestGDB_AL_Z16_c1.gdb'
state_abbrev = 'AL'
state_name = 'Alabama'
county_name = 'Geneva'
county_outline_folder = r'N:\Remote Sensing Projects\2016 Cooperative Agreement Poultry Barns\Documents\Deliverables\Library\CountyOutlines'
county_outline = os.path.join(county_outline_folder,
                                          state_name + '.gdb',
                                          county_name + 'Co' + state_abbrev + '_outline')

def run():
    global simSamplingFile
    simSamplingFile = simulatedSampling(collapsePointsFile, probSurfaceRaster, clusterGDB, state_abbrev, county_name, ssBins='default' )
    
run()

print "Ready to test."
