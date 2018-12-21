from Automated_Review import *
import numpy as np
import arcpy
import os

if 1==1:
    prob_surface_file = r'R:\Nat_Hybrid_Poultry\Results\Automated_Review_Results\Massachusetts.gdb\ProbSurf_MA_Worcester'
    intermed_list = []
    cluster_GDB = os.path.dirname(prob_surface_file)
    state_abbrev = 'MA'
    state_name = nameFormat(state_abbrev_to_name[state_abbrev])
    county_name = 'Worcester'
    county_outline_folder = r'N:\Remote Sensing Projects\2016 Cooperative Agreement Poultry Barns\Documents\Deliverables\Library\CountyOutlines'
    county_outline = os.path.join(county_outline_folder,
                                              state_name + '.gdb',
                                              county_name + 'Co' + state_abbrev + '_outline')

def fn():
    collapse_points_file = collapse_points(prob_surface_file,
                                                       cluster_GDB, state_abbrev,
                                                       county_name)


# TEST
# TEST
# TEST
# TEST
    
print "Ready to test."
