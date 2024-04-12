"""
M. P. Vossen
Created: Feburary 3rd, 2024

Description:
Module that holds functions to save to various unity file types
"""

import struct
import numpy as np
import os
import mcubes as mc  
import warnings
from pint import UnitRegistry
import pandas as pd
import modules.folder_file_operations as ffops
from datetime import datetime, timezone
import json


def save_vector_field(U, V, W, filename, normalize=True):
    """
    Function that processes three demensional data into vectors.
    The vector data is then structured so it to be written into a .vf file so it can be 
    read by the Unity game engine as a vector field.

    Args:
        U (NUMPY ARRAY): An array that holds X component of a vector.  Must be 3 demensional.  
        V (NUMPY ARRAY): An array that holds Y component of a vector.  Must be 3 demensional.
        W (NUMPY ARRAY): An array that holds Z component of a vector.  Must be 3 demensional.
        filename (STRING): The file path and name of where the .vf file will be saved to
        normalize (BOOL, OPTIONAL): Whether to normalize the data to be between -1 and 1. Defaults to True.

    Returns:
        None
    """

    ###################
    # Data checks
    ###################
    if filename.find("/") != -1:
        sep = "/"
    elif filename.find(os.sep) != -1:
        sep = os.sep
    else:
        sep = ""

    if len(sep) != 0:
        split = filename.split(sep)
        split = split[:-1]
        filepath = "/".join(split)
        if os.path.exists(filepath) == False:
            raise FileNotFoundError(f"The directory path {filepath}/ does not exist")
        end_file_name = split[-1]
        filepath += "/"
    else:
        filepath = ""
        end_file_name = filename
    


    u_shape = U.shape
    v_shape = V.shape
    w_shape = W.shape

    for shape, dim in zip([u_shape, v_shape, w_shape], ["U", "V", "W"]):
        #verify the data is 3D
        if len(shape) != 3:
            raise ValueError(f"{dim} is {str(len(shape))} demensional.  The data needs to be 3 demensional.")

    #verify arrays match in size
    if u_shape != v_shape:
        raise ValueError(f"U ({str(u_shape)}) and V ({str(v_shape)}) arrays shape do not match")
    if u_shape != w_shape:
        raise ValueError(f"U ({str(u_shape)}) and W ({str(w_shape)}) arrays shape do not match")
    if v_shape != w_shape:
        raise ValueError(f"V ({str(v_shape)}) and W ({str(w_shape)}) arrays shape do not match")

    

    ###################
    # Process Data
    ###################

    #stack the data together to get one array.
    vector_field = np.stack((W,V,U))
    
    #this is where the data normalization happens
    if normalize == True:
        v_field = np.absolute(vector_field)
        maximum = np.amax(v_field)
        vector_field = vector_field / maximum

    # Determine volume size
    i, depth, height, width = vector_field.shape
    volume_size = (width, height, depth)
    fourcc = b'VF_F'
    stride = 3
    if vector_field.dtype == np.float64:
        vector_field = vector_field.astype(np.float32)  # Convert to float32
    elif vector_field.dtype == np.float16:
        vector_field = vector_field.astype(np.float32)  # Convert to float32
    elif vector_field.dtype == np.float128:
        vector_field = vector_field.astype(np.float32)  # Convert to float32
    else:
        raise ValueError(f"Unsupported data type")

    unity_axes = ["y", "z", "x"]
    for i, axis in enumerate(["y", "z", "x"]):
        # Open file and write data
        with open(f"{filepath}{axis}_{end_file_name}", 'wb') as f:
            # Write FourCC
            f.write(fourcc)

            # Write volume size
            f.write(struct.pack('<HHH', *volume_size))

            # Write data
            for z in range(depth):
                for y in range(height):
                    for x in range(width):
                        value = vector_field[i, z, y, x]
                        f.write(struct.pack('<f', value))



