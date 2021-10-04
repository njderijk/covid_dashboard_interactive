import pandas as pd
import numpy as np
import geopandas as gpd
import requests
import cbsodata
import dateparser
import datetime as dt
from datetime import datetime as date
import xlsxwriter
import plotly.express as px
import geojson as gjs
 
#NL1
def updateNL1():
    #download data
    source = "src/nl_data1.csv"
    url = 'https://data.rivm.nl/covid-19/COVID-19_aantallen_gemeente_per_dag.csv'
    try:
        r = requests.get(url)
    except Exception as e:
        print('NL1: Error code: ', e.code)
    
    #open data as pandas dataframe
    with open(source, "wb") as f:
        f.write(r.content)
    global NL1
    NL1 = pd.read_table(source, delimiter =";", skiprows = 0)
    
    #clean dataframe
    NL1 = pd.DataFrame(NL1, columns = ['Date_of_publication', 'Security_region_code', 'Security_region_name', 'Total_reported', 'Hospital_admission', 'Deceased'])
    NL1 = NL1.replace('Twente', 'Overijssel')
    NL1 = NL1.replace('IJsselland', 'Overijssel')
    NL1 = NL1.replace('Noord- en Oost-Gelderland', 'Gelderland')
    NL1 = NL1.replace('Gelderland-Midden', 'Gelderland')
    NL1 = NL1.replace('Gelderland-Zuid', 'Gelderland')
    NL1 = NL1.replace('Amsterdam-Amstelland', 'Noord-Holland')
    NL1 = NL1.replace('Noord-Holland-Noord', 'Noord-Holland')
    NL1 = NL1.replace('Zaanstreek-Waterland', 'Noord-Holland')
    NL1 = NL1.replace('Gooi en Vechtstreek', 'Noord-Holland')
    NL1 = NL1.replace('Kennemerland', 'Noord-Holland')
    NL1 = NL1.replace('Zuid-Holland-Zuid', 'Zuid-Holland')
    NL1 = NL1.replace('Hollands-Midden', 'Zuid-Holland')
    NL1 = NL1.replace('Rotterdam-Rijnmond', 'Zuid-Holland')
    NL1 = NL1.replace('Haaglanden', 'Zuid-Holland')
    NL1 = NL1.replace('Brabant-Zuidoost', 'Noord-Brabant')
    NL1 = NL1.replace('Midden- en West-Brabant', 'Noord-Brabant')
    NL1 = NL1.replace('Brabant-Noord', 'Noord-Brabant')
    NL1 = NL1.replace('Limburg-Zuid', 'Limburg')
    NL1 = NL1.replace('Limburg-Noord', 'Limburg')
    NL1['Total_reported'] = NL1.groupby(['Date_of_publication', 'Security_region_name'])['Total_reported'].transform('sum')
    NL1['Hospital_admission'] = NL1.groupby(['Date_of_publication', 'Security_region_name'])['Hospital_admission'].transform('sum')
    NL1['Deceased'] = NL1.groupby(['Date_of_publication', 'Security_region_name'])['Deceased'].transform('sum')
    NL1 = NL1.drop_duplicates(subset=['Date_of_publication', 'Security_region_name'])
    #NL1 = NL1.dropna()
    
    print("NL1 UPDATED")
 
    
