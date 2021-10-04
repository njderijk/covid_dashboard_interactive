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

from datetime import datetime, timedelta
import math
import os
import base64

import xlrd


BS = "https://stackpath.bootstrapcdn.com/bootstrap/4.4.1/css/bootstrap.min.css"

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

def readData():
    source = "output.xlsx"
    global NL, BE, UK, NLgeo, BEgeo, UKgeo
    NL = pd.read_excel(io=source, sheet_name="NL", index_col=0)
    BE = pd.read_excel(io=source, sheet_name="BE", index_col=0)
    UK = pd.read_excel(io=source, sheet_name="UK", index_col=0)
    NLgeo = pd.read_excel(io=source, sheet_name="NLgeo", index_col=0)
    BEgeo = pd.read_excel(io=source, sheet_name="BEgeo", index_col=0)
    UKgeo = pd.read_excel(io=source, sheet_name="UKgeo", index_col=0)
    
readData()

#Last recorded date
date = datetime.strptime(UK['DATE'].max(), "%Y-%m-%d").strftime("%Y-%m-%d")

#Day before the last recorded date
date_yesterday = str(datetime.strptime(UK['DATE'].max(), "%Y-%m-%d") + timedelta(days=-14)).split(' ')[0]

#14 days before the last recorded date
date_14_days_before = str(datetime.strptime(UK['DATE'].max(), "%Y-%m-%d") + timedelta(days=-14)).split(' ')[0]

#28 days before the last recorded date
date_28_days_before = str(datetime.strptime(UK['DATE'].max(), "%Y-%m-%d") + timedelta(days=-28)).split(' ')[0]

#Number of active cases in the last two weeks
Active_Cases_UK = UK[(UK['DATE'] > date_14_days_before) & (UK['DATE'] <= date)].Tested_positive.sum()

#Number of inhabitants today
Inhabitants_UK = UK[(UK['DATE'] == date)].Inhabitants.sum()

#Number of active cases per 100.000 inhabitants
Active_Cases_Per_100k_UK = int(round(100000*Active_Cases_UK/Inhabitants_UK,0))

#Number of tests today
Tests_UK = UK[(UK['DATE'] == date)].Total_tested.sum()

#Number of tests per 100.000 inhabitants
Tests_Per_100k_UK = int(round(100000*Tests_UK/Inhabitants_UK,0))

#Number of positive tests on this day
Positive_Tests_UK = UK[(UK['DATE'] == date)].Tested_positive.sum()

#Number of postitive tests of the day before
Positive_Tests_UK_yesterday = UK[(UK['DATE'] == date_yesterday)].Tested_positive.sum()

#Number of hospital admissions in the last two weeks
Hospital_Admissions_UK = UK[(UK['DATE'] > date_14_days_before) & (UK['DATE'] <= date)].Hospital_admission.sum()

#Number of hospital admissions in the last two weeks
Hospital_Admissions_UK_before = UK[(UK['DATE'] > date_28_days_before) & (UK['DATE'] <= date_14_days_before)].Hospital_admission.sum()


def  get_data_num(case_type):    
    '''
    Generate case table, incremental number and percentage
    '''
    df_tmp = pd.read_csv('./lineplot_data/df_{}.csv'.format(case_type))
    df_tmp = df_tmp.astype({'Date': 'datetime64'})
    plusNum = df_tmp['plusNum'][0]
    plusPercent = df_tmp['plusPercentNum'][0]

    return df_tmp, plusNum, plusPercent


filename = os.listdir('./raw_data/')
sheet_name = [i.replace('.csv', '')
                        for i in filename if 'data' not in i and i.endswith('.csv')]
sheet_name.sort(reverse=True)

brazil_file_name = [i for i in os.listdir('./') if i.endswith('Brazil_data.csv')]
germany_file_name = [i for i in os.listdir('./') if i.endswith('Germany_data.csv')]

# Add coordinates for each area in the list for the latest table sheet
# To save time, coordinates calling was done seperately
# Import the data with coordinates
df_latest = pd.read_csv('{}_data.csv'.format(sheet_name[0]))
df_latest = df_latest.astype({'Date_last_updated_AEDT': 'datetime64'})

