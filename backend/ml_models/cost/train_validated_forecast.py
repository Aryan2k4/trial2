import os
os.environ.setdefault('OMP_NUM_THREADS','4')
import sys,json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
import numpy as np,pandas as pd,joblib
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import Ridge,HuberRegressor
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import TimeSeriesSplit
from sklearn.metrics import mean_absolute_error,r2_score
from app.utils.spend_model import RecentSpendRegressor
from ml_models.cost.train_forecast_model import build_weekly_series,engineer_features,FEATURES,DATA_PATH,MODEL_DIR

def train():
    e=engineer_features(build_weekly_series(pd.read_csv(DATA_PATH)))
    train=e.iloc[:-7];test=e.iloc[-5:] # purge 2 rows: targets span 3 future weeks
    models={'last_week':RecentSpendRegressor(),'recent_median':RecentSpendRegressor('roll3_median'),'ridge_1':make_pipeline(StandardScaler(),Ridge(alpha=1)),'ridge_100':make_pipeline(StandardScaler(),Ridge(alpha=100)),'huber':make_pipeline(StandardScaler(),HuberRegressor(max_iter=500)),'random_forest':RandomForestRegressor(n_estimators=200,max_depth=3,random_state=42,n_jobs=4)}
    scores={}
    for name,m in models.items():
        errors=[]
        for a,b in TimeSeriesSplit(n_splits=3,gap=2).split(train):
            m.fit(train.iloc[a][FEATURES],train.iloc[a].target)
            p=np.maximum(0,np.expm1(m.predict(train.iloc[b][FEATURES])))
            errors.append(mean_absolute_error(np.expm1(train.iloc[b].target),p))
        scores[name]=float(np.mean(errors))
    best=min(scores,key=scores.get);model=models[best].fit(train[FEATURES],train.target)
    p=np.maximum(0,np.expm1(model.predict(test[FEATURES])));y=np.expm1(test.target)
    report={'selected':best,'validation_mae':scores,'mae':float(mean_absolute_error(y,p)),'r2':float(r2_score(y,p)),'test_weeks':len(test),'train_weeks':len(train),'points':[{'actual':float(a),'predicted':float(b)} for a,b in zip(y,p)]}
    print(json.dumps(report,indent=2))
    (MODEL_DIR/'experiment_report.json').write_text(json.dumps(report,indent=2))
    # Candidate was worse on the benchmark; do not replace the deployed artifact.
if __name__=='__main__':train()
