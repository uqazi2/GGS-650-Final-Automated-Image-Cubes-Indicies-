import os

import numpy
import rasterio
import pandas



def create_image_stacks(raw_path,year,stack_path):
    """
    This Function stacks individual bands of imagery from subfolders. 
    -----------
    input parameters:
    raw_path: path to raw data
    year: year to be processed 
    stack_path: path for outputted images
    -----------
    output:
    multiband rasters 
    """
    
    #get path to data for selected year
    full_path = os.path.join(raw_path, year)

    #create empty folder to store filepaths in year folder 
    folders_path = []

    #get subfolder paths 
    for foldername in os.listdir(full_path):
        
        #Append individual file paths to  "folders_path"
        folders_path.append(os.path.join(full_path,foldername))
        
    
    #go through each subfolder of year to read bands  
    for idx,tile in enumerate(folders_path):
        #print(idx,tile)
        contents = os.listdir(tile)

        #create list to store bands in order 
        img_stack = []

        #read bands and assign them to list 
        for file in contents:
            if file.endswith('B1.TIF'):
                coastal_aerosol = os.path.join(tile,file) 
                img_stack.append(coastal_aerosol)   
            if file.endswith('B2.TIF'):
                blue = os.path.join(tile,file) 
                img_stack.append(blue)
            if file.endswith('B3.TIF'):
                green = os.path.join(tile,file) 
                img_stack.append(green)
            if file.endswith('B4.TIF'):
                red = os.path.join(tile,file)
                img_stack.append(red)
            if file.endswith('B5.TIF'):
                nir = os.path.join(tile,file)
                img_stack.append(nir) 
            if file.endswith('B6.TIF'):
                swir1 = os.path.join(tile,file)
                img_stack.append(swir1)
            if file.endswith('B7.TIF'):
                swir2 = os.path.join(tile,file)
                img_stack.append(swir2)
            
        # print(img_stack)
        
        #check first band
        src = rasterio.open(img_stack[0])
        # print(src)

        #check metadata 
        metadata = src.meta
        
        #update metadata
        metadata.update(count=len(img_stack))
        metadata.update(driver='GTiff')

        #define outpath 
        outpath = os.path.join(stack_path,year)

        #check if outpath exists, if not create 
        if os.path.exists(outpath):
            print('Images will be written to: Processed/{} folder'.format(year))
        if not os.path.exists(outpath):
            os.makedirs(outpath)

        #define name for images 
        fullname = (str(tile))
        img_name = '/' + fullname[-23:-6] + '_stack.tif'
        #print(img_name)
        
        #write image out
        with rasterio.open(outpath + img_name,'w', **metadata) as dst:
            for id, layer in enumerate(img_stack, start=1):
                with rasterio.open(layer) as src:
                    dst.write(src.read(1),id)
        print('image written:',img_name)


