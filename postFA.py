##
## Post Feature Analyst script
##
## This scirpt would be great to make an ArcGIS tool out of.
##

counties = []

# This next one needs to be formated so that it works in a loop.
#arcpy.CalculateField_management(in_table="alabama_ortho_al089_2015_Rsm2", field="AspRatio", expression="[Length]/[Width]", expression_type="VB", code_block="")

arcpy.Clip_analysis(in_features="%s Group\%sCo_CVM" %(county, county), clip_features="%s Group\%sCoAL_outline" %(county, county), out_feature_class="A:/Alabama/AL1cluster.gdb/%sCo_Clip" %(county), cluster_tolerance="")

arcpy.AddField_management(in_table="%s Group\%sCo_Prems_FINAL" %(county, county),\
                          field_name="AspRatio", field_type="SHORT", \
                          field_precision="", field_scale="", field_length="", \
                          field_alias="", field_is_nullable="NULLABLE", \
                          field_is_required="NON_REQUIRED", field_domain="")

# delete features based on the Length and AspRatio fields

# apply probability surface and/or masks

arcpy.Integrate_management(in_features="'%s Group\%sCo_Int' #" %(county, county), cluster_tolerance="100 Meters") 
	
arcpy.CollectEvents_stats(Input_Incident_Features="%s Group\%sCo_Int" %(county, county), Output_Weighted_Point_Feature_Class="A:/Alabama/AL1cluster.gdb/%sCo_Int_CollectEvents" %(county))

# project it into WGS 1984 Geographic Coordinate System?

arcpy.AddXY_management(in_features)
