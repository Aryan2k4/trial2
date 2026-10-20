"""Timestamp-based, causal features shared by training and live utilization forecasts."""
import numpy as np
import pandas as pd
FEATURES=['target_hour','target_dow','target_weekend','target_hour_sin','target_hour_cos','capacity','util_now','mean1h','mean4h','std1h','trend1h','yesterday_target','last_week_target','is_workspace','is_meeting_room','is_common_area','is_restricted']
def build_features(frame,zone_type,capacity):
    g=frame.copy(); g['timestamp']=pd.to_datetime(g.timestamp)
    g=g.sort_values('timestamp').drop_duplicates('timestamp',keep='last').reset_index(drop=True)
    s=g.set_index('timestamp').utilization_pct
    target=g.timestamp+pd.Timedelta(hours=1)
    g['target_hour']=target.dt.hour+target.dt.minute/60
    g['target_dow']=target.dt.dayofweek
    g['target_weekend']=(g.target_dow>=5).astype(int)
    g['target_hour_sin']=np.sin(2*np.pi*g.target_hour/24);g['target_hour_cos']=np.cos(2*np.pi*g.target_hour/24)
    g['capacity']=capacity;g['util_now']=g.utilization_pct
    g['mean1h']=s.rolling('1h',min_periods=1).mean().to_numpy()
    g['mean4h']=s.rolling('4h',min_periods=1).mean().to_numpy()
    g['std1h']=s.rolling('1h',min_periods=1).std().fillna(0).to_numpy()
    g['trend1h']=g.utilization_pct-(g.timestamp-pd.Timedelta(hours=1)).map(s).fillna(g.utilization_pct)
    for name,days in [('yesterday_target',1),('last_week_target',7)]:
        g[name]=(target-pd.Timedelta(days=days)).map(s).fillna(g.utilization_pct)
    for z in ['workspace','meeting_room','common_area','restricted']:g['is_'+z]=int(zone_type==z)
    return g
