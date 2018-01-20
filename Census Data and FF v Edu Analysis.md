

```python
# Dependencies
import requests as req
import numpy as np
from scipy import stats
import json
import pandas as pd
from pandas import ExcelWriter
from pandas import ExcelFile
import matplotlib.pyplot as plt
import seaborn as sns
```


```python
###############################################################################
# Income and Education DataFrames to use:
    # By County:
        # By Value:
            # incomeDFmapped - INCOME
            # eduDFmapped - EDUCATION
        # Normalized
            # normIncome - INCOME
            # normEdu - EDUCATION
    # By State:
        # By Value:
            # incomeByState - INCOME
            # eduByState - EDUCATION
        # Normalized
            # incomeByStateNorm - INCOME
            # eduByStateNorm - EDUCATION
###############################################################################

##### MAP GEOCODES (FIPS) TO STATES/COUNTIES #####
# Create function to make Geocode Data into DataFrame
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
# Create DataFrame of States and Abbreviations
abbrMap = pd.read_excel('resources/stateAbbreviation.xlsx')

# Create merged DataFrame with County and State FIPS and Names
geocodeMap = pd.merge(geocodeMapState,geocodeMapCounty, how='outer', on='State Code (FIPS)')

#/ Variables/DFs to use:
    #/ For state/county mapping: geocodeMap
    #/ remember to merge on BOTH State and County (county FIPs repeat)

##### CENSUS DATA #####
#/// SETUP 'GET' Variables \\\#
# Function to dynamically create variable ID lists
def createIdList(r1,r2,s,avoid=[]): #range start, range stop, id string, avoid ids (optional)

    i = [] # List variable

    # For all variables in the range
    for x in range(r1,r2):

        # If there are variables to avoid, pass
        if x in avoid:
            pass

        # If id is greater than 9
        elif x > 9:
            i.append(s+str(x)+'E')

        # Add a leading zero for IDs below 10
        else:
            i.append(s+'0'+str(x)+'E')

    # Return list
    return i

# Function to create a dictionary of IDs and their string
def createIdDict(k,v):

    n = 0 #counter
    d = {} #dictionary

    # For each ID in list
    for x in k:

        # Add it as a key and add appropriate bucket as value
        d[x] = v[n%len(v)] #use remainder to determine bucket (if it loops)
        n += 1 # Increase counter

    # Rename state/county to match geomap
    d['state'] = 'State Code (FIPS)'
    d['county'] = 'County Code (FIPS)'

    # Return Dictionary
    return d

# HOUSEHOLD INCOME: Create List and Dictionary
householdIncomeIdList = createIdList(2,18,'B19001_0')
householdIncomeBuckets = ['< $10k',
                          '$10K - $14,999',
                          '$15K - $19,999',
                          '$20K - $24,999',
                          '$25K - $29,999',
                          '$30K - $34,999',
                          '$35K - $39,999',
                          '$40K - $44,999',
                          '$45K - $49,999',
                          '$50K - $59,999',
                          '$60K - $74,999',
                          '$75K - $99,999',
                          '$100K - $124,999',
                          '$125K - $149,999',
                          '$150K - $199,999',
                          '$200K +']
householdIncomeDict = createIdDict(householdIncomeIdList,householdIncomeBuckets)

# EDUCATIONAL ATTAINMENT: Create List and Dictionary
notInclude = [1,2,3,11,19,27,35,43,44,52,60,68,76] #id's not to include in list
educationIdList = createIdList(1,84,'B15001_0',notInclude)
educationAttainmentBuckets = ['Less than 9th grade',
                              '9th to 12th grade, no diploma',
                              'High school graduate',
                              'Some college, no degree',
                              'Associate\'s degree',
                              'Bachelor\'s degree',
                              'Graduate or professional degree']
educationDict = createIdDict(educationIdList,educationAttainmentBuckets)
# Split education list in 2 because of 50 variable arg max
educationIdList1 = educationIdList[:int(len(educationIdList)/2)]
educationIdList2 = educationIdList[int(len(educationIdList)/2):]

# POPULATION: Create Dictionary
populationDict = createIdDict(['B01001_001E'],['Population'])

# Create string of ID's to query
idLists = [householdIncomeIdList,educationIdList1,educationIdList2] # List of lists
getArgs = []

# Create list of get arguments (all id's)
for l in idLists:

    getIds = '' #string

    # For all IDs in the list
    for i in l:

        getIds = getIds + i + ',' #add ID to final string

    getIds = getIds[:-1] #remove last comma
    getArgs.append(getIds) #add to ID list

# Append population to get args
getArgs.append((list(populationDict.keys()))[0])

#/// Setup Query URL \\\#
# Variables
year = 2016
apiKey = 'a9bba28cbc522f8f9d8ae3b88ef030fba6034516'
baseURL = 'https://api.census.gov/data/{}/acs/acs1/'.format(year)
forArgs = 'county:*'

# Create list of URLs to query
urlList = [] #empty list
for x in getArgs:
    URLArgs = '?get={}&for={}&key={}'.format(x,forArgs,apiKey)
    queryURL = baseURL + URLArgs
    urlList.append(queryURL)


#/// Create Dataframes \\\#
# Create function
def makeDataFrame(url,labelDict):

    #Get response data from API
    response = req.get(url)
    jsonData = response.json() #create json

    # Create data frame from json
    df = pd.DataFrame(jsonData, columns=jsonData[0]) #rename headers with first row values
    df = df.rename(columns=labelDict) #rename columnns using associated dictionary
    df = df.drop(df.index[0]) #remove first row

    # Remove leading zeros from state and county
    df['State Code (FIPS)'] = df['State Code (FIPS)'].str.lstrip('0')
    df['County Code (FIPS)'] = df['County Code (FIPS)'].str.lstrip('0')

    # Make all numbers in DF numeric
    df = df.apply(pd.to_numeric)

    return df

# Make DF using Function
incomeDF = makeDataFrame(urlList[0],householdIncomeDict)
eduDF1 = makeDataFrame(urlList[1],educationDict)
eduDF2 = makeDataFrame(urlList[2],educationDict)
populationDF = makeDataFrame(urlList[3],populationDict)

#/// Merge Education DataFrames \\\#
# Create joint DF
eduDF = pd.merge(eduDF1,eduDF2,how='outer',on=['State Code (FIPS)','County Code (FIPS)'])

# Create dictionary to remove appeneded X's and Y's on column names
removeAppend = {}
for i in educationAttainmentBuckets:
    s1 = i + '_x'
    s2 = i + '_y'
    removeAppend[s1] = i
    removeAppend[s2] = i

# Rename column headers
eduDF = eduDF.rename(columns=removeAppend)

# Sum columns with same names in DF
eduDF = eduDF.groupby(lambda x:x, axis=1).sum()

#/// Map Geocodes and add to DF \\\#
# Create function to automate
def mergeOnGeocode(df1,df2):
    try:
        return pd.merge(df1,df2,how='inner',on=['State Code (FIPS)','County Code (FIPS)'])
    except:
        return pd.merge(df1,df2,how='inner',on=['State Code (FIPS)'])


# Map census DFs to FIPS
incomeDFmapped = mergeOnGeocode(incomeDF,geocodeMap)
eduDFmapped = mergeOnGeocode(eduDF,geocodeMap)

popDFmapped = mergeOnGeocode(populationDF,geocodeMap)
popDFmapped = pd.merge(popDFmapped,abbrMap, how='inner',on=['State'])

#/ Variables/DFs to use:
    #/ To normalize data, use this DF: popDFmapped (FIPS mapped to names)
    #/ Income data DF to use: incomeDFmapped (FIPS mapped to names) or incomeDF (FIPS only)
    #/ Education data DF to use: eduDFmapped (FIPS mapped to names) or eduDF (FIPS only)
```


