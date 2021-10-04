import dash
import dash_table
from dash_table.Format import Format
import dash_table.FormatTemplate as FormatTemplate
import dash_core_components as dcc
import dash_html_components as html
import dash_daq as daq
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output, State

import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.express as px

import pandas as pd
import geopandas as gpd

import requests
import cbsodata

import dateparser
from datetime import date, timedelta, datetime

from sklearn.linear_model import LinearRegression

import math
import os
import base64

import xlsxwriter

from pandas.plotting import autocorrelation_plot
from statsmodels.tsa.arima.model import ARIMA

import geojson

import data_prep


BS = ["bootstrap.min.css", "team04_style.css"]

app = dash.Dash(__name__,
                assets_folder = './assets/',
                external_stylesheets = [BS]
                # meta_tags = [
                #     {"name": "author", "content": "Team 04 Business Intelligence"},
                #     {"name": "keywords", "content": "coronavirus dashboard, COVID-19, dashborad, global cases, coronavirus, monitor, real time, 世界，疫情, 冠状病毒, 肺炎, 新型肺炎, 最新疫情, 实时疫情, 疫情地图, 疫情"},
                #     {"name": "description", "content": "The coronavirus COVID-19 dashboard/monitor provides up-to-date data, map, cumulative curve, growth trajectory for the global spread of coronavirus.\
                #       As of {}, there are {:,d} confirmed cases globally.\
                #      Together we stop the spread!",
                #     {"property": "og:title",
                #         "content": "Coronavirus COVID-19 Outbreak Global Cases Monitor Dashboard"},
                #     {"property": "og:type", "content": "website"},
                #     {"property": "og:description",
                #         "content": "The coronavirus COVID-19 dashboard/monitor provides up-to-date data and map for the global spread of coronavirus.\
                #       As of {}, there are {:,d} confirmed cases globally.\
                #      In the meanwhile, please keep calm, stay home and wash your hand!",
                #     {"name": "viewport",
                #         "content": "width=device-width, height=device-height, initial-scale=1.0"}
                # ]
      )

# PYTHON CODE Q

def readData():
    global NL, BE, UK, NLgeo, BEgeo, UKgeo
 
    data_prep.updateALL()  
 
    NL = data_prep.mergeNL()
    BE = data_prep.mergeBE()
    UK = data_prep.mergeUK()
    NLgeo = data_prep.updateNLgeo()
    BEgeo = data_prep.updateBEgeo()
    UKgeo = data_prep.updateUKgeo()
 
    data_prep.writeXLSX()
 
    return NL, BE, UK, NLgeo, BEgeo, UKgeo
 
readData()




def computeData(country):
        # Make all variables that are used global
 
    global latestDate
    global Active_Cases_Per_100k
    global Active_Cases_Per_100k_before
    global Active_Cases_Color
    global Active_Cases_Color_Sub
    global Active_Cases_Difference
    
    global Tests_Per_100k
    global Tests_Per_100k_before
    global Tests_Color
    global Tests_Difference
    
    global Positive_Tests
    global Positive_Tests_before
    global Positive_Tests_Color
    global Positive_Tests_Difference
    
    global Hospital_Admissions
    global Hospital_Admissions_before
    global Hospital_Admissions_Color
    global Hospital_Admissions_Difference
    
        # Dates
    country['DATE'] = country['DATE'].astype(str)
    latestDate = datetime.strptime(country['DATE'].max(), "%Y-%m-%d").strftime("%Y-%m-%d")  #Last recorded date in the dataset
    date_yesterday = str(datetime.strptime(country['DATE'].max(), "%Y-%m-%d") + timedelta(days=-1)).split(' ')[0] #Day before the last recorded date in dataset
    date_7_days_before = str(datetime.strptime(country['DATE'].max(), "%Y-%m-%d") + timedelta(days=-7)).split(' ')[0] #7 days before the last recorded date in dataset
    date_14_days_before = str(datetime.strptime(country['DATE'].max(), "%Y-%m-%d") + timedelta(days=-14)).split(' ')[0] #14 days before the last recorded date in dataset
    date_28_days_before = str(datetime.strptime(country['DATE'].max(), "%Y-%m-%d") + timedelta(days=-28)).split(' ')[0] #28 days before the last recorded date in dataset
 
        # Active Cases
    Active_Cases = country[(country['DATE'] > date_14_days_before) & (country['DATE'] <= latestDate)].Tested_positive.sum() #Number of positive tests in the last 14 days
    Inhabitants = country[(country['DATE'] > date_14_days_before) & (country['DATE'] <= latestDate)].Inhabitants.sum()/14 #Mean number of Inhabitants in the last 14 days
    Active_Cases_Per_100k = int(round(100000*Active_Cases/Inhabitants,0)) #Number of active cases per 100.000 inhabitants
        # Active Cases 14 days before
    Active_Cases_before = country[(country['DATE'] > date_28_days_before) & (country['DATE'] <= date_14_days_before)].Tested_positive.sum()
    Inhabitants_before = country[(country['DATE'] > date_28_days_before) & (country['DATE'] <= date_14_days_before)].Inhabitants.sum()/14
    Active_Cases_Per_100k_before = int(round(100000*Active_Cases_before/Inhabitants_before,0))
        #if-statement Cases
    if Active_Cases_Per_100k >= 150:
        Active_Cases_Color = '#B30000' #RED
    elif Active_Cases_Per_100k < 150:
        Active_Cases_Color = '#00B300' #Green
        
            # Difference    
    Active_Cases_Difference = Active_Cases_Per_100k - Active_Cases_Per_100k_before
    if Active_Cases_Difference > 0:
        Active_Cases_Color_Sub = '#B30000' #RED
    elif Active_Cases_Difference <= 0:
        Active_Cases_Color_Sub = '#00B300' #Green
    
        # Tests
    Tests = country[(country['DATE'] > date_7_days_before) & (country['DATE'] <= latestDate)].Total_tested.sum()/7 #Mean number of tests recorded in the last week
    Tests_Per_100k = int(round(100000*Tests/Inhabitants,0)) #Number of tests per 100.000 inhabitants
        # Tests week before
    Tests_before = country[(country['DATE'] > date_14_days_before) & (country['DATE'] <= date_7_days_before)].Total_tested.sum()/7 #Mean number of tests recorded in the last week
    Tests_Per_100k_before = int(round(100000*Tests_before/Inhabitants,0)) #Number of tests per 100.000 inhabitants
        # Difference
    Tests_Difference = Tests_Per_100k - Tests_Per_100k_before
        #if-statement Cases
    if Tests_Difference > 0:
        Tests_Color = '#B30000' #RED
    elif Tests_Difference < 0:
        Tests_Color = '#00B300' #Green
    elif Tests_Difference == 0:
        Tests_Color = '#7f7f7f' #Grey
    
        # Positive tests
    Positive_Tests = int(country[(country['DATE'] > date_7_days_before) & (country['DATE'] <= latestDate)].Tested_positive.sum()/7) # Mean number of positive tests on this week
    Positive_Tests_before = int(country[(country['DATE'] > date_14_days_before) & (country['DATE'] <= date_7_days_before)].Tested_positive.sum()/7) # Mean number of postitive tests of the week before
    # Difference
    Positive_Tests_Difference = Positive_Tests - Positive_Tests_before
        #if-statement Cases
    if Positive_Tests_Difference > 0:
        Positive_Tests_Color = '#B30000' #RED
    elif Positive_Tests_Difference < 0:
        Positive_Tests_Color = '#00B300' #Green
    elif Positive_Tests_Difference == 0:
        Positive_Tests_Color = '#7f7f7f' #Grey
        
        # Hospital Admissions
    Hospital_Admissions = int(country[(country['DATE'] > date_14_days_before) & (country['DATE'] <= latestDate)].Hospital_admission.sum()) #Number of hospital admissions in the last two weeks
    Hospital_Admissions_before = int(country[(country['DATE'] > date_28_days_before) & (country['DATE'] <= date_14_days_before)].Hospital_admission.sum()) #Number of hospital admissions in the two weeks before
    # Difference
    Hospital_Admissions_Difference = Hospital_Admissions - Hospital_Admissions_before
        #if-statement Cases
    if Hospital_Admissions_Difference > 0:
        Hospital_Admissions_Color = '#B30000' #RED
    elif Hospital_Admissions_Difference < 0:
        Hospital_Admissions_Color = '#00B300' #Green
    elif Hospital_Admissions_Difference == 0:
        Hospital_Admissions_Color = '#7f7f7f' #Grey
        
