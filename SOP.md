## PHASE 1: CREATING MODELS 
For all 594 US counties selected for analysis, NAIP imagery was downloaded from the [NRCS website](https://nrcs.app.box.com/v/naip). County mosiac layers were availabe at 1m or smaller resolution and were resampled to 2m using `resample_NAIP.py`.
The Feature Analyst extension for ArcGIS 10.5 was used to create model files (extension `.afe`) for each US state that contained at least one county from the 596 selected counties. This model file was then used to create 'Batch' files by running the model in Feature Analyst on the resampled NAIP files for counties within the same US state. For further methods of how the model files were created and used to create the Bach files, see documentation from the regional pilot study with 35 counties. 
A strict naming convention is used throughout the files used for this project, which can be found in `naming_conventions.md`. For `Automated_Review.py` to function, it is important that all Batch files are named like 'Batch_\[ST]_\[County Name]', otherwise the script will overlook the files (having Z\[##] and c\[#] between state abbreviation and county name will not effect anything).
    
## PHASE 2: AUTOMATED REVIEW SCRIPT
### Getting the script running
#### Step 1. Open the Automated_Review.py file in IDLE(Python GUI), the IDE that comes with ArcGIS. Click `File > Open` and navigate to `Automated_Review.py`. Click `Run > Run Module` and save if prompted.
DO NOT DOUBLE CLICK OR RUN THE SCRIPT FILE WITHOUT CHECKING THAT THE PARAMETERS ARE CORRECT FIRST! 

#### Step 2. Allow the script to run. Watch for errors, and if something looks really wrong, hit `ctrl + c` to stop IDLE.
Watch the readout, as it will print out the current step that is running and will give useful information. It is expected that each county will take about 7 minutes, so running many counties at once can take quite a while.
It is recommended to do these in batches.

### More detail about the Automated_Review.py script
Things required to run the script: 
1. A computer with ArcGIS 10.5 or more recent installed. Previous versions of ArcGIS may work, but they are untested. It is recommended to run this script in the IDLE program that comes with ArcGIS. 
2. The Spatial Analyst ArcGIS extension. It needs to be installed and have at least one available license. 
3. Batch files. These are point shapefile or feature class files which were derived from the resampled NAIP files and the model files. These files have a lot of clutter and false positives which are later removed by `Automated_Review.py`.
	* Associated parameters: 
	  * `cluster_list`
	  * `county_outline_folder`
	* Associated functions: 
	  * `clip(…)`
	  * `add_FIPS_info(…)` which is used in the `clip(…)` and  `collapse_points(…)` functions 
	  * `clip_buffer(…)` which is within `masking(…)` 
4. Probability surface raster file. This is for the entire contiguous US, sometimes abbreviated prob_surf, and is originally from FLAPS. 
	* Associated parameters: 
	  * `prob_surface_raster`
	  * `prob_surface_threshold`
	* Associated functions: 
	  * `probSurface(…)`
5. Mask shapefiles or feature classes, along with any buffer values. Buffer values can be zero. Masks can be either negative masks (no barns will appear within this area; ex: 15m buffer from roads) or positive masks (barns will should only appear inside this area; ex: commercial land polygons). If no masks are to be used, either for neg_masks or pos_masks, follow the directions in the code for formatting. 
    * Associated parameters: 
	  * `neg_masks`
	  * `pos_masks`
	* Associated functions: 
	  * `masking(…)` 
6. A CSV file for Adjusted FLAPS. This involves taking raw FLAPS output for Pullets, Layers and Turkeys and deleting all points below a threshold (400 birds, 1000 birds, etc) to eliminate any 'backyard' farms that are not large scale production facilities.  The CSV should have farm totals for each county, which will be used to determine how many points should be selected during the simulatedSampling(…) function. 
	* Associated parameters: 
	  * `adjFLAPS_CSV`
	* Associated functions: 
	  * `simulated_sampling(…)`
7. A location for the tracking file. It is not necessary to create a CSV file at this location, the script will create a blank one and fill it if needed. Optionally, this can be turned off by setting `track_completed_counties = False`.
	* Associated parameters: 
	  * `progress_tracking_file`
	  * `track_completed_counties`
	* Associated functions: 
	  * `mark_county_as_completed(…)`
8. Output location to store all the files. This should probably have a terabyte of storage space or more, just in case. 
	* Associated parameters: 
	  * `output_folder`
	  * `save_intermediates`
	* Associated functions: 
	  * Basically any function that outputs a file will put them at the location specified in output_folder unless told otherwise. 
9. Important numeric parameters. These include the following variables:  
 	* `prob_surface_threshold`
 	* `L_max_threshold`
 	* `L_min_threshold`
 	* `AR_max_threshold`
 	* `AR_min_threshold`
 	* `num_iterations`

### General structure of the script:
1. Description 
	* A general overview of the script. 
2. Setup 
	* Those seeking to modify the code should be aware and at least generally competent with the following libraries: 
	  * `os`
	  * `sys` 
	  * `numpy` (referred to as `np`)
3. Parameters
	* Some parameters are optional and may or may not need to be specified. They are as follows: 
	  * `run_script_as_tool`
	  * `save_intermediates`
	  * `track_completed_counties`
	  * `regional_35_counties`
	  * `ssBins_matrix`
	  * `skip_list`
	  * The whole `if run_script_as_tool == True:` section. Ignore this if you aren't using the script as a custom arcGIS tool. 
	  * `LAR_thresholds`, This doesn't need to be messed with because it is really just putting 4 parameters into a single list which is easier to input into the LAR function. Note that the individual `L_max_threshold` and similar parameters still need to be checked.
4. Define Dictionaries 
	* This section describes the naming structure used throughout the project for all the files and GDBs. 
	  * `prefix_dict` is a dictionary that includes the prefixes and descriptions for all files associated with this section of the project.  
	  * `central_meridian` is used when projecting data, and only contains information for the contiguous US. The key is the UTM zone, the value is the central meridian as a string in the proper format. 
5. Define Functions
	* This section is where the various functions that `Automated_Review.py` uses to function. Each function has a small description at the very beginning of its code that summarizes what it does and anything else important about it.
	* The major functions that actually do geoprocessing are:
	  * `clip(...)`
	  * `LAR(...)`
	  * `masking(...)`
	  * `prob_surface(...)`
	  * `collapse_points(...)`
	  * `simulated_sampling(...)`
	  * `project(...)`
6. Do Stuff 
	* This section is composed of a series of loops. The first loop loops for each cluster, which then reads all the Batch files in the cluster, then loops for each Batch file within the cluster.
	* In order, `clip(...)`, `LAR(...)`, `masking(...)`, `prob_surface(...)`, `collapse_points(...)`, `simulated_sampling(...)`, and `project(...)` are all used.
	* Any errors that happen during any of the functions are saved in a list called `errors`, which is printed at the end. Be sure to check it after the script has been run.
## PHASE 3: APPLYING FLAPS
    On a random 1-for-1 basis in the 594 high poultry counties, FLAPS locations will be swapped out for our more accurate remotely sensed locations from the Automated_Review script. This will create a dataset that has 594 US counties with points with FLAPS demographics and remotely sensed locations, and in the non-594 counties will be straight FLAPS.