```python
#/// Create Normalized DFs \\\*

# Create function to normalize data
def normalizeData(df1,df2,buckets):

    # Merge dicts on geocode
    df = mergeOnGeocode(df1,df2)

    # For each column, divide by the total population column
    for bucket in buckets:
        df[bucket] = df[bucket]/df['Population']

    # Drop population column
    df.drop(['Population'], axis=1, inplace=True)

    # Return df
    return df

# HOUSEHOLDS TOTAL: Create DF
var = 'B19001_001E'
householdDict = createIdDict([var],['Population']) #create dict

URLArgs = '?get={}&for={}&key={}'.format(var,forArgs,apiKey)
queryURL = baseURL + URLArgs #put together query URL

householdDF = makeDataFrame(queryURL,householdDict) #create DF

# +18 POPULATION TOTAL: Create DF
var = 'B15001_001E'
over18Dict = createIdDict([var],['Population']) #create dict

URLArgs = '?get={}&for={}&key={}'.format(var,forArgs,apiKey)
queryURL = baseURL + URLArgs #put together query URL

over18DF = makeDataFrame(queryURL,over18Dict) #create DF

# Normalize Income and Education DFs
normIncome = normalizeData(incomeDF,householdDF,householdIncomeBuckets) #normalizedIncome
normEdu = normalizeData(eduDF,over18DF,educationAttainmentBuckets) #normalizedEdu

#/// Create Normalized DFs for States \\\*

# Function to breakdown DFs by state FIPS
def breakdownByState(dfIn):
    df = dfIn.groupby(['State Code (FIPS)']).sum()
    df.drop(['County Code (FIPS)'], axis=1, inplace=True)
    df = df.reset_index()
    return df

# Function to set state as index
def setStateAsIndex(df):

    # Merge on state only
    df = mergeOnGeocode(df,geocodeMapState)
    df.drop('State Code (FIPS)', axis=1, inplace=True)
    df = df.set_index('State')
    return df

# Function to Normalize state DFs
def createStateNormDF (df1,df2,buckets):

    # Breakdown DFs by STate and Normalize
    df1n = breakdownByState(df1)
    df2n = breakdownByState(df2)
    df = normalizeData(df1n,df2n,buckets)

    # Set state as the index
    df = setStateAsIndex(df)

    return df

# Create State DF's
# Income
incomeByState = setStateAsIndex(breakdownByState(incomeDF))
incomeByState = incomeByState[householdIncomeBuckets] #reorder columns
# Education
eduByState = setStateAsIndex(breakdownByState(eduDF))
eduByState = eduByState[educationAttainmentBuckets] #reorder columns

# Create State Normalized DF's
# Income
incomeByStateNorm = createStateNormDF(incomeDF,householdDF,householdIncomeBuckets)
incomeByStateNorm = incomeByStateNorm[householdIncomeBuckets] #reorder columns
# Education
eduByStateNorm = createStateNormDF(eduDF,over18DF,educationAttainmentBuckets)
eduByStateNorm = eduByStateNorm[educationAttainmentBuckets] #reorder columns

# Reduce income buckets
def reduceBuckets(df):
    df['< $25K'] = df[householdIncomeBuckets[0]] + df[householdIncomeBuckets[1]] + df[householdIncomeBuckets[2]] + df[householdIncomeBuckets[3]]
    df['\$25K - $49,999'] = df[householdIncomeBuckets[4]] + df[householdIncomeBuckets[5]] + df[householdIncomeBuckets[6]] + df[householdIncomeBuckets[7]] + df[householdIncomeBuckets[8]]
    df['\$50K - $99,999'] = df[householdIncomeBuckets[9]] + df[householdIncomeBuckets[10]] + df[householdIncomeBuckets[11]]
    df['\$100K - $149,999'] = df[householdIncomeBuckets[12]] + df[householdIncomeBuckets[13]]

    df = df[['< $25K',
             '\$25K - $49,999',
             '\$50K - $99,999',
             '\$100K - $149,999',
             '$150K - $199,999',
             '$200K +'
            ]]
    
    df = df.rename({'$150K - $199,999' : '\$150K - $199,999'})
    
    return df

# Run function on income to reduce buckets
incomeByStateBuckets = reduceBuckets(incomeByState) #volume
incomeByStateNormBuckets = reduceBuckets(incomeByStateNorm) #normalized
```


