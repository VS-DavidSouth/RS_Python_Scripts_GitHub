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

from Automated_Review import check_time
import pandas as pd
import numpy as np
import arcpy
import csv
import os

results = r'R:\Nat_Hybrid_Poultry\Results\Automated_Review_Results'

csv_file = r'C:\Users\apddsouth\Desktop\csv.csv'

def find_files(folder):
    print ("Finding files...")
    relevant_files = []
    walk = arcpy.da.Walk(folder, type="Point")
    for dirpath, dirnames, filenames in walk:
        for filename in filenames:
            relevant_files.append(os.path.join(dirpath, filename))
    print ("Files found. Time so far:", check_time())
    return(relevant_files)


def write_list_to_CSV(lst, file_path):
    with open(file_path, 'wb') as myfile:
        wr = csv.writer(myfile, quoting=csv.QUOTE_ALL)
        for row in lst:
            wr.writerow(row)
    print ("List saved to CSV here:", file_path)


def read_CSV_to_list(CSV_file_path):
    lst = []
    with open(csv_file) as csvfile:
        readCSV = csv.reader(csvfile, delimiter=',')
        for row in readCSV:
            lst.append(row[0])
    return(lst)

def count_points(files, csv_folder_path=None):
    print("Doing some math.")
    steps = ['Batch', 'Clip', 'Masking', 'LAR',
             'ProbSurf', 'CollectEvents', 'SimSampling',
             'AutoReview']
    totals = np.zeros(8)

    timer = 0.0
    current = 0.0
    # timer_delay is how frequently it should save a CSV and check time
    timer_delay = 10

    def save_csv(final=False):
        previous_csv_path = os.path.join(csv_folder_path, "count_" + str(int(current-timer_delay)) + ".csv")
        csv_path = os.path.join(csv_folder_path, "count_" + str(int(current)) + ".csv")
        write_list_to_CSV(np.array((steps, totals)), csv_path)
        
        # Don't do this for the first set, because no previous csv exists.
        if not current == timer_delay and final==False:
            os.remove(previous_csv_path)

    for item in files:
        count = arcpy.GetCount_management(item)
        count = int(count[0]) # Turn it into int, instead of the weird ArcGIS output.

        for index in range(0, len(steps)):
            # For the step that matches the file name, tally that up
            if (steps[index] + "_") in os.path.basename(item):
                totals[index] += count
                break

        del count

        timer += 1
        current += 1
        
        if timer == timer_delay:
            if csv_folder_path is not None:
                save_csv()

            print int(current), "files computationally calculated, (" + str(int(round(current/len(files))*100)) + '% complete). Time so far:', check_time()
            
            timer = 0.0

    # Once the loop is completed, all files have been calculated:
    save_csv(final=True)
    print("Math completed. Whew that was a lot of addition. I need a bigger abacus.")
    
    return(np.array((steps, totals)))

x = read_CSV_to_list(csv_file)
y = count_points(x, r'C:\Users\apddsouth\Desktop')
print (y)

