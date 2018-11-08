from Automated_Review import *
import numpy as np
import arcpy
import os

if 1==2:
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


def check_parameters():
    should_be_files = [prob_surface_raster, ]
    should_be_folder = [county_outline_folder, ]
    should_be_booleans = [run_script_as_tool, save_intermediates, track_completed_counties, ]
    should_be_lists = [cluster_list, neg_masks, pos_masks, skip_list, ]
    should_be_number = [prob_surface_threshold, L_max_threshold, L_min_threshold, AR_max_threshold, AR_min_threshold,
                        num_iterations, ]
    for thing in should_be_files:
        try:
            os.path.isfile(thing)
        except Exception:
            raise TypeError('Needs to be a file.')
    for thing in should_be_folder:
        try:
            os.path.isdir(thing)
        except Exception:
            raise TypeError('Needs to be a folder/directory')
    for thing in should_be_booleans:
        if thing is True or thing is False:
            ()
        else:
            raise TypeError('Not Boolean')
    for thing in should_be_lists:
        if not isinstance(thing, list):
            raise TypeError('Not list')
    for thing in should_be_number:
        try:
            thing + 1
        except Exception:
            raise TypeError('Not number')


print "Ready to test."