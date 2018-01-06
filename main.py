# Dependencies
import requests as req
import json

#
years = []
for x in range(2011,2017):
    years.append(x)

apiKey = 'a9bba28cbc522f8f9d8ae3b88ef030fba6034516'
baseURL = 'https://api.census.gov/data/2016/acs/acs1/'
getArgs = 'B25121_001E,C15002_001E'
forArgs = 'county'
URLArgs = '?get={}&for={}:*&key={}'.format(getArgs,forArgs,apiKey)


queryURL = baseURL + URLArgs

print(queryURL)

#HOUSEHOLD INCOME IN THE PAST 12 MONTHS (IN 2016 INFLATION-ADJUSTED DOLLARS) BY VALUE

# SEX BY EDUCATIONAL ATTAINMENT FOR THE POPULATION 25 YEARS AND OVER


#?subject
# education: S1501_C01_001E
    #EDUCATIONAL ATTAINMENT
