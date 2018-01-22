# Dependencies
import requests as req
import numpy as np
import json
import pandas as pd
from pandas import ExcelWriter
from pandas import ExcelFile
import matplotlib.pyplot as plt
import seaborn as sns

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

#/// Create Bar Charts \\\*
sns.palplot(sns.hls_palette(16, l=.3, s=.8))

# Function to create bar charts
def createBarChart(df,title,x,y,lt,l,c):

    # Plot DF as bar graph
    df.plot(kind='bar',
            stacked=True,
            title=title,
            figsize=(20,10),
            fontsize=14
           )

    # Add title/labels
    plt.title(title,fontsize=18) #Create graph title
    plt.xlabel(x, fontsize=14) #Create x-axis label
    plt.ylabel(y,fontsize=14) #Create y-axis label
    plt.tick_params(axis='both', labelsize=12) #Format Axis

    # Add legend
    legend = plt.legend(loc='lower center',bbox_to_anchor=(.5, l), ncol=c, borderaxespad=0., title=lt, fontsize=12)
    legend.get_title().set_fontsize('14') #Set legend title font size

    # Show plot
    plt.show()

# Bar Chart: Household Income for All States
createBarChart(incomeByState,'Household Income by Volume for All States','State','Households','Household Income Buckets',-.45,6)

# Normalized Household Income for All States
createBarChart(incomeByStateNorm,'Normalized Household Income for All States','State','Normalized % Population','Household Income Buckets',-.45,6)

# Educational Attainment (18+) for All States
createBarChart(eduByState,'Educational Attainment (18+) by Volume for All States','State','Population','Educational Attainment Buckets',-.4,5)

# Normalized Education (18+) for All States
createBarChart(eduByStateNorm,'Normalized Education (18+) for All States','State','Normalized % Population','Educational Attainment Buckets',-.4,5)


# Reading files
# Reading files
death_data = '../fastfoodfacts/resources/NCHS_LeadingCauses.csv'
chronic_ind_data = '../fastfoodfacts/resources/U.S._Chronic_Disease_Indicators_N.csv'
death_data_df = pd.read_csv(death_data, encoding = 'ISO-8859-1')
chronic_ind_data_df = pd.read_csv(chronic_ind_data, encoding = 'ISO-8859-1')

# Starting analysis on the chronic indicators file
# Note the number of records
chronic_ind_data_df.info()

# Notice the drop in the number of records
chronic_ind_data_df[chronic_ind_data_df['YearEnd'] == 2015].info()

# Need the 2015 only data
chronic_ind_data_df = chronic_ind_data_df[chronic_ind_data_df['YearEnd'] == 2015]
# chronic_ind_data_df['Topic'].value_counts()
counts_ind = chronic_ind_data_df['Topic'].value_counts()

# Plotting chronic indicators for 2015
counts_ind.plot(kind='bar', color=['gray'])
plt.ylabel("Quantity Reported", size=10)
plt.grid(True, color='gray', linestyle='-', linewidth=.5)
plt.xlabel("Chronic Indicators", size=10)
plt.title('Listing of Top Chronic Indicators for 2015', size=17)
plt.savefig('../fastfoodfacts/resources/TopdiseaseInd.png', bbox_inches='tight', pad_inches=2)
plt.show()

# Analysis on Three Indicators (Diabeties, Heart, Nutrition)
# Chronic data based on Diabeties
chronic_dia_ind_df = chronic_ind_data_df[chronic_ind_data_df['Topic'].str.contains('Dia')]
chronic_dia_ind_df['Question'].value_counts()

chronic_gb_dia_ind_df = chronic_dia_ind_df.groupby(by=['YearEnd', 'LocationDesc', 'Question']).sum()
# chronic_gb_dia_ind_df

# Chronic data for the Cardio disease type
chronic_heart_ind_df = chronic_ind_data_df[chronic_ind_data_df['Topic'].str.contains('Cardio')]
chronic_heart_ind_df['Question'].value_counts()

# Analyzing nutrition data
chronic_nutri_ind_df = chronic_ind_data_df[chronic_ind_data_df['Topic'].str.contains('Nutr')]
chronic_nutri_ind_df['Question'].value_counts()

# Looked at pulmonary data and it doesn't seem to fit the fast food deal
# Recommendation will be to focus on diabeties, heart, nutrition
chronic_pulm_ind_df = chronic_ind_data_df[chronic_ind_data_df['Topic'].str.contains('Pulmonar')]
chronic_pulm_ind_df['Question'].value_counts()

# Death data by state
death_data_year = death_data_df[death_data_df['Year'] == 2015]
# death_data_year.head()

# Analyzing the deaths by type and state
death_data_year['113 Cause Name'].value_counts()
death_data_year['113 Cause Name'].unique()

# Getting the min death type and state
death_data_year.min()

