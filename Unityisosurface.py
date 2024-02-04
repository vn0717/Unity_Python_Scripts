'''
M. P. Vossen
Feburary, 2019
Program that creates isosurfaces for the unity game engine to read and display

M. P. Vossen
Feburary, 2024
Modernized and cleaned up the code

'''
import numpy as np 
import netCDF4 as nc 
import mcubes as mc  
from metpy import calc 
from metpy.units import units
from datetime import datetime
import pandas as pd  

##########################
# User Settings          #
##########################

#Path to file and file name
filepath = ''

#where the output unity asses is going to be save to
saveFilepath = ''

#the start and end dates you want isosurfaces for
t_start = datetime(2014,2,19,0)
t_end = datetime(2014,2,22,18)

#how frequently you want data for.  This follows the convention
#used by the pandas date_range funtion for frequency
t_freq = "6H"

#indecies to use to slice out.  This is grabage and should
#be changed to lat lon using xarray.  I don't have this file
#type and I don't know how it is structured and so I can't fix
#it right now
latstart = 65
latend = 140
lonstart = 460
lonend = 600

#the first theta level you want in kelvin
lowest_theta = 280
#the last theta level you want in kelvin
highest_theta = 340
#the resolution of theta level you want in between the lowest
#and highest theta level in kelvin
theta_resolution = 5

###############################
# End User Settings           #
###############################

dates = pd.date_range(t_start,t_end, freq=t_freq)

for day in dates:
    #the date_range function outputs numpy dates, regular datetimes
    #are easier to work with and so we convert
    day = pd.to_datetime(day)

    #filename
    filename = f"{day:%Y%m%d_%H}_pres_trimmed.nc"

    #Extracting data from netCDF4 data
    data = nc.Dataset(filepath + filename)



    #extract temp varable for teh theta calculation
    temperature = data.variables['TMP_P0_L100_GLL0'][:,latstart:latend, lonstart:lonend] * units.kelvin
    pressurelevels = data.variables["lv_ISBL0"][:]

    #create bland pressure array of ones
    pressure = np.ones(np.shape(temperature))

    #creating an array of pressure for each pressure level
    #NEEDED FOR METPY CALCULATION
    for count, p in enumerate(pressurelevels):
        #go to pressure index and set it equal to the pressure
        pressure[count,:,:] = pressure[count,:,:] * p

    
    #give unts for pressure.  METPY needs this
    pressure = pressure * units.pascals

    #calculate theta
    theta = calc.potential_temperature(pressure, temperature)

    #get rid of theta units
    theta = np.array(theta)

    for Theta in range(lowest_theta,highest_theta+theta_resolution,theta_resolution):

        #does something for the isosurface. (varable to find isosurface of level)
        vertices, triangles = mc.marchin_cubes(theta, Theta)

        #export results as a dae file
        mc.export_mesh(vertices, triangles, f"{saveFilepath}{day:%d}thetaSurfaces/{day:%H}zSurfaces/{day:%H}z_{day:%d}_{str(Theta)}Theta.dae", f"{str(Theta)}Surface")
        print(f"Finished {day:%m/%d/%Y %H%M} UTC {str(Theta)}K Surface")
