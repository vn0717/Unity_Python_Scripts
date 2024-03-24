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
