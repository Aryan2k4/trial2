"""Causal smoothing candidates for RUL; all windows use only past/current readings."""
import pandas as pd
from app.utils.rul_features import SENSOR_COLS

FEATURES = ['cycle'] + [f'{c}_{kind}' for c in SENSOR_COLS for kind in ['mean20', 'mean40', 'trend20']]

def features(frame, group_col):
    out = frame.sort_values([group_col, 'cycle']).copy()
    for c in SENSOR_COLS:
        group = out.groupby(group_col)[c]
        out[c+'_mean20'] = group.transform(lambda s: s.rolling(20,min_periods=1).mean())
        out[c+'_mean40'] = group.transform(lambda s: s.rolling(40,min_periods=1).mean())
        out[c+'_trend20'] = out[c+'_mean20'] - out.groupby(group_col)[c+'_mean20'].shift(20).fillna(out[c+'_mean20'])
    return out
