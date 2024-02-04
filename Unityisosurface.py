'''
M. Vossen
Feburary, 2019
Program that creates isosurfaces for unity to read
'''


import numpy as np 
import netCDF4 as nc 
import mcubes as mc  
from metpy import calc 
from metpy.units import units  

#Path to file
filepath = ''
saveFilepath = ''


for days in ["19", "20", "21", "22"]:
    for hours in ["00","06","12","18"]:
        #filename
        filename = "201402" + days + "_" + hours + "_pres_trimmed.nc"

        #Extracting data from netCDF4 data
        data = nc.Dataset(filepath + filename)

        #slice out the domain needed
        latstart = 65
        latend = 140
        lonstart = 460
        lonend = 600

        #extract temp varable for teh theta calculation
        temperature = data.variables['TMP_P0_L100_GLL0'][:,latstart:latend, lonstart:lonend] * units.kelvin
        pressurelevels = data.variables["lv_ISBL0"][:]

        #create bland pressure array of ones
        pressure = np.ones(np.shape(temperature))

        #initalize the counter to keep track of the pressur eindex of the array
        count = 0

        #creating an array of pressure for each pressure level
        #NEEDED FOR METPY CALCULATION
        for p in pressurelevels:
            #go to pressure index and set it equal to the pressure
            pressure[count,:,:] = pressure[count,:,:] * p
            #go up an index
            count += 1
        
        #give unts for pressure.  METPY needs this
        pressure = pressure * units.pascals

        #calculate theta
        theta = calc.potential_temperature(pressure, temperature)

        #get rid of theta units
        theta = theta * (1/units.kelvin)

        for Theta in range(280,345,5):

            #does something for the isosurface. (varable to find isosurface of level)
            vertices, triangles = mc.marchin_cubes(np.array(theta), Theta)

            #export results as a dae file
            mc.export_mesh(vertices, triangles, saveFilepath + days + "thetaSurfaces/" + hours + "zSurfaces/" + hours + "z_" + days + "_" + str(Theta) + "Theta.dae", str(Theta) + "Surface")
            print("Finished " + days + "_" + hours + "z_" + str(Theta) + "Surface")
