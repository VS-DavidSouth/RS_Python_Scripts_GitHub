## PHASE 1: CREATING MODELS 
    A. Requires resampled NAIP imagery 
        i. Resample_NAIP.py script 
    B. See documentation from the regional pilot study with 35 counties.
    
    
## PHASE 2: USING FEATURE ANALYST TO CREATE BATCH FILES 
    A. Each Batch file needs to have 'Batch' as a prefix and the state abbreviation and county name
    
    
## PHASE 3: AUTOMATED REVIEW SCRIPT
###    SECTION A. Getting set up to run the Automated_Review Python script 
        i. How to run the script: 
            Open the Automated_Review.py file in IDLE(Python GUI), the IDE that comes with ArcGIS. This can be done by right clicking the Automated_Review.py file on a computer with ArcGIS installed, and clicking "Edit with IDLE" 
        ii. DO NOT DOUBLE CLICK OR RUN THE SCRIPT FILE WITHOUT CHECKING THAT THE PARAMETERS ARE CORRECT FIRST! 
        iii. Once parameters are double checked, run the module from the IDLE window. You can  
        iv. Things required to run the script: 
            1. A computer with ArcGIS 10.5 or more recent installed. Previous versions of ArcGIS may work, but they are untested. It is recommended to run this script in the IDLE program that comes with ArcGIS. 
            2. The ArcGIS extension Spatial Analyst, which needs to be installed and have at least one available license. 
            3. One or more remotely sensed point shapefile or feature class files which will be hereafter referred to as the 'Batch' files. These are the files that you want to remove a bunch of clutter from, get rid of False Positives. 
                a. Associated parameters: 
                    clusterList 
            4. A folder full of polygon files, with folders for each state, with shapefiles within for each county. 
                a. Associated parameters: 
                    county_outline_folder 
                b. Associated functions: 
                    clip(…) 
                    addFipsInfo(…) which is used in the clip(…) and  collapsePoints(…) functions 
                    clip_buffer(…) which is within masking(…) 
            5. The probability surface raster file from FLAPS, for the entire contiguous US. If this is not available, ensure the code does not use the probSurface function.  
                a. Associated parameters: 
                    prob_surface_raster 
                    prob_surface_threshold 
                b. Associated functions: 
                    probSurface(…) 
            6. Mask shapefiles or feature classes, along with any buffer values. Buffer values can be zero. Masks can be either negative masks (no barns will appear within this area; ex: 15m buffer from roads) or positive masks (barns will should only appear inside this area; ex: commercial land polygons). If no masks are to be used, either for neg_masks or pos_masks, follow the directions in the code for formatting. 
                a. Associated parameters: 
                    neg_masks
                    pos_masks 
                b. Associated functions: 
                    masking(…) 
            7. A CSV file for Adjusted FLAPS. This involves taking raw FLAPS output for Pullets, Layers and Turkeys and deleting all points below a threshold (400 birds, 1000 birds, etc) to eliminate any 'backyard' farms that are not large scale production facilities.  The CSV should have farm totals for each county, which will be used to determine how many points should be selected during the simulatedSampling(…) function. 
                a. Associated parameters: 
                    adjFLAPS_CSV 
                b. Associated functions: 
                    simulatedSampling(…) 
            8. A location for the tracking file. It is not necessary to create a CSV file at this location, the script will create a blank one and fill it if needed. Optionally, this can be turned off by setting trackWhichCountiesAreCompleted = False.
                a. Associated parameters: 
                    progress_tracking_file 
                    trackWhichCountiesAreCompleted 
                b. Associated functions: 
                    markCountyAsCompleted(…) 
            9. Output location to store all the files. This should probably have a terabyte of storage space or more, just in case. 
                a. Associated parameters: 
                    output_folder 
                    saveIntermediates 
                b. Associated functions: 
                    Basically any function that outputs a file will put them at the location specified in output_folder unless told otherwise. 
            10. All of the values to be used for the Parameters section of the code. These include the following variables:  
                prob_surface_threshold 
                L_max_threshold 
                L_min_threshold 
                AR_max_threshold 
                AR_min_threshold 
                numIterations 
                
 ###       SECTION B. Main sections of the Automated_Review script 
            1. Description 
                a. A general overview of the script. 
            2. Setup 
                a. Those seeking to modify the code should be aware and at least generally competent with the following libraries: 
                    os 
                    sys 
                    numpy 
                    Parameters 
                b. Most of the parameters are important to look at, but several are entirely optional and there only to make things easier. They are as follows: 
                    runScriptAsTool 
                    saveIntermediates 
                    trackWhichCountiesAreCompleted 
                    regional_35_counties 
                    The whole "if runScriptAsTool == True:" section. Ignore this if you aren't using the script as a custom arcGIS tool. 
                    LAR_thresholds, this one is really just putting 4 parameters into a single list which is easier to input into the LAR function. Note that the individual L_max_threshold etc still need to be checked, but 'LAR_thresholds' is just a placeholder.
            3. Define Dictionaries 
                This section describes the naming structure used throughout the project for all the files and GDBs. 
                prefix_dict is a dictionary that includes the prefixes and descriptions for all files associated with this section of the project.  
                centralMeridian is used when projecting data, and only contains information for the contiguous US. The key is the UTM zone, the value is the central meridian as a string in the proper format. 
            4. Define Functions 
            5. Do Stuff 

## PHASE 4: APPLYING FLAPS
    TBD
