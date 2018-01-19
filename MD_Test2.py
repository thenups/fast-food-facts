res_data = pd.ExcelFile('../Workspace/DataDownload.xls')
restaurant_df = pd.read_excel(res_data, 'RESTAURANTS')

restaurant_df = restaurant_df.rename(columns={'FFR09':'Fast Food Restaurants 2009',
                                              'FFR14':'Fast Food Restaurants 2014',
                                              'PCH_FFR_09_14':'Fast-food restaurants (% change)',
                                              'FFRPTH09':'Fast-food restaurants/1,000 pop 2009',
                                              'FFRPTH14':'Fast-food restaurants/1,000 pop 2014',
                                              'PCH_FFRPTH_09_14':'Fast-food restaurants/1,000 pop (% change)'})
restaurant_df.head()

fast_food_df=restaurant_df[['FIPS',
                            'State',
                            'County',
                            'Fast Food Restaurants 2009',
                            'Fast Food Restaurants 2014',
                            'Fast-food restaurants (% change)',
                            'Fast-food restaurants/1,000 pop 2009',
                            'Fast-food restaurants/1,000 pop 2014',
                            'Fast-food restaurants/1,000 pop (% change)']].copy()
fast_food_df.head()

# fast_food_df.insert(loc=0,column='Yearly Growth Rate %',value=int)
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
resbystate.head()

sns.palplot(sns.hls_palette(16, l=.3, s=.8))
plt.figure(figsize=(20,5))
x_axis = np.arange(len(resbystate))
tick_locations = [value for value in x_axis]
ff1=plt.bar(x_axis, resbystate['Restaurant Count 2015 (prj)'], width = 0.2,align='center')
ff2=plt.bar(x_axis + 0.25, resbystate['Restaurant Count 2014'], width = 0.2,align='center')

plt.xticks(tick_locations, resbystate['State'], rotation="vertical")
plt.title('Projected Restaurant Volume for 2015')
plt.xlabel('States')
plt.ylabel('Restaurant Volume')
plt.legend()
plt.tight_layout()
plt.show()

countypop = pd.merge(ff_df,popDFmapped,how='inner',on=['Abbreviation','County'])
countypop.head()


for index,row in countypop.iterrows():
    pop = row['Population']
    ffres14 = row['Fast Food Restaurants 2014']
    ffres15 = row['Fast Food Restaurants 2015 (PROJECTED)']
    ffpercap14 = ((ffres14/pop)*100)
    ffpercap15 = ((ffres15/pop)*100)
    ff_df.set_value(index,'Fast Food Restaurants Per Capita, 2014',ffpercap14)
    ff_df.set_value(index,'Fast Food Restaurants Per Capita, 2015',ffpercap15)
    
countypop.head()

#Normalized bar chart  
sns.palplot(sns.hls_palette(16, l=.3, s=.8))
plt.figure(figsize=(20,5))
x_axis = np.arange(len(countypop))
tick_locations = [value for value in x_axis]
ff1=plt.bar(x_axis, countypop['Fast Food Restaurants Per Capita, 2014'], width = 0.2,align='center')
ff2=plt.bar(x_axis + 0.25, countypop['Fast Food Restaurants Per Capita, 2015'], width = 0.2,align='center')

# plt.xticks(tick_locations, countypop['Abbreviation'], rotation="vertical")
plt.title('Fast Food Restaurant Volume per Capita, 2014-2015')
plt.xlabel('States')
plt.ylabel('Restaurant Volume')
plt.legend()
plt.tight_layout()
plt.show()