computeData(UK)

# END PYTHON CODE Q

# PYTHON CODE JOCHEM
UK_groupby = UK.groupby(by="DATE").sum()[["Hospital_admission", "Deceased", "Total_tested", "Tested_positive", "Inhabitants"]]
NL_groupby = NL.groupby(by="DATE").sum()[["Hospital_admission", "Deceased", "Total_tested", "Tested_positive", "Inhabitants"]]
BE_groupby = BE.groupby(by="DATE").sum()[["Hospital_admission", "Deceased", "Total_tested", "Tested_positive", "Inhabitants"]]

def add_country_to_df(df, country_name):
    df["Country"] = [country_name for i in range(df.shape[0])]
    return
    
add_country_to_df(UK_groupby, "UK")
add_country_to_df(NL_groupby, "NL")
add_country_to_df(BE_groupby, "BE")
    
df_total = pd.concat([UK_groupby, NL_groupby, BE_groupby])

def make_columns_relative(df, column, multiplier):
    string_name = column + "_relative"
    df[string_name] = (df[column] / df["Inhabitants"]) * multiplier
    return

make_columns_relative(df_total, "Hospital_admission", 1000000)
make_columns_relative(df_total, "Deceased", 100000)
make_columns_relative(df_total, "Total_tested", 100000)
make_columns_relative(df_total, "Tested_positive", 100000)



def seven_day_average(variable_name, new_column_name):
    list_UK = df_total[df_total.Country == "UK"][variable_name]
    list_NL = df_total[df_total.Country == "NL"][variable_name]
    list_BE = df_total[df_total.Country == "BE"][variable_name]

    all_average_values = []
    for country in [list_UK, list_NL, list_BE]:
        for i in range(len(country)):
            selection = country[(i-7):i]
            average = round(selection.sum() / 7)
            if average == 0:
                all_average_values.append(country[i])
            else:
                all_average_values.append(average)

    df_total[new_column_name] = all_average_values
    return

seven_day_average("Tested_positive", "7_day_average_positive_tests")
seven_day_average("Hospital_admission", "7_day_average_hospital_admission")
seven_day_average("Total_tested", "7_day_average_total_tested")

def make_columns_relative(df, column, multiplier):
    string_name = column + "_relative"
    df[string_name] = (df[column] / df["Inhabitants"]) * multiplier
    return

def give_color_code(df, threshold):
    if type(threshold) == str:
        threshold = float(threshold)
        
    hospital_list = []
    active_list = []
    for country in df.index.unique():
        df_province = df[df.index == country] 
        hospital_score = df_province["Hospital_admission_relative"].iloc[0]
        active_score = df_province["Active_cases_relative"].iloc[0]
        if hospital_score < (4*threshold):
            hospital_code = 1
        if hospital_score >= (4*threshold) and hospital_score < (16*threshold):
            hospital_code = 2
        if hospital_score >= (16*threshold) and hospital_score < (27*threshold):
            hospital_code = 3
        if hospital_score >= (27*threshold):
            hospital_code = 4
        hospital_list.append(hospital_code)
        
        if active_score < (35*threshold):
            active_cases_code = 1
        if active_score >= (35*threshold) and active_score < (100*threshold):
            active_cases_code = 2
        if active_score >= (100*threshold) and active_score < (250*threshold):
            active_cases_code = 3
        if active_score > (250*threshold):
            active_cases_code = 4
            
        active_list.append(active_cases_code)
        
    df['Hospital_color'] = hospital_list
    df["Active_cases_color"] = active_list
    
    color_list = []
    for score in df[["Hospital_color", "Active_cases_color"]].max(axis=1):
        if score == 1:
            color = "Caution"
        if score == 2:
            color = "Concern"
        if score == 3:
            color = "Serious"
        if score == 4:
            color = "Severe"
        color_list.append(color)
    df["color_score"] = color_list
        
    return df
# END PYTHON CODE NOUD



# HTML HTML HTML HTML HTML HTML HTMl
app.title = 'RIVM COVID-19 Travel Advisory Dashboard'