```python
# Household income volume
incomeByState.head()
```




<div>
<style>
    .dataframe thead tr:only-child th {
        text-align: right;
    }

    .dataframe thead th {
        text-align: left;
    }

    .dataframe tbody tr th {
        vertical-align: top;
    }
</style>
<table border="1" class="dataframe">
  <thead>
    <tr style="text-align: right;">
      <th></th>
      <th>&lt; $10k</th>
      <th>$10K - $14,999</th>
      <th>$15K - $19,999</th>
      <th>$20K - $24,999</th>
      <th>$25K - $29,999</th>
      <th>$30K - $34,999</th>
      <th>$35K - $39,999</th>
      <th>$40K - $44,999</th>
      <th>$45K - $49,999</th>
      <th>$50K - $59,999</th>
      <th>$60K - $74,999</th>
      <th>$75K - $99,999</th>
      <th>$100K - $124,999</th>
      <th>$125K - $149,999</th>
      <th>$150K - $199,999</th>
      <th>$200K +</th>
      <th>&lt; $25K</th>
      <th>\$25K - $49,999</th>
      <th>\$50K - $99,999</th>
      <th>\$100K - $149,999</th>
    </tr>
    <tr>
      <th>State</th>
      <th></th>
      <th></th>
      <th></th>
      <th></th>
      <th></th>
      <th></th>
      <th></th>
      <th></th>
      <th></th>
      <th></th>
      <th></th>
      <th></th>
      <th></th>
      <th></th>
      <th></th>
      <th></th>
      <th></th>
      <th></th>
      <th></th>
      <th></th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>Alabama</th>
      <td>117740</td>
      <td>82051</td>
      <td>81954</td>
      <td>77103</td>
      <td>75533</td>
      <td>73493</td>
      <td>69537</td>
      <td>64044</td>
      <td>57363</td>
      <td>109256</td>
      <td>130940</td>
      <td>163814</td>
      <td>106967</td>
      <td>57537</td>
      <td>60731</td>
      <td>54724</td>
      <td>358848</td>
      <td>339970</td>
      <td>404010</td>
      <td>164504</td>
    </tr>
    <tr>
      <th>Alaska</th>
      <td>5148</td>
      <td>4504</td>
      <td>4093</td>
      <td>5404</td>
      <td>5336</td>
      <td>5885</td>
      <td>4815</td>
      <td>5904</td>
      <td>6524</td>
      <td>13298</td>
      <td>16693</td>
      <td>24791</td>
      <td>21870</td>
      <td>13700</td>
      <td>17154</td>
      <td>14205</td>
      <td>19149</td>
      <td>28464</td>
      <td>54782</td>
      <td>35570</td>
    </tr>
    <tr>
      <th>Arizona</th>
      <td>178550</td>
      <td>118827</td>
      <td>113126</td>
      <td>125785</td>
      <td>125696</td>
      <td>120881</td>
      <td>120530</td>
      <td>125073</td>
      <td>103507</td>
      <td>214202</td>
      <td>247124</td>
      <td>309522</td>
      <td>195761</td>
      <td>116701</td>
      <td>123372</td>
      <td>119731</td>
      <td>536288</td>
      <td>595687</td>
      <td>770848</td>
      <td>312462</td>
    </tr>
    <tr>
      <th>Arkansas</th>
      <td>53205</td>
      <td>34318</td>
      <td>33389</td>
      <td>37538</td>
      <td>34367</td>
      <td>36272</td>
      <td>30819</td>
      <td>34560</td>
      <td>31788</td>
      <td>55521</td>
      <td>64676</td>
      <td>71239</td>
      <td>47523</td>
      <td>27354</td>
      <td>25144</td>
      <td>25572</td>
      <td>158450</td>
      <td>167806</td>
      <td>191436</td>
      <td>74877</td>
    </tr>
    <tr>
      <th>California</th>
      <td>688487</td>
      <td>572418</td>
      <td>512769</td>
      <td>568814</td>
      <td>485542</td>
      <td>529878</td>
      <td>489353</td>
      <td>507198</td>
      <td>450680</td>
      <td>874479</td>
      <td>1199686</td>
      <td>1551800</td>
      <td>1213874</td>
      <td>797890</td>
      <td>1010483</td>
      <td>1301650</td>
      <td>2342488</td>
      <td>2462651</td>
      <td>3625965</td>
      <td>2011764</td>
    </tr>
  </tbody>
</table>
</div>




```python
# Household Income Normalized
incomeByStateNorm.head()
```




<div>
<style>
    .dataframe thead tr:only-child th {
        text-align: right;
    }

    .dataframe thead th {
        text-align: left;
    }

    .dataframe tbody tr th {
        vertical-align: top;
    }