#NL2 https://opendata.cbs.nl/#/CBS/nl/dataset/37230ned/table?dl=5409C
def updateNL2():
    #open dataframe via the cbs opendata pakage
    global NL2
    NL2 = pd.DataFrame(
        cbsodata.get_data('37230ned', select=['Perioden','RegioS', 'BevolkingAanHetBeginVanDePeriode_1']))
    
    #Clean the dataframe
    NL2 = NL2.rename(columns={"Perioden": "Date_of_publication", "RegioS":"Security_region_name"}) 
    NL2 = NL2.dropna()
    
    #fix the date
    NL2 = NL2.sort_values(by=['Date_of_publication'])
    NL2 = NL2.iloc[113851: , :]
    NL2['Security_region_name'] = NL2['Security_region_name'].map(lambda x: x.rstrip(' (PV)'))
    NL2 = NL2[NL2['Security_region_name'].isin(['Utrecht','Groningen','Zuid-Holland', 'Fryslân', 'Drenthe','Overijssel', 'Flevoland', 'Gelderland','Noord-Holland','Zeeland','Noord-Brabant','Limburg'])]
    
    #Parse dutch date to correct datetime
    ####Might take quite a while####
    NL2['Date_of_publication'] = NL2['Date_of_publication'] + ' 01'
    NL2.Date_of_publication = NL2.Date_of_publication.apply(lambda x: dateparser.parse(x))
    NL2['Date_of_publication'] = pd.to_datetime(NL2['Date_of_publication'])
    NL2 = NL2.set_index('Date_of_publication').groupby('Security_region_name').resample('1D')['BevolkingAanHetBeginVanDePeriode_1'].ffill().reset_index()
    
    
    #insert missing dates and the last known inhabitant number in the DF
    
    #get datetime of today
    today = date.today()
    #loop over all provinces in list
    for i in NL2.Security_region_name.unique():
        newdf = NL2.loc[NL2['Security_region_name'] == i]  
        #get last known inhabitant number
        lastknownvalue = newdf['BevolkingAanHetBeginVanDePeriode_1'].iloc[-1]
        #get last known date
        lastknowndate = newdf['Date_of_publication'].iloc[-1]
        #Make index of first date till today
        #fill dates between
        idx = pd.date_range(lastknowndate, today)
        idx = idx[1:]
        for j in idx:
            #add inhabitant number to new dates
            NL2 = NL2.append({"Security_region_name":i, "Date_of_publication":j, "BevolkingAanHetBeginVanDePeriode_1":lastknownvalue}, ignore_index = True)
    
    NL2.drop_duplicates(subset = None, keep= False, inplace = True)
    print("NL2 UPDATED")
 
#NL3
def updateNL3():
    #Download data
    source = "src/nl_data3.csv"
    url = 'https://data.rivm.nl/covid-19/COVID-19_uitgevoerde_testen.csv'
    try:
        r = requests.get(url)
        with open(source, "wb") as f:
            f.write(r.content)    
    except Exception as e:
        print('NL3: Error code: ', e.code)
    
    #Open data as pandas dataframe
    global NL3
    NL3 = pd.read_table(source, delimiter =";", skiprows = 0)
    
    #Clean dataframe: Change dutch 'Veiligheidsregio's' to the according provinces and sum the numbers. e.g. Province Gelderland consists of veiligheidsregio's Noord- en Oost-Gelderland, Midden-Gelderland and Zuid-Gelderland 
    NL3 = pd.DataFrame(NL3, columns = ['Date_of_statistics', 'Security_region_code', 'Security_region_name', 'Tested_with_result', 'Tested_positive'])
    NL3 = NL3.rename(columns={"Date_of_statistics": "Date_of_publication"})
    NL3 = NL3.replace('Twente', 'Overijssel')
    NL3 = NL3.replace('IJsselland', 'Overijssel')
    NL3 = NL3.replace('Noord- en Oost-Gelderland', 'Gelderland')
    NL3 = NL3.replace('Gelderland-Midden', 'Gelderland')
    NL3 = NL3.replace('Gelderland-Zuid', 'Gelderland')
    NL3 = NL3.replace('Amsterdam-Amstelland', 'Noord-Holland')
    NL3 = NL3.replace('Noord-Holland-Noord', 'Noord-Holland')
    NL3 = NL3.replace('Zaanstreek-Waterland', 'Noord-Holland')
    NL3 = NL3.replace('Gooi en Vechtstreek', 'Noord-Holland')
    NL3 = NL3.replace('Kennemerland', 'Noord-Holland')
    NL3 = NL3.replace('Zuid-Holland-Zuid', 'Zuid-Holland')
    NL3 = NL3.replace('Hollands-Midden', 'Zuid-Holland')
    NL3 = NL3.replace('Rotterdam-Rijnmond', 'Zuid-Holland')
    NL3 = NL3.replace('Haaglanden', 'Zuid-Holland')
    NL3 = NL3.replace('Brabant-Zuidoost', 'Noord-Brabant')
    NL3 = NL3.replace('Midden- en West-Brabant', 'Noord-Brabant')
    NL3 = NL3.replace('Brabant-Noord', 'Noord-Brabant')
    NL3 = NL3.replace('Limburg-Zuid', 'Limburg')
    NL3 = NL3.replace('Limburg-Noord', 'Limburg')
    NL3['Tested_with_result'] = NL3.groupby(['Date_of_publication', 'Security_region_name'])['Tested_with_result'].transform('sum')
    NL3['Tested_positive'] = NL3.groupby(['Date_of_publication', 'Security_region_name'])['Tested_positive'].transform('sum')
    NL3 = NL3.drop_duplicates(subset=['Date_of_publication', 'Security_region_name'])
    NL3 = NL3.dropna()
    print("NL3 UPDATED")
    
