# Dependencies
import requests as req
import numpy as np
import json
import pandas as pd
from pandas import ExcelWriter
from pandas import ExcelFile

##### Create function to make Geocode Data into DataFrame #####
def makeGeocodeDF(pdExel,sumLevel,fipsCol1,colName,fipsCol2=0):
    # Create DF out of excel
    df = pdExel.loc[pdExel['Summary Level'] == sumLevel]

    # If the summary level is 'county'
    if sumLevel == 50:
        # Add both fips code levels
        df = df[[fipsCol1,fipsCol2,'Area Name (including legal/statistical area description)']]
    else:
        # only add one fips code level
        df = df[[fipsCol1,'Area Name (including legal/statistical area description)']]

    # Rename columns
    df = df.rename(columns={'Area Name (including legal/statistical area description)' : colName})

    # Return DataFrame
    return df

# Read excel file of geo codes
geocodeMap = pd.read_excel('resources/2015-allgeocodes.xlsx', sheetname='Sheet1')

# Create DataFrame of States/State FIPS
geocodeMapState = makeGeocodeDF(geocodeMap,40,'State Code (FIPS)','State')
# Create DataFrame of County Names/County FIPS/State FIPS/
geocodeMapCounty = makeGeocodeDF(geocodeMap,50,'County Code (FIPS)','County','State Code (FIPS)')

# Create merged DataFrame with County and State FIPS and Names
geocodeMap = pd.merge(geocodeMapState,geocodeMapCounty, how='outer', on='State Code (FIPS)')

#####
##### USE geocodeMap to map FIPS to counties/states #####
#####