# Import Brazil data
df_brazil = pd.read_csv('{}'.format(brazil_file_name[0]))
df_brazil = df_brazil.astype({'Date_last_updated_AEDT': 'datetime64'})

# Import Germany data
df_germany = pd.read_csv('{}'.format(germany_file_name[0]))
df_germany = df_germany.astype({'Date_last_updated_AEDT': 'datetime64'})

# Save numbers into variables to use in the app
confirmedCases = df_latest['Confirmed'].sum()
deathsCases = df_latest['Deaths'].sum()
recoveredCases = df_latest['Recovered'].sum()
remainCases = df_latest['Confirmed'].sum() - (df_latest['Deaths'].sum() + df_latest['Recovered'].sum())

# Construct confirmed cases dataframe for line plot and 24-hour window case difference
df_confirmed, plusConfirmedNum, plusPercentNum1 = get_data_num('confirmed')

# Construct recovered cases dataframe for line plot and 24-hour window case difference
df_recovered, plusRecoveredNum, plusPercentNum2 = get_data_num('recovered')

# Construct death case dataframe for line plot and 24-hour window case difference
df_deaths, plusDeathNum, plusPercentNum3 = get_data_num('deaths')

# Construct remaining case dataframe for line plot and 24-hour window case difference
df_remaining, plusRemainNum, plusRemainNum3 = get_data_num('remaining')


@app.callback(Output('combined-line-plot', 'figure'),
              [Input('log-button', 'on')])

def render_combined_line_plot(log):
  if log is True:
    axis_type = 'log'
  else:
    axis_type = 'linear'

  # Line plot for combine recovered cases
  # Set up tick scale based on total recovered case number
  #tickList = np.arange(0, df_remaining['Total'].max()+10000, 30000)

  # Create empty figure canvas
  fig_combine = go.Figure()
  # Add trace to the figure
  
  fig_combine.add_trace(go.Scatter(x=df_remaining['Date'], y=df_remaining['Total'],
                                mode='lines+markers',
                                line_shape='spline',
                                name='Active',
                                line=dict(color='#f0953f', width=2),
                                marker=dict(size=2, color='#f0953f',
                                            line=dict(width=.5, color='#f0953f')),
                                text=[datetime.strftime(
                                    d, '%b %d %Y GMT+10') for d in df_deaths['Date']],
                                hovertext=['Total active<br>{:,d} cases<br>'.format(
                                    i) for i in df_remaining['Total']],
                                hovertemplate='%{hovertext}' +
                                              '<extra></extra>'))
  fig_combine.add_trace(go.Scatter(x=df_confirmed['Date'], y=df_confirmed['Total'],
                                   mode='lines+markers',
                                   line_shape='spline',
                                   name='Confirmed',
                                   line=dict(color='#f03f42', width=2),
                                   marker=dict(size=2, color='#f03f42',
                                               line=dict(width=.5, color='#f03f42')),
                                   text=[datetime.strftime(
                                       d, '%b %d %Y GMT+10') for d in df_confirmed['Date']],
                                   hovertext=['Total confirmed<br>{:,d} cases<br>'.format(
                                       i) for i in df_confirmed['Total']],
                                   hovertemplate='%{hovertext}' +
                                                 '<extra></extra>'))
  fig_combine.add_trace(go.Scatter(x=df_recovered['Date'], y=df_recovered['Total'],
                                   mode='lines+markers',
                                   line_shape='spline',
                                   name='Recovered',
                                   line=dict(color='#2ecc77', width=2),
                                   marker=dict(size=2, color='#2ecc77',
                                               line=dict(width=.5, color='#2ecc77')),
                                   text=[datetime.strftime(
                                       d, '%b %d %Y GMT+10') for d in df_recovered['Date']],
                                   hovertext=['Total recovered<br>{:,d} cases<br>'.format(
                                       i) for i in df_recovered['Total']],
                                   hovertemplate='%{hovertext}' +
                                                 '<extra></extra>'))
  fig_combine.add_trace(go.Scatter(x=df_deaths['Date'], y=df_deaths['Total'],
                                mode='lines+markers',
                                line_shape='spline',
                                name='Death',
                                line=dict(color='#7f7f7f', width=2),
                                marker=dict(size=2, color='#7f7f7f',
                                            line=dict(width=.5, color='#7f7f7f')),
                                text=[datetime.strftime(
                                    d, '%b %d %Y GMT+10') for d in df_deaths['Date']],
                                hovertext=['Total death<br>{:,d} cases<br>'.format(
                                    i) for i in df_deaths['Total']],
                                hovertemplate='%{hovertext}' +
                                              '<extra></extra>'))
  # Customise layout
  fig_combine.update_layout(
    margin=go.layout.Margin(
        l=10,
        r=10,
        b=10,
        t=5,
        pad=0
    ),
    yaxis_type=axis_type,
    yaxis=dict(
        showline=False, linecolor='#272e3e',
        zeroline=False,
        # showgrid=False,
        gridcolor='rgba(203, 210, 211,.3)',
        gridwidth=.1,
        #tickmode='array',
        # Set tick range based on the maximum number
        #tickvals=tickList,
        # Set tick label accordingly
        #ticktext=["{:.0f}k".format(i/1000) for i in tickList]
    ),
#    yaxis_title="Total Confirmed Case Number",
    xaxis=dict(
        showline=False, linecolor='#272e3e',
        showgrid=False,
        gridcolor='rgba(203, 210, 211,.3)',
        gridwidth=.1,
        zeroline=False
    ),
    xaxis_tickformat='%b %d',
    hovermode='x unified',
    legend_orientation="h",
    legend=dict(x=.26, y=-.1,),
    plot_bgcolor='#ffffff',
    paper_bgcolor='#ffffff',
    font=dict(color='#292929', size=10)
  )
  
  return fig_combine






