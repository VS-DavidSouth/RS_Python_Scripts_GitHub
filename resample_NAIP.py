##
## resample_NAIP.py
##

import arcpy, os

# this next line gives us access to the nameFormat function
sys.path.insert(0, r'O:\AI Modeling Coop Agreement 2017\David_working\Python') 
from Converting_state_names_and_abreviations import *

def resample(input_raster, output_location, state_abbrev, county_name):
    ##
    ## This function reprojects the selected raster to 2m resolution.
    ##
    ## Input Variables:
    ##      input_raster:   The file location of the native NAIP imagery.
    ##                       This is likely in 1m resolution, but may be
    ##                       as small as .3m in some states like California.
    ##
    ##      output_location:    The path to the folder where the reprojected file should
    ##                           be placed in. This does not include the filename.
    ##
    ##      state_abbrev & county_name: The respective state abbreviation, 'NC' for
    ##                                   example, and the respective county name,
    ##                                   such as 'Union'.
    ##
    outputName = 'NAIP_2m_' + state_abbrev + '_' + nameFormat(county_name)
    if not arcpy.Exists(os.path.join(output_location, outputName)):
        if arcpy.Exists(input_raster):
            print "Resampling", state_abbrev, county_name, "..."
            arcpy.Resample_management (input_raster, os.path.join(output_location, outputName), \
                                        cell_size="2 2", resampling_type="NEAREST")
        else:
            print "--", state_abbrev, county_name, "input NAIP imagery not found."
    else:
        print "-- Resampled raster for", state_abbrev, county_name, "already exists!"
            # may want to remove the above line in case it gets annoying for users
    

if __name__ == '__main__':
    ()    

    