# Getting the max death type and state
death_data_year.max()

# Looking at the number of deaths and seeing which state has the most and what type
death_data_year.sort_values(by='Deaths', ascending=False).head()

# Since 'all causes' acts as a summary I want to strip that out of the figures
death_data_not_all_causes = death_data_year[death_data_year['113 Cause Name'] != 'All Causes']

# death_data_not_all_causes.head()

# In this dataset notice that the United States shows up as a state so let's strip that out as well
death_data_not_all_causes.sort_values(by='Deaths', ascending=False).head(10)

# This dataset is all death types and all states only
# This dataset is all death types and all states only
death_data_NAC_noUS = death_data_not_all_causes[death_data_not_all_causes['State'] != 'United States']
# death_data_NAC_noUS.head()

# Creating a groupby by year and state
death_gb_state_data = death_data_NAC_noUS.groupby(by=['Year', 'State']).sum().reset_index()

# Plotting deaths by state
death_gb_state_data.plot(kind='bar', x='State', y='Deaths', subplots=False)
plt.ylabel("Number of Deaths", size=10)
plt.xlabel("States", size=10)
plt.title('Total Death Volume by State', size=17)
plt.savefig('../fastfoodfacts/resources/StatesDeath.png', bbox_inches='tight', pad_inches=2)
plt.show()

# Preparing data to plot
death_gb_state_data = death_data_NAC_noUS.groupby(by=['Year', 'State']).sum().reset_index()
death_gb_state_data.sort_values('Deaths', ascending=False).head(20)
death_top20_states = death_gb_state_data.sort_values('Deaths', ascending=False).head(20)

# Plotting top 20 states
death_top20_states.plot.bar('State', 'Deaths', color='gray')
plt.ylabel("Number of Deaths", size=10)
plt.xlabel("States", size=10)
plt.title('Top 20 States by Volume', size=17)
plt.savefig('../fastfoodfacts/resources/Top20StatesDeath.png', bbox_inches='tight', pad_inches=2)
plt.show()

# Lets study  3 southern states - Alabama, Tennessee, Georgia
death_data_NAC_noUS[death_data_NAC_noUS['State'] == 'Georgia'].plot.bar('Cause Name', 'Deaths', color='gray')
plt.ylabel("Number of Deaths", size=10)
plt.xlabel("Death Types", size=10)
plt.title('2015 Deaths - Georgia', size=17)
plt.savefig('../fastfoodfacts/resources/GADeath.png', bbox_inches='tight', pad_inches=2)
plt.show()

death_data_NAC_noUS[death_data_NAC_noUS['State'] == 'Tennessee'].plot.bar('Cause Name', 'Deaths', color='gray')
plt.ylabel("Number of Deaths", size=10)
plt.xlabel("Death Types", size=10)
plt.title('2015 Deaths - Tennessee', size=17)
plt.savefig('../fastfoodfacts/resources/TNDeath.png', bbox_inches='tight', pad_inches=2)
plt.show()

death_data_NAC_noUS[death_data_NAC_noUS['State'] == 'Alabama'].plot.bar('Cause Name', 'Deaths', color='gray')
plt.ylabel("Number of Deaths", size=10)
plt.xlabel("Death Types", size=10)
plt.savefig('../fastfoodfacts/resources/ALDeath.png', bbox_inches='tight', pad_inches=2)
plt.title('2015 Deaths - Alabama', size=17)
plt.show()


# Analysis suggest that some states don't have the same level of death cardio or cancer death rates
# Notice that Virginia has less heart disease than the southern states
death_data_NAC_noUS[death_data_NAC_noUS['State'] == 'Virginia'].plot.bar('Cause Name', 'Deaths', color='gray')
plt.ylabel("Number of Deaths", size=10)
plt.xlabel("Death Types", size=10)
plt.title('2015 Deaths - Virginia', size=17)
plt.savefig('../fastfoodfacts/resources/VADeath.png')
plt.show()

# Notice that Arizona has less heart disease than the southern states
death_data_NAC_noUS[death_data_NAC_noUS['State'] == 'Arizona'].plot.bar('Cause Name', 'Deaths', color='gray')
plt.ylabel("Number of Deaths", size=10)
plt.xlabel("Death Types", size=10)
plt.title('2015 Deaths - Arizona', size=17)
plt.show()



# I want to compare size of population to number of deaths/death types
# This is where I will insert that code

death_gb_cause_data = death_data_NAC_noUS.groupby(by=['Year', '113 Cause Name']).sum().reset_index()


death_gb_cause_data.plot(kind='bar', x='113 Cause Name', y='Deaths', color='gray')
plt.ylabel("Number of Deaths", size=10)
plt.xlabel("Death Types", size=10)
plt.title('Top Death Types by Volume', size=17)
plt.savefig('../fastfoodfacts/resources/topDeathtypes.png', bbox_inches='tight', pad_inches=2)
plt.show()


