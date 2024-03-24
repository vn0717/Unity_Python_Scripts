## Metadata JSON File Documentation
<br>
Every time isosurface files or vector files are created a metadata.json file will be created by this program.  This is intended to give Unity developers something to reference when they build their program wind since the .dae, .obj, and .vf files do not contain any spatial information.  This file will contain the following information in the hierarchy specified here. 
<br>
<br>

* <b>FILE_GENERATED:</b> (STRING) The time the files were created in UTC formatted mm/dd/yyyy HHMMSS
* <b>radar:</b> The section that contains information related to the radar.  This section is optional and will not be present when the data does not work with actual radar data
    * <b>id:</b> (STRING) The four letter identifier of the radar
    * <b>latitude:</b> (FLOAT) The latitude of the radar in decimal degrees
    * <b>longitude:</b> (FLOAT) The longitude of the radar in decimal degrees
    * <b>elevation:</b> (INTEGER) The height of the radar above sea level.  This number also includes the radar tower height.
    * <b>elevation_units:</b> (STRING) The units that the elevation is in.
* <b>isosurface:</b> The section that contains information for the isosurface files.  This section is optional and will not be present when the data does not create isosurfaces
    * <b>grid:</b> (STRING) The type of grid all of the isosurface files are on.  It can be cartesian or latlon right now.
    * <b>unity_dims:</b> (BOOL) If the data has been converted to unity dimensions.  True means it has, False means it has not.
    * <b>smooth:</b> (BOOL) If the data has been smoothed by the mccubes smoother.  True means the data has been smoothed.
    * <b>Date:</b> (STRING) The date the data is valid for.  Formatted mm/dd/yyyy HHMMSS in the timezone specifed by the user.  This option is used for real data cases and will be replaced by Run_Time for ideal cases
    * <b>Run_Time:</b> (STRING) The time stamp in seconds that the data is valid for in seconds.  This option is used for ideal cases and will be replaced with Date for real cases.
    * <b>FILE NAME:</b> Instead of FILE NAME this will be the actual name of the file.  In this subsection there is data that is specific to the file.
        * <b>x_min:</b> (STRING) The left most distance or point that had data used to create the isosurface.  Will be N/A if there is no data for the isosurface.
        * <b>x_max:</b> (STRING) The right most distance or point that had data used to create the isosurface  Will be N/A if there is no data for the isosurface.
        * <b>x_coordinate_units:</b> (STRING) The units of the x axis coordinate.
        * <b>y_min:</b> (STRING) The minimum distance or point in the y axis that had values used in the isosurface.  This is in unity coordinates if unity_dims = True.  Will be N/A if there is no data for the isosurface.
        * <b>y_max:</b> (STRING) The maximum distance or point in the y axis that had values used in the isosurface.  This is in unity coordinates if unity_dims = True.  Will be N/A if there is no data for the isosurface.
        * <b>y_coordinate_units:</b> (STRING) The units of the y axis coordinate.  This is in unity coordinates if unity_dims = True.
        * <b>z_min:</b> (STRING) The minimum distance or point in the z axis that had values used in the isosurface.  This is in unity coordinates if unity_dims = True.  Will be N/A if there is no data for the isosurface.
        * <b>z_max:</b> (STRING) The maximum distance or point in the z axis that had values used in the isosurface.  This is in unity coordinates if unity_dims = True.  Will be N/A if there is no data for the isosurface.
        * <b>z_coordinate_units:</b> (STRING) The units of the z axis coordinate.  This is in unity coordinates if unity_dims = True.
        * <b>isosurface_units:</b> (STRING) The units that the isosurface level is in
        * <b>isosurface_level:</b> (STRING) The value that was used to create the isosurface
        * <b>variable:</b> (STRING) The variable that the isosurface was created from
* <b>vector_field:</b> The section that contatins information for the vector field files.  This section is optional and will not be present when the data does not create vector fields
    * <b>grid:</b> (STRING) The type of grid all of the isosurface files are on.  It can be cartesian or latlon right now.
    * <b>unity_dims:</b> (BOOL) If the data has been converted to unity dimensions.  True means it has, False means it has not.
    * <b>Date:</b> (STRING) The date the data is valid for.  Formatted mm/dd/yyyy HHMMSS in the timezone specifed by the user.  This option is used for real data cases and will be replaced by Run_Time for ideal cases
    * <b>Run_Time:</b> (STRING) The time stamp in seconds that the data is valid for in seconds.  This option is used for ideal cases and will be replaced with Date for real cases.
    * <b>FILE NAME:</b> Instead of FILE NAME this will be the actual name of the file.  In this subsection there is data that is specific to the file.
        * <b>x_min:</b> (STRING) The left most distance or point that had data used to create the vector field.
        * <b>x_max:</b> (STRING) The right most distance or point that had data used to create the vector field.
        * <b>x_coordinate_units:</b> (STRING) The units of the x axis coordinate.
        * <b>y_min:</b> (STRING) The minimum distance or point in the y axis that had values used in the vector field.  This is in unity coordinates if unity_dims = True.
        * <b>y_max:</b> (STRING) The maximum distance or point in the y axis that had values used in the vector field.  This is in unity coordinates if unity_dims = True.
        * <b>y_coordinate_units:</b> (STRING) The units of the y axis coordinate.  This is in unity coordinates if unity_dims = True.
        * <b>z_min:</b> (STRING) The minimum distance or point in the z axis that had values used in the vector field.  This is in unity coordinates if unity_dims = True.
        * <b>z_max:</b> (STRING) The maximum distance or point in the z axis that had values used in the vector field.  This is in unity coordinates if unity_dims = True.
        * <b>z_coordinate_units:</b> (STRING) The units of the z axis coordinate.  This is in unity coordinates if unity_dims = True.

        
