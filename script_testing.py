from Automated_Review import *
import numpy as np
import arcpy
import os


def project_counties_custom(county_files, county_names, state_name, state_abbrev,
                            output_file_path, output_names):
    """
    NOTE: This function doesn't function. It needs work for it to work.
    This function modifies the project(...) function. It can project multiple counties at once.
    It assumes all counties are in the same US state and should be placed in the same directory.
    """
    # Check for issues.
    if not all([isinstance(item, basestring) for item in (county_files, county_names, output_names)]) \
           and not (len(county_files)==len(county_names)==len(output_names)):
        raise ValueError("county_files, county_names, and output_names should contain the same number of values.")

    for t in range(0, len(county_files)):
        dirrr = os.path.dirname(county_files[t])
        county_outline = os.path.join(county_outline_folder,
                                    state_name + '.gdb',
                                    county_names[t] + 'Co' + state_abbrev + '_outline')
        FIPS, UTM = find_FIPS_UTM(county_outline)
        project(county_files[t], dirrr, UTM, state_abbrev, county_names[t], custom_file_name=output_names[t])

if __name__ == "__main__":
    county_files = (r'O:\AI Modeling Coop Agreement 2017\Grace Cap Stone Validation\Validation_Results\TP_FN_Counties\MN_Cottonwood_TP_FN_OLD.shp',
                    r'O:\AI Modeling Coop Agreement 2017\Grace Cap Stone Validation\Validation_Results\TP_FN_Counties\MN_Kandiyohi_TP_FN_OLD.shp',
                    r'O:\AI Modeling Coop Agreement 2017\Grace Cap Stone Validation\Validation_Results\TP_FN_Counties\MN_Redwood_TP_FN_OLD.shp')
    county_names = ("Cottonwood", "Kandiyohi", "Redwood")
    cust_names = []   
    for thing in county_names:
        cust_names += ["MN_"+thing+"_TP_FN.shp"]

    #project_counties_custom(county_files, county_names, "Minnesota", "MN", os.path.dirname(county_files[0]), cust_names)
    
    print "Ready to test."
    