def indicie_from_stack(stack_path,year,indicie):
    """
    This Function relies on images created from the 'create_image_stacks' functions 
    and computes one of the following spectral indicies:
    
    Normalized Difference Vegetation Index: NDVI = (NIR - RED) / (NIR + RED) 

    Normalized Difference Moisture Index: NDMI = (NIR - SWIR1) / (NIR + SWIR1)

    Normalized Burn Ratio: NBR = (NIR - SWIR2) / (NIR + SWIR2)

    -----------
    input parameters:
    stack_path: path to folder containing image stacks 
    year: year to be processed
    indicie: user's choice of spectral index, where '0' = NDVI, '1' = NDMI, '2' = NBR  
    -----------
    output:
    single band index raster 
    """

    #get full path 
    stack_path = os.path.join(stack_path,year)

    #Create empty list to store paths of image stacks 
    stacks = []    

    #Get paths to image stacks 
    for idx,image in enumerate(os.listdir(stack_path)[:-1]):
        # print(idx,image)
        if image.endswith('.tif'):
            image_path = os.path.join(stack_path, image)
            # print(image_path)

            #append stack paths to 'stacks list'
            stacks.append(image_path)
    
    print(stacks)

    #Create empty list to hold to indicie arrays 
    indicies_holder = [] 

    #parse through stacks list, open each file, and create calculations 
    for idx, stack in enumerate(stacks):
        raster = rasterio.open(stack)
        # print(raster)
        raster_read = raster.read()

        #Get metadata from band 
        metadata = raster.meta
        
        #Avoid Errors with 'true divide' 
        numpy.seterr(divide='ignore', invalid='ignore')

        if indicie == 0:
            print('Calculating NDVI')
            index_name = 'NDVI'

            #Calculate NDVI 
            spectral_index = ((raster_read[4].astype(float) - raster_read[3].astype(float))/(raster_read[4].astype(float) + raster_read[3].astype(float)))

        elif indicie == 1:
            print('Calculating NDMI')
            index_name = 'NDMI'

            #Calculate NDMI 
            spectral_index = ((raster_read[4].astype(float) - raster_read[5].astype(float))/(raster_read[4].astype(float) + raster_read[5].astype(float)))
        
        elif indicie == 2:
            print('Calculating NBR')
            index_name = 'NBR'

            #Calculate NBR 
            spectral_index = ((raster_read[4].astype(float) - raster_read[6].astype(float))/(raster_read[4].astype(float) + raster_read[6].astype(float)))
        
        elif indicie != 0 or 1 or 2:
            raise ValueError('please check indicie selection, must be in range: 0-2, where 0 = NDVI, 1 = NDMI, 2 = NBR')

        #define name for images 
        fullname = str(raster)
        indicie_name = '/' + fullname[-38:-21] + '_{}.tif'.format(index_name)
        

        #Check Min and Max values of indicie
        print('max {} value for'.format(index_name), indicie_name, 'is: ', numpy.nanmax(spectral_index))
        print('min {} value for'.format(index_name), indicie_name, 'is: ', numpy.nanmin(spectral_index))

        #append indicies arrays to list 
        indicies_holder.append(spectral_index)

        #update metadata 
        indicie_dtype = spectral_index.dtype
        metadata.update(dtype=indicie_dtype)
        metadata.update(count=1)

        #define path out 
        outpath = os.path.join(stack_path,index_name)

        #check if outpath exists, if not create 
        if os.path.exists(outpath):
            print('Images will be written to: Processed/{}/{} folder'.format(year,index_name))
        if not os.path.exists(outpath):
            os.makedirs(outpath)

        #write image out
        with rasterio.open(outpath + indicie_name, 'w', **metadata) as dst:
            for id, spectral_index in enumerate(indicies_holder, start=1):
                    dst.write(spectral_index,1)
        print('image written:', indicie_name)


    print('Completed Writing {} Images out'.format(index_name)) 


