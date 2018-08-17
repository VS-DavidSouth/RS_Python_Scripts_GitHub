from Automated_Review import *
import numpy as np
import arcpy, os

larFile = r'R:\Nat_Hybrid_Poultry\Remote_Sensing\Feature_Analyst\Alabama\BatchGDB_AL_Z16_c1_masks_test.gdb\LAR_AL_Coffee'
intermed_list = []
clusterGDB = r'R:\Nat_Hybrid_Poultry\Remote_Sensing\Feature_Analyst\Alabama\BatchGDB_AL_Z16_c1_masks_test.gdb'
state_abbrev = 'AL'
state_name = 'Alabama'
county_name = 'Coffee'
county_outline_folder = r'N:\Remote Sensing Projects\2016 Cooperative Agreement Poultry Barns\Documents\Deliverables\Library\CountyOutlines'
county_outline = os.path.join(county_outline_folder,
                                          state_name + '.gdb',
                                          county_name + 'Co' + state_abbrev + '_outline')

def run():
    global maskFile
    maskFile = masking(larFile, clusterGDB, state_abbrev, county_name, county_outline, neg_masks, pos_masks)



print "Ready to test."