</style>
<table border="1" class="dataframe">
  <thead>
    <tr style="text-align: right;">
      <th></th>
      <th>&lt; $10k</th>
      <th>$10K - $14,999</th>
      <th>$15K - $19,999</th>
      <th>$20K - $24,999</th>
      <th>$25K - $29,999</th>
      <th>$30K - $34,999</th>
      <th>$35K - $39,999</th>
      <th>$40K - $44,999</th>
      <th>$45K - $49,999</th>
      <th>$50K - $59,999</th>
      <th>$60K - $74,999</th>
      <th>$75K - $99,999</th>
      <th>$100K - $124,999</th>
      <th>$125K - $149,999</th>
      <th>$150K - $199,999</th>
      <th>$200K +</th>
      <th>&lt; $25K</th>
      <th>\$25K - $49,999</th>
      <th>\$50K - $99,999</th>
      <th>\$100K - $149,999</th>
    </tr>
    <tr>
      <th>State</th>
      <th></th>
      <th></th>
      <th></th>
      <th></th>
      <th></th>
      <th></th>
      <th></th>
      <th></th>
      <th></th>
      <th></th>
      <th></th>
      <th></th>
      <th></th>
      <th></th>
      <th></th>
      <th></th>
      <th></th>
      <th></th>
      <th></th>
      <th></th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>Alabama</th>
      <td>0.085147</td>
      <td>0.059337</td>
      <td>0.059267</td>
      <td>0.055759</td>
      <td>0.054624</td>
      <td>0.053148</td>
      <td>0.050288</td>
      <td>0.046315</td>
      <td>0.041484</td>
      <td>0.079011</td>
      <td>0.094693</td>
      <td>0.118467</td>
      <td>0.077356</td>
      <td>0.041609</td>
      <td>0.043919</td>
      <td>0.039575</td>
      <td>0.259511</td>
      <td>0.245859</td>
      <td>0.292171</td>
      <td>0.118966</td>
    </tr>
    <tr>
      <th>Alaska</th>
      <td>0.030403</td>
      <td>0.026600</td>
      <td>0.024173</td>
      <td>0.031915</td>
      <td>0.031514</td>
      <td>0.034756</td>
      <td>0.028437</td>
      <td>0.034868</td>
      <td>0.038530</td>
      <td>0.078536</td>
      <td>0.098586</td>
      <td>0.146412</td>
      <td>0.129161</td>
      <td>0.080910</td>
      <td>0.101309</td>
      <td>0.083892</td>
      <td>0.113091</td>
      <td>0.168104</td>
      <td>0.323534</td>
      <td>0.210071</td>
    </tr>
    <tr>
      <th>Arizona</th>
      <td>0.072629</td>
      <td>0.048335</td>
      <td>0.046016</td>
      <td>0.051166</td>
      <td>0.051129</td>
      <td>0.049171</td>
      <td>0.049028</td>
      <td>0.050876</td>
      <td>0.042104</td>
      <td>0.087131</td>
      <td>0.100523</td>
      <td>0.125904</td>
      <td>0.079630</td>
      <td>0.047471</td>
      <td>0.050184</td>
      <td>0.048703</td>
      <td>0.218146</td>
      <td>0.242308</td>
      <td>0.313558</td>
      <td>0.127100</td>
    </tr>
    <tr>
      <th>Arkansas</th>
      <td>0.082708</td>
      <td>0.053348</td>
      <td>0.051904</td>
      <td>0.058354</td>
      <td>0.053424</td>
      <td>0.056386</td>
      <td>0.047909</td>
      <td>0.053724</td>
      <td>0.049415</td>
      <td>0.086309</td>
      <td>0.100540</td>
      <td>0.110743</td>
      <td>0.073875</td>
      <td>0.042522</td>
      <td>0.039087</td>
      <td>0.039752</td>
      <td>0.246314</td>
      <td>0.260858</td>
      <td>0.297591</td>
      <td>0.116398</td>
    </tr>
    <tr>
      <th>California</th>
      <td>0.053978</td>
      <td>0.044878</td>
      <td>0.040201</td>
      <td>0.044595</td>
      <td>0.038067</td>
      <td>0.041543</td>
      <td>0.038366</td>
      <td>0.039765</td>
      <td>0.035334</td>
      <td>0.068560</td>
      <td>0.094056</td>
      <td>0.121662</td>
      <td>0.095168</td>
      <td>0.062555</td>
      <td>0.079222</td>
      <td>0.102050</td>
      <td>0.183653</td>
      <td>0.193073</td>
      <td>0.284278</td>
      <td>0.157724</td>
    </tr>
  </tbody>
</table>
</div>




```python
# Household Income with reduced buckets (normalized)
incomeByStateNormBuckets.head()
```




<div>
<style>
    .dataframe thead tr:only-child th {
        text-align: right;
    }

    .dataframe thead th {
        text-align: left;
    }

    .dataframe tbody tr th {
        vertical-align: top;
    }
</style>
<table border="1" class="dataframe">
  <thead>
    <tr style="text-align: right;">
      <th></th>
      <th>&lt; $25K</th>
      <th>\$25K - $49,999</th>
      <th>\$50K - $99,999</th>
      <th>\$100K - $149,999</th>
      <th>$150K - $199,999</th>
      <th>$200K +</th>
    </tr>
    <tr>
      <th>State</th>
      <th></th>
      <th></th>
      <th></th>
      <th></th>
      <th></th>
      <th></th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>Alabama</th>
      <td>0.259511</td>
      <td>0.245859</td>
      <td>0.292171</td>
      <td>0.118966</td>
      <td>0.043919</td>
      <td>0.039575</td>
    </tr>
    <tr>
      <th>Alaska</th>
      <td>0.113091</td>
      <td>0.168104</td>
      <td>0.323534</td>
      <td>0.210071</td>
      <td>0.101309</td>
      <td>0.083892</td>
    </tr>
    <tr>
      <th>Arizona</th>
      <td>0.218146</td>
      <td>0.242308</td>
      <td>0.313558</td>
      <td>0.127100</td>
      <td>0.050184</td>
      <td>0.048703</td>
    </tr>
    <tr>
      <th>Arkansas</th>
      <td>0.246314</td>
      <td>0.260858</td>
      <td>0.297591</td>
      <td>0.116398</td>
      <td>0.039087</td>
      <td>0.039752</td>
    </tr>
    <tr>
      <th>California</th>
      <td>0.183653</td>
      <td>0.193073</td>
      <td>0.284278</td>
      <td>0.157724</td>
      <td>0.079222</td>
      <td>0.102050</td>
    </tr>
  </tbody>
