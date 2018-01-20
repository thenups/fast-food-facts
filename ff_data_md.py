##dataframes of interest::
##resbystate: shows the fast food restaurant volumes by state
##

# In[3]:


res_data = pd.ExcelFile('../Workspace/DataDownload.xls')
restaurant_df = pd.read_excel(res_data, 'RESTAURANTS')
restaurant_df.head()


# In[9]:


restaurant_df = restaurant_df.rename(columns={'FFR09':'Fast Food Restaurants 2009',
                                              'FFR14':'Fast Food Restaurants 2014',
                                              'PCH_FFR_09_14':'Fast-food restaurants (% change)',
                                              'FFRPTH09':'Fast-food restaurants/1,000 pop 2009',
                                              'FFRPTH14':'Fast-food restaurants/1,000 pop 2014',
                                              'PCH_FFRPTH_09_14':'Fast-food restaurants/1,000 pop (% change)'})
restaurant_df.head()


# In[10]:


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


# In[195]:


# fast_food_df.insert(loc=0,column='Yearly Growth Rate %',value=int)
# fast_food_df.head()
# fast_food_df.insert(loc=0,column='Fast Food Restaurants 2015 (PROJECTED)',value=int)
# fast


# In[11]:


# fast_food_df.insert(loc=0,column='Yearly Growth Rate %',value=int)

ff_df=fast_food_df[['FIPS',
                    'State',
                    'County',
                    'Fast Food Restaurants 2009',
                    'Fast Food Restaurants 2014',
                    'Fast-food restaurants (% change)',
                    'Fast-food restaurants/1,000 pop 2009',
                    'Fast-food restaurants/1,000 pop 2014',
                    'Fast-food restaurants/1,000 pop (% change)']].copy()
ff_df.head()


# In[12]:


popDFmapped.head()


# In[13]:


for index,row in ff_df.iterrows():
    total_gr = row['Fast-food restaurants (% change)']
    yr_gr = total_gr/5
    ff_df.set_value(index,'Yearly Growth Rate %',yr_gr)
    ff09 = row['Fast Food Restaurants 2009']
    ff14 = row['Fast Food Restaurants 2014']
    projection = round((ff14*(yr_gr/100)) + ff14,0)
    ff_df.set_value(index,'Fast Food Restaurants 2015 (PROJECTED)',projection)
   
    
    
    
        
ff_df.head()
# del ff_df['Fast-food restaurants/1,000 pop 2009']
del ff_df['Fast-food restaurants/1,000 pop 2014']
del ff_df['Fast-food restaurants/1,000 pop (% change)']
ff_df.head()


# In[14]:


# ff_df['County'] = ff_df['County'] + ' County'
# ff_df['County'] = ff_df['County'].str.rstrip(' County')
# ff_df['County'] = ff_df['County'] + ' County'
ff_df.head()


# In[1]:


# FIPSandRes = pd.merge(ff_df,popDFmapped,how='inner',on=['County'])

# FIPSandRes.head()
# del FIPSandRes['Fast-food restaurants/1,000 pop 2009']
# del FIPSandRes['Fast-food restaurants/1,000 pop 2014']
# del FIPSandRes['Fast-food restaurants/1,000 pop (% change)']
# FIPSandRes.head(25)


# In[17]:


resbystate15 = ff_df.groupby(["State"])['Fast Food Restaurants 2015 (PROJECTED)'].sum()
resbystate14 =  ff_df.groupby(["State"])['Fast Food Restaurants 2014'].sum()
resbystate15.head(20)
resbystate=pd.DataFrame({'Abbreviation':resbystate15.index,'Fast Food Restaurant Count 2014':resbystate14.values, 'Fast Food Restaurant Count 2015 (prj)':resbystate15.values}).copy()
resbystate.head()








# In[25]:


#bar chart of 2015 restaurants NOT NORMALIZED 
sns.palplot(sns.hls_palette(16, l=.3, s=.8))
plt.figure(figsize=(20,5))
x_axis = np.arange(len(resbystate))
tick_locations = [value for value in x_axis]
ff1=plt.bar(x_axis, resbystate['Fast Food Restaurant Count 2015 (prj)'], width = 0.2,align='center')
ff2=plt.bar(x_axis + 0.25, resbystate['Fast Food Restaurant Count 2014'], width = 0.2,align='center')

plt.xticks(tick_locations, resbystate['Abbreviation'], rotation="vertical")
plt.title('Projected Restaurant Volume for 2015')
plt.xlabel('States')
plt.ylabel('Restaurant Volume')
plt.legend()
plt.tight_layout()
plt.show()


# In[37]:






# In[61]:



ff_df.rename(columns={'State':'Abbreviation'}, inplace=True)

ff_df.head()


# In[39]:


# countypop = pd.merge(ff_df,popDFmapped,how='inner',on=['Abbreviation','County'])
# countypop.head()


# for index,row in countypop.iterrows():
#     pop = row['Population']
#     ffres14 = row['Fast Food Restaurants 2014']
#     ffres15 = row['Fast Food Restaurants 2015 (PROJECTED)']
#     ffpercap14 = ((ffres14/pop)*100)
#     ffpercap15 = ((ffres15/pop)*100)
#     ff_df.set_value(index,'Fast Food Restaurants Per Capita, 2014',ffpercap14)
#     ff_df.set_value(index,'Fast Food Restaurants Per Capita, 2015',ffpercap15)
    
# countypop.head()


# In[ ]:


states = countypop.groupby('')


# In[80]:


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

##To create top 10 and bottom 10 graphs 
top10=resbystate.sort_values('Fast Food Restaurant Count 2015 (prj)', ascending=False).head(10)
bottom10=resbystate.sort_values('Fast Food Restaurant Count 2015 (prj)').head(10)

