# Dependencies
import requests as req
import numpy as np
import json
import pandas as pd
from pandas import ExcelWriter
from pandas import ExcelFile

##### SETUP 'GET' Variables #####

# Income variable id's
censusIncomeIdDict = {'B25121_002E' : '< $10k',
                      'B25121_017E' : '\$10K - $19,999',
                      'B25121_032E' : '\$20K - $34,999',
                      'B25121_047E' : '\$35K - $49,999',
                      'B25121_062E' : '\$50K - $74,999',
                      'B25121_077E' : '\$75K - $99,999',
                      'B25121_092E' : '\$100K +'
                      }

# Education variable id's
educationIdList = [] #setup list of all IDs
notInclude = [1,2,3,11,19,27,35,43,44,52,60,68,76] #id's not to include in list
for x in range(1,84):  #dynamically create id's
    if x in notInclude:
        pass
    else:
        if x < 10:
            educationIdList.append('B15001_00'+str(x)+'E')
        else:
            educationIdList.append('B15001_0'+str(x)+'E')

educationAttainment = ['Less than 9th grade',
                       '9th to 12th grade, no diploma',
                       'High school graduate (includes equivalency)',
                       'Some college, no degree',
                       'Associate\'s degree',
                       'Bachelor\'s degree',
                       'Graduate or professional degree']

censusEduIdDict = {} #setup dictionary for education IDs
n = 0

for x in educationIdList: #dynamically create dictionary of all education IDs
    censusEduIdDict[x] = educationAttainment[n%len(educationAttainment)]
    n += 1

# Split education dictionary in 2 because of 50 variable arg max
censusEduIdDict1 = {key:censusEduIdDict[key] for i, key in enumerate(censusEduIdDict) if i % 2 == 0}
censusEduIdDict2 = {key:censusEduIdDict[key] for i, key in enumerate(censusEduIdDict) if i % 2 == 1}

# List of dictionaries
allDictIds = [censusIncomeIdDict,censusEduIdDict1,censusEduIdDict2]
getArgs = []

# Create list of get arguments (all id's)
for x in allDictIds:
    getIds = ''

    for y in x:
        getIds = getIds + y + ',' #add income ids to get args

    getIds = getIds[:-1] #remove last comma
    getArgs.append(getIds) #add to ID list

##### Setup Query URL #####
year = 2016
apiKey = 'a9bba28cbc522f8f9d8ae3b88ef030fba6034516'
baseURL = 'https://api.census.gov/data/{}/acs/acs1/'.format(year)
forArgs = 'county:*'
urlList = []

for x in getArgs:
    URLArgs = '?get={}&for={}&key={}'.format(getArgs[getArgs.index(x)],forArgs,apiKey)
    queryURL = baseURL + URLArgs
    urlList.append(queryURL)

def makeDataFrames(url,labelDict):
    response = req.get(url)
    jsonData = response.json()
    df = pd.DataFrame(jsonData, columns=jsonData[0])
    df = df.rename(columns=labelDict)
    df = df.drop(df.index[0])
    return df

incomeDF = makeDataFrames(urlList[0],censusIncomeIdDict)
eduDF1 = makeDataFrames(urlList[1],censusEduIdDict1)
eduDF2 = makeDataFrames(urlList[2],censusEduIdDict2)

eduDF1 = eduDF1.groupby(lambda x:x, axis=1).sum()
eduDF2 = eduDF2.groupby(lambda x:x, axis=1).sum()

eduDF = pd.merge(eduDF1,eduDF2,how='outer',on='state')
eduLabels = list(eduDF.columns.values)
eduLabels.remove('state')

eduDFDic = {}
n = 0

for x in eduLabels: #dynamically create dictionary of all education IDs
    eduDFDic[x] = educationAttainment[n%len(educationAttainment)]
    n += 1

eduDF = eduDF.rename(columns=eduDFDic)
eduDF = eduDF.groupby(lambda x:x, axis=1).sum()

geocodeMap = pd.read_excel('resources/2016-allgeocodes.xlsx', sheetname='Sheet1')
geocodeMap = geocodeMap.loc[geocodeMap['Summary Level'] == 50]
geocodeMap = geocodeMap[['County Code (FIPS)','Area Name (including legal/statistical area description)']]
geocodeMap


#print stuff
print(urlList[0])
