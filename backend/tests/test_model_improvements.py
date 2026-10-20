"""Regression checks for causal features, artifact/runtime agreement and forecast calendars."""
import json
from pathlib import Path
import numpy as np
import pandas as pd
from app.utils.rul_smoothing import features, FEATURES
from app.utils.utilization_features import build_features, FEATURES as UTIL_FEATURES
from app.services.health_service import _build_features

ROOT=Path(__file__).resolve().parents[1]

def test_rul_features_ignore_future_and_other_engines():
    from ml_models.maintenance.train_health_model import load_train
    raw=load_train()
    engine=raw[raw.asset_id==raw.asset_id.iloc[0]].iloc[:70].copy()
    full=features(engine,'asset_id')
    prefix=features(engine.iloc[:40],'asset_id')
    np.testing.assert_allclose(full.iloc[39][FEATURES].to_numpy(dtype=float),prefix.iloc[-1][FEATURES].to_numpy(dtype=float))
    mixed=features(pd.concat([engine,raw[raw.asset_id!=raw.asset_id.iloc[0]].iloc[:80]]),'asset_id')
    np.testing.assert_allclose(full[FEATURES],mixed[mixed.asset_id==engine.asset_id.iloc[0]][FEATURES])
    np.testing.assert_allclose(_build_features(engine,FEATURES),full.iloc[[-1]][FEATURES])

def test_occupancy_features_use_timestamps_and_ignore_future():
    dates=pd.date_range('2026-01-01',periods=220,freq='15min')
    g=pd.DataFrame({'timestamp':dates,'utilization_pct':np.arange(220)%100})
    full=build_features(g,'workspace',80)
    prefix=build_features(g.iloc[:180],'workspace',80)
    np.testing.assert_allclose(full.iloc[179][UTIL_FEATURES].to_numpy(dtype=float),prefix.iloc[-1][UTIL_FEATURES].to_numpy(dtype=float))
    # Missing rows must not turn yesterday's feature into a positional lag.
    missing=g.drop(index=[100,101]);f=build_features(missing,'workspace',80).iloc[-1]
    target=g.timestamp.iloc[-1]+pd.Timedelta(hours=1)
    expected=g.set_index('timestamp').loc[target-pd.Timedelta(days=1),'utilization_pct']
    assert f.yesterday_target==expected
    assert f.target_hour==target.hour+target.minute/60

def test_published_rul_artifact_reproduces_benchmark():
    import joblib
    from ml_models.maintenance.train_health_model import RAW_DIR,COLS_RAW,RAW_RENAME,load_official_test
    from sklearn.metrics import mean_absolute_error,r2_score
    d=ROOT/'ml_models'/'maintenance'
    bundle=joblib.load(d/'health_rul_model.pkl')
    metrics=json.loads((d/'model_metrics.json').read_text())
    raw=pd.read_csv(RAW_DIR/'test_FD001.txt',sep=r'\s+',header=None,names=COLS_RAW).rename(columns=RAW_RENAME)
    x=features(raw,'unit_nr').groupby('unit_nr').tail(1)[FEATURES]
    pred=np.clip(bundle['model'].predict(x),0,125);actual=load_official_test().true_rul_cycles
    selected=metrics['all_models'][metrics['best_model']]
    assert round(mean_absolute_error(actual,pred),2)==selected['held_out_test_mae_cycles']
    assert round(r2_score(actual,pred),4)==selected['held_out_test_r2']
    assert np.all(bundle['lo_model'].predict(x)<=pred)
    assert np.all(bundle['hi_model'].predict(x)>=pred)

def test_cost_inference_uses_target_week(monkeypatch):
    from app.utils import cost_analytics
    dates=pd.to_datetime(['2025-12-22','2025-12-29','2026-01-05'])
    # ISO week for Jan 12 is 3, including the year boundary.
    class CorrectCapture:
        def predict(self,x):
            assert x.week_of_year.iloc[0]==3
            return [np.log1p(100)]
    monkeypatch.setattr(cost_analytics,'_load',lambda *a:{'model':CorrectCapture(),'features':['lag1','lag2','roll3_median','week_of_year']})
    result=cost_analytics.forecast_trend(pd.DataFrame({'date':dates,'amount_inr':[100,200,300]}))
    assert result['next_week']=='2026-01-12'
    assert result['predicted_next_3wk_avg_spend_inr']==100

def test_security_artifact_reproduces_later_day_metrics():
    import joblib
    from sklearn.metrics import f1_score,precision_score,recall_score
    from app.utils.security_analytics import _engineer_features
    d=ROOT/'ml_models'/'security'
    metrics=json.loads((d/'model_metrics.json').read_text())
    bundle=joblib.load(d/'anomaly_model.pkl')
    events=_engineer_features(pd.read_csv(ROOT/'data'/'processed'/'security_access_events.csv'))
    test=events[events.timestamp>=pd.Timestamp(metrics['test_start'])]
    pred=bundle['model'].predict(test[bundle['features']])==-1
    for key,metric in [('f1',f1_score),('precision',precision_score),('recall',recall_score)]:
        assert abs(metric(test.is_anomaly,pred)-metrics[key])<1e-10
    assert len(test)==metrics['n_events']
    assert 'is_anomaly' not in bundle['features']
    assert 'anomaly_type' not in bundle['features']