</table>
</div>




```python
# Education Attainment Volume
eduByState.head()
```




<div>
<style>
    .dataframe thead tr:only-child th {
        text-align: right;
    }

    .dataframe thead th {
        text-align: left;
    }

    .dataframe tbody tr th {
        vertical-align: top;
    }
</style>
<table border="1" class="dataframe">
  <thead>
    <tr style="text-align: right;">
      <th></th>
      <th>Less than 9th grade</th>
      <th>9th to 12th grade, no diploma</th>
      <th>High school graduate</th>
      <th>Some college, no degree</th>
      <th>Associate's degree</th>
      <th>Bachelor's degree</th>
      <th>Graduate or professional degree</th>
    </tr>
    <tr>
      <th>State</th>
      <th></th>
      <th></th>
      <th></th>
      <th></th>
      <th></th>
      <th></th>
      <th></th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>Alabama</th>
      <td>111784</td>
      <td>266587</td>
      <td>801204</td>
      <td>694519</td>
      <td>219221</td>
      <td>447864</td>
      <td>264964</td>
    </tr>
    <tr>
      <th>Alaska</th>
      <td>6267</td>
      <td>18345</td>
      <td>101141</td>
      <td>111073</td>
      <td>32571</td>
      <td>70282</td>
      <td>36635</td>
    </tr>
    <tr>
      <th>Arizona</th>
      <td>268015</td>
      <td>426722</td>
      <td>1289846</td>
      <td>1409771</td>
      <td>412632</td>
      <td>869186</td>
      <td>496777</td>
    </tr>
    <tr>
      <th>Arkansas</th>
      <td>51095</td>
      <td>97309</td>
      <td>387489</td>
      <td>326751</td>
      <td>81629</td>
      <td>208442</td>
      <td>115674</td>
    </tr>
    <tr>
      <th>California</th>
      <td>2591171</td>
      <td>2414803</td>
      <td>6425995</td>
      <td>7160282</td>
      <td>2181414</td>
      <td>5739416</td>
      <td>3242559</td>
    </tr>
  </tbody>
</table>
</div>




```python
# Education Attainment Normalized
eduByStateNorm.head()
```




<div>
<style>
    .dataframe thead tr:only-child th {
        text-align: right;
    }

    .dataframe thead th {
        text-align: left;
    }

    .dataframe tbody tr th {
        vertical-align: top;
    }
</style>
<table border="1" class="dataframe">
  <thead>
    <tr style="text-align: right;">
      <th></th>
      <th>Less than 9th grade</th>
      <th>9th to 12th grade, no diploma</th>
      <th>High school graduate</th>
      <th>Some college, no degree</th>
      <th>Associate's degree</th>
      <th>Bachelor's degree</th>
      <th>Graduate or professional degree</th>
    </tr>
    <tr>
      <th>State</th>
      <th></th>
      <th></th>
      <th></th>
      <th></th>
      <th></th>
      <th></th>
      <th></th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>Alabama</th>
      <td>0.039835</td>
      <td>0.095001</td>
      <td>0.285518</td>
      <td>0.247500</td>
      <td>0.078122</td>
      <td>0.159601</td>
      <td>0.094423</td>
    </tr>
    <tr>
      <th>Alaska</th>
      <td>0.016654</td>
      <td>0.048749</td>
      <td>0.268768</td>
      <td>0.295160</td>
      <td>0.086553</td>
      <td>0.186764</td>
      <td>0.097352</td>
    </tr>
    <tr>
      <th>Arizona</th>
      <td>0.051811</td>
      <td>0.082491</td>
      <td>0.249344</td>
      <td>0.272528</td>
      <td>0.079767</td>
      <td>0.168025</td>
      <td>0.096034</td>
    </tr>
    <tr>
      <th>Arkansas</th>
      <td>0.040283</td>
      <td>0.076719</td>
      <td>0.305497</td>
      <td>0.257611</td>
      <td>0.064356</td>
      <td>0.164336</td>
      <td>0.091198</td>
    </tr>
    <tr>
      <th>California</th>
      <td>0.087082</td>
      <td>0.081154</td>
      <td>0.215959</td>
      <td>0.240636</td>
      <td>0.073311</td>
      <td>0.192885</td>
      <td>0.108973</td>
    </tr>
  </tbody>
</table>
</div>




```python
#/// Create Bar Charts \\\*
sns.palplot(sns.hls_palette(9, l=.3, s=.8))

# Function to create bar charts
def createBarChart(df,title,x,y,lt,l,c,save):

    # Plot DF as bar graph
    df.plot(kind='bar',
            stacked=True,
            title=title,
            figsize=(30,10),
            fontsize=14
           )

    # Add title/labels
    plt.title(title,fontsize=18) #Create graph title
    plt.xlabel(x, fontsize=14) #Create x-axis label
    plt.ylabel(y,fontsize=14) #Create y-axis label
    plt.tick_params(axis='both', labelsize=12) #Format Axis

    # Add legend
    legend = plt.legend(loc='lower center',bbox_to_anchor=(.5, l), ncol=c, borderaxespad=0., title=lt, fontsize=12,frameon=True)
    legend.get_title().set_fontsize('14') #Set legend title font size
    
    # Show plot
    plt.show()
```


