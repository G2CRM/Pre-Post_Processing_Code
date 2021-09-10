"""
Stage Volume Input Generator v1.2

Generate stage volume inputs required by G2CRM using ArcMap. Requires 
setting up 5 input params. Variable names do not matter, but they
must be in the following order: 

    Model Area Layer: Layer
    Model Area Field: String
    DEM Layer: Layer
    Max Depth: String
    Output Folder: Folder

Output csv files with the following format:

    X           Y
    500         0
    1254        1
    3000        2
    7874        3
    16054       4
    19007       5
    ...         ...
    20000       max_depth


************************
Change Log

v1.1 - 8/27/2020

Removed dependency on "Plan_Areas" field
Added param ma_field to input model area field specifier name

v1.2 9/24/2020
Generate output xlsx instead of csv
    Requires openpyxl package - might not be a standard ArcMap package
"""

import arcpy
import pandas as pd
import os

################################
#   Inputs
################################

ma_shape_layer = arcpy.GetParameterAsText(0)
ma_field = arcpy.GetParameterAsText(1)
dem_layer = arcpy.GetParameterAsText(2)
depth_max = int(arcpy.GetParameterAsText(3))
output_folder = arcpy.GetParameterAsText(4)

start_depth = 1 # first value for stage i.e. column Y in output
depth_field_name = 'Flood_Model'

# debug mode
flag_debugging = False # set True to debug - will only run 1 specific MA
debug_ma = 'MA01a' # specify MA for debug mode

################################
#   Code Implementation
################################

arcpy.AddMessage('****************************************************')
arcpy.AddMessage('G2CRM Stage-Volume Input Data Generator')
arcpy.AddMessage('****************************************************')


arcpy.env.overwriteOutput = True
mxd = arcpy.mapping.MapDocument("Current")
df = arcpy.mapping.ListDataFrames(mxd)[0]

def move_layer_to_group(mxd, df, layer_name, group_name):
    """
    Move layer to group based on str names.
    layer_name: str
    group_name: str
    """
    arcpy.AddMessage(arcpy.mapping.ListLayers(mxd, group_name, df))
    layer_group = arcpy.mapping.ListLayers(mxd, group_name, df)[0]
    for lyr in arcpy.mapping.ListLayers(mxd):
        if lyr.name.lower() == layer_name.lower():
            arcpy.mapping.AddLayerToGroup(df, layer_group, lyr, 'BOTTOM')
            arcpy.mapping.RemoveLayer(df, lyr)


with arcpy.da.SearchCursor(ma_shape_layer, [ma_field], 
    where_clause=(ma_field + " = \'" + debug_ma + "'" if flag_debugging else None)) as cur: # debugging
# with arcpy.da.SearchCursor(ma_shape_layer, ['MA', 'Plan_Areas'], where_clause="") as cur: # debugging
# with arcpy.da.SearchCursor(ma_shape_layer, ['MA', 'Plan_Areas']) as cur:
    len_ma = arcpy.GetCount_management(ma_shape_layer) # number of MAs
    for i, row in enumerate(cur): #iterate through all MAs
        ma = row[0]
        arcpy.AddMessage('-----------')
        arcpy.AddMessage(str(i+1) + '/' + (str(1) if flag_debugging else str(len_ma)) + ' Working on ' + ma)

        # create boundary layers
        boundary_layer_name = 'Boundary_' + ma
        arcpy.analysis.Select(ma_shape_layer, boundary_layer_name, "MA = '" + ma + "'")

        # extract dem by mask
        dem_by_mask_name = 'Mask_' + ma
        new_mask = arcpy.sa.ExtractByMask(dem_layer, boundary_layer_name)
        new_mask.save(dem_by_mask_name)

        working_depth_volume_pair = []

        for depth in range(start_depth, depth_max + 1): # iterate through all depth ranges
            arcpy.AddMessage('Calculating volume at depth=' + str(depth))
            # Edit Flood Grid Attribute Field in separate Model shapefile
            if depth == start_depth: arcpy.AddField_management(boundary_layer_name, depth_field_name, "DOUBLE")
            arcpy.CalculateField_management(boundary_layer_name, depth_field_name, depth, 'PYTHON_9.3')

            # Create Grid for each flood elevation
            depth_layer_name = 'Depth_' + ma + "_" + str(depth) + "ft"
            arcpy.PolygonToRaster_conversion(boundary_layer_name, depth_field_name, depth_layer_name)

            # Calculate Cutfill between flood elevation and DEM
            cf_layer_name = "CF_" + depth_layer_name
            new_cf = arcpy.sa.CutFill(dem_by_mask_name, depth_layer_name)
            new_cf.save(cf_layer_name)

            # Calculate Volume Sum
            volume_at_depth = -sum(filter(lambda x: x < 0, [row[0] for row in arcpy.da.SearchCursor(cf_layer_name, 'VOLUME')]))
            working_depth_volume_pair.append((volume_at_depth, depth))

            # clean up depth layers - potential feature
            # move_layer_to_group(mxd, df, depth_layer_name, depth_group_name)
            # move_layer_to_group(mxd, df, cf_layer_name, cf_group_name)
        
        # clean-up non-depth layers - potential feature
        # move_layer_to_group(mxd, df, boundary_layer_name, boundary_group_name)
        # move_layer_to_group(mxd, df, dem_by_mask_var_name, mask_group_name)

        # Populate G2CRM Stage Volume Excel Spreadsheet
        csv_file_name = 'VolumeStageFunction_' + ma + '.xlsx'
        working_df = pd.DataFrame(working_depth_volume_pair, columns=['X', 'Y'])
        save_path = os.path.join(output_folder, csv_file_name)
        arcpy.AddMessage('Calculations for model area saved.')

        # populating function meta sheet
        vsf_df = pd.DataFrame(
            [["Base","FromDEM"]], 
            columns=["VolumeStageFunctionName", "VolumeStageFunctionDescription"])

        # pd.core.format.header_style = None
        # pd.io.formats.excel.header_style = None
        pd.formats.format.header_style = None # for pandas version 0.18.1 and before

        with pd.ExcelWriter(save_path) as writer:
            vsf_df.to_excel(writer, sheet_name='VolumeStageFunction', index=False)
            working_df.to_excel(writer, sheet_name='Base', index=False)

arcpy.env.overwriteOutput = False

arcpy.AddMessage('-----------')
arcpy.AddMessage('Calculations finished. All output files are saved to:')
arcpy.AddMessage(output_folder)
arcpy.AddMessage('****************************************************')

