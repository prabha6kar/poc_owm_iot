import os

import dash_html_components as html
from dash.dependencies import Input, Output
from app import app
from apps import main, code
from apps.plot_graph import *

if 'DYNO' in os.environ:
    app_name = os.environ['DASH_APP_NAME']
else:
    app_name = 'POC_OWM_IOT/'

def app_layout():
    
    global check_interval
    
    return html.Div([
        html.Div([
            html.Div([html.H4('Temperature History and Live Feed - ' + location)], className="six columns"),
            
            html.Div([dcc.RadioItems(id='xaxis-type', options=[{'label': i, 'value': i} for i in ['OWM', 'Sensor']],
                                     value='OWM', labelStyle={'display': 'inline-block'})], className="six columns"),
            
            html.Div([html.Div(id='live-update-text')]),

            html.Div([dcc.Graph(id='live-update-graph'), dcc.Interval(id='interval-component', interval=check_interval*1000, n_intervals=0)]),
            
        ], className="row")
    ])

app.layout = app_layout

# external_css = ['https://codepen.io/chriddyp/pen/bWLwgP.css', 
# 		# "https://cdnjs.cloudflare.com/ajax/libs/skeleton/2.0.4/skeleton.min.css",
#                 # "//fonts.googleapis.com/css?family=Raleway:400,300,600",
#                 # "//fonts.googleapis.com/css?family=Dosis:Medium",
#                 # "https://cdn.rawgit.com/plotly/dash-app-stylesheets/62f0eb4f1fadbefea64b2404493079bf848974e8/dash-uber-ride-demo.css",
#                 #"https://maxcdn.bootstrapcdn.com/font-awesome/4.7.0/css/font-awesome.min.css"
# 		]
# for css in external_css:
#     app.css.append_css({"external_url": css})

@app.callback(Output('live-update-text', 'children'),
              [Input('interval-component', 'n_intervals'), Input('xaxis-type', 'value'),])
def update_heading(n, xaxis_type):
    text_h2 = 'Live tracking OWM... Page last loaded at: ' if xaxis_type == 'OWM' else 'Live tracking IOT Sensor... Page last loaded at: '
    return html.P(text_h2 + str(datetime.datetime.now()))

# Multiple components can update everytime interval gets fired.
@app.callback(Output('live-update-graph', 'figure'),
              [Input('interval-component', 'n_intervals'), Input('xaxis-type', 'value'),])
def update_graph_live(n, xaxis_type):
    OWM = True if (xaxis_type == 'OWM') else False
    return update_live_data_graph(all_config, OWM)

if __name__ == '__main__':
    app.run_server(host='0.0.0.0', debug=True, use_reloader=False)