def save_isosurface(data, isosurfaces, variable_name, save_path, file_type="dae", smoothing = False):
    """
    Funtion to save isosurface of the data to a file format that the unity game engine can read

    Args:
        data (NUMPY ARRAY): The data to pull isosurfaces from
        isosurfaces (FLOAT or ARRAY LIKE): The isosurface or isosurfaces to pull from the data
        variable_name (STRING): Name of variable.  Is only used to create the filename
        save_path (STRING): Full path to where the data is to be save excluding the file name
        file_type (STRING, OPTIONAL): The Unity file type to create. Options are dae or obj. Defaults to "dae".
        smoothing (BOOL, OPTIONAL): Whether to smooth the data before pulling isosurfaces. Defaults to False.

    Returns:
        None

    """

    #################
    # Data checks
    #################

    if os.path.exists(save_path) == False:
            raise FileNotFoundError(f"The directory path {save_path} does not exist")

    #verify data is 3D
    if len(data.shape) != 3:
        raise ValueError(f"The isosurface data is {str(len(data.shape))} demensional.  The data needs to be 3 demensional.")
    
    #see if we have an array of surfaces or just one.  If it is just one, put it into a list so the loop works
    if len(np.shape(isosurfaces)) == 0:
        isosurfaces = [isosurfaces]

    #to avoid capitalization mistakes that cause logic errors, make sure everything is lower case
    file_type = file_type.lower()

    #just incase someone adds a . at the begining. This gets rid of it a prevents the logic error it would throw
    file_type = file_type.replace(".", "")



    #########################
    # Process data
    #########################

    #if we want smoothing, smooth the data
    if smoothing == True:
        data = mc.smooth(data)



    

    files_created = []

    #for each isosurface we want
    for surface in isosurfaces:

        #does something for the isosurface. (varable to find isosurface of level)
        vertices, triangles = mc.marching_cubes(data, surface)

        if file_type == "dae":
            file_name =  f"{save_path}{str(surface)}_{variable_name}.dae"
            #export results as a dae file
            mc.export_mesh(vertices, triangles, file_name, f"{str(surface)}Surface")

        elif file_type == "obj":
            file_name = f"{save_path}{str(surface)}_{variable_name}.obj"
            mc.export_obj(vertices, triangles, f"{save_path}{str(surface)}_{variable_name}.obj")

        else:
            raise ValueError(f"{file_type} is not a valid file type.  Only dae and obj files are supported.")
        
        files_created.append(file_name)
        