def indicie_from_band(raw_path,year,indicie,stack_path):
    """
    This Function calculates a user's desired spectral index for a given year from individual bands of data. 
    It computes one of the following spectral indicies:
    
    Normalized Difference Vegetation Index: NDVI = (NIR - RED) / (NIR + RED) 

    Normalized Difference Moisture Index: NDMI = (NIR - SWIR1) / (NIR + SWIR1)

    Normalized Burn Ratio: NBR = (NIR - SWIR2) / (NIR + SWIR2)

    -----------
    input parameters:
    raw_path: path to raw data 
    year: year to be processed
    indicie: user's choice of spectral index, where '0' = NDVI, '1' = NDMI, '2' = NBR  
    -----------
    output:
    single band index raster 
    """
    #get path to data for selected year
    full_path = os.path.join(raw_path, year)

    #create empty folder to store filepaths in year folder 
    folders_path = []

    #create empty folder to store indicie arrays 
    indicies_holder = []

    #get subfolder paths 
    for foldername in os.listdir(full_path):
        
        #Append individual file paths to  "folders_path"
        folders_path.append(os.path.join(full_path,foldername))

    #create list to store bands in order 
    img_stack = []    

    #go through each subfolder of year to read bands  
    for idx,tile in enumerate(folders_path):
        #print(idx,tile)
        contents = os.listdir(tile)

        #read bands and assign them to list 
        for file in contents:
            if file.endswith('B1.TIF'):
                coastal_aerosol = os.path.join(tile,file) 
                img_stack.append(coastal_aerosol)   
            if file.endswith('B2.TIF'):
                blue = os.path.join(tile,file) 
                img_stack.append(blue)
            if file.endswith('B3.TIF'):
                green = os.path.join(tile,file) 
                img_stack.append(green)
            if file.endswith('B4.TIF'):
                red = os.path.join(tile,file)
                img_stack.append(red)
            if file.endswith('B5.TIF'):
                nir = os.path.join(tile,file)
                img_stack.append(nir) 
            if file.endswith('B6.TIF'):
                swir1 = os.path.join(tile,file)
                img_stack.append(swir1)
            if file.endswith('B7.TIF'):
                swir2 = os.path.join(tile,file)
                img_stack.append(swir2)

        #check first band
        src = rasterio.open(img_stack[0])
        # print(src)
        
        #check metadata 
        metadata = src.meta
        
        #Avoid Errors with 'true divide' 
        numpy.seterr(divide='ignore', invalid='ignore')        
                
        if indicie == 0:
            print('Calculating NDVI')
            index_name = 'NDVI'

            for img in img_stack:

                #Open Bands 
                red_band = rasterio.open(red)
                nir_band = rasterio.open(nir)

                #Read Bands
                red_band = red_band.read()
                nir_band = nir_band.read()

                #Calculate NDVI
                spectral_index = ((nir_band.astype(float) - red_band.astype(float))/(nir_band.astype(float) + red_band.astype(float)))
                

        elif indicie == 1:
            print('Calculating NDMI')
            index_name = 'NDMI'

            for img in img_stack:

                #Open Bands 
                nir_band = rasterio.open(nir)
                swir1_band = rasterio.open(swir1)

                #Read Bands 
                nir_band = nir_band.read()
                swir1_band = swir1_band.read()

                #Calculate NDMI
                spectral_index = ((nir_band.astype(float) - swir1_band.astype(float))/(nir_band.astype(float) + swir1_band.astype(float)))
        
        elif indicie == 2:
            print('Calculating NBR')
            index_name = 'NBR'

            for img in img_stack:

                #Open Bands
                nir_band = rasterio.open(nir)
                swir2_band = rasterio.open(swir2)

                #Read Bands 
                nir_band = nir_band.read()
                swir2_band = swir2_band.read() 

                #Calculate NBR
                spectral_index = ((nir_band.astype(float) - swir2_band.astype(float))/(nir_band.astype(float) + swir2_band.astype(float)))

            
        elif indicie != 0 or 1 or 2:
            raise ValueError('please check indicie selection, must be in range: 0-2, where 0 = NDVI, 1 = NDMI, 2 = NBR')

        #define name for images 
        fullname = str(tile)
        indicie_name = '/' + fullname[-23:-6] + '_{}.tif'.format(index_name)
        #print(indicie_name) 

        #Check Min and Max values of indicie
        print('max {} value for'.format(index_name), indicie_name, 'is: ', numpy.nanmax(spectral_index))
        print('min {} value for'.format(index_name), indicie_name, 'is: ', numpy.nanmin(spectral_index))

        #append indicies arrays to list 
        indicies_holder.append(spectral_index)

        #update metadata 
        indicie_dtype = spectral_index.dtype
        metadata.update(dtype=indicie_dtype)
        metadata.update(count=1)

        #define path out 
        #outpath = (r'C:\Users\cfcni\Desktop\FALL 22 GGS\GGS 650\final-proj\proccesed\{}\{}'.format(year,index_name))
        outpath = os.path.join(stack_path,year,index_name)

        #check if outpath exists, if not create 
        if os.path.exists(outpath):
            print('Images will be written to: Processed/{}/{} folder'.format(year,index_name))
        if not os.path.exists(outpath):
            os.makedirs(outpath)

        #write image out
        with rasterio.open(outpath + indicie_name, 'w', **metadata) as dst:
            for id, spectral_index in enumerate(indicies_holder):
                    dst.write(spectral_index)
        print('image written:', indicie_name, id)


    print('Completed Writing {} Images out'.format(index_name)) 