```python
# Bar Chart: Household Income for All States
createBarChart(incomeByStateBuckets,'Household Income by Volume for All States','State','Households','Household Income Buckets',-.35,6,'graphs/incomebyvolume.png')
```


![png](output_9_0.png)



![png](output_9_1.png)



```python
# Bar Chart: Normalized Household Income for All States
createBarChart(incomeByStateNormBuckets,'Normalized Household Income for All States','State','Normalized % Population','Household Income Buckets',-.35,6,'graphs/incomebynorm.png')
plt.savefig('graphs/incomebynorm.png')
```


![png](output_10_0.png)



```python
# Bar Chart: Educational Attainment (18+) for All States
createBarChart(eduByState,'Educational Attainment (18+) by Volume for All States','State','Population','Educational Attainment Buckets',-.4,5,'graphs/edubyvolume.png')
```


    <matplotlib.figure.Figure at 0x11a23a780>



![png](output_11_1.png)



```python
# Bar Chart: Normalized Education (18+) for All States
createBarChart(eduByStateNorm,'Normalized Education (18+) for All States','State','Normalized % Population','Educational Attainment Buckets',-.4,5,'graphs/edubynorm.png')
```


![png](output_12_0.png)



```python
# MONA'S DATAFRAMES FOR COMPARISON

res_data = pd.ExcelFile('resources/FastFoodData.xls')
restaurant_df = pd.read_excel(res_data, 'RESTAURANTS')

restaurant_df = restaurant_df.rename(columns={'FFR09':'Fast Food Restaurants 2009',
                                              'FFR14':'Fast Food Restaurants 2014',
                                              'PCH_FFR_09_14':'Fast-food restaurants (% change)',
                                              'FFRPTH09':'Fast-food restaurants/1,000 pop 2009',
                                              'FFRPTH14':'Fast-food restaurants/1,000 pop 2014',
                                              'PCH_FFRPTH_09_14':'Fast-food restaurants/1,000 pop (% change)'})

fast_food_df=restaurant_df[['FIPS',
                            'State',
                            'County',
                            'Fast Food Restaurants 2009',
                            'Fast Food Restaurants 2014',
                            'Fast-food restaurants (% change)',
                            'Fast-food restaurants/1,000 pop 2009',
                            'Fast-food restaurants/1,000 pop 2014',
                            'Fast-food restaurants/1,000 pop (% change)']].copy()


# fast_food_df.head()
# fast_food_df.insert(loc=0,column='Fast Food Restaurants 2015 (PROJECTED)',value=int)

ff_df=fast_food_df[['FIPS',
                    'State',
                    'County',
                    'Fast Food Restaurants 2009',
                    'Fast Food Restaurants 2014',
                    'Fast-food restaurants (% change)',
                    'Fast-food restaurants/1,000 pop 2009',
                    'Fast-food restaurants/1,000 pop 2014',
                    'Fast-food restaurants/1,000 pop (% change)']].copy()

for index,row in ff_df.iterrows():
    total_gr = row['Fast-food restaurants (% change)']
    yr_gr = total_gr/5
    ff_df.set_value(index,'Yearly Growth Rate %',yr_gr)
    ff09 = row['Fast Food Restaurants 2009']
    ff14 = row['Fast Food Restaurants 2014']
    projection = round((ff14*(yr_gr/100)) + ff14,0)
    ff_df.set_value(index,'Fast Food Restaurants 2015 (PROJECTED)',projection)
   
    
# del ff_df['Fast-food restaurants/1,000 pop 2009']
# del ff_df['Fast-food restaurants/1,000 pop 2014']
# del ff_df['Fast-food restaurants/1,000 pop (% change)']

resbystate15 = ff_df.groupby(["State"])['Fast Food Restaurants 2015 (PROJECTED)'].sum()
resbystate14 =  ff_df.groupby(["State"])['Fast Food Restaurants 2014'].sum()
resbystate15.head(20)
resbystate=pd.DataFrame({'Abbreviation':resbystate15.index,'Fast Food Restaurant Count 2014':resbystate14.values, 'Fast Food Restaurant Count 2015 (prj)':resbystate15.values}).copy()

# Condense dataframe
resbystate2015 = resbystate[['Abbreviation','Fast Food Restaurant Count 2015 (prj)']]
resbystate2015.head()
```




<div>
<style>
    .dataframe thead tr:only-child th {
        text-align: right;
    }

    .dataframe thead th {
        text-align: left;
    }

    .dataframe tbody tr th {
        vertical-align: top;
    }
</style>
<table border="1" class="dataframe">
  <thead>
    <tr style="text-align: right;">
      <th></th>
      <th>Abbreviation</th>
      <th>Fast Food Restaurant Count 2015 (prj)</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>0</th>
      <td>AK</td>
      <td>425.0</td>
    </tr>
    <tr>
      <th>1</th>
      <td>AL</td>
      <td>3626.0</td>
    </tr>
    <tr>
      <th>2</th>
      <td>AR</td>
      <td>1963.0</td>
    </tr>
    <tr>
      <th>3</th>
      <td>AZ</td>
      <td>4241.0</td>
    </tr>
    <tr>
      <th>4</th>
      <td>CA</td>
      <td>28842.0</td>
    </tr>
  </tbody>
</table>
</div>




