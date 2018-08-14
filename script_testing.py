from Automated_Review import *
import numpy as np
import arcpy, os

larFile = r'R:\Nat_Hybrid_Poultry\Remote_Sensing\Feature_Analyst\Alabama\BatchGDB_AL_Z16_c1_mask_test.gdb\LAR_AL_Geneva'
intermed_list = []


def run():
    global maskFile
    maskFile = masking(larFile, clusterGDB, state_abbrev, county_name, county_outline, neg_masks, pos_masks)



print "Ready to test."
