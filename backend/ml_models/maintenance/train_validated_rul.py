"""Select RUL model using engine-grouped validation, then report the fixed NASA benchmark.
Run from backend: python ml_models/maintenance/train_validated_rul.py
The official test set has been used by earlier project iterations; this is a
reused benchmark, not a new untouched external certification.
"""
import os
os.environ.setdefault('OMP_NUM_THREADS','4')
import sys,json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
import joblib,numpy as np,pandas as pd
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVR
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.model_selection import GroupKFold
from sklearn.metrics import mean_absolute_error,r2_score
from sklearn.inspection import permutation_importance
from ml_models.maintenance.train_health_model import load_train,load_official_test,RAW_DIR,COLS_RAW,RAW_RENAME,MODEL_DIR
from app.utils.rul_smoothing import features,FEATURES
from app.utils.rul_features import SENSOR_COLS
from app.utils.interval_model import OffsetRegressor

def train():
    df=features(load_train(),'asset_id')
    rng=np.random.default_rng(732)
    indices={g:int(rng.choice(d.index[d.cycle.ge(30)])) for g,d in df.groupby('asset_id')}
    candidates={f'svr_C{c}':make_pipeline(StandardScaler(),SVR(C=c,epsilon=3)) for c in [10,30,100]}
    candidates.update({f'hgb_depth{d}':HistGradientBoostingRegressor(max_iter=250,max_depth=d,learning_rate=.05,l2_regularization=10,early_stopping=False,random_state=42) for d in [3,5]})
    scores,residuals={},{}
    for name,model in candidates.items():
        errors=[]
        for tr,va in GroupKFold(3).split(df,groups=df.asset_id):
            train=df.iloc[tr].iloc[::3]
            valid=df.loc[[indices[g] for g in df.iloc[va].asset_id.unique()]]
            model.fit(train[FEATURES],train.true_rul_cycles)
            errors.extend(abs(valid.true_rul_cycles-np.clip(model.predict(valid[FEATURES]),0,125)))
        scores[name]=float(np.mean(errors)); residuals[name]=errors
    best=min(scores,key=scores.get)
    model=candidates[best]
    # Explainability weights come from training validation, never the test set.
    importance=permutation_importance(
        model,valid[FEATURES],valid.true_rul_cycles,
        scoring='neg_mean_absolute_error',n_repeats=3,random_state=42,
    ).importances_mean.clip(min=0)
    importance=importance/max(float(importance.sum()),1e-9)
    weights=dict(zip(FEATURES,map(float,importance)))
    train=df.iloc[::3]
    model.fit(train[FEATURES],train.true_rul_cycles)
    radius=float(np.quantile(residuals[best],.8,method='higher'))
    test=pd.read_csv(RAW_DIR/'test_FD001.txt',sep=r'\s+',header=None,names=COLS_RAW).rename(columns=RAW_RENAME)
    test=features(test,'unit_nr').groupby('unit_nr').tail(1)
    y=load_official_test().true_rul_cycles.to_numpy()
    pred=np.clip(model.predict(test[FEATURES]),0,125)
    lo,hi=np.clip(pred-radius,0,125),np.clip(pred+radius,0,125)
    mae=float(mean_absolute_error(y,pred)); r2=float(r2_score(y,pred))
    naive=float(mean_absolute_error(y,np.full(len(y),df.true_rul_cycles.mean())))
    metrics=json.loads((MODEL_DIR/'model_metrics.json').read_text())
    metrics.setdefault('previous_model_benchmark',{'model':metrics['best_model'],'metrics':metrics['all_models'][metrics['best_model']]})
    metrics.update(best_model=best,live_model=best,feature_cols=FEATURES,feature_importances_best_model=weights)
    metrics['all_models']={best:{'held_out_test_mae_cycles':round(mae,2),'held_out_test_r2':round(r2,4)}}
    metrics['cv_tuning']={'method':'3-fold engine-grouped validation, one seeded truncation per validation engine; final benchmark excluded from selection','cv_mae_cycles':round(scores[best],3),'candidate_mae':scores}
    metrics['prediction_interval']={'nominal_coverage_pct':80,'empirical_coverage_pct':float(np.mean((y>=lo)&(y<=hi))*100),'mean_interval_width_cycles':float(np.mean(hi-lo)),'note':'Symmetric band from grouped out-of-fold residuals; empirical benchmark coverage, not a guaranteed confidence interval.'}
    metrics['naive_baseline']={'strategy':'training mean','mae_cycles':round(naive,2)}
    metrics['improvement_over_naive_pct']=round((1-mae/naive)*100,1)
    metrics['training_distribution']={c:{'mean':float(df[c].mean()),'std':float(df[c].std())} for c in SENSOR_COLS}
    metrics['note']='Selected only on engine-grouped training validation. NASA FD001 test is a reused project benchmark on 100 different engines. Sensor smoothing is causal; no future readings or test labels enter model fitting. R2 is not classification accuracy.'
    metrics.pop('lstm_vs_tree_comparison',None)
    joblib.dump({'model':model,'model_name':best,'features':FEATURES,'rul_clip':125,'feature_pipeline':'causal_smoothing_v2','lo_model':OffsetRegressor(model,-radius),'hi_model':OffsetRegressor(model,radius),'feature_importances':weights,'feature_means':df[FEATURES].mean().to_dict(),'feature_stds':df[FEATURES].std().to_dict()},MODEL_DIR/'health_rul_model.pkl',compress=3)
    (MODEL_DIR/'model_metrics.json').write_text(json.dumps(metrics,indent=2))
    scatter={'model':best,'r2':round(r2,4),'unit':'cycles','points':[{'actual':round(float(a),1),'predicted':round(float(p),1),'lower':round(float(l),1),'upper':round(float(h),1)} for a,p,l,h in zip(y,pred,lo,hi)]}
    (MODEL_DIR/'prediction_scatter.json').write_text(json.dumps(scatter,indent=2))
    print(json.dumps({'selected':best,'MAE':mae,'R2':r2,'interval_coverage':metrics['prediction_interval']['empirical_coverage_pct']},indent=2))
if __name__=='__main__': train()
