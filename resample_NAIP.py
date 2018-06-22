##
## resample_NAIP.py
##

import arcpy, os

def resample(input_raster, output_location, state_abbrev, county_name):
    ##
    ## This function reprojectes the selected file to 2m resolution.
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
    outputName = 'NAIP_2m_' + state_abbrev + '_' + county_name
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