#BE1
def updateBE1():
    #Download excel sheet
    source = "src/be_data1.xlsx"
    url = 'https://epistat.sciensano.be/Data/COVID19BE.xlsx'
    try:
        r = requests.get(url)
        with open(source, "wb") as f:
            f.write(r.content)
    except Exception as e:
        print('BE1: Error code: ', e.code)
    
    #Open the sheets as seperate dataframes
    global BE1, BE11, BE12, BE13
    tab = 'TESTS'
    BE11 = pd.read_excel(io=source, sheet_name=tab)
    BE11 = pd.DataFrame(BE11, columns = ['DATE', 'PROVINCE', 'REGION', 'TESTS_ALL', 'TESTS_ALL_POS'])
    tab = 'HOSP'
    BE12 = pd.read_excel(io=source, sheet_name=tab)
    BE12 = pd.DataFrame(BE12, columns = ['DATE', 'PROVINCE', 'REGION', 'TOTAL_IN'])
    tab = 'MORT'
    BE13 = pd.read_excel(io=source, sheet_name=tab)
    BE13 = pd.DataFrame(BE13, columns = ['DATE', 'REGION', 'DEATHS'])
    print("BE1 UPDATED")
 
#BE2
def updateBE2():
    #Download excel sheet
    source = "src/be_data2.xlsx"
    url = 'https://statbel.fgov.be/sites/default/files/files/documents/bevolking/5.1%20Structuur%20van%20de%20bevolking/Bevolking_per_gemeente.xlsx'
    tab = "Bevolking in 2020"
    try:
        r = requests.get(url)
        with open(source, "wb") as f:
            f.write(r.content)
    except Exception as e:
        print('BE2: Error code: ', e.code)
    
    #Open the needed sheets as dataframes
    global BE2
    BE2 = pd.read_excel(io=source, sheet_name=tab, skiprows = 1)
    # Clean the dataframe: first and last rows do not contain useful information, NIS Codes represent Provinces, so these need to be replaced.
    BE2 = BE2[2:len(BE2)-4]
    BE2 = pd.DataFrame(BE2, columns = ['NIS code', 'Totaal'])
    BE2['NIS code'] = BE2['NIS code'].str.slice(stop=1)
    BE2['NIS code'] = BE2['NIS code'].replace('0', 'Antwerpen')
    BE2['NIS code'] = BE2['NIS code'].replace('1', 'BrabantWallon')
    BE2['NIS code'] = BE2['NIS code'].replace('2', 'VlaamsBrabant')
    BE2['NIS code'] = BE2['NIS code'].replace('3', 'WestVlaanderen')
    BE2['NIS code'] = BE2['NIS code'].replace('4', 'OostVlaanderen')
    BE2['NIS code'] = BE2['NIS code'].replace('5', 'Hainaut')
    BE2['NIS code'] = BE2['NIS code'].replace('6', 'Liège')
    BE2['NIS code'] = BE2['NIS code'].replace('7', 'Limburg')
    BE2['NIS code'] = BE2['NIS code'].replace('8', 'Luxembourg')
    BE2['NIS code'] = BE2['NIS code'].replace('9', 'Namur')
   
    BE2 = BE2.rename(columns={"NIS code": "PROVINCE"})
    BE2 = BE2.drop_duplicates(subset=['PROVINCE'])
    
    print("BE2 UPDATED")
 
#UK1
def updateUK1():
    #Download csv
    source = "src/uk_data1.csv"
    url = 'https://api.coronavirus.data.gov.uk/v2/data?areaType=nhsRegion&metric=newAdmissions&metric=hospitalCases&format=csv'
    try:
        r = requests.get(url)
        with open(source, "wb") as f:
            f.write(r.content)
    except Exception as e:
        print('UK1: Error code: ', e.code)
 
    #Open sheet as dataframe
    global UK1
    UK1 = pd.read_table(source, delimiter =",")
    UK1 = UK1[['areaName', 'date', 'hospitalCases', 'newAdmissions']]
    UK1 = UK1.rename(columns={"date":"DATE", "areaName":"PROVINCE", "newAdmissions":"Hospital_admission"})
    UK1 = UK1[['DATE', 'PROVINCE', 'Hospital_admission']]
    print("UK1 UPDATED")
 
