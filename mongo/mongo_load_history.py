import json, pandas as pd
from pandas.io.json import json_normalize
from . import mongoaccess as mg_ac

def mongo_load_history(temp_threshold, db, collection, query, proj, host, port, username, password, no_id=True):
    
    mg_df = mg_ac.read_mongo(db, collection, query, proj, host, port, username, password, no_id)
    
    mg_df_norm = pd.DataFrame(json.loads(mg_df['data'].to_json(orient="records"))[0])
    mg_df_norm = pd.concat([mg_df_norm.dt, json_normalize(mg_df_norm.main, 
                                                          meta='main', 
                                                          record_prefix='main')], 
                           axis=1)
    
    weather_df_mg = mg_df_norm.sort_values(['dt']).groupby('dt').head(1)
    weather_df_mg['disp_date'] = pd.to_datetime(weather_df_mg['dt'],unit='s')
    weather_df_mg['disp_date'] = weather_df_mg['disp_date'].apply(lambda x: x + pd.DateOffset(years=2, months=3))
    
    #Add average
    weather_df_mg['average_temp'] = weather_df_mg['temp'].mean()

    #Add Threshold
    weather_df_mg['threshold_temp'] = temp_threshold
    
    return weather_df_mg