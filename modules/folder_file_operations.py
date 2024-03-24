import os

def check_directory(directory):
    if os.path.isdir(directory) == False:
            raise FileNotFoundError(f"The directory {directory} does not exist")
        
    if directory.find("/") != -1:
        delim = "/"
    elif directory.find(os.sep) != -1:
        delim = os.sep
    else:
        delim = "/"
    if directory[-1] != delim:
        directory += delim
    return directory