app.title = 'RIVM COVID-19 Travel Advisory Dashboard'

app.layout = html.Div(
    id='app-body',
    children=[
        html.Div(
            ## HEADER ##
            id="header",
            children=[
                html.H4(
                    id='dashboard-title',
                    children="RIVM Dashboard for COVID-19 Travel Advisories"),
                html.P(
                    id="description",
                    children=dcc.Markdown(
                        children=(
                            '''
                            On Dec 31, 2019, the World Health Organization (WHO) was informed 
                            an outbreak of “pneumonia of unknown cause” detected in Wuhan, Hubei Province, China. 
                            The virus that caused the outbreak of COVID-19 was lately known as _severe acute respiratory syndrome coronavirus 2_ (SARS-CoV-2). 
                            The WHO declared the outbreak to be a Public Health Emergency of International Concern on 
                            Jan 30, 2020 and recognized it as a pandemic on Mar 11, 2020. As of {}, there are {:,d} confirmed cases globally.
                        
                            This dashboard is developed to help the RIVM to make accurate and timely travel advisories for foreign countries.'''
                        )
                    )
                ),
                html.P(
                    className='time-stamp',
                    children="Last update: {}." # (Hover over items for additional information)".format(latestDate)
                ),
                html.Hr(
                ),
            ]
        ),
        ## NUMBER PLATES
        html.Div(
            className="number-plate",
            children=[
                html.Div(
                    className='number-plate-single',
                    id='number-plate-active',
                    style={'border-top': '#f0953f solid .2rem',},
                    children=[
                        html.H5(
                            style={'color': '#f0953f'},
                            children="Active cases"
                        ),
                        html.H3(
                        	style={'color': '#f0953f'},
                            children=[
                                '{:,d}'.format(Active_Cases_Per_100k_UK),
                                html.P(
                                    children='+ {:,d} in the past 24h ({:.1%})'.format(plusRemainNum, plusRemainNum3) if plusRemainNum > 0 else '{:,d} in the past 24h ({:.1%})'.format(plusRemainNum, plusRemainNum3)
                                ),      
                            ]
                        ),
                    ]
                ),
                html.Div(
                    className='number-plate-single',
                    id='number-plate-confirm',
                    style={'border-top': '#f03f42 solid .2rem',},
                    children=[
                        html.H5(
                            style={'color': '#f03f42'},
                            children="Confirmed cases"
                        ),
                        html.H3(
                            style={'color': '#f03f42'},
                            children=[
                                '{:,d}'.format(confirmedCases),
                                html.P(
                                    children='+ {:,d} in the past 24h ({:.1%})'.format(plusConfirmedNum, plusPercentNum1)
                                ),
                                
                            ]
                        ),
                        
                    ]
                ),
                html.Div(
                    className='number-plate-single',
                    id='number-plate-recover',
                    style={'border-top': '#2ecc77 solid .2rem',},
                    children=[
                        html.H5(
                            style={'color': '#2ecc77'},
                            children="Number of tests"
                        ),
                        html.H3(
                            style={'color': '#2ecc77'},
                            children=[
                                '{:,d}'.format(recoveredCases),
                                html.P(
                                    children='+ {:,d} in the past 24h ({:.1%})'.format(plusRecoveredNum, plusPercentNum2)
                                ),
                                
                            ]
                        ),
                        
                    ]
                ),
                html.Div(
                    className='number-plate-single',
                    id='number-plate-death',
                    style={'border-top': '#7f7f7f solid .2rem',},
                    children=[
                        html.H5(
                            style={'color': '#7f7f7f'},
                            children="Hospital admissions"
                        ),
                        html.H3(
                        	style={'color': '#7f7f7f'},
                            children=[
                                '{:,d}'.format(deathsCases),
                                html.P(
                                    children='+ {:,d} in the past 24h ({:.1%})'.format(plusDeathNum, plusPercentNum3)
                                ),
                                
                            ]
                        ),
                        
                    ]
                ),
                dbc.Tooltip(
                    target='number-plate-active',
                    style={"fontSize":"1.8em", 'textAlign':'right', 'padding':'10px',},
                    children=
                        dcc.Markdown(
                            '''
                            1 day ago: **{:,d}**

                            2 days ago: **{:,d}** 

                            '''.format(df_confirmed['Total'][1] - df_deaths['Total'][1] - df_recovered['Total'][1], df_confirmed['Total'][2]- df_deaths['Total'][2] - df_recovered['Total'][2]),
                        ) 
                ),
                dbc.Tooltip(
                    target='number-plate-confirm',
                    style={"fontSize":"1.8em", 'textAlign':'right', 'padding':'10px',},
                    children=
                        dcc.Markdown(
                            '''
                            1 day ago: **{:,d}**

                            2 days ago: **{:,d}** 

                            '''.format(df_confirmed['Total'][1], df_confirmed['Total'][2]),
                        ) 
                ),
                dbc.Tooltip(
                    target='number-plate-recover',
                    style={"fontSize":"1.8em", 'textAlign':'right', 'padding':'10px',},
                    children=
                        dcc.Markdown(
                            '''
                            1 day ago: **{:,d}**

                            2 days ago: **{:,d}** 

                            '''.format(df_recovered['Total'][1], df_recovered['Total'][2]),
                        ) 
                ),
                dbc.Tooltip(
                    target='number-plate-death',
                    style={"fontSize":"1.8em", 'textAlign':'right', 'padding':'10px',},
                    children=
                        dcc.Markdown(
                            '''
                            1 day ago: **{:,d}**

                            2 days ago: **{:,d}** 

                            '''.format(df_deaths['Total'][1], df_deaths['Total'][2]),
                        ) 
                ),
            ]
        ),
        # DESCRIPTIVE STATISTICS FOR COUNTRY
        html.Div(
                className='row dcc-plot',
                children=[
                    html.Div(
                        className='dcc-sub-plot',
                        children=[
                            html.Div(
                                id='case-timeline-log-button',
                                children=[
                                    html.H5(
                                        children='Aantal besmettingen per 100.000 inwoners'
                                    ),
                                    daq.PowerButton(
                                        id='log-button',
                                        size=22,
                                        color="#2674f6",
                                        on=False,
                                    ),
                                    dbc.Tooltip(
                                        "Switch between linear and logarithmic y-axis",
                                        target='log-button',
                                        style={"fontSize":"1.8em"},
                                    ),
                                ],
                            ),
                            dcc.Graph(
                                id='combined-line-plot',
                                config={"displayModeBar": False, "scrollZoom": False}, 
                            ),
                        ]
                    )
                ]
            )
])

if __name__ == '__main__':
    app.run_server(host='0.0.0.0', port=8080, debug=True)