#UK2
def updateUK2():
    source = "src/uk_data2.csv"
    url = 'https://api.coronavirus.data.gov.uk/v2/data?areaType=region&metric=newCasesByPublishDate&metric=newDeathsByDeathDate&metric=newVirusTests&format=csv'
    try:
        r = requests.get(url)
        with open(source, "wb") as f:
            f.write(r.content)
    except Exception as e:
        print('UK2: Error code: ', e.code)
 
    global UK2
    UK2 = pd.read_table(source, delimiter =",")
    UK2 = UK2.replace('Yorkshire and The Humber', 'North East and Yorkshire')
    UK2 = UK2.replace('North East', 'North East and Yorkshire')
    UK2 = UK2.replace('East Midlands', 'Midlands')
    UK2 = UK2.replace('West Midlands', 'Midlands')
 
    UK2['newCasesByPublishDate'] = UK2.groupby(['date', 'areaName'])['newCasesByPublishDate'].transform('sum')
    UK2['newDeathsByDeathDate'] = UK2.groupby(['date', 'areaName'])['newDeathsByDeathDate'].transform('sum')
    UK2 = UK2.drop_duplicates(subset=['date', 'areaName'])
    UK2.dropna()
    
    UK2 = UK2[['areaName', 'date', 'newCasesByPublishDate', 'newDeathsByDeathDate']]
    UK2 = UK2.rename(columns={"date":"DATE", "areaName":"PROVINCE", "newCasesByPublishDate":"Tested_positive", "newDeathsByDeathDate":"Deceased"})
    UK2 = UK2[['DATE', 'PROVINCE', 'Tested_positive', 'Deceased']]
 
    print("UK2 UPDATED")
    
#UK3
def updateUK3():
    source = "src/uk_data3.csv"
    url = 'https://api.coronavirus.data.gov.uk/v2/data?areaType=nation&areaCode=E92000001&metric=newPCRTestsByPublishDate&format=csv'
    try:
        r = requests.get(url)
        with open(source, "wb") as f:
            f.write(r.content)
    except Exception as e:
        print('UK3: Error code: ', e.code)
 
    global UK3
    UK3 = pd.read_table(source, delimiter =",")
    UK3 = UK3[['date', 'newPCRTestsByPublishDate']]
    UK3 = UK3.rename(columns={"date":"DATE", "newPCRTestsByPublishDate":"Total_tested"})
    UK3 = UK3[['DATE', 'Total_tested']]
    print("UK3 UPDATED")
 
#UK4
def updateUK4():
    source = "src/uk_data4.csv"
    url = 'https://download.ons.gov.uk/downloads/filter-outputs/400ca094-d964-4335-8402-3039a098691d.csv'
    try:
        r = requests.get(url)
        with open(source, "wb") as f:
            f.write(r.content)
    except Exception as e:
        print('UK4: Error code: ', e.code)
 
    global UK4
    UK4 = pd.read_table(source, delimiter =",")
 
    UK4 = UK4.replace('Yorkshire and The Humber', 'North East and Yorkshire')
    UK4 = UK4.replace('North East', 'North East and Yorkshire')
    UK4 = UK4.replace('East Midlands', 'Midlands')
    UK4 = UK4.replace('West Midlands', 'Midlands')
    UK4['v4_0'] = UK4.groupby(['Time', 'Geography'])['v4_0'].transform('sum')
    UK4 = UK4.drop_duplicates(subset=['Time', 'Geography'])
    UK4.dropna()
    
    UK4 = UK4[['v4_0', 'Time', 'Geography']]
    UK4 = UK4.rename(columns={"v4_0":"Inhabitants", "Time":"Year", "Geography":"PROVINCE"})
    UK4 = UK4[['Year', 'PROVINCE', 'Inhabitants']]
 
    UK4 = UK4[UK4['Year'] >= 2019]
 
    print("UK4 UPDATED")
 
#NLgeo
def updateNLgeo():
    global NLgeo 
    source = "src/nl_datageo.geojson"
    url = 'https://www.webuildinternet.com/articles/2015-07-19-geojson-data-of-the-netherlands/provinces.geojson'
    try:
        r = requests.get(url)
        with open(source, "wb") as f:
            f.write(r.content)
    except Exception as e:
        print('NLgeo: Error')
        
    NLgeo = gpd.read_file(source)
    NLgeo = NLgeo.replace(to_replace =["Friesland (Fryslân)"], value ="Fryslân")
    NLgeo.rename(columns={'name':'PROVINCE'}, inplace=True)
    NLgeo.to_file("src/NLgeo_updated.geojson", driver='GeoJSON')
 
    print("NLgeo UPDATED")
    return NLgeo
    