app.layout = html.Div(
    id='app-body',
    children=[        
        html.Header(
            className="masthead",
            children = [
                html.Div(
                    className="container h-100",
                    children = [
                        html.Div(
                            className="row h-100 w-100 align-items-center",
                            children = [
                                html.Div(
                                className="col-12 text-center",
                                children = [
                                    html.H1("COVID-19 RIVM Travel Advisory Dashboard", className="font-weight-light"),
                                    html.P("This dashboard has been created as an assignment for the Business Intelligence course at Utrecht University in The Netherlands. In this dashboard the COVID-19 data of three different countries are shown using descriptive, predictive, and prescriptive analytics. The aim of this dashboard is to support the Dutch governmental health organisation (RIVM) with making the decisions about travel advisories for distinct provinces and regions.", className="lead"),
                                    html.Button('Update data', className="btn btn-outline-primary btn-lg", id="show-secret"),
                                    html.P('(Updating may take a while...)'),
                                    html.P(
                                        className="lead",
                                        children="Last update: {}.".format(latestDate)
                                    ),
                                    html.P('Country selection', className="lead mt-5"),
                                    dcc.RadioItems(
                                        id='country_name',
                                        style={},
                                        options=[{'label': i, 'value': i} for i in ['UK', 'NL', 'BE']],
                                        value='UK',
                                        labelStyle={'display': 'inline-block', 
                                                    'margin': '10px 10px 20px 10px', 
                                                    'font-weight' : '500'},
                                        inputStyle={'margin': '3px'}
                                    )
                            ]
                            )]
                        )
                    ],
                )      
            ],
        ),
        html.Section(
            className="",
            children=[
                html.Div(
                    className="",
                    children = [
                        html.H4(
                            children="Descriptive Statistics",
                            style={'margin-left' : '55px', 'margin-top' : '25px'},
                        ),                        
        ## HTML CODE QUENTIN HTML CODE QUENTIN HTML CODE QUENTIN HTML CODE QUENTIN 
                        html.Div(id="UK_number_plate", 
                            style={'display': ' '},
                            className="number-plate",
                            children=[computeData(UK),
                                html.Div(
                                    className='number-plate-single',
                                    id='number-plate-active1',
                                    style={'border': '#7f7f7f solid .2rem'},
                                    children=[
                                        html.H5(
                                            style={'color': Active_Cases_Color, 'padding-bottom':'0', 'margin-bottom':'0', 'font-weight':'500', 'font-size':'2em'},
                                            children="Active cases"
                                        ),
                                        html.P(
                                            style={'color': Active_Cases_Color, 'text-align': 'center', 'padding-top':'0', 'margin-top':'0'},
                                            children="Per 100.000 inhabitants"
                                        ),
                                        html.H3(
                                            style={'color': Active_Cases_Color},
                                            children=[
                                                '{:,d}'.format(Active_Cases_Per_100k),
                                                html.P(
                                                    style={'color': Active_Cases_Color_Sub},
                                                    children='+ {:,d} in the past 2 weeks'.format(Active_Cases_Difference) if Active_Cases_Difference > 0 else '{:,d} in the past 2 weeks'.format(Active_Cases_Difference)
                                                ),      
                                            ]
                                        ),
                                        html.P(
                                            style={'color': Active_Cases_Color, 'text-align': 'center', 'padding-top':'0', 'margin-top':'0'},
                                            children="(threshold = 150)"
                                        ),
                                    ]
                                ),
                                html.Div(
                                    className='number-plate-single',
                                    id='number-plate-confirm1',
                                    style={'border': '#7f7f7f solid .2rem'},
                                    children=[
                                        html.H5(
                                            style={'color': Tests_Color, 'padding-bottom':'0', 'margin-bottom':'0', 'font-weight':'500', 'font-size':'2em'},
                                            children="Tests performed"
                                        ),
                                        html.P(
                                            style={'color': Tests_Color, 'text-align': 'center', 'padding-top':'0', 'margin-top':'0'},
                                            children="Per 100.000 inhabitants"
                                        ),
                                        html.H3(
                                            style={'color': Tests_Color},
                                            children=[
                                                '{:,d}'.format(Tests_Per_100k),
                                                html.P(
                                                    children='+ {:,d} compared to last week'.format(Tests_Difference) if Tests_Difference > 0 else '{:,d} compared to last week'.format(Tests_Difference)
                                                ),
                                                
                                            ]
                                        ),
                                        
                                    ]
                                ),
                                html.Div(
                                    className='number-plate-single',
                                    id='number-plate-recover1',
                                    style={'border': '#7f7f7f solid .2rem',},
                                    children=[
                                        html.H5(
                                            style={'color': Positive_Tests_Color, 'padding-bottom':'0', 'margin-bottom':'0', 'font-weight':'500', 'font-size':'2em'},
                                            children="Positive tests"
                                        ),
                                        html.P(
                                            style={'color': Positive_Tests_Color, 'text-align': 'center', 'padding-top':'0', 'margin-top':'0'},
                                            children="Per day"
                                        ),
                                        html.H3(
                                            style={'color': Positive_Tests_Color},
                                            children=[
                                                '{:,d}'.format(Positive_Tests),
                                                html.P(
                                                    children='+ {:,d} compared to last week'.format(Positive_Tests_Difference) if Positive_Tests_Difference > 0 else '{:,d} compared to last week'.format(Positive_Tests_Difference)
                                                ),
                                                
                                            ]
                                        ),
                                        
                                    ]
                                ),
                                html.Div(
                                    className='number-plate-single',
                                    id='number-plate-death1',
                                    style={'border': '#7f7f7f solid .2rem',},
                                    children=[
                                        html.H5(
                                            style={'color': Hospital_Admissions_Color, 'padding-bottom':'0', 'margin-bottom':'0', 'font-weight':'500', 'font-size':'2em'},
                                            children="Hospital admissions"
                                        ),
                                        html.P(
                                            style={'color': Hospital_Admissions_Color, 'text-align': 'center', 'padding-top':'0', 'margin-top':'0'},
                                            children="Total in the last 2 weeks"
                                        ),
                                        html.H3(
                                            style={'color': Hospital_Admissions_Color},
                                            children=[
                                                '{:,d}'.format(Hospital_Admissions),
                                                html.P(
                                                    children='+ {:,d} in the past 2 weeks'.format(Hospital_Admissions_Difference) if Hospital_Admissions_Difference > 0 else '{:,d} in the past 2 weeks'.format(Hospital_Admissions_Difference)
                                                ),
                                                
                                            ]
                                        ),
                                        
                                    ]
                                ),
                                
                            ]
                        ),
                        html.Div(id="NL_number_plate",
                            style={'display': 'none'},
                            className="number-plate",
                            children=[computeData(NL),
                                html.Div(
                                    className='number-plate-single',
                                    id='number-plate-active2',
                                    style={'border': '#7f7f7f solid .2rem',},
                                    children=[
                                        html.H5(
                                            style={'color': Active_Cases_Color, 'padding-bottom':'0', 'margin-bottom':'0', 'font-weight':'500', 'font-size':'2em'},
                                            children="Active cases"
                                        ),
                                        html.P(
                                            style={'color': Active_Cases_Color, 'text-align': 'center', 'padding-top':'0', 'margin-top':'0'},
                                            children="Per 100.000 inhabitants"
                                        ),
                                        html.H3(
                                            style={'color': Active_Cases_Color},
                                            children=[
                                                '{:,d}'.format(Active_Cases_Per_100k),
                                                html.P(
                                                    style={'color': Active_Cases_Color_Sub},
                                                    children='+ {:,d} in the past 2 weeks'.format(Active_Cases_Difference) if Active_Cases_Difference > 0 else '{:,d} in the past 2 weeks'.format(Active_Cases_Difference)
                                                ),      
                                            ]
                                        ),
                                        html.P(
                                            style={'color': Active_Cases_Color, 'text-align': 'center', 'padding-top':'0', 'margin-top':'0'},
                                            children="(threshold = 150)"
                                        ),
                                    ]
                                ),
                                html.Div(
                                    className='number-plate-single',
                                    id='number-plate-confirm2',
                                    style={'border': '#7f7f7f solid .2rem'},
                                    children=[
                                        html.H5(
                                            style={'color': Tests_Color, 'padding-bottom':'0', 'margin-bottom':'0', 'font-weight':'500', 'font-size':'2em'},
                                            children="Tests performed"
                                        ),
                                        html.P(
                                            style={'color': Tests_Color, 'text-align': 'center', 'padding-top':'0', 'margin-top':'0'},
                                            children="Per 100.000 inhabitants"
                                        ),
                                        html.H3(
                                            style={'color': Tests_Color},
                                            children=[
                                                '{:,d}'.format(Tests_Per_100k),
                                                html.P(
                                                    children='+ {:,d} compared to last week'.format(Tests_Difference) if Tests_Difference > 0 else '{:,d} compared to last week'.format(Tests_Difference)
                                                ),
                                                
                                            ]
                                        ),
                                        
                                    ]
                                ),
                                html.Div(
                                    className='number-plate-single',
                                    id='number-plate-recover2',
                                    style={'border': '#7f7f7f solid .2rem',},
                                    children=[
                                        html.H5(
                                            style={'color': Positive_Tests_Color, 'padding-bottom':'0', 'margin-bottom':'0', 'font-weight':'500', 'font-size':'2em'},
                                            children="Positive tests"
                                        ),
                                        html.P(
                                            style={'color': Positive_Tests_Color, 'text-align': 'center', 'padding-top':'0', 'margin-top':'0'},
                                            children="Per day"
                                        ),
                                        html.H3(
                                            style={'color': Positive_Tests_Color},
                                            children=[
                                                '{:,d}'.format(Positive_Tests),
                                                html.P(
                                                    children='+ {:,d} compared to last week'.format(Positive_Tests_Difference) if Positive_Tests_Difference > 0 else '{:,d} compared to last week'.format(Positive_Tests_Difference)
                                                ),
                                                
                                            ]
                                        ),
                                        
                                    ]
                                ),
                                html.Div(
                                    className='number-plate-single',
                                    id='number-plate-death2',
                                    style={'border': '#7f7f7f solid .2rem',},
                                    children=[
                                        html.H5(
                                            style={'color': Hospital_Admissions_Color, 'padding-bottom':'0', 'margin-bottom':'0', 'font-weight':'500', 'font-size':'2em'},
                                            children="Hospital admissions"
                                        ),
                                        html.P(
                                            style={'color': Hospital_Admissions_Color, 'text-align': 'center', 'padding-top':'0', 'margin-top':'0'},
                                            children="Total in the last 2 weeks"
                                        ),
                                        html.H3(
                                            style={'color': Hospital_Admissions_Color},
                                            children=[
                                                '{:,d}'.format(Hospital_Admissions),
                                                html.P(
                                                    children='+ {:,d} in the past 2 weeks'.format(Hospital_Admissions_Difference) if Hospital_Admissions_Difference > 0 else '{:,d} in the past 2 weeks'.format(Hospital_Admissions_Difference)
                                                ),
                                                
                                            ]
                                        ),
                                        
                                    ]
                                ),
                                
                            ]
                        ),
                        html.Div(id="BE_number_plate",
                            style={'display': 'none'},
                            className="number-plate",
                            children=[computeData(BE),
                                html.Div(
                                    className='number-plate-single',
                                    id='number-plate-active3',
                                    style={'border': '#7f7f7f solid .2rem',},
                                    children=[
                                        html.H5(
                                            style={'color': Active_Cases_Color, 'padding-bottom':'0', 'margin-bottom':'0', 'font-weight':'500', 'font-size':'2em'},
                                            children="Active cases"
                                        ),
                                        html.P(
                                            style={'color': Active_Cases_Color, 'text-align': 'center', 'padding-top':'0', 'margin-top':'0'},
                                            children="Per 100.000 inhabitants"
                                        ),
                                        html.H3(
                                            style={'color': Active_Cases_Color},
                                            children=[
                                                '{:,d}'.format(Active_Cases_Per_100k),
                                                html.P(
                                                    style={'color': Active_Cases_Color_Sub},
                                                    children='+ {:,d} in the past 2 weeks'.format(Active_Cases_Difference) if Active_Cases_Difference > 0 else '{:,d} in the past 2 weeks'.format(Active_Cases_Difference)
                                                ),      
                                            ]
                                        ),
                                        html.P(
                                            style={'color': Active_Cases_Color, 'text-align': 'center', 'padding-top':'0', 'margin-top':'0'},
                                            children="(threshold = 150)"
                                        ),
                                    ]
                                ),
                                html.Div(
                                    className='number-plate-single',
                                    id='number-plate-confirm3',
                                    style={'border': '#7f7f7f solid .2rem'},
                                    children=[
                                        html.H5(
                                            style={'color': Tests_Color, 'padding-bottom':'0', 'margin-bottom':'0', 'font-weight':'500', 'font-size':'2em'},
                                            children="Tests performed"
                                        ),
                                        html.P(
                                            style={'color': Tests_Color, 'text-align': 'center', 'padding-top':'0', 'margin-top':'0'},
                                            children="Per 100.000 inhabitants"
                                        ),
                                        html.H3(
                                            style={'color': Tests_Color},
                                            children=[
                                                '{:,d}'.format(Tests_Per_100k),
                                                html.P(
                                                    children='+ {:,d} compared to last week'.format(Tests_Difference) if Tests_Difference > 0 else '{:,d} compared to last week'.format(Tests_Difference)
                                                ),
                                                
                                            ]
                                        ),
                                        
                                        
                                    ]
                                ),
                                html.Div(
                                    className='number-plate-single',
                                    id='number-plate-recover3',
                                    style={'border': '#7f7f7f solid .2rem',},
                                    children=[
                                        html.H5(
                                            style={'color': Positive_Tests_Color, 'padding-bottom':'0', 'margin-bottom':'0', 'font-weight':'500', 'font-size':'2em'},
                                            children="Positive tests"
                                        ),
                                        html.P(
                                            style={'color': Positive_Tests_Color, 'text-align': 'center', 'padding-top':'0', 'margin-top':'0'},
                                            children="Per day"
                                        ),
                                        html.H3(
                                            style={'color': Positive_Tests_Color},
                                            children=[
                                                '{:,d}'.format(Positive_Tests),
                                                html.P(
                                                    children='+ {:,d} compared to last week'.format(Positive_Tests_Difference) if Positive_Tests_Difference > 0 else '{:,d} compared to last week'.format(Positive_Tests_Difference)
                                                ),
                                                
                                            ]
                                        ),
                                        
                                    ]
                                ),
                                html.Div(
                                    className='number-plate-single',
                                    id='number-plate-death3',
                                    style={'border': '#7f7f7f solid .2rem',},
                                    children=[
                                        html.H5(
                                            style={'color': Hospital_Admissions_Color, 'padding-bottom':'0', 'margin-bottom':'0', 'font-weight':'500', 'font-size':'2em'},
                                            children="Hospital admissions"
                                        ),
                                        html.P(
                                            style={'color': Hospital_Admissions_Color, 'text-align': 'center', 'padding-top':'0', 'margin-top':'0'},
                                            children="Total in the last 2 weeks"
                                        ),
                                        html.H3(
                                            style={'color': Hospital_Admissions_Color},
                                            children=[
                                                '{:,d}'.format(Hospital_Admissions),
                                                html.P(
                                                    children='+ {:,d} in the past 2 weeks'.format(Hospital_Admissions_Difference) if Hospital_Admissions_Difference > 0 else '{:,d} in the past 2 weeks'.format(Hospital_Admissions_Difference)
                                                ),
                                                
                                            ]
                                        ),
                                        
                                    ]
                                ),
                                
                            ]
                        ),
                        html.P(id='placeholder', children=[]),
                
        #HTML CODE JOCHEM HTML CODE JOCHEM HTML CODE JOCHEM

        html.Div(
                        className='row dcc-plot',
                        children=[
                            html.Div(
                                className='dcc-full-plot',                        
                                children=[
                                    html.Div(
                                        id='graph-7-days-average-title',
                                        children=[
                                            html.H5(
                                                children='7-day average of positive tests '
                                            )
                                        ],
                                    ),
                                    dcc.Graph(
                                        id='graph-7-days-average',
                                        config={"displayModeBar": False, "scrollZoom": False}, 
                                    ),
                                ]
                            )                            
                        ]
                    ),
                html.Div(
                    className='row dcc-plot',
                    children=[
                        html.Div(
                            className='dcc-sub-plot',                        
                            children=[
                                html.Div(
                                    id='graph-total-tested-title',
                                    children=[
                                        html.H5(
                                            children='7-day average of total tests'
                                        )
                                    ],
                                ),
                                dcc.Graph(
                                    id='graph-total-tested',
                                    config={"displayModeBar": False, "scrollZoom": False}, 
                                ),
                            ]
                        ),
                        html.Div(
                                className='dcc-sub-plot',                        
                                children=[
                                    html.Div(
                                        id='graph-hospital-admissions-title',
                                        children=[
                                            html.H5(
                                                children='7-day average of hospital admissions'
                                            )
                                        ]
                                    ),
                                    dcc.Graph(
                                        id='graph-hospital-admissions',
                                        config={"displayModeBar": False, "scrollZoom": False}, 
                                    )
                                ]
                            )
                    ]
                ),
            
            
            ]),
                ]
        ),
                
       
        
# HTML CODE NOUD HTML CODE NOUD HTML CODE NOUD HTML CODE NOUD HTML CODE NOUD  
        # DESCRIPTIVE STATISTICS FOR COUNTRY DESCRIPTIVE STATISTICS FOR COUNTRY
        html.H4(
                    id='predictive-title',
                    style={'margin-left' : '55px', 'margin-top' : '25px'},
                    children="Predictive Statistics"),
        
        html.Div(
            className='row dcc-plot',
            children=[
                html.Div(
                    className='dcc-sub-plot',                        
                    children=[
                        html.Div(
                            id='graph-positive-tested-predictions-title',
                            children=[
                                html.H5(
                                    children='Prediction plot of 14 days for positive tests'
                                )
                            ],
                        ),
                        dcc.Graph(
                            id='graph-positive-tested-predictions',
                            config={"displayModeBar": False, "scrollZoom": False}, 
                        ),
                    ]
                ),
                html.Div(
                    className='dcc-sub-plot',                        
                    children=[
                        html.Div(
                            id='graph-total-tested-predictions-title',
                            children=[
                                html.H5(
                                    children='Prediction plot of 14 days for total tests'
                                )
                            ]
                        ),
                        dcc.Graph(
                            id='graph-total-tested-predictions',
                            config={"displayModeBar": False, "scrollZoom": False}, 
                        )
                    ]
                ),
            ]
        ),
        html.Div(
            className='row dcc-plot',
            children=[
                
                html.Div(
                    className='dcc-sub-plot',                        
                    children=[
                        html.Div(
                            id='graph-hospital-predictions-title',
                            children=[
                                html.H5(
                                    children='Prediction plot of 14 days for hospital admissions'
                                ),
                            ]
                        ),
                        dcc.Graph(
                            id='graph-hospital-predictions',
                            config={"displayModeBar": False, "scrollZoom": False}, 
                        ),
                    ]
                ),
            ]
        ),
        html.H4(
                id='prescriptive-title',
                style={'margin-left' : '55px', 'margin-top' : '25px'},
                children="Prescriptive Statistics"),
        
        html.Div(
            className='prescriptive-content',
            style={'text-align':'center'},
            children=[
                html.Div(
                    className='center',
                    children=[
                        html.H5(
                            id='threshold-title',
                            children="Adjust threshold:"),
                        dcc.Input(
                        id="input-threshold", placeholder="1", value="1")
                    ]),
        dcc.Graph(
                            id='graph-map',
                            config={"displayModeBar": False, "scrollZoom": False}, 
                        ),
            ]),
        html.Section(
            className="masthead-two",
            children = [
                html.Div(
                    className="container h-100",
                    children = [
                        html.Div(
                            className="row h-100 w-100",
                            style={'margin-top' : '10rem'},
                            children = [
                                html.Div(
                                className="col-12 text-center",
                                children = [
                                    html.H1("Remarks on Dashboard Usage", className="font-weight-light"),
                                    html.P(['''

                                    When making travel advice, the RIVM looks at different indicators to decide whether it is safe to travel to a country or not. This dashboard visualizes the things that the RIVM uses for making a travel advice. In this way it tries to support the users for making the best decision on travel bans.''', html.Br(), '''

                                    ''', html.Br(), '''Descriptive analytics''', html.Br(), '''
                                    The RIVM looks at the trend of hospital admissions, total conducted tests and total positive tests to see how the situation in a country or a specific region is developing. To help them understand the ongoing trend, the three variables are visualized and there is a blue line that shows the seven-day average trend. Next to this a user can zoom in and out to investigate trends for a more specific time frame. The numbers shown are absolute values and should therefore only be seen as an indication of a development in the situation. ''', html.Br(), '''

                                   ''', html.Br(), ''' Predictive analytics''', html.Br(), '''
                                    Not only the current situation is important for the travel advisories, but also signals of an upcoming increase in positive tests, total tests, or hospital admissions. Therefore, the predictive plots have been incorporated to also weigh in on the establishment of travel advisories. This is done for a time period of fourteen days in the future. Fourteen days is chosen since this is also the time frame for which the RIVM looks into the future.''', html.Br(), '''

                                    ''', html.Br(), '''Map''', html.Br(), '''
                                    Lastly, all data is incorporated into the map of a country's regions or provinces. The legend shows the travel advisories per region or province based on the current ruling travel advisory categorizations (caution, concern, serious, severe). When a region or province is classified as green, it can be safe to travel there. When a country is classified as yellow or orange, it is strongly advised to not travel there and only go for really necessary things. When a country is classified as red, it is under no condition safe to travel there. ''', html.Br(), '''

                                    These classifications are based on the guidelines from the RIVM for the Netherlands. There are no guidelines available for foreign countries so this dashboard applies the Dutch guidelines to all the countries. The guidelines are completely based on the relative number of hospital admission and total positive tests. The hospital admissions are per 1.000.000 inhabitants and the total positive tests are per 100.000 inhabitants. The number at which the decision is based is the average number of the past seven days.
                                    The risks levels are assigned according to the following value ranges:''', html.Br(), '''
                                    For positive tests: lower than 35 is caution, between 35 and 100 is concern, between 100 and 250 is serious and higher than 250 is severe.''', html.Br(), '''
                                    For hospital admissions: lower than 4 is caution, between 4 and 16 is concern, between 16 and 27 is serious and higher than 27 is severe.''', html.Br(), '''
                                    
                                    It is important to note that the highest risk level of either positive tests or hospital admissions is taken as the leading risk level. For example, if positive tests is 50 and thus a concern risk level and hospital admissions is 20 and thus a serious risk level, the serious risk level is assigned to the corresponding region.''', html.Br(), '''

                                    The threshold value that a user of the dashboard can input works as follows; the number that is inputted is multiplied with the value ranges that are described above. A threshold value lower than 1.0 makes the value ranges more narrow and therefore stricter. A threshold value higher than 1.0 makes the value ranges wider and therefore lenient.''', html.Br(), '''

                                    Lastly, the predicted variables still have to be accounted for when making an ultimate travel advisory.''', html.Br(), '''
                                    
                                    '''], className="lead"),                                    
                            ]
                            )]
                        )
                    ],
                )      
            ],
        )
        # html.H4(
        #         id='remarks-title',
        #         children="General remarks"),
        #         style={'margin-left' : '55px', 'margin-top' : '25px'}
        # html.P(
        #         id='remarks-p',
        #         children="Lorem ipsum dolor sit amet, consectetuer adipiscing elit. Aenean commodo ligula eget dolor. Aenean massa. Cum sociis natoque penatibus et magnis dis parturient montes, nascetur ridiculus mus. Donec quam felis, ultricies nec, pellentesque eu, pretium quis, sem. Nulla consequat massa quis enim. Donec pede justo, fringilla vel, aliquet nec, vulputate eget, arcu. In enim justo, rhoncus ut, imperdiet a, venenatis vitae, justo. Nullam dictum felis eu pede mollis pretium. Integer tincidunt. Cras dapibus. Vivamus elementum semper nisi. Aenean vulputate eleifend tellus. Aenean leo ligula, porttitor eu, consequat vitae, eleifend ac, enim. Aliquam lorem ante, dapibus in, viverra quis, feugiat a, tellus. Phasellus viverra nulla ut metus varius laoreet. Quisque rutrum. Aenean imperdiet. Etiam ultricies nisi vel augue. Curabitur ullamcorper ultricies nisi. Nam eget dui. ")

    


            
])

