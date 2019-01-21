import os
import arcpy


def delete_outdated(folder):
    walk = arcpy.da.Walk(folder, type="Point")
    for dirpath, dirnames, filenames in walk:
        for name in filenames:
            if 'AutoReview_' in name or 'Clip_' in name or 'CollectEvents_' in name or 'Integrate_' in name or 'Masking_' in name or 'LAR_' in name or 'ProbSurf_' in name or 'SimSampling_' in name:
                print "Deleting:", name
                arcpy.Delete_management(os.path.join(dirpath, name))
    print "\n\nAll done!"