```python
# Merge Mona's data with Abbreviation map
resbystate2015merged = pd.merge(resbystate2015,abbrMap,how='inner',on=['Abbreviation'])
resbystate2015merged = resbystate2015merged[['Fast Food Restaurant Count 2015 (prj)','State']]

resbystate2015merged.head()
```




<div>
<style>
    .dataframe thead tr:only-child th {
        text-align: right;
    }

    .dataframe thead th {
        text-align: left;
    }

    .dataframe tbody tr th {
        vertical-align: top;
    }
</style>
<table border="1" class="dataframe">
  <thead>
    <tr style="text-align: right;">
      <th></th>
      <th>Fast Food Restaurant Count 2015 (prj)</th>
      <th>State</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>0</th>
      <td>425.0</td>
      <td>Alaska</td>
    </tr>
    <tr>
      <th>1</th>
      <td>3626.0</td>
      <td>Alabama</td>
    </tr>
    <tr>
      <th>2</th>
      <td>1963.0</td>
      <td>Arkansas</td>
    </tr>
    <tr>
      <th>3</th>
      <td>4241.0</td>
      <td>Arizona</td>
    </tr>
    <tr>
      <th>4</th>
      <td>28842.0</td>
      <td>California</td>
    </tr>
  </tbody>
</table>
</div>




```python
# Consolidate Education budgets by Degree and no degree
eduByState['No Degree'] = eduByState['Less than 9th grade'] + eduByState['9th to 12th grade, no diploma'] + eduByState['High school graduate'] +  eduByState['Some college, no degree']
eduByState['Degree'] = eduByState['Associate\'s degree'] + eduByState['Bachelor\'s degree'] + eduByState['Graduate or professional degree']
eduByState['Total'] = eduByState['No Degree'] + eduByState['Degree']

# Degreelist = ['Less than 9th grade',
# '9th to 12th grade, no diploma',
# 'High school graduate',
# 'Some college, no degree',
# 'Associate\'s degree',
# 'Bachelor\'s degree',
# 'Graduate or professional degree']

eduByState['No Degree Normalized'] = eduByState['No Degree'] / eduByState['Total']
eduByState['Degree Normalized'] = eduByState['Degree'] / eduByState['Total']
eduByState['Less than 9th grade Normalized'] = eduByState['Less than 9th grade'] / eduByState['Total']
eduByState['9th to 12th grade, no diploma Normalized'] = eduByState['9th to 12th grade, no diploma'] / eduByState['Total']
eduByState['High school graduate Normalized'] = eduByState['High school graduate'] / eduByState['Total']
eduByState['Some college, no degree Normalized'] = eduByState['Some college, no degree'] / eduByState['Total']
eduByState['Associate\'s degree Normalized'] = eduByState['Associate\'s degree'] / eduByState['Total']
eduByState['Bachelor\'s degree Normalized'] = eduByState['Bachelor\'s degree'] / eduByState['Total']
eduByState['Graduate or professional degree Normalized'] = eduByState['Graduate or professional degree'] / eduByState['Total']

eduByStateBuckets = eduByState[['No Degree Normalized',
                                'Degree Normalized',
                                'Less than 9th grade Normalized',
                                '9th to 12th grade, no diploma Normalized',
                                'High school graduate Normalized',
                                'Some college, no degree Normalized',
                                'Associate\'s degree Normalized',
                                'Bachelor\'s degree Normalized',
                                'Graduate or professional degree Normalized'
                               ]]
eduByStateBuckets = eduByStateBuckets.reset_index()

eduByStateBuckets.head()
```




<div>
<style>
    .dataframe thead tr:only-child th {
        text-align: right;
    }

    .dataframe thead th {
        text-align: left;
    }

    .dataframe tbody tr th {
        vertical-align: top;
    }
</style>
<table border="1" class="dataframe">
  <thead>
    <tr style="text-align: right;">
      <th></th>
      <th>State</th>
      <th>No Degree Normalized</th>
      <th>Degree Normalized</th>
      <th>Less than 9th grade Normalized</th>
      <th>9th to 12th grade, no diploma Normalized</th>
      <th>High school graduate Normalized</th>
      <th>Some college, no degree Normalized</th>
      <th>Associate's degree Normalized</th>
      <th>Bachelor's degree Normalized</th>
      <th>Graduate or professional degree Normalized</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>0</th>
      <td>Alabama</td>
      <td>0.667854</td>
      <td>0.332146</td>
      <td>0.039835</td>
      <td>0.095001</td>
      <td>0.285518</td>
      <td>0.247500</td>
      <td>0.078122</td>
      <td>0.159601</td>
      <td>0.094423</td>
    </tr>
    <tr>
      <th>1</th>
      <td>Alaska</td>
      <td>0.629331</td>
      <td>0.370669</td>
      <td>0.016654</td>
      <td>0.048749</td>
      <td>0.268768</td>
      <td>0.295160</td>
      <td>0.086553</td>
      <td>0.186764</td>
      <td>0.097352</td>
    </tr>
    <tr>
      <th>2</th>
      <td>Arizona</td>
      <td>0.656174</td>
      <td>0.343826</td>
      <td>0.051811</td>
      <td>0.082491</td>
      <td>0.249344</td>
      <td>0.272528</td>
      <td>0.079767</td>
      <td>0.168025</td>
      <td>0.096034</td>
    </tr>
    <tr>
      <th>3</th>
      <td>Arkansas</td>
      <td>0.680110</td>
      <td>0.319890</td>
      <td>0.040283</td>
      <td>0.076719</td>
      <td>0.305497</td>
      <td>0.257611</td>
      <td>0.064356</td>
      <td>0.164336</td>
      <td>0.091198</td>
    </tr>
    <tr>
      <th>4</th>
      <td>California</td>
      <td>0.624831</td>
      <td>0.375169</td>
      <td>0.087082</td>
      <td>0.081154</td>
      <td>0.215959</td>
      <td>0.240636</td>
      <td>0.073311</td>
      <td>0.192885</td>
      <td>0.108973</td>
    </tr>
  </tbody>