@app.callback(
    Output('placeholder', 'children'),
    Input(component_id='show-secret', component_property='n_clicks')
)

def updateData(n_clicks):
    
    global NL, BE, UK, NLgeo, BEgeo, UKgeo
    if n_clicks != 'NoneType':
        data_prep.updateALL() 
        NL = data_prep.mergeNL()
        BE = data_prep.mergeBE()
        UK = data_prep.mergeUK()
        NLgeo = data_prep.updateNLgeo()
        BEgeo = data_prep.updateBEgeo()
        UKgeo = data_prep.updateUKgeo()
        data_prep.writeXLSX()
        readData() 
        
    else:
        readData()



@app.callback(
    [Output('graph-7-days-average', 'figure'), 
     Output('graph-hospital-admissions', 'figure'),
     Output('graph-total-tested', 'figure'),
     Output('graph-hospital-predictions', 'figure'),
     Output('graph-total-tested-predictions', 'figure'),
     Output('graph-positive-tested-predictions', 'figure'),
     Output('graph-map', 'figure'),
     Output('UK_number_plate', 'style'),
     Output('NL_number_plate', 'style'),
     Output('BE_number_plate', 'style')],
    [Input('country_name', 'value'), Input('input-threshold', 'value')])

def update_graph(country_name, threshold_value):
    # DESCRIPTIVE PLOTS
    global fig_map
    global dfmap
    global geo
    global risk_level

    df = df_total[df_total.Country == country_name]

    fig_positive_tested = px.line(df, x=df.index, y="7_day_average_positive_tests",
                                 labels={
                                     "7_day_average_positive_tests": "Amount of positive cases"
                                 })
    fig_positive_tested.add_bar(x=df.index, y=df["Tested_positive"], name="Test_positive")

    fig_positive_tested.update_yaxes(showline=True, linewidth=2, linecolor='black', zeroline=False)
    fig_positive_tested.update_yaxes(zeroline=True, zerolinewidth=2 , zerolinecolor='black', showgrid=True, gridcolor='LightGrey')

    
    fig_positive_tested.update_layout(title= "Daily covid-19 cases and 7 day average of positive tests", title_x=0.5, plot_bgcolor='rgba(0,0,0,0)')
    fig_positive_tested['data'][0]['showlegend']=True
    fig_positive_tested['data'][0]['name']='Seven day average'
    
    today = date.today()
    three_months_ago = today - timedelta(days=92)
    initial_range = [
    three_months_ago, today
    ]

    # Add range slider
    fig_positive_tested.update_layout(
        xaxis=dict(
            rangeselector=dict(
                buttons=list([
                    dict(count=1,
                         label="1m",
                         step="month",
                         stepmode="backward"),
                    dict(count=3,
                         label="3m",
                         step="month",
                         stepmode="backward"),
                    dict(count=1,
                         label="YTD",
                         step="year",
                         stepmode="todate"),
                    dict(count=1,
                         label="1y",
                         step="year",
                         stepmode="backward"),
                    dict(step="all")
                ])
            )
        )
    )
    fig_positive_tested['layout']['xaxis'].update(range=initial_range)
    
    fig_hospital_admissions = px.line(df, x=df.index, y="7_day_average_hospital_admission",
                                 labels={
                                     "7_day_average_hospital_admission": "Amount of hospital admissions"
                                 })
    fig_hospital_admissions.add_bar(x=df.index, y=df["Hospital_admission"], name="Hospital_admission")
    
    fig_hospital_admissions.update_yaxes(showline=True, linewidth=2, linecolor='black', zeroline=False)
    fig_hospital_admissions.update_yaxes(zeroline=True, zerolinewidth=2 , zerolinecolor='black', showgrid=True, gridcolor='LightGrey')

    
    fig_hospital_admissions.update_layout(title= "Daily covid-19 hospital admissions and 7 day average of hospital admissions", title_x=0.5, plot_bgcolor='rgba(0,0,0,0)')
    fig_hospital_admissions['data'][0]['showlegend']=True
    fig_hospital_admissions['data'][0]['name']='Seven day average'

    fig_hospital_admissions.update_layout(
        xaxis=dict(
            rangeselector=dict(
                buttons=list([
                    dict(count=1,
                         label="1m",
                         step="month",
                         stepmode="backward"),
                    dict(count=3,
                         label="3m",
                         step="month",
                         stepmode="backward"),
                    dict(count=1,
                         label="YTD",
                         step="year",
                         stepmode="todate"),
                    dict(count=1,
                         label="1y",
                         step="year",
                         stepmode="backward"),
                    dict(step="all")
                ])
            )
        )
    )
    fig_hospital_admissions['layout']['xaxis'].update(range=initial_range)

    fig_total_tested = px.line(df, x=df.index, y="7_day_average_total_tested",
                                 labels={
                                     "7_day_average_total_tested": "Amount of conducted tests"
                                 })
    fig_total_tested.add_bar(x=df.index, y=df["Total_tested"], name="Total_tested")
    
    fig_total_tested.update_yaxes(showline=True, linewidth=2, linecolor='black', zeroline=False)
    fig_total_tested.update_yaxes(zeroline=True, zerolinewidth=2 , zerolinecolor='black', showgrid=True, gridcolor='LightGrey')

    fig_total_tested.update_layout(title= "Daily covid-19 tests and 7 day average of conducted tests", title_x=0.5, plot_bgcolor='rgba(0,0,0,0)')
    fig_total_tested['data'][0]['showlegend']=True
    fig_total_tested['data'][0]['name']='Seven day average'
    
    
    fig_total_tested.update_layout(
        xaxis=dict(
            rangeselector=dict(
                buttons=list([
                    dict(count=1,
                         label="1m",
                         step="month",
                         stepmode="backward"),
                    dict(count=3,
                         label="3m",
                         step="month",
                         stepmode="backward"),
                    dict(count=1,
                         label="YTD",
                         step="year",
                         stepmode="todate"),
                    dict(count=1,
                         label="1y",
                         step="year",
                         stepmode="backward"),
                    dict(step="all")
                ])
            )
        )
    )
    fig_total_tested['layout']['xaxis'].update(range=initial_range)
    
    # PREDICTION PLOT - HOSPITAL ADMISSIONS
    series_hospital = df["Hospital_admission"].tail(14)
    model_hospital = ARIMA(series_hospital, order=(1,0,1))
    model_fit_hospital = model_hospital.fit()
    hospital_predictions = model_fit_hospital.predict(start=series_hospital.count(), end=series_hospital.count()+13)
    fig_hospital_predictions = px.line(hospital_predictions, x=hospital_predictions.index, y="predicted_mean")
    fig_hospital_predictions.add_bar(x=df.index, y=df["Hospital_admission"], name="Historic hospital admissions")
    fig_hospital_predictions['data'][0]['showlegend']=True
    fig_hospital_predictions['data'][0]['name']='Prediction hospital admissions'
    fig_hospital_predictions.update_yaxes(showline=True, linewidth=2, linecolor='black', zeroline=False)
    fig_hospital_predictions.update_yaxes(zeroline=True, zerolinewidth=2 , zerolinecolor='black', showgrid=True, gridcolor='LightGrey')    
    fig_hospital_predictions.update_layout(title= "Predicted trend hospital admissions", title_x=0.5, plot_bgcolor='rgba(0,0,0,0)')
    
    today = date.today() + timedelta(days=13)
    three_months_ago = today - timedelta(days=92)
    initial_range = [
    three_months_ago, today
    ]
    
    # Add range slider
    fig_hospital_predictions.update_layout(
        xaxis=dict(
            rangeselector=dict(
                buttons=list([
                    dict(count=1,
                         label="1m",
                         step="month",
                         stepmode="backward"),
                    dict(count=3,
                         label="3m",
                         step="month",
                         stepmode="backward"),
                    dict(count=1,
                         label="YTD",
                         step="year",
                         stepmode="todate"),
                    dict(count=1,
                         label="1y",
                         step="year",
                         stepmode="backward"),
                    dict(step="all")
                ])
            )
        )
    )
    fig_hospital_predictions['layout']['xaxis'].update(range=initial_range)

    
    # PREDICTION PLOT - POSITIVE TESTS
    series_positive_tests = df["Tested_positive"].tail(14)
    model_positive = ARIMA(series_positive_tests, order=(1,0,1))
    model_fit_positive = model_positive.fit()
    positive_tests_predictions = model_fit_positive.predict(start=series_positive_tests.count(), end=series_positive_tests.count()+13)
    fig_positive_tested_predictions = px.line(positive_tests_predictions, x=positive_tests_predictions.index, y="predicted_mean")
    fig_positive_tested_predictions.add_bar(x=df.index, y=df["Tested_positive"], name="Historic positive tests") 
    fig_positive_tested_predictions['data'][0]['showlegend']=True
    fig_positive_tested_predictions['data'][0]['name']='Prediction positive tests'
    fig_positive_tested_predictions.update_yaxes(showline=True, linewidth=2, linecolor='black', zeroline=False)
    fig_positive_tested_predictions.update_yaxes(zeroline=True, zerolinewidth=2 , zerolinecolor='black', showgrid=True, gridcolor='LightGrey')    
    fig_positive_tested_predictions.update_layout(title= "Predicted trend positive tests", title_x=0.5, plot_bgcolor='rgba(0,0,0,0)')
    
    # Add range slider
    fig_positive_tested_predictions.update_layout(
        xaxis=dict(
            rangeselector=dict(
                buttons=list([
                    dict(count=1,
                         label="1m",
                         step="month",
                         stepmode="backward"),
                    dict(count=3,
                         label="3m",
                         step="month",
                         stepmode="backward"),
                    dict(count=1,
                         label="YTD",
                         step="year",
                         stepmode="todate"),
                    dict(count=1,
                         label="1y",
                         step="year",
                         stepmode="backward"),
                    dict(step="all")
                ])
            )
        )
    )
    fig_positive_tested_predictions['layout']['xaxis'].update(range=initial_range)


    # PREDICTION PLOT - TOTAL TESTS
    series_total_tests = df["Total_tested"].tail(14)
    model_total = ARIMA(series_total_tests, order=(1,0,1))
    model_fit_total = model_total.fit()
    total_tests_predictions = model_fit_total.predict(start=series_total_tests.count(), end=series_total_tests.count()+13)
    fig_total_tested_predictions = px.line(total_tests_predictions, x=total_tests_predictions.index, y="predicted_mean")
    fig_total_tested_predictions.add_bar(x=df.index, y=df["Total_tested"], name="Historic total tests") 
    fig_total_tested_predictions['data'][0]['showlegend']=True
    fig_total_tested_predictions['data'][0]['name']='Prediction line'
    fig_total_tested_predictions.update_yaxes(showline=True, linewidth=2, linecolor='black', zeroline=False)
    fig_total_tested_predictions.update_yaxes(zeroline=True, zerolinewidth=2 , zerolinecolor='black', showgrid=True, gridcolor='LightGrey')    
    fig_total_tested_predictions.update_layout(title= "Predicted trend total tests tests", title_x=0.5, plot_bgcolor='rgba(0,0,0,0)')
    
    # Add range slider
    fig_total_tested_predictions.update_layout(
        xaxis=dict(
            rangeselector=dict(
                buttons=list([
                    dict(count=1,
                         label="1m",
                         step="month",
                         stepmode="backward"),
                    dict(count=3,
                         label="3m",
                         step="month",
                         stepmode="backward"),
                    dict(count=1,
                         label="YTD",
                         step="year",
                         stepmode="todate"),
                    dict(count=1,
                         label="1y",
                         step="year",
                         stepmode="backward"),
                    dict(step="all")
                ])
            )
        )
    )
    fig_total_tested_predictions['layout']['xaxis'].update(range=initial_range)
    
    # MAP
    if country_name == 'UK':
        dfmap = UK[['DATE', 'PROVINCE', 'Inhabitants', 'Total_tested', 'Tested_positive', 'Hospital_admission']]
        geo = UKgeo        

        #datum kiezen
        last_date_in_df = dfmap['DATE'].iloc[-1]
        dfmap = dfmap.loc[dfmap['DATE'] == last_date_in_df]
        dfmap = dfmap[['PROVINCE', 'Inhabitants', 'Total_tested', 'Tested_positive', 'Hospital_admission']]
        #namen correct zetten
        dfmap=dfmap.replace(to_replace =["Midlands"], value ="West Midlands + East Midlands.")
        dfmap=dfmap.replace(to_replace =["North East and Yorkshire"], value ="North East + Yorkshire.")
        #dubbele midsland en yorkshiremaken
        midsland = dfmap.loc[dfmap['PROVINCE'] == 'West Midlands + East Midlands.']
        yorkshire = dfmap.loc[dfmap['PROVINCE'] == 'North East + Yorkshire.']
        #dubbele appenden
        dfmap = midsland.append(dfmap, ignore_index=True)
        dfmap = yorkshire.append(dfmap, ignore_index=True)
        #eerste 2 rows aanpassen naar correcte naam
        dfmap.at[0,'PROVINCE']='North East + Yorkshire'
        dfmap.at[1,'PROVINCE']='West Midlands + East Midlands'
        #zonder resetten werkt het niet
        dfmap = dfmap.reset_index(drop=True)

        last_two_week_rows = len(dfmap['PROVINCE'].unique())*7
        df_uk_groupby = dfmap.tail(last_two_week_rows).groupby(by='PROVINCE').mean()
        df_uk_groupby['Active_cases'] = df_uk_groupby['Tested_positive'] * 7
        make_columns_relative(df_uk_groupby, "Hospital_admission", 1000000)
        make_columns_relative(df_uk_groupby, "Active_cases", 100000)

        df_color_code = give_color_code(df_uk_groupby, threshold_value)

        fig_map = px.choropleth_mapbox(dfmap, geojson=geo, color=df_color_code["color_score"],
                           locations="PROVINCE", featureidkey="properties.PROVINCE",
                           center={"lat": 52.7555, "lon": -1.743},
                           mapbox_style="carto-positron", zoom=5.1,
                           hover_data=['Hospital_admission', 'Total_tested'],
                           color_discrete_map={
                            "Caution": "#006B3E",
                            "Concern": "#FFE733",
                            "Serious": "#FFAA1C",
                            "Severe": "#ED2938"}
                            )
        fig_map.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
        fig_map.show()

    elif country_name == 'NL':
        dfmap = NL[['DATE', 'PROVINCE', 'Inhabitants', 'Total_tested', 'Tested_positive', 'Hospital_admission']]
        geo = NLgeo
        
        #datum kiezen
        last_date_in_df = dfmap['DATE'].iloc[-1]
        dfmap = dfmap.loc[dfmap['DATE'] == last_date_in_df]
        dfmap = dfmap[['PROVINCE', 'Inhabitants', 'Total_tested', 'Tested_positive', 'Hospital_admission']]
        #zonder resetten werkt het niet
        dfmap = dfmap.reset_index(drop=True)

        last_two_week_rows = len(NL['PROVINCE'].unique())*7
        df_nl_groupby = dfmap.tail(last_two_week_rows).groupby(by='PROVINCE').mean()
        df_nl_groupby['Active_cases'] = df_nl_groupby['Tested_positive'] * 7
        make_columns_relative(df_nl_groupby, "Hospital_admission", 1000000)
        make_columns_relative(df_nl_groupby, "Active_cases", 100000)

        df_color_code = give_color_code(df_nl_groupby, threshold_value)

        fig_map = px.choropleth_mapbox(dfmap, geojson=geo, color=df_color_code["color_score"],
                           locations="PROVINCE", featureidkey="properties.PROVINCE",
                           center={"lat": 52.23, "lon": 4.55},
                           mapbox_style="carto-positron", zoom=6,
                           hover_data=['Hospital_admission', 'Total_tested'],
                           color_discrete_map={
                            "Caution": "#006B3E",
                            "Concern": "#FFE733",
                            "Serious": "#FFAA1C",
                            "Severe": "#ED2938"}
                            )
        fig_map.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
        fig_map.show()

    elif country_name == 'BE':
        dfmap = BE[['DATE', 'PROVINCE', 'Inhabitants', 'Total_tested', 'Tested_positive', 'Hospital_admission']]
        geo = BEgeo

        #datum kiezen
        last_date_in_df = dfmap['DATE'].iloc[-1]
        dfmap = dfmap.loc[dfmap['DATE'] == last_date_in_df]
        dfmap = dfmap[['PROVINCE', 'Inhabitants', 'Total_tested', 'Tested_positive', 'Hospital_admission']]

        #namen correct zetten
        dfmap=dfmap.replace(to_replace =["VlaamsBrabant"], value ="VlaamsBrabant + Brussel.")

        #hier maak ik de provincie brussels het zelfde als vlaams brabant
        vlaams = dfmap.loc[dfmap['PROVINCE'] == 'VlaamsBrabant + Brussel.']
        dfmap = vlaams.append(dfmap, ignore_index=True)
        #eerste row aanpassen naar correcte naam
        dfmap.at[0,'PROVINCE']='VlaamsBrabant + Brussel'

        #zonder resetten werkt het niet
        dfmap = dfmap.reset_index(drop=True)

        last_two_week_rows = len(BE['PROVINCE'].unique())* 7
        df_be_groupby = dfmap.tail(last_two_week_rows).groupby(by='PROVINCE').mean()
        df_be_groupby['Active_cases'] = df_be_groupby['Tested_positive'] * 7
        make_columns_relative(df_be_groupby, "Hospital_admission", 1000000)
        make_columns_relative(df_be_groupby, "Active_cases", 100000)

        df_color_code = give_color_code(df_be_groupby, threshold_value)

        fig_map = px.choropleth_mapbox(dfmap, geojson=geo, color=df_color_code["color_score"],
                           locations="PROVINCE", featureidkey="properties.PROVINCE",
                           center={"lat": 50.5039, "lon": 4.4699},
                           mapbox_style="carto-positron", zoom=6.5,
                           hover_data=['Hospital_admission', 'Total_tested'],
                           color_discrete_map={
                            "Caution": "#006B3E",
                            "Concern": "#FFE733",
                            "Serious": "#FFAA1C",
                            "Severe": "#ED2938"}
                            )
        fig_map.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
        fig_map.show()
    
    if country_name == 'UK':
        return fig_positive_tested, fig_hospital_admissions, fig_total_tested, fig_hospital_predictions, fig_total_tested_predictions, fig_positive_tested_predictions, fig_map,{'display': ' '}, {'display': 'none'}, {'display': 'none'}
    elif country_name == 'NL':
        return fig_positive_tested, fig_hospital_admissions, fig_total_tested, fig_hospital_predictions, fig_total_tested_predictions, fig_positive_tested_predictions, fig_map,{'display': 'none'}, {'display': ' '}, {'display': 'none'}
    elif country_name == 'BE':
        return fig_positive_tested, fig_hospital_admissions, fig_total_tested, fig_hospital_predictions, fig_total_tested_predictions, fig_positive_tested_predictions, fig_map,{'display': 'none'}, {'display': 'none'}, {'display': ' '}


if __name__ == '__main__':
    app.run_server(host='0.0.0.0', port=8080, debug=True)