class unity_files:
    def __init__(self):
        self.__units__ = UnitRegistry()
        self.__cartesian__ = True
        self.__iso_data__ = {}
        self.__vector_dims__ = {}
        self.__radar__ = False
        self.__build_iso__ = False
        self.__build_vector__ = False
        self.__dim_strs__ = ['x', 'y', 'z']
        self.__radar_meta__ = None

    def input_isosurface_data(self, x, y, z, iso_surface_data, iso_surface_levels, time=None, file_type = ".dae", smooth=True, variable_name=None):
        """
        Method to input data to create isosurfaces.  This method does not
        create the isosurfaces and only intalizes the data.  You must
        run this method first before creating isosurfaces.

        Args:
            x (PINT ARRAY): The 3D x coordinate array of the data in normal x,y,z.  Must have pint units.
            y (PINT ARRAY): The 3D z coordinate array of the data in normal x,y,z.  Must have pint units.
            z (PINT ARRAY): The 3D z coordinate array of the data in normal x,y,z.  Must have pint units.
            iso_surface_data (PINT ARRAY): The 3D isosurface array of the data in normal x,y,z.
            iso_surface_values (ARRAY): A 1D array of values that isosurfaces should be created for
            time (DATETIME or PINT QUANTITY, OPTIONAL) : The time the data is valid for
            file_type (STRING, OPTIONAL): The Unity file type to create. Options are dae or obj. Defaults to "dae".
            smooth (BOOL, OPTIONAL): If the isosurfaces should be smoothed.  Defaults to True.  Can be computationaly expensive.
            variable_name (STRING, OPTIONAL) : A string that is the name of the variable
     
        """
    
        self.__build_iso__ = True
        self.__cartesian__, self.__iso_dims__ = self.__create_dim_data__(x,y,z)
        self.__iso_dims__["var"] = self.__create_var_data__(iso_surface_data)
        self.__isosurface_levels__ = iso_surface_levels
        self.__iso_smooth__ = smooth
        self.__iso_file_type__ = file_type
        self.__iso_var_name__ = variable_name
        if time is not None:
            self.__iso_dims__['time'] = time
        else:
            self.__iso_dims__['time'] = 0 * self.__units__.seconds



    def input_vector_data(self, x, y, z, U, V=None, W=None, time=None, normalize=False):
        """
        Method to input data to create vector data.  This method does not
        create the vector field and only intalizes the data.  You must
        run this method first before creating vector data.

        Args:
            x (PINT ARRAY): The 3D x coordinate array of the data in normal x,y,z.  Must have pint units.
            y (PINT ARRAY): The 3D z coordinate array of the data in normal x,y,z.  Must have pint units.
            z (PINT ARRAY): The 3D z coordinate array of the data in normal x,y,z.  Must have pint units.
            U (PINT ARRAY): The 3D array holding the u component of the vectors in the normal x,y,z coordinates.
            V (PINT ARRAY, OPTIONAL): The 3D array holding the v component of the vectors in the normal x,y,z coordinates. Defaults to None.
            W (PINT ARRAY, OPTIONAL): The 3D array holding the w component of the vectors in the normal x,y,z coordinates. Defaults to None.
            time (DATETIME or PINT QUANTITY, OPTIONAL) : The time the data is valid for
            normalize (BOOL, OPTIONAL): Whether to make wind values between -1 and 1 (True) or to use the full value (False).  Defaults to False
        """

        self.__build_vector__ = True
        self.__cartesian__, self.__vector_dims__ = self.__create_dim_data__(x,y,z)
        self.__vector_normalize__ = normalize
        self.__vector_dims__["U"] = self.__create_var_data__(U)
        if V is not None:
            self.__vector_dims__["V"] = self.__create_var_data__(V)
        if W is not None:
            self.__vector_dims__["W"] = self.__create_var_data__(W)

        if time is not None:
            self.__vector_dims__['time'] = time
        else:
            self.__vector_dims__['time'] = 0 * self.__units__.seconds
        





    def init_radar(self, radar_id):
        """
        Method to initalize radar data out puts.  This method
        mainly takes the radar id and finds the radar lat, lon,
        and elevation data to add to the final meta data file.

        Args:
            radar_id (STRING): 4 letter ID for the radar you are 
                creating unity files for


        """
        self.__radar__ = True

        #make sure the id is four letter.  If it is not, then we don't have an id to work with
        if len(radar_id) != 4:
            raise ValueError(f"{radar_id} is not a 4 letter id.  Enter the 4 letter ID of the radar.")

        #make all the letters in the id to be upper case
        radar_id = radar_id.upper()
        module_dir = os.path.dirname(__file__)
        #open the radar info csv that is contained in the repository from NVU-Lyndon
        #we need to find the module directory or else it uses the working
        #directory.
        radar_info = pd.read_csv(f"{module_dir}{os.sep}nexrad_sites.csv")
        #change the index to be the radar ID to make things simpler to index
        radar_info = radar_info.set_index("ID")

        #see if we get radar info for the radar id.  If we do the radar exists.
        #if we don't the radar does not exist as long as Lyndon's list is complete 
        try:
            coord_str = radar_info.loc[radar_id]["Coordinates"]
        except KeyError:
            raise ValueError(f"{radar_id} is not a valid NEXRAD site.")

        #the coordinates in Lyndon's list are unessisarly complex
        #and so we have to parse it out here
        coord_str = coord_str.replace(" ", "")
        coords = coord_str.split("/")

        lon = int(coords[1][:3])
        lon += (int(coords[1][3:5]) / 60)
        lon += (int(coords[1][5:7]) / 3600)
        if coords[1][-1] != "E":
            lon *= -1

        lat = int(coords[0][:2])
        lat += (int(coords[0][2:4]) / 60)
        lat += (int(coords[0][4:6]) / 3600)
        if coords[0][-1] == "S":
            lat *= -1

        #finally package everything up into a dictonary attached to the object
        self.__radar_meta__ = {
            "id":radar_id,
            "latitude":lat,
            "longitude":lon,
            "elevation": int(radar_info.loc[radar_id]["Elevation"]) + int(radar_info.loc[radar_id]["Tower_h"]),
            "elevation_units": "meter"
        }

    def remove_radar(self):
        """
        Method for removing the radar meta data.  This is 
        just in case someone accedently initalzes the radar
        data when they don't want it.
        """
        self.__radar__ = False
        self.__radar_meta__ = None
        

    def create_files(self, file_location):
        """
        Driver method for creating the selected unity files.
        It also build the meta data file.

        Args:
            file_location (STRING): Location to save files to.
        """
        meta = {}
        #python deprecated the easy .utcnow and this is the new way
        now = datetime.now(timezone.utc)
        meta["FILE_GENERATED"] = f"{now:%m/%d/%Y %H%M%S} UTC"


        file_location = ffops.check_directory(file_location)
        if self.__radar__ == True:
            meta["radar"] = self.__radar_meta__
        if self.__build_iso__ == True:
            meta["isosurface"] = self.__create_isosurface_files__(file_location)
        if self.__build_vector__ == True:
            meta["vector_field"] = self.__create_vector_files__(file_location)

        with open(f"{file_location}meta.json", "w") as outfile:
            json.dump(meta, outfile)




    def __create_isosurface_files__(self, file_location):
        """
        Method for creating isosurface files

        Args:
            file_location (STRING): Location where isosurface files are to be saved.

        Returns:
            DICTONARY: Meta data from the isosurface files
        """

        meta = {}
        if self.__cartesian__ == True:
            meta["grid"] = "cartesian"
        else:
            meta["grid"] = "latlon"

        #see if we have an array of surfaces or just one.  If it is just one, put it into a list so the loop works
        if len(np.shape(self.__isosurface_levels__)) == 0:
            self.__isosurface_levels__ = [self.__isosurface_levels__]

        #to avoid capitalization mistakes that cause logic errors, make sure everything is lower case
        file_type = self.__iso_file_type__.lower()

        #just incase someone adds a . at the begining. This gets rid of it a prevents the logic error it would throw
        file_type = file_type.replace(".", "")

        #correct the dimensions from the statndard math x,y,z to unity x,z,y.
        data = np.swapaxes(self.__iso_dims__["var"]["data"], 1, 2)
        x = np.swapaxes(self.__iso_dims__["x"]["data"],1,2)
        y = np.swapaxes(self.__iso_dims__["z"]["data"],1,2)
        z = np.swapaxes(self.__iso_dims__["y"]["data"],1,2)
        x_unit = self.__iso_dims__["x"]["units"]
        y_unit = self.__iso_dims__["z"]["units"]
        z_unit = self.__iso_dims__["y"]["units"]

        meta["unity_dims"] = True



        #########################
        # Process data
        #########################

        #if we want smoothing, smooth the data
        if self.__iso_smooth__ == True:
            data = mc.smooth(data)
        
        meta["smooth"] = self.__iso_smooth__

        if self.__iso_var_name__ is not None:
            variable_name = self.__iso_var_name__
        else:
            variable_name = "NVNP"

        time_f, time = self.__process_time__(self.__iso_dims__["time"])

        meta[time_f] = time

        #for each isosurface we want
        for surface in self.__isosurface_levels__:

            #does something for the isosurface. (varable to find isosurface of level)
            vertices, triangles = mc.marching_cubes(data, surface)

            if file_type == "dae":
                file_name =  f"{file_location}{str(surface)}_{variable_name}.dae"
                #export results as a dae file
                mc.export_mesh(vertices, triangles, file_name, f"{str(surface)}Surface")

            elif file_type == "obj":
                file_name = f"{file_location}{str(surface)}_{variable_name}.obj"
                mc.export_obj(vertices, triangles, f"{file_location}{str(surface)}_{variable_name}.obj")

            else:
                raise ValueError(f"{file_type} is not a valid file type.  Only dae and obj files are supported.")
            
            meta[f"{str(surface)}_{variable_name}.{file_type}"] = self.__get_iso_edges__(x,y,z,x_unit, y_unit, z_unit, data, surface)
            meta[f"{str(surface)}_{variable_name}.{file_type}"]["isosurface_units"] = str(self.__iso_dims__["var"]["units"])
            meta[f"{str(surface)}_{variable_name}.{file_type}"]["isosurface_level"] = str(surface)
            if variable_name != "NVNP":
                meta[f"{str(surface)}_{variable_name}.{file_type}"]["variable"] =  variable_name
            else:
                meta[f"{str(surface)}_{variable_name}.{file_type}"]["variable"] =  "No Variable Provided"
            
        return meta

    def __create_vector_files__(self, file_location):
        """
        Method for creating vector files

        Args:
            file_location (STRING): Location where to save the vector files


        Returns:
            DICTONARY: Meta data for the vector files
        """
        meta = {}
        #add valid time to the meta data
        time_f, time = self.__process_time__(self.__vector_dims__["time"])
        meta[time_f] = time

        #add the grid type to the meta data
        if self.__cartesian__ == True:
            meta["grid"] = "cartesian"
        else:
            meta["grid"] = "latlon"


        vector_dim_to_process = []
        dims = {}
        dim_units = {}

        #correct the dimensions from the statndard math x,y,z to unity x,z,y.
        U = np.swapaxes(self.__vector_dims__["U"]["data"],1,2)
        dim_units[f"x_vector_units"] = str(self.__vector_dims__["U"]["units"])
        vector_dim_to_process.append("x")
        try:
            V = np.swapaxes(self.__vector_dims__["W"]["data"],1,2)
            dim_units[f"y_vector_units"] = str(self.__vector_dims__["W"]["units"])
            y_exist = True
            vector_dim_to_process.append("y")
        except KeyError:
            y_exist = False
        try:
            W = np.swapaxes(self.__vector_dims__["V"]["data"],1,2)
            dim_units[f"z_vector_units"] = str(self.__vector_dims__["V"]["units"])
            vector_dim_to_process.append("z")
            z_exist = True
        except KeyError:
            z_exist = False


        x = np.swapaxes(self.__vector_dims__["x"]["data"],1,2)
        y = np.swapaxes(self.__vector_dims__["z"]["data"],1,2)
        z = np.swapaxes(self.__vector_dims__["y"]["data"],1,2)

        x_unit = self.__vector_dims__["x"]["units"]
        y_unit = self.__vector_dims__["z"]["units"]
        z_unit = self.__vector_dims__["y"]["units"]
               


        meta["unity_dims"] = True
            

        ###################
        # Process Data
        ###################
        if y_exist == True and z_exist == True:
            #stack the data together to get one array.
            vector_field = np.stack((W,V,U))
        elif y_exist == True and z_exist == False:
            #stack the data together to get one array.
            vector_field = np.stack((V,U))
        elif y_exist == False and z_exist == True:
            #stack the data together to get one array.
            vector_field = np.stack((W,U))
        else:
            vector_field = U[None, :]
        #this is where the data normalization happens
        if self.__vector_normalize__ == True:
            v_field = np.absolute(vector_field)
            maximum = np.amax(v_field)
            vector_field = vector_field / maximum

        # Determine volume size
        i, depth, height, width = vector_field.shape
        volume_size = (width, height, depth)
        fourcc = b'VF_F'
        stride = 3
        if vector_field.dtype != np.float32:
            vector_field = vector_field.astype(np.float32)  # Convert to float32       


        for dim, dim_str, dim_unit in zip([x,y,z], self.__dim_strs__, [x_unit, y_unit, z_unit]):
            dims[f"{dim_str}_min"] = str(np.nanmin(dim))
            dims[f"{dim_str}_max"] = str(np.nanmax(dim))
            dims[f"{dim_str}_coordinate_units"] = str(dim_unit)
            


        for i, axis in enumerate(vector_dim_to_process):
            # Open file and write data
            file_name = f"{axis}_vector.vf"
            with open(f"{file_location}{file_name}", 'wb') as f:
                # Write FourCC
                f.write(fourcc)

                # Write volume size
                f.write(struct.pack('<HHH', *volume_size))

                # Write data
                for z in range(depth):
                    for y in range(height):
                        for x in range(width):
                            value = vector_field[i, z, y, x]
                            try:
                                f.write(struct.pack('<f', value))
                            except:
                                raise Exception(f"Value = {str(value)}")

            meta[file_name] = dims
            meta[file_name][f"vector_units"] = dim_units[f"{axis}_vector_units"]

        return meta



    def __get_iso_edges__(self, x,y,z,x_unit, y_unit, z_unit, iso_data, level):
        """
        Method to find edges of isosurfaces for meta data

        Args:
            x (NUMPY ARRAY): The unity x coordinate of the data
            y (NUMPY ARRAY): The unity y coordinate of the data
            z (NUMPY ARRAY): The unity z coordinate of the data
            x_unit (STRING): The unity x coordinate variable
            y_unit (STRING): The unity y coordinate variable
            z_unit (STRING): The unity z coordinate variable
            iso_data (NUMPY ARRAY): The data being used to create isosurfaces in unity coodinates
            level (FLOAT or INT): The isosurface elvel

        Returns:
            DICTONARY: The meta data for the particular isosurface
        """
        meta = {}
        xs = x[iso_data >= level]
        ys = y[iso_data >= level]
        zs = z[iso_data >= level]
        
        for dim, dim_str, dim_unit in zip([xs,ys,zs], self.__dim_strs__, [x_unit, y_unit, z_unit]):
            #sometimes the isosurface doen't exist
            try:
                meta[f"{dim_str}_min"] = str(np.nanmin(dim))
                meta[f"{dim_str}_max"] = str(np.nanmax(dim))
            except:
                meta[f"{dim_str}_min"] = "N/A"
                meta[f"{dim_str}_max"] = "N/A"
            meta[f"{dim_str}_cooridnate_units"] = str(dim_unit)
        return meta


    def __create_var_data__(self, var):
        """
        Method to create variable dictonary data for the main variable dictonary

        Args:
            var (PINT ARRAY or ARRAY LIKE): The variable to be processed

        Returns:
            DICTONARY: Dictonary with variable data
        """
        final = {}
        try:
            if len(var.magnitude.shape) != 3:
                raise ValueError(f"The isosuface variable data is {str(len(var.magntitude.shape))} demensional.  The data needs to be 3 demensional.")
            final["units"] = var.units
            final["data"] = var.magnitude

        except AttributeError as e:
            if len(var.shape) != 3:
                raise ValueError(f"The isosuface variable data is {str(len(var.shape))} demensional.  The data needs to be 3 demensional.")
            final["units"] = "dimensionless"
            final["data"] = var
        return final
    
    def __create_dim_data__(self, x, y, z):
        """
        Method to create dimension variable dictonary

        Args:
            x (PINT ARRAY): The 3D x coordinate array of the data in normal x,y,z.  Must have pint units.
            y (PINT ARRAY): The 3D y coordinate array of the data in normal x,y,z.  Must have pint units.
            z (PINT ARRAY): The 3D z coordinate array of the data in normal x,y,z.  Must have pint units.

        Returns:
            DICTONARY: Dictonary with coordinate variable data
        """

        dims = {}
        #for each dimension lets seperate out the unit and magnitude of the data
        for dim_str, dim in zip(self.__dim_strs__, [x,y,z]):
            #verify data is 3D
            if len(dim.shape) != 3:
                raise ValueError(f"The {dim_str} cooridnate data is {str(len(dim.shape))} demensional.  The data needs to be 3 demensional.")
            #make sure we have units.  If not raise an error
            try:
                unit = dim.units
            except AttributeError:
                raise AttributeError(f"{dim_str} does not have any units.  Please use pint to add units to the data.")
            
            #if the unit is degrees then we are dealing with geographical data and thus 
            #we are not working with a carteasian coordinate
            if unit == "degree":
                if dim_str == "x":
                    cartesian = False
            #if the grid is cartesian then lets get everything to the same units
            #I choose meter to be the standard unit.
            else:
                dim = dim.to(self.__units__.meter)
                if dim_str == "x":
                    cartesian = True
            dims[dim_str] = {}
            dims[dim_str]["data"] = dim.magnitude
            dims[dim_str]["units"] = dim.units
        return cartesian, dims

    
    def __process_time__(self,time):
        """
        Method to determine time data type.  This method also reformats the
        time for use in the meta data

        Args:
            time (DATETIME or PINT QUANTITY): The time

        Returns:
            STRING: The time format
            STRING: The formatted time
        """
        if type(time) == datetime or type(time) == pd._libs.tslibs.timestamps.Timestamp:
            return "Date", f"{time:%m/%d/%Y %H%M%S}"
        else:
            time.to(self.__units__.seconds)
            return "Run_Time", str(round(time.magnitude,3))