</table>
</div>




```python
# Map state population
popDFmappedCond = popDFmapped[['Population','State']]
popDFmappedState = popDFmappedCond.groupby(['State']).sum()
popDFmappedState = popDFmappedState.reset_index()

# Merged Fastfood normalized totals to DF
ffData = pd.merge(resbystate2015merged,popDFmappedState,how='inner',on=['State'])
ffData['Fastfood Normalized'] = ffData['Fast Food Restaurant Count 2015 (prj)'] / ffData['Population']
ffData = ffData[['Fastfood Normalized','State']]
ffData.head()
```




<div>
<style>
    .dataframe thead tr:only-child th {
        text-align: right;
    }

    .dataframe thead th {
        text-align: left;
    }

    .dataframe tbody tr th {
        vertical-align: top;
    }
</style>
<table border="1" class="dataframe">
  <thead>
    <tr style="text-align: right;">
      <th></th>
      <th>Fastfood Normalized</th>
      <th>State</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>0</th>
      <td>0.000845</td>
      <td>Alaska</td>
    </tr>
    <tr>
      <th>1</th>
      <td>0.000999</td>
      <td>Alabama</td>
    </tr>
    <tr>
      <th>2</th>
      <td>0.001173</td>
      <td>Arkansas</td>
    </tr>
    <tr>
      <th>3</th>
      <td>0.000627</td>
      <td>Arizona</td>
    </tr>
    <tr>
      <th>4</th>
      <td>0.000744</td>
      <td>California</td>
    </tr>
  </tbody>
</table>
</div>




```python
# Create joined output DF to graph against
outputDF = pd.merge(eduByStateBuckets,ffData,how='inner',on=['State'])
outputDF = outputDF.set_index('State')
outputDF = outputDF * 1000 #multiplied dataframe to get per capita (1000)

outputDF.head()
```




<div>
<style>
    .dataframe thead tr:only-child th {
        text-align: right;
    }

    .dataframe thead th {
        text-align: left;
    }

    .dataframe tbody tr th {
        vertical-align: top;
    }
</style>
<table border="1" class="dataframe">
  <thead>
    <tr style="text-align: right;">
      <th></th>
      <th>No Degree Normalized</th>
      <th>Degree Normalized</th>
      <th>Less than 9th grade Normalized</th>
      <th>9th to 12th grade, no diploma Normalized</th>
      <th>High school graduate Normalized</th>
      <th>Some college, no degree Normalized</th>
      <th>Associate's degree Normalized</th>
      <th>Bachelor's degree Normalized</th>
      <th>Graduate or professional degree Normalized</th>
      <th>Fastfood Normalized</th>
    </tr>
    <tr>
      <th>State</th>
      <th></th>
      <th></th>
      <th></th>
      <th></th>
      <th></th>
      <th></th>
      <th></th>
      <th></th>
      <th></th>
      <th></th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>Alabama</th>
      <td>667.854062</td>
      <td>332.145938</td>
      <td>39.835461</td>
      <td>95.001217</td>
      <td>285.517880</td>
      <td>247.499504</td>
      <td>78.121821</td>
      <td>159.601275</td>
      <td>94.422843</td>
      <td>0.998711</td>
    </tr>
    <tr>
      <th>Alaska</th>
      <td>629.330825</td>
      <td>370.669175</td>
      <td>16.653646</td>
      <td>48.749183</td>
      <td>268.767572</td>
      <td>295.160425</td>
      <td>86.552719</td>
      <td>186.764245</td>
      <td>97.352211</td>
      <td>0.844658</td>
    </tr>
    <tr>
      <th>Arizona</th>
      <td>656.173877</td>
      <td>343.826123</td>
      <td>51.810872</td>
      <td>82.491051</td>
      <td>249.344426</td>
      <td>272.527527</td>
      <td>79.767266</td>
      <td>168.025241</td>
      <td>96.033616</td>
      <td>0.626996</td>
    </tr>
    <tr>
      <th>Arkansas</th>
      <td>680.109966</td>
      <td>319.890034</td>
      <td>40.283383</td>
      <td>76.718578</td>
      <td>305.496973</td>
      <td>257.611033</td>
      <td>64.356440</td>
      <td>164.336020</td>
      <td>91.197574</td>
      <td>1.173249</td>
    </tr>
    <tr>
      <th>California</th>
      <td>624.831158</td>
      <td>375.168842</td>
      <td>87.081676</td>
      <td>81.154463</td>
      <td>215.958890</td>
      <td>240.636128</td>
      <td>73.310942</td>
      <td>192.884979</td>
      <td>108.972921</td>
      <td>0.744396</td>
    </tr>
  </tbody>
</table>
</div>




```python
# Create Scatter Plot
y = 'No Degree Normalized'
x = 'Fastfood Normalized'
d = outputDF

# Show the results of a linear regression within each dataset
ax = sns.regplot(x=x, y=y, data=d)

plt.title('Number of Fastfood Restaurants per 18+ Year old with No Degree (by 1000)')

plt.show()
```


![png](output_18_0.png)



```python
# Calculate r-squared and line equation
x = outputDF['No Degree Normalized']
y = outputDF['Fastfood Normalized']
slope, intercept, r_value, p_value, std_err = stats.linregress(x,y)

rsquare = r_value**2
intercept
slope
```




    -0.00066703058579024356


