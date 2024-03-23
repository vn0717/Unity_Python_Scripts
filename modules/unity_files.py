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
        self.files_to_build()
        self.__cartesian__ = True
        self.__iso_dims__ = {}
        self.__vector_dims__ = {}
        self.__radar__ == False
        self.__build_iso__ = False
        self.__build_vector__ = False
        self.__dim_strs__ = ['x', 'y', 'z']
        self.__radar_meta__ = None

    def input_isosurface_coordinate_data(self, x, y, z):
        """
        Method to input data coordinate data to create isosurfaces.  This method does not
        create the isosurfaces and only intalizes settings.  You must
        run this method first before creating isosurfaces.

        Args:
            x (PINT ARRAY): The x coordinate of the data in normal x,y,z.  Must have pint units.
            y (PINT ARRAY): The y coordinate of the data in normal x,y,z.  Must have pint units.
            z (PINT ARRAY): The z coordinate of the data in normal x,y,z.  Must have pint units.
     
        """
        self.__iso_dims__ = {}
        self.__build_iso__ = True

        #for each dimension lets seperate out the unit and magnitude of the data
        for dim_str, dim in zip(self.__dim_strs__, [x,y,z]):

            #make sure we have units.  If not raise an error
            try:
                unit = dim.units
            except AttributeError:
                raise AttributeError(f"{dim_str} does not have any units.  Please use pint to add units to the data.")
            
            #if the unit is degrees then we are dealing with geographical data and thus 
            #we are not working with a carteasian coordinate
            if unit == "degree":
                self.__cartesian__ = False
            #if the grid is cartesian then lets get everything to the same units
            #I choose meter to be the standard unit.
            else:
                dim = dim.to(self.__units__.meter)
                self.__cartesian__ = True
            
            self.__iso_dims__[dim_str]["data"] = dim.magnitude
            self.__iso_dims__[dim_str]["units"] = dim.units





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

        #open the radar info csv that is contained in the repository from NVU-Lyndon
        radar_info = pd.read_csv("../extra/nexrad_sites.csv")
        #change the index to be the radar ID to make things simpler to index
        radar_info = radar_info.set_index["ID"]

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
        print(coord_str)

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
            "elevation_units": "m"
        }

    def remove_radar(self):
        """
        Method for removing the radar meta data.  This is 
        just in case someone accedently initalzes the radar
        data when they don't want it.
        """
        self.__radar__ = False
        self.__radar_meta__ = None
        

    def create_files(self):

    
