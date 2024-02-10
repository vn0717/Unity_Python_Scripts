"""
NEXRAD to Unity

An object that transforms NEXRAD radar data into an isosurface
that Unity is able to read in.

Michael P. Vossen
Created: 2/10/2024
Last Worked on: 2/10/2024
"""

import s3fs
from datetime import datetime
import warnings
import numpy as np
from Modules import unity_files

class nexrad_to_unity:
    def __init__(self, radar, time):
        self.__s3__ = s3fs.S3FileSystem(anon=True)
        self.__radar__ = radar.upper()
        self.__time__ = time
        self.__nexrad_bucket__ = "noaa-nexrad-level2"
        self.__check_radar_inputs__()

        self.change_radar_grid()



    def change_radar(self, radar, time):
        """
        Method that changes the radar and time to get radar data for

        Args:
            radar (STRING): The four letter identifier for the radar
            time (DATETIME): The time radar data is requested for
        """
        self.__radar__ = radar
        self.__time__ = time
        self.__check_radar_inputs__()

    def change_radar_grid(self, horizontal_resolution=1000, x_start=-100, x_end=100, y_start=-100, y_end=100, z_start=0, z_end=20, vertical_resolution = 500):
        """
        Method to change radar grid values

        Args:
            horizontal_resolution (FLOAT, OPTIONAL): Horizontal resolution of the radar grid in meters. Defaults to 1000.
            x_start (FLOAT, OPTIONAL): The distance from the radar in the x direction that the left edge of the box starts in km. Defaults to -100.
            x_end (FLOAT, OPTIONAL): The distance from the radar in the x direction that the right edge of the box starts in km. Defaults to 100.
            y_start (FLOAT, OPTIONAL): The distance from the radar in the y direction that the bottom edge of the box starts in km. Defaults to -100.
            y_end (FLOAT, OPTIONAL): The distance from the radar in the y direction that the top edge of the box starts in km. Defaults to 100.
            z_start (FLOAT, OPTIONAL): The bottom of the grid the z direction in km. Defaults to 0.
            z_end (FLOAT, OPTIONAL): The top of teh gird in the z direction in km. Defaults to 20.
            vertical_resolution (FLOAT, OPTIONAL): Vertical resolution of the radar grid in meters. Defaults to 500.
        """

        self.__horizontal_resolution__ = horizontal_resolution
        self.__x_start__ = x_start * 1000
        self.__x_end__ = x_end * 1000
        self.__y_end__ = y_end * 1000
        self.__y_start__ = y_start * 1000
        self.__z_start__ = z_start * 1000
        self.__z_end__ = z_end * 1000
        self.__vertical_resolution__ = vertical_resolution
        self.__check_grid_inputs__()

    def create_file(self, save_location, isosurfaces, variable = "reflectivity", file_type="dae", smooth=False):
        """
        Method to create Unity Isosurface file from radar data

        Args:
            save_location (STRING): The directory path to where you want the isosurface files saved to
            isosurfaces (ARRAY LIKE): The variable values you want isosurfaces for
            variable (STRING, OPTIONAL): The radar variable you want isosurfaces for. Defaults to "reflectivity".
            file_type(BOOL, OPTIONAL): If you want isosurfaces smoothed before they are saved. Defaults to False.

        """


        from pyart.io import read_nexrad_archive
        from pyart import filters
        from pyart.map import grid_from_radars

        ####################################
        # Find Radar File
        ####################################
        #list files in bucket for day
        radar_files = self.__s3__.ls(self.__bucket_string__)

        #for each file find the time it is for and find the one that is closest
        #to the date of choice
        for f_index, file in enumerate(radar_files):
            #need to initalize future time due to logic later
            #this date is arbritrary
            if f_index == 0:
                future_time = datetime(1970,1,1)

            #create a list of the differnt directories with the file name in the last index
            directories = file.split("/")
            file_name = directories[-1]
            file_ending = file_name[-3:]

            #NEXRAD files have changed over the years, this deals with that
            #We don't use these files
            if file_ending == "MDM" or file_ending == "tar":
                pass
            #.gz is a file type we use
            elif file_ending == ".gz":
                file_sub_ending = file_name[-6:-3]
                if file_sub_ending == "V03":
                    file_date = datetime.strptime(file_name, f"{self.__radar__}%Y%m%d_%H%M%S_V03.gz")
                elif file_sub_ending == "V06":
                    file_date = datetime.strptime(file_name, f"{self.__radar__}%Y%m%d_%H%M%S_V06.gz")
                else:
                    file_date = datetime.strptime(file_name, f"{self.__radar__}%Y%m%d_%H%M%S.gz")
            #the modern files
            elif file_ending == "V06":
                file_date = datetime.strptime(file_name, f"{self.__radar__}%Y%m%d_%H%M%S_V06")
            #if it is a file type we don't know raise and error
            else:
                raise Exception(f"Unknown file type of {file_name}.  This is not your problem but it is mine.")
            if file_ending != "MDM" and file_ending != "tar":
                #set dates in case we break out of the loop.  This helps
                #find the closest time since the files are sequential
                past_time = future_time
                future_time = file_date

                #if the file date is after the time we want, stop the loop
                if file_date > self.__time__:
                    break
        #if the file isn't the first one, we have past times
        if f_index != 0:
            future_file = radar_files[f_index]
            past_file = radar_files[f_index-1]
            #just in cast the file one index in the past is 
            #the files we don't care about
            if past_file[-3:] == "tar" or past_file[-3:] == "MDM":
                past_file = radar_files[f_index-2]

            dt_past = self.__time__ - past_time
            dt_future = future_time - self.__time__

            if dt_past >= dt_future:
                file = future_file
                f_time = future_time
                dt = dt_future
            else:
                file = past_file
                f_time = past_time
                dt = dt_past
        #if the file is the first file in the list, we have not past times and so the first one
        #in the list is our file
        else:
            file = radar_files[f_index]
            f_time = future_time
            dt = future_time - self.__time__

        t_min = dt.seconds / 60

        if t_min >= 15:
            warnings.warn(f"Data is not close to the file and is {str(round(t_min,2))} minutes off from the selected time of {self.__time__:%m/%d/%Y %H%M} UTC")
        print(f"Selected file for {self.__radar__} at {f_time:%m/%d/%Y %H%M%S} UTC")


        ######################################
        #Grid Radar Data
        ######################################

        #find the number of grid points based on the starting and ending points using the resolution
        x_grid_points = int((self.__x_end__ - self.__x_start__) / self.__horizontal_resolution__)
        y_grid_points = int((self.__y_end__ - self.__y_start__) / self.__horizontal_resolution__)
        z_grid_points = int((self.__z_end__ - self.__z_start__) / self.__vertical_resolution__)

        #open radar file
        radar = read_nexrad_archive(f"s3://{file}")
        #create gate filter
        gatefilter = filters.GateFilter(radar)
        gatefilter.exclude_transition()
        gatefilter.exclude_masked(variable)

        #grid the radar data
        radar_grid = grid_from_radars(
            (radar,),
            gatefilters=(gatefilter,),
            grid_shape=(z_grid_points, y_grid_points, x_grid_points),
            grid_limits=((self.__z_start__, self.__z_end__), (self.__y_start__, self.__y_end__), (self.__x_start__, self.__x_end__)),
            fields=[variable],
        )


        ################################
        #Save Isosurface
        ################################

        #save the isosurfaces
        unity_files.save_isosurface(radar_grid.fields[variable]["data"],isosurfaces, variable, save_location, file_type=file_type, smoothing=smooth)
        print(f"Isosurface files of {self.__radar__} for {f_time:%m/%d/%Y %H%M%S} UTC created in {save_location}")


    def get_grid_info(self):
        print(f"\
        Horizontal Resolution:  {self.__horizontal_resolution__} m\n\
        Vertical Resolution:    {self.__vertical_resolution__} m\n\
        \n\
        Left X or Starting X:   {str(self.__x_start__/1000)} km\n\
        Right X or Ending X:    {str(self.__x_end__/1000)} km\n\
        \n\
        Bottom Y or Starting Y: {str(self.__y_start__/1000)} km\n\
        Top Y or Ending Y:      {str(self.__y_end__/1000)} km\n\
        \n\
        Bottom Z or Starting Z: {str(self.__z_start__/1000)} km\n\
        Top Z or Ending Z:      {str(self.__z_end__/1000)} km\n\
        \n\
        ")

    def get_radar_info(self):
        print(f"NEXRAD to Unity is looking for radar data at {self.__time__:%m/%d/%Y %H%M} UTC for {self.__radar__}")




    def __check_radar_inputs__(self):
        """
        A private method for checking user radar inputs to make sure they are available in the NEXRAD data

        """
        #check data types to make sure they are correct
        if type(self.__time__) != datetime:
            raise ValueError("The time you have entered for time in nexrad_to_unity is not a datetime.  Make sure time is a datetime.")
        if type(self.__radar__) != str:
            raise ValueError("The radar you have entered for radar in nexrad_to_unity is not a string.  Make sure radar is a string.")
        if len(self.__radar__) != 4:
            raise ValueError(f"{self.__radar__} is not a valid radar.  Make your your radar is a 4 digit string (e.g., KMPX).")

        #we will create the bucket string as we go
        self.__bucket_string__ = self.__nexrad_bucket__

        #check the year and make sure it exists in the NEXRAD bucket
        av = self.__s3__.ls(self.__bucket_string__ , detail=False)
        check = self.__check_list_val__(f"{self.__time__:%Y}", av)
        if check == False:
            raise ValueError(f"{self.__time__:%Y} is a year that falls outside the years that NEXRAD is operational.  Your year is likely too old or in the future.")
        else:
            self.__bucket_string__  += f"/{self.__time__:%Y}"

        #check the month and make sure it exists in the NEXRAD bucket
        av = self.__s3__.ls(self.__bucket_string__ , detail=False)
        check = self.__check_list_val__(f"{self.__time__:%m}", av)
        if check == False:
            raise ValueError(f"{self.__time__:%m} is a month that is not available in the year {self.__time__:%Y}.  Your month is likely too old or in the future.")
        else:
            self.__bucket_string__ += f"/{self.__time__:%m}"

        #check the day and make sure it exists in the NEXRAD bucket
        av = self.__s3__.ls(self.__bucket_string__, detail=False)
        check = self.__check_list_val__(f"{self.__time__:%d}", av)
        if check == False:
            raise ValueError(f"{self.__time__:%d} is a day that is not available in the for {self.__time__:%B %Y}.  Your day is likely too old or in the future.")
        else:
            self.__bucket_string__ += f"/{self.__time__:%d}"

        #check the radar and make sure it exists for the date in the bucket
        av = self.__s3__.ls(self.__bucket_string__, detail=False)
        check = self.__check_list_val__(self.__radar__, av)
        if check == False:
            raise ValueError(f"{self.__radar__} is not available for {self.__time__:%m/%d/%Y}.")
        else:
            self.__bucket_string__ += f"/{self.__radar__}"

    def __check_grid_inputs__(self):
        """
        A private method to check the grid specification inputs

        """

        if self.__x_start__ > self.__x_end__:
            raise ValueError(f"The starting x ({str(self.__x_start__ / 1000)}) value cannot be greater than the ending x ({str(self.__x_end__ / 1000)})")
        if self.__y_start__ > self.__y_end__:
            raise ValueError(f"The starting y ({str(self.__y_start__ / 1000)}) value cannot be greater than the ending y ({str(self.__y_end__ / 1000)})")
        if self.__z_start__ > self.__z_end__:
            raise ValueError(f"The starting z ({str(self.__z_start__ / 1000)}) value cannot be greater than the ending z ({str(self.__z_end__ / 1000)})") 
        if self.__z_start__ < 0:
            raise ValueError(f"Your starting z must be greater than 0.  {str(self.__z_start__ / 1000)} is below ground.")
        
        for distance,description in zip([self.__x_start__, self.__x_end__, self.__y_start__, self.__y_end__], ["X start", "X end", "Y start", "Y end"]):
            if distance > 230000:
                warnings.warn(f"{description} is greater than 230 km and is beyond the maximum range of NEXRAD")
            elif distance < -230000:
                warnings.warn(f"{description} is less than -230 km and is beyond the maximum range of NEXRAD")


        

        if self.__horizontal_resolution__ <= 0:
            raise ValueError(f"A radar horizontal resolution of {str(self.__horizontal_resolution__)} meters is not possible and must be greater than 0")
        if self.__vertical_resolution__ <= 0:
            raise ValueError(f"A radar vertical resolution of {str(self.__vertical_resolution__)} meters is not possible and must be greater than 0")
        


        if self.__horizontal_resolution__ < 250:
            warnings.warn(f"Horizontal resolution of {str(self.__horizontal_resolution__)} meters is set lower than spatial resolution of NEXRAD (250 meters)")

        if self.__horizontal_resolution__ > 10000:
            warnings.warn(f"Horizontal resolution of the radar data is very coarse and features may be missing")

        if self.__vertical_resolution__ > 2000:
            warnings.warn(f"Vertical resolution of the radar data is very coarse and features may be missing")


    def __check_list_val__(self, val, check_list):
        """
        A private method to check to see if a directory exists in a list of directories
        Args:
            val (STRING): Value of a directory to look for in list
            check_list (LIST): List of directories to find a value in

        Returns:
            BOOL : Whether the value exists in the string
        """
        for check_string in check_list:
            check_vals = check_string.split("/")
            check_val = check_vals[-1]
            if check_val == val:
                return True
            
        return False





if __name__ == "__main__":
    a = nexrad_to_unity("KMPX", datetime(2010,3,3,0,30))
    a.get_grid_info()
    a.get_radar_info()
    a.create_file("C:/Users/mpvos/Desktop/", [20])