# Plotting diabeties data
death_dia_data = death_data_NAC_noUS[death_data_NAC_noUS['Cause Name'].str.contains('Dia')]
death_dia_data.sort_values('Deaths', ascending=False)
death_dia_data.sort_values('Deaths', ascending=False).tail(10)

# Plotting cardio data
death_heart_data = death_data_NAC_noUS[death_data_NAC_noUS['Cause Name'].str.contains('Heart')]
death_heart_data.sort_values('Deaths', ascending=False)
death_heart_data.sort_values('Deaths', ascending=False).tail(10)

count_edu_AL = eduByState.loc['Alabama', :].describe()
count_edu_TN = eduByState.loc['Tennessee', :].describe()
count_edu_GA = eduByState.loc['Georgia', :].describe()
count_edu_VA = eduByState.loc['Virginia', :].describe()

fig, ax = plt.subplots()
count_edu_AL[3:8].plot(ax=ax, color='blue', linestyle='--', label='Alabama', marker='>')
count_edu_TN[3:8].plot(ax=ax, color='gray', linestyle='--', label='Tennessee', marker='o')
count_edu_GA[3:8].plot(ax=ax, color='black', linestyle='--', label='Georgia', marker='^')
count_edu_VA[3:8].plot(ax=ax, color='red', linestyle='--', label='Virginia', marker='<')
plt.grid(True, color='gray', linestyle='-', linewidth=.5)
plt.ylabel("# of People - Educated", size=10)
plt.xlabel("Quartiles", size=10)
plt.legend(loc='best')
plt.title('# of People per Quartile', size=20)
plt.show()

ttest_GA = eduByState.loc['Georgia', :]
ttest_VA = eduByState.loc['Virginia', :]
stats.ttest_ind(ttest_GA,ttest_VA)
ttest_AL = eduByState.loc['Alabama', :]
ttest_VA = eduByState.loc['Virginia', :]
stats.ttest_ind(ttest_GA,ttest_VA)

popDFstate = popDFmapped.groupby(by='State').sum().sort_values(by='Population', ascending=False)
popDFstate_only = popDFstate['Population']
popDFstate_only = pd.DataFrame(popDFstate_only, columns=['Population'])
popDFstate_only = popDFstate_only.reset_index()
popDeathstateDataDF = pd.merge(popDFstate_only, death_gb_state_data, on='State', how='outer')
popDeathstateDataDF = popDeathstateDataDF[['Year', 'State', 'Population', 'Deaths']]

for x in popDeathstateDataDF.iterrows():
    ratio = (x[1]['Deaths'] / x[1]['Population']) * 100
    popDeathstateDataDF.set_value(value=ratio, col='ratio', index=x[0])

avgpopDeathstateDF = popDeathstateDataDF['ratio'].describe()
above_avg_death_rate = popDeathstateDataDF[popDeathstateDataDF['ratio'] >= avgpopDeathstateDF['mean']]

fig, (ax1, ax2, ax3) = plt.subplots(3, 1, sharex='all', figsize=(18,5))
plt.suptitle('States with Death Rates Above the Mean', x=0.5, y=1.05, fontsize=22)
above_avg_death_rate.plot.bar(x='State', y='Population', ax=ax1, color='pink', label='Population')
above_avg_death_rate.plot.bar(x='State', y='Deaths', ax=ax2, color='red', label='Deaths')
above_avg_death_rate.plot.bar(x='State', y='ratio', ax=ax3, color='gray', label='Rate')
plt.legend(loc='best')
plt.tight_layout()
plt.savefig('../fastfoodfacts/resources/statesabovemean.png', bbox_inches='tight', pad_inches=2)
plt.xticks(np.arange(18), above_avg_death_rate.loc[:, 'State'], rotation=90 )
plt.show()

ff_df_gb_state = ff_df.groupby(by='State').sum()
ff_df_gb_state = ff_df_gb_state.reset_index()
ff_df_gb_state = pd.merge(ff_df_gb_state, abbrMap, left_on='State', right_on='Abbreviation', how='outer')
ff_df_gb_state = ff_df_gb_state[['State_y', 'Fast Food Restaurants 2015 (PROJECTED)']]
incomeByState = incomeByState.reset_index()
incomeByState_ff_df = pd.merge(incomeByState, ff_df_gb_state, left_on='State', right_on='State_y', how='outer')
for index,row in incomeByState_ff_df.iterrows():
    incBelow40 = row[1:8].sum()
    incAbove40 = row[8:17].sum()
    incomeByState_ff_df.set_value(value=incBelow40, col='IncBelow40', index=index)
    incomeByState_ff_df.set_value(value=incAbove40, col='IncAbove40', index=index)