#BEgeo
def updateBEgeo():
    source = "src/be_datageo.geojson"
    url = 'https://raw.githubusercontent.com/mathiasleroy/Belgium-Geographic-Data/master/dist/polygons/geojson/Belgium.provinces.WGS84.geojson'
    try:
        r = requests.get(url)
        with open(source, "wb") as f:
            f.write(r.content)
    except Exception as e:
        print('BEgeo: Error')
 
    global BEgeo
    BEgeo = gpd.read_file(source)
    BEgeo=BEgeo[['NameDUT','geometry']]
    BEgeo=BEgeo.replace(to_replace =["Brussels Hoofdstedelijk Gewest"], value ="VlaamsBrabant + Brussel.")
    BEgeo=BEgeo.replace(to_replace =["Provincie Antwerpen"], value ="Antwerpen")
    BEgeo=BEgeo.replace(to_replace =["Provincie Vlaams-Brabant"], value ="VlaamsBrabant + Brussel")
    BEgeo=BEgeo.replace(to_replace =["Provincie Waals-Brabant"], value ="BrabantWallon")
    BEgeo=BEgeo.replace(to_replace =["Provincie West-Vlaanderen"], value ="WestVlaanderen")
    BEgeo=BEgeo.replace(to_replace =["Provincie Oost-Vlaanderen"], value ="OostVlaanderen")
    BEgeo=BEgeo.replace(to_replace =["Provincie Henegouwen"], value ="Hainaut")
    BEgeo=BEgeo.replace(to_replace =["Provincie Luik"], value ="Liège")
    BEgeo=BEgeo.replace(to_replace =["Provincie Limburg"], value ="Limburg")
    BEgeo=BEgeo.replace(to_replace =["Provincie Namen"], value ="Namur")
    BEgeo=BEgeo.replace(to_replace =["Provincie Luxemburg"], value ="Luxembourg")
    
    BEgeo.rename(columns={'NameDUT':'PROVINCE'}, inplace=True)
    
    BEgeo.to_file("src/BEgeo_updated.geojson", driver='GeoJSON')
    
    print("BEgeo UPDATED")
    return BEgeo
    
#UKgeo: misschien de NHS regions gebruiken van de volgende link, rest van de data is in nhs regions: https://data.gov.uk/dataset/66a7bb97-3da6-4e19-975b-1f0784909cd5/nhs-england-regions-april-2020-boundaries-en-bgc
def updateUKgeo():
    source = "src/uk_datageo.json"
    url = 'http://geoportal1-ons.opendata.arcgis.com/datasets/01fd6b2d7600446d8af768005992f76a_4.geojson'
    try:
        r = requests.get(url)
        with open(source, "wb") as f:
            f.write(r.content)
    except Exception as e:
        print('UKgeo: Error code: ', e.code)
 
    global UKgeo    
    UKgeo = gpd.read_file(source)
    UKgeo = UKgeo[['nuts118nm','geometry']]
    UKgeo = UKgeo.replace(to_replace =["East of England"], value ="East of England")
    UKgeo = UKgeo.replace(to_replace =["North East (England)"], value ="North East + Yorkshire.")
    UKgeo = UKgeo.replace(to_replace =["Yorkshire and The Humber"], value ="North East + Yorkshire")
    UKgeo = UKgeo.replace(to_replace =["South East (England)"], value ="South East")
    UKgeo = UKgeo.replace(to_replace =["South West (England)"], value ="South West")
    UKgeo = UKgeo.replace(to_replace =["West Midlands (England)"], value ="West Midlands + East Midlands.")
    UKgeo = UKgeo.replace(to_replace =["East Midlands (England)"], value ="West Midlands + East Midlands")
    UKgeo = UKgeo.replace(to_replace =["North West (England)"], value ="North West")
    UKgeo.rename(columns={'nuts118nm':'PROVINCE'}, inplace=True)
 
    UKgeo.to_file("src/UKgeo_updated.geojson", driver='GeoJSON')
 
    print("UKgeo UPDATED")
 
    return UKgeo
 
#Update all files or tables
def updateALL():
    updateNL1()
    updateNL2()
    updateNL3()
    updateBE1()
    updateBE2()
    updateUK1()
    updateUK2()
    updateUK3()
    updateUK4()
    # updateNLgeo()
    # updateBEgeo()
    # updateUKgeo()
    print("FINISHED")
 
