# This script is designed to go through all of the Automated Review
# output files and calculate how many points were removed at each
# step in the process.

# Order that the Automated Review did the steps:
# 1. clipping
# 2. masking
# 3. LAR
# 4. prob_surface
# 5. collapse_points
# 6. simulated_sampling
# 7. project (auto_review final file output)

import pandas as pd  # reference this for data frame https://www.geeksforgeeks.org/python-pandas-dataframe/
import numpy as np
import arcpy
import os

results = r'R:\Nat_Hybrid_Poultry\Remote_Sensing\Feature_Analyst'

def find_files(folder):
    print ("Finding files...")
    relevant_files = []
    walk = arcpy.da.Walk(folder, type="Point")
    for dirpath, dirnames, filenames in walk:
        for filename in filenames:
            relevant_files.append(os.path.join(dirpath, filename))
    print ("Files found.")
    return(relevant_files)

def count_points(files):
    batch_total = 0
    clip_total = 0
    masking_total = 0
    LAR_total = 0
    prob_surface_total = 0
    collapse_points_total = 0
    sim_sampling_total = 0
    auto_review_total = 0
    for item in files:
        count = arcpy.GetCount_management(item)
        count = int(count[0]) # Turn it into int, instead of the weird ArcGIS output.
        if 'Batch_' in item:
           batch_total += count
        elif 'Clip_' in item:
            clip_total += count
        elif 'Masking_' in item:
           masking_total += count
        elif 'LAR_' in item:
           LAR_total += count
        elif 'ProbSurf_' in item:
           prob_surtface_total += count
        elif 'CollectEvents_' in item:
           collapse_points_total += count
        elif 'SimSampling_' in item:
           sim_sampling_total += count
        elif 'AutoReview_' in item:
           auto_review_total += count
           
        del count

        summary = pd.DataFrame({'Automated Review step':['Batch', 'Clip', 'Masking', 'LAR',
                                                         'ProbSurf', 'CollectEvents', 'SimSampling',
                                                         'AutoReivew'],
                                'Row count total': [batch_total, clip_total, masking_total, LAR_total,
                                                    prob_surface_total, collapse_points_total,
                                                    sim_sampling_total, auto_review_total]})
        return(summary)