incomeByState_ff_df = incomeByState_ff_df[['State', 'Fast Food Restaurants 2015 (PROJECTED)','IncBelow40', 'IncAbove40']]

x1 = incomeByState_ff_df['Fast Food Restaurants 2015 (PROJECTED)']
y1 = incomeByState_ff_df['IncBelow40']
x1 = x1.fillna(0)
y1 = y1.fillna(0)
slope, intercept, r_value, p_value, std_err = stats.linregress(x1, y1)
plt.plot(x1, y1, 'o', label='original data')
plt.plot(x1, intercept + slope*x1, 'r', label='fitted line')
plt.legend()
plt.show()

x1 = incomeByState_ff_df['Fast Food Restaurants 2015 (PROJECTED)']
y1 = incomeByState_ff_df['IncBelow40']
x1 = x1.fillna(0)
y1 = y1.fillna(0)
slope, intercept, r_value, p_value, std_err = stats.linregress(x1, y1)
x2 = incomeByState_ff_df['Fast Food Restaurants 2015 (PROJECTED)']
y2 = incomeByState_ff_df['IncAbove40']
x2 = x2.fillna(0)
y2 = y2.fillna(0)
slope, intercept, r_value, p_value, std_err = stats.linregress(x2, y2)
fig, ax = plt.subplots(figsize=(10,5), sharey='all')
plt.suptitle('Volume of FF Restaurants to Salary', x=0.5, y=1, fontsize=22)
incomeByState_ff_df.plot.scatter(x='Fast Food Restaurants 2015 (PROJECTED)', ax=ax, y='IncBelow40', color='red', marker='o')
incomeByState_ff_df.plot.scatter(x='Fast Food Restaurants 2015 (PROJECTED)', ax=ax, y='IncAbove40', color='black', marker='o')
plt.plot(x1, intercept + slope*x1, 'r', label='<40k fitted line')
plt.plot(x2, intercept + slope*x2, 'black', label='>40k fitted line')
plt.legend(loc='best')
plt.savefig('../fastfoodfacts/resources/ffincrelation.png', bbox_inches='tight', pad_inches=2)
plt.show()

# rg=sns.regplot
x1 = incomeByState_ff_df['Fast Food Restaurants 2015 (PROJECTED)']
y1 = incomeByState_ff_df['IncBelow40']
x1 = x1.fillna(0)
y1 = y1.fillna(0)
slope, intercept, r_value, p_value, std_err = stats.linregress(x1, y1)
y = y1
x = x1
d = incomeByState_ff_df
# Show the results of a linear regression within each dataset
ax = sns.regplot(x=x, y=y, data=d, color='gray')
plt.title('FF Restaurant Volume for <40k Salary')
plt.show()

# rg=sns.regplot
x2 = incomeByState_ff_df['Fast Food Restaurants 2015 (PROJECTED)']
y2 = incomeByState_ff_df['IncAbove40']
x2 = x2.fillna(0)
y2 = y2.fillna(0)
slope, intercept, r_value, p_value, std_err = stats.linregress(x2, y2)
y = y2
x = x2
d = incomeByState_ff_df
# Show the results of a linear regression within each dataset
ax = sns.regplot(x=x, y=y, data=d, color='blue')
plt.title('FF Restaurant Volume for <40k Salary')
plt.show()

# rg=sns.regplot
x2 = incomeByState_ff_df['Fast Food Restaurants 2015 (PROJECTED)']
y2 = incomeByState_ff_df['IncAbove40']
x2 = x2.fillna(0)
y2 = y2.fillna(0)
slope, intercept, r_value, p_value, std_err = stats.linregress(x2, y2)
y = y2
x = x2
d = incomeByState_ff_df
r2 = r_value*r_value
print('x1 slope=', slope, 'x1 r^2=', r2)
# Show the results of a linear regression within each dataset
ax = sns.regplot(x=x, y=y, data=d, color='blue', label='<40k Salary')
x1 = incomeByState_ff_df['Fast Food Restaurants 2015 (PROJECTED)']
y1 = incomeByState_ff_df['IncBelow40']
x1 = x1.fillna(0)
y1 = y1.fillna(0)
slope, intercept, r_value, p_value, std_err = stats.linregress(x1, y1)
y = y1
x = x1
d = incomeByState_ff_df
r3 = r_value*r_value
print('x2 slope=', slope, 'x2 r^2=', r3)
# Show the results of a linear regression within each dataset
ax = sns.regplot(x=x, y=y, data=d, color='gray', label='>40k Salary')
plt.suptitle('FF Restaurant Volume for Salary - Above and Below 40k', x=0.5, y=1, fontsize=12)
plt.legend(loc='best')
plt.savefig('../fastfoodfacts/resources/ffsalaryincrelation.png', bbox_inches='tight', pad_inches=2)
plt.show()