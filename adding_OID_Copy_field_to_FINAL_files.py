## This file is meant to be used to add a copy of the OBJECTID field
##  for the _FINAL and _FINAL_FINAL files, so that later on the field
##  can be used to determine where to draw the line between TP and FN.
##
## Note: this didn't work. The OBJECTID field just reset and counted
##  up from one, so this made no change at all.  


import arcpy, os

def findField(fc, fn):  #fn is short for Field Name
  fieldnames = [field.name for field in arcpy.ListFields(fc)]
  if fn in fieldnames:
    return True
  else:
    return False

#folderLocation = r'N:\Remote Sensing Projects\2016 Cooperative Agreement Poultry Barns\Documents\Deliverables\Library\Poultry_Premises_Results'
folderLocation = r'O:\AI Modeling Coop Agreement 2017\David_working\TEST.gdb'


walk = arcpy.da.Walk(folderLocation, datatype = "FeatureClass", type = "Point")

for dirpath, dirnames, filenames in walk:
    for filename in filenames:
        filepath = os.path.join(dirpath, filename)
        if findField(filepath, "OID_Copy") == False:
            if filename == 'FranklinCo_FN_tttttesssttttt':  # Remove this later
                arcpy.AddField_management(in_table = filepath, field_name = "OID_Copy", field_type = "SHORT", field_precision = "", field_scale = "", field_length = "", field_alias = "", field_is_nullable = "NULLABLE", field_is_required = "NON_REQUIRED", field_domain = "")
                arcpy.CalculateField_management(in_table = filepath, field = "OID_Copy", expression = "!OBJECTID!", expression_type = "PYTHON", code_block = "")                                            

                print filename, "completed."
