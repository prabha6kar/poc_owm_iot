#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Created on Fri Jun  28 22:23:52 2019

@author: prabhakaran
"""

import datetime, configparser, requests, sys, smtplib, ssl, ast
import pandas as pd, numpy as np, time

import dash_core_components as dcc
import dash_html_components as html

# plotly libraries
import plotly.plotly as py
import plotly.graph_objs as go
from plotly import tools
from plotly.offline import download_plotlyjs, init_notebook_mode, plot, iplot

# from dask_app.dask_load_history import dask_load_history
from IOT import GetRealTimeTemp as sensor # import and connect the client to server

from mongo import mongo_load_history as mongo_load

def get_config(config_file_name):
    config = configparser.ConfigParser(interpolation=configparser.ExtendedInterpolation())
    config.read(config_file_name)
    return config

def get_weather(config):
    location, api_key = config['location'], config['api']
    url = "https://api.openweathermap.org/data/2.5/weather?q={}&appid={}&unit=metric".format(location, api_key)
    r = requests.get(url)
    return r.json()

def smtp_send_message(context, config, temp, threshold, location, OWM):
    receiver_email_list = ast.literal_eval(config['receiver_email_list'])
    source_text = ' Reporting from Open Weather Map API' if OWM else ' Reporting from Sensors'
    message = \
        "From: " + config['sender_email'] + \
        "\nTo: " + str(receiver_email_list) + \
        """\nSubject: Threshold notification e-mail for """+ str(location) + source_text +\
        """\n\n timestamp """+ time.strftime('%Y-%m-%d %H:%M:%S', time.localtime()) + \
        """-  Temperature = """ + str(temp) + """ in Kelvin """ + \
        """ threshold is """ + str(threshold) + """ in Kelvin """ + \
        """ for """ + str(location)
    
    with smtplib.SMTP_SSL(config['mail_server'], config['port'], context=context) as server:
        server.login(config['sender_email'], config['password'])
        server.sendmail(config['sender_email'], receiver_email_list, message)

def plot_history_graph(weather_df_cityid):
    # Create and style traces
    trace0 = go.Scatter(
        x = weather_df_cityid['disp_date'],
        y = weather_df_cityid['temp'],
        name = 'Temp (K)',
        line = dict(color = ('purple'), width = 5, dash = 'dashdot')
    )
    trace1 = go.Scatter(
        x = weather_df_cityid['disp_date'],
        y = weather_df_cityid['temp_max'],
        yaxis='y4',
        name = 'Max Temp (K)',
        mode = 'markers',
        marker = dict(color = ('cyan'), size = 15, symbol = 'triangle-up-open')
    )
    trace2 = go.Scatter(
        x = weather_df_cityid['disp_date'],
        y = weather_df_cityid['temp_min'],
        yaxis='y5',
        name = 'Min Temp (K)',
        mode = 'markers',
        marker = dict(color = ('orange'), size = 15, symbol = 'triangle-up-dot')
    )
    trace3 = go.Scatter(
        x = weather_df_cityid['disp_date'],
        y = weather_df_cityid['pressure'],
        yaxis='y2',
        name = 'Pressure (hPa)',
        line = dict(color = ('yellow'), width = 1)
    )
    trace4 = go.Scatter(
        x = weather_df_cityid['disp_date'],
        y = weather_df_cityid['humidity'],
        yaxis='y3',
        name = 'Humidity (%)',
        line = dict(color = ('green'), width = 1)
    )

    trace5 = go.Scatter(
        x = weather_df_cityid['disp_date'],
        y = weather_df_cityid['average_temp'],
        name = 'Avg Temp (K)',
        line = dict(color = ('blue'), width = 2)
    )

    trace6 = go.Scatter(
        x = weather_df_cityid['disp_date'],
        y = weather_df_cityid['threshold_temp'],
        name = 'Threshold Temp (K)',
        line = dict(color = ('red'), width = 3)
    )

    data = [trace0, trace3, trace4, trace5, trace1, trace2, trace6]

    # Edit the layout
    layout = dict( # title = 'Temperature Trend for ' + location,
                  height=650,
                  autosize=True,
                  xaxis = dict(range=[trace0.x[-1] - datetime.timedelta(hours=12), trace0.x[-1] + datetime.timedelta(hours=1)],
                               rangeselector=dict(
                                                  buttons=list([
                                                      dict(count=1, label='1H', step='hour', stepmode='backward'),
                                                      dict(count=6, label='6H', step='hour', stepmode='backward'),
                                                      dict(count=12, label='12H', step='hour', stepmode='backward'),
                                                      dict(count=1, label='1D', step='day', stepmode='backward'),
                                                      dict(count=7, label='1W', step='day', stepmode='backward'),
                                                      dict(count=1, label='1M', step='month', stepmode='backward'),
                                                      dict(count=6, label='6M', step='month', stepmode='backward'),
                                                      dict(count=1, label='1Y', step='year', stepmode='backward'),
                                                      dict(step='all'),]),
                                                   x = 0.01, y = 1.1, xanchor = 'left', yanchor = 'top',
                                                 ), 
                               rangeslider=dict(visible = True,), type='date'),
                  yaxis = dict(title = 'Temp (K)', anchor='free', automargin=True, autorange= True, fixedrange= False,), # range=[270,315],
                  yaxis2= dict(title = 'Pres(hPa)', anchor='free', automargin=True, autorange= True, fixedrange= False,
                               overlaying='y', side='right', showgrid=False, position=0.99,),
                  yaxis3= dict(title = 'Humidity(%)', anchor='free', automargin=True, autorange= True, fixedrange= False,
                               overlaying='y', side='right', showgrid=False, position=0.95,),
                  yaxis4= dict(title = 'Max(K)', anchor='free', automargin=True, autorange= True, fixedrange= False,
                               overlaying='y', side='left', showgrid=False, position=0.04,),
                  yaxis5= dict(title = 'Min(K)', anchor='free', automargin=True, autorange= True, fixedrange= False,
                               overlaying='y', side='left', showgrid=False, position=0.08,),
                  )
    
    return go.FigureWidget(data=data, layout=layout)

def update_live_data_graph(config, OWM=True):

    global fig, run_once, check_interval
    
    if not run_once :
        run_once = True # exists for reduced time during initial loading
        print (datetime.datetime.now(), '- Loading data from history this takes up to a min approx... Please wait...')

        weather_df_cityid = mongo_load.mongo_load_history(temp_threshold,
                                                          config['mongo']['db'],
                                                          config['mongo']['collection'],
                                                          ast.literal_eval(config['mongo']['query']), 
                                                          ast.literal_eval(config['mongo']['proj']), 
                                                          config['mongo']['host'], 
                                                          int(config['mongo']['port']),
                                                          ast.literal_eval(config['mongo']['username']),
                                                          ast.literal_eval(config['mongo']['password']),
                                                          ast.literal_eval(config['mongo']['no_id']),
                                                          )
        
        fig = plot_history_graph(weather_df_cityid)
        
        print (datetime.datetime.now(), '- Loaded data from huge file Preparing Plot and FLASK based DASH server to project PLOTLY graph... Please wait...')
        check_interval = float(config['control']['check_interval'])
        print (datetime.datetime.now(), '- Will start checking for every', float(config['control']['check_interval']), 'Seconds from now on')
        
    if fig == None: # to handle when fig is still not loaded
        return 0
    
    run_once = True # this means fig was already loaded and so setting run_once to True
    # Collect current weather data
    weat = get_weather(config['openweathermap'])
    temp_max = float(weat['main']['temp_max'])
    temp_min = float(weat['main']['temp_min'])
    pressure = float(weat['main']['pressure'])
    humidity = float(weat['main']['humidity'])
    
    if OWM:
        temp = float(weat['main']['temp'])
        fig.data[0].line.color= "purple"
    else:
        sensor.get_temp_from_sensor()
        temp = float(sensor.MQTT_MESSAGE.payload) + 273.15 # convert to Kelvin
        fig.data[0].line.color= "mediumseagreen"

    if temp >= temp_threshold:
        smtp_send_message(context, config['smtp'], temp, temp_threshold, location, OWM)
    
    disp_date = fig.data[0].x[-1] + datetime.timedelta(minutes=15) # use a 3 hour epoch time for demo
    
    avg_temp = fig.data[3].y[-1]
    
    fig.data[0].x = np.append(fig.data[0].x, disp_date)
    fig.data[1].x = np.append(fig.data[0].x, disp_date)
    fig.data[2].x = np.append(fig.data[0].x, disp_date)
    fig.data[3].x = np.append(fig.data[0].x, disp_date)
    fig.data[4].x = np.append(fig.data[0].x, disp_date)
    fig.data[5].x = np.append(fig.data[0].x, disp_date)
    fig.data[6].x = np.append(fig.data[0].x, disp_date)
    
    fig.data[0].y = np.append(fig.data[0].y, temp)
    fig.data[1].y = np.append(fig.data[1].y, pressure)
    fig.data[2].y = np.append(fig.data[2].y, humidity)
    fig.data[3].y = np.append(fig.data[3].y, avg_temp)
    fig.data[4].y = np.append(fig.data[4].y, temp_max)
    fig.data[5].y = np.append(fig.data[5].y, temp_min)
    fig.data[6].y = np.append(fig.data[6].y, temp_threshold)
    
    fig.layout.xaxis.range = tuple([i+ datetime.timedelta(minutes=15) for i in fig.layout.xaxis.range])
    
    return fig

fig = None
run_once = False
context = ssl.create_default_context()
all_config = get_config('config.ini')
jsonfilename = all_config['history']['jsonfilename']
location = all_config['openweathermap']['location']
temp_threshold = float(all_config['control']['threshold'])
check_interval = float(all_config['control']['initial_load_interval'])