def average_indicie(stack_path, year, indicie):
    """
    This Function calculates a  composite image for a user's desired spectral index for a given year from pre-created indicie products. 
    It computes a composite image for one of the following spectral indicies:
    
    Normalized Difference Vegetation Index: NDVI = (NIR - RED) / (NIR + RED) 

    Normalized Difference Moisture Index: NDMI = (NIR - SWIR1) / (NIR + SWIR1)

    Normalized Burn Ratio: NBR = (NIR - SWIR2) / (NIR + SWIR2)

    -----------
    input parameters:
    stack_path: path to folder containing image stacks
    year: year to be processed
    indicie: user's choice of spectral index, where '0' = NDVI, '1' = NDMI, '2' = NBR  
    -----------
    output:
    single band averaged index raster 
    """
    
    #Check which indicie is selected for path
    if indicie == 0:
        index_name = 'NDVI'
    elif indicie ==1:
        index_name = 'NDMI'
    elif indicie == 2:
        index_name = 'NBR'
    elif indicie != 0 or 1 or 2:
        print('please check indicie selection, must be in range: 0-2, where 0 = NDVI, 1 = NDMI, 2 = NBR')

    #get path to data for selected year
    full_path = os.path.join(stack_path, year, index_name)
    if os.path.exists(full_path):
        print('checking folder for {},{}'.format(year,index_name))
        
    if not os.path.exists(full_path):
        print('Path does not exist, Check that desired indicie: {} products have been calculated'.format(index_name))
    
    
    #Create empty list to store image paths 
    image_paths = []

    #Create list to store image names 
    image_names = []
    
    #Get list of paths to each indicie image 
    for idx, image in enumerate(os.listdir(full_path)):
        if image.endswith('{}.tif'.format(index_name)):
            image_path = os.path.join(full_path,image)
            image_paths.append(image_path)

    
    #Get length of list, needed for averaging calculations 
    num_files = len(image_paths)

    #Avoid Errors with 'true divide' 
    numpy.seterr(divide='ignore', invalid='ignore')

    #Create list to store numpy arrays of indicies 
    arrays_list = []

    #Create list to store dict of image information 
    values_list = []

    #parse through image paths list and open images 
    for idx, image in enumerate(image_paths):
        raster = rasterio.open(image)
        
        #get metadata 
        metadata = raster.meta

        #Get names for each raster 
        raster_str = (str(raster))
        image_name = raster_str[-37:-15]

        #Read raster as numpy array 
        raster_read = raster.read()
        arrays_list.append(raster_read)

        #Add data to values list
        values_list.append({
            'Filename' : image_name,
            'Min': numpy.nanmin(raster_read),
            'Max': numpy.nanmax(raster_read),
            'Mean': numpy.nanmean(raster_read),
            'Median':numpy.nanmedian(raster_read)
        })
        
        
    #Get Shape of Array    
    master_shape = numpy.shape(arrays_list[0])

    #Calculate smallest array so all others can be resized for calculations 
    for i in range(0,len(arrays_list)):
        if numpy.shape(arrays_list[i]) < master_shape:
            master_shape = numpy.shape(arrays_list[i])

    print(master_shape)
    
    #Create empty list to store reshaped arrays 
    reshaped_arrays = []

    #Reshape Arrays 
    for idx,array in enumerate(arrays_list):
    # for array in arrays_list:
        try:
            new_array = numpy.reshape(array, master_shape, order='A')
            print('reshaping arrays')
            reshaped_arrays.append(new_array)
        except ValueError:
            new_array = numpy.resize(array, master_shape)
            print('Cannot Reshape Array Sized: {}, Will Resize Instead, though results may decline'.format(numpy.shape(array)))
            reshaped_arrays.append(new_array) 

    #Calculate averaged array
    out_array = sum(reshaped_arrays) / num_files 
    
    #add averaged data to values_list
    values_list.append({
            'Filename' : 'AVERAGE_{}'.format(index_name),
            'Min': numpy.nanmin(out_array),
            'Max': numpy.nanmax(out_array),
            'Mean': numpy.nanmean(out_array),
            'Median':numpy.nanmedian(out_array)
        })
    
    #convert values_list to pandas dataframe
    values_df = pandas.DataFrame(values_list) 

    #create path to averages folder
    averages_path = os.path.join(stack_path,year,'AVERAGES')
    
    #check if outpath exists, if not create    
    if os.path.exists(averages_path):
            print('Images and CSV will be written to: Processed/{}/AVERAGES folder'.format(year))
    if not os.path.exists(averages_path):
            os.makedirs(averages_path)
    
    #define out path for csv 
    csv_path = os.path.join(averages_path, 'averages_{}_{}.csv'.format(index_name,year))

    #wrtie csv out 
    values_df.to_csv(csv_path, index=False)

    #define path out for image 
    img_path = os.path.join(averages_path, 'averaged_{}_{}.tif'.format(index_name,year))

    #write image out 
    with rasterio.open(img_path,'w', **metadata) as dst:
        dst.write(out_array)



raw_path = (r"D:\ggs 650 final\raw")
stack_path = (r"D:\ggs 650 final\processed")


indicies = [0,1,2]
years = [2022,2020,2021]

for year in years:
    year = str(year)
    #create_image_stacks(raw_path,year,stack_path)

    for indicie in indicies:
        
        #indicie_from_stack(stack_path,year,indicie)

        indicie_from_band(raw_path,year,indicie,stack_path)

        average_indicie(stack_path,year,indicie)


# year = '2021'
# indicie = 1
#create_image_stacks(raw_path,year,stack_path)

#indicie_from_stack(stack_path,year,indicie)

#indicie_from_band(raw_path,year,indicie,stack_path)

"""
INDICIES FROM BAND REMEDIES THE SHAPING ERROR
"""

#average_indicie(stack_path,year,indicie)
    

