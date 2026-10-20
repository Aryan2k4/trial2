import os
os.environ.setdefault('OMP_NUM_THREADS','4')
import sys,json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
import numpy as np,pandas as pd,joblib
from sklearn.ensemble import HistGradientBoostingRegressor,ExtraTreesRegressor,RandomForestRegressor
from sklearn.metrics import mean_absolute_error,r2_score
from sklearn.model_selection import TimeSeriesSplit
from app.utils.utilization_features import build_features,FEATURES
from ml_models.occupancy.train_utilization_forecast import build_dataset,DATA_PATH,MODEL_DIR

def dataset():
    df=pd.read_csv(DATA_PATH,parse_dates=['timestamp']);frames=[]
    for zone,g in df.groupby('zone_id'):
        f=build_features(g,g.zone_type.iloc[0],g.capacity.iloc[0])
        s=f.set_index('timestamp').utilization_pct
        f['target_time']=f.timestamp+pd.Timedelta(hours=1)
        f['target']=f.target_time.map(s)
        frames.append(f.iloc[96:])
    return pd.concat(frames).dropna(subset=['target']).sort_values('timestamp').reset_index(drop=True)

def train():
    df=dataset();old=build_dataset().sort_values('timestamp')
    cutoff=old.iloc[int(len(old)*.85)].timestamp
    train=df[df.target_time<cutoff];test=df[df.timestamp>=cutoff]
    candidates={f'hgb_{leaf}':HistGradientBoostingRegressor(max_iter=180,max_leaf_nodes=leaf,min_samples_leaf=30,l2_regularization=10,learning_rate=.06,early_stopping=False,random_state=42) for leaf in [8,16,31]}
    candidates['extra_trees']=ExtraTreesRegressor(n_estimators=120,max_depth=12,min_samples_leaf=5,n_jobs=4,random_state=42)
    candidates['random_forest']=RandomForestRegressor(n_estimators=120,max_depth=12,min_samples_leaf=5,n_jobs=4,random_state=42)
    times=np.array(sorted(train.timestamp.unique()));scores={}
    for name,model in candidates.items():
        errs=[]
        for ti,vi in TimeSeriesSplit(3).split(times):
            a=train[train.target_time<times[vi[0]]];b=train[train.timestamp.isin(times[vi])]
            model.fit(a[FEATURES],a.target)
            errs.append(mean_absolute_error(b.target,np.clip(model.predict(b[FEATURES]),0,100)))
        scores[name]=float(np.mean(errs));print(name,scores[name],flush=True)
    best=min(scores,key=scores.get);model=candidates[best].fit(train[FEATURES],train.target)
    pred=np.clip(model.predict(test[FEATURES]),0,100)
    print('BENCHMARK',best,'MAE',mean_absolute_error(test.target,pred),'R2',r2_score(test.target,pred),flush=True)
    report={'selected':best,'validation_mae':scores,'mae':float(mean_absolute_error(test.target,pred)),'r2':float(r2_score(test.target,pred)),'test_start':str(cutoff),'train_rows':len(train),'test_rows':len(test)}
    (MODEL_DIR/'validation_report.json').write_text(json.dumps(report,indent=2))
    naive=float(mean_absolute_error(test.target,test.util_now))
    metrics={'best_model':best,'all_models':{best:{'held_out_test_mae_pct':round(report['mae'],2),'held_out_test_r2':round(report['r2'],4),'cv_mae_pct':round(scores[best],2)}},'improvement_over_best_naive_pct':round((1-report['mae']/naive)*100,1),'naive_flat_mae_pct':round(naive,2),'features':FEATURES,'horizon_minutes':60,'train_rows':len(train),'test_rows':len(test),'validation_mae':scores,'training_distribution':{c:{'mean':float(train[c].mean()),'std':float(train[c].std())} for c in ['util_now','capacity']},'note':'Time-ordered validation with a one-hour purge; timestamps shared by zones stay in the same fold. Features use target clock time and only past observations. Synthetic multi-zone data; R2 is not classification accuracy.'}
    sample=np.linspace(0,len(test)-1,min(250,len(test)),dtype=int)
    metrics['prediction_scatter']={'model':best,'r2':round(report['r2'],4),'points':[{'actual':round(float(test.target.iloc[i]),2),'predicted':round(float(pred[i]),2)} for i in sample]}
    (MODEL_DIR/'forecast_model_metrics.json').write_text(json.dumps(metrics,indent=2))
    joblib.dump({'model':model,'features':FEATURES,'model_name':best,'horizon_steps':4,'feature_pipeline':'timestamp_v2'},MODEL_DIR/'utilization_forecast_model.pkl',compress=3)
if __name__=='__main__':train()