def mergeNL():
    #Merge the 2 tabs of NL to 1 dataframe
    NL13 = pd.merge(NL1, NL3, how="inner", on=["Date_of_publication", "Security_region_name"])
 
    #parse to correct datetime
    NL13['Date_of_publication'] = pd.to_datetime(NL13.Date_of_publication)
    NL13.drop('Total_reported',axis='columns', inplace=True)
    global NL123
    #merge the first merge with the number of inhabitants
    NL123 = pd.merge(NL13, NL2, how="left", on=["Date_of_publication", "Security_region_name"])
    #NL123['Month'] = pd.DatetimeIndex(NL123['Date_of_publication']).month
    #NL123['Year'] = pd.DatetimeIndex(NL123['Date_of_publication']).year
    
    #Rename columns to uniform names
    NL123 = NL123.rename(columns={"Date_of_publication": "DATE", "Security_region_name":"PROVINCE", "BevolkingAanHetBeginVanDePeriode_1":"Inhabitants", "Tested_with_result":"Total_tested"})
    NL123.drop('Security_region_code_x',axis='columns', inplace=True)
    NL123.drop('Security_region_code_y',axis='columns', inplace=True)
 
    #NLmerged2.to_excel("output.xlsx",sheet_name='NL')
    global NL
    NL = NL123.sort_values(by="DATE", ascending=False)
 
    print("NL: FINISHED")
    return NL
 
    
def mergeBE():
  #Merge the dataframes into 1 dataframe
    BE11and12 = pd.merge(BE11, BE12, how="inner", on=["DATE", "PROVINCE", "REGION"])
    BE11and12and13 = pd.merge(BE11and12, BE13, how="inner", on=["DATE", "REGION"])
    
    #Save the merged dataframe as a global variable, drop the region column, duplicates and finally rename all columns to be uniform. 
    global BE    
    BE = pd.merge(BE11and12and13, BE2, how="inner", on=["PROVINCE"])
    BE.drop('REGION',axis='columns', inplace=True)
    BE = BE.drop_duplicates(subset=['PROVINCE', "DATE"])
    BE = BE.rename(columns={"Totaal":"Inhabitants", "DEATHS":"Deceased", "TOTAL_IN":"Hospital_admission", "TESTS_ALL":"Total_tested", "TESTS_ALL_POS":"Tested_positive"})
    BE = BE[['DATE', 'PROVINCE', 'Hospital_admission', 'Deceased', 'Total_tested', 'Tested_positive', 'Inhabitants']]
    BE = BE.sort_values(by="DATE", ascending=False)
 
    print("BE: FINISHED")      
    return BE
 
def mergeUK():
    #Merge all UK datasets as the UK dataset
    global UK, UK123, UK4
    UK12 = pd.merge(UK1, UK2, how="inner", on=["DATE", "PROVINCE"])
    UK123 = pd.merge(UK12, UK3, how="inner", on=["DATE"])
    UK123 = UK123[['DATE', 'PROVINCE', 'Hospital_admission', 'Deceased', 'Total_tested', 'Tested_positive']]
    UK123['Year'] = pd.DatetimeIndex(UK123['DATE']).year
 
    #The latest inhabitant numbers per NHS region are used in our dataframe, since no newer sources are available, in this case it it the 2019 data.
    #UK123['Year'] = UK123['Year'].fillna(value = UK123['Year'].max())
    UK123['Year'] = UK123['Year'].replace(2020, UK4['Year'].max())
    UK123['Year'] = UK123['Year'].replace(2021, UK4['Year'].max())
 
    UK = pd.merge(UK123, UK4, how="outer", on=["Year", "PROVINCE"])
    UK.drop('Year',axis='columns', inplace=True)
    UK = UK.sort_values(by="DATE", ascending=False)
 
    print("UK: FINISHED")
    return UK
 
def mergeALL():
    mergeNL()
    mergeBE()
    mergeUK()
 
 
def writeXLSX():
    XLSXwriter = pd.ExcelWriter('src/output.xlsx', engine='xlsxwriter')
    
    NL.to_excel(XLSXwriter, sheet_name='NL')
    BE.to_excel(XLSXwriter, sheet_name='BE')
    UK.to_excel(XLSXwriter, sheet_name='UK')
    
    XLSXwriter.save()
    print("output.XLSX created")