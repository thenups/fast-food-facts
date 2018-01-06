# Dependencies
import requests as req
import json

#
year = 2016
apiKey = 'a9bba28cbc522f8f9d8ae3b88ef030fba6034516'
baseURL = 'https://api.census.gov/data/{}/acs/acs1/'.format(year)
getArgs = ''
forArgs = 'county:*'
URLArgs = '?get={}&for={}&key={}'.format(getArgs,forArgs,apiKey)


queryURL = baseURL + URLArgs

print(queryURL)

hoseholdIncomeIds = {'< $10k' : 'B25121_002E',
                     '$10K - $19,999' : 'B25121_017E',
                     '$20K - $34,999' : 'B25121_032E',
                     '$35K - $49,999' : 'B25121_047E',
                     '$50K - $74,999' : 'B25121_062E',
                     '$75K - $99,999' : 'B25121_077E',
                     '$100K +' : 'B25121_092E'
                    }

#HOUSEHOLD INCOME IN THE PAST 12 MONTHS (IN 2016 INFLATION-ADJUSTED DOLLARS) BY VALUE



# SEX BY EDUCATIONAL ATTAINMENT FOR THE POPULATION 25 YEARS AND OVER
