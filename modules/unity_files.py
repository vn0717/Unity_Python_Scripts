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

    #convert to unity coordinates
    #unity switches the z and y coordiantes  
    data = np.swapaxes(data,1,2)


    #for each isosurface we want
    for surface in isosurfaces:

        #does something for the isosurface. (varable to find isosurface of level)
        vertices, triangles = mc.marching_cubes(data, surface)

        if file_type == "dae":
            #export results as a dae file
            mc.export_mesh(vertices, triangles, f"{save_path}{str(surface)}_{variable_name}.dae", f"{str(surface)}Surface")

        elif file_type == "obj":
            mc.export_obj(vertices, triangles, f"{save_path}{str(surface)}_{variable_name}.obj")

        else:
            raise ValueError(f"{file_type} is not a valid file type.  Only dae and obj files are supported.")
        
