# Dependencies
import requests as req
import json

#
years = []
for x in range(2011,2017):
    years.append(x)

apiKey = 'a9bba28cbc522f8f9d8ae3b88ef030fba6034516'
baseURL = 'https://api.census.gov/data/2016/acs/acs1/'
getArgs = 'B00001_001E'
forArgs = 'county'
URLArgs = '?get={}&for={}:*&key={}'.format(getArgs,forArgs,apiKey)


queryURL = baseURL + URLArgs

print(queryURL)
