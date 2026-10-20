"""Chronological evaluation of labeled synthetic access patterns, not real incident accuracy."""
import os
os.environ.setdefault('OMP_NUM_THREADS','4')
import sys,json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
import joblib,numpy as np,pandas as pd
from sklearn.ensemble import RandomForestClassifier,HistGradientBoostingClassifier
from sklearn.metrics import precision_score,recall_score,f1_score,confusion_matrix
from app.utils.security_analytics import _engineer_features
from app.utils.security_pattern_model import PatternScorer
from ml_models.security.train_anomaly_model import DATA_DIR,MODEL_DIR,FEATURE_COLS

def train():
    df=_engineer_features(pd.read_csv(DATA_DIR/'security_access_events.csv'))
    # Whole calendar days stay together; trailing data remains unseen during selection.
    dates=df.timestamp.dt.floor('D');unique=sorted(dates.unique())
    val_start=unique[int(len(unique)*.6)];test_start=unique[int(len(unique)*.8)]
    a=df[dates<val_start];b=df[(dates>=val_start)&(dates<test_start)];test=df[dates>=test_start]
    models={'rf_depth8':RandomForestClassifier(n_estimators=120,max_depth=8,min_samples_leaf=3,class_weight='balanced',n_jobs=4,random_state=42),'rf_depth12':RandomForestClassifier(n_estimators=120,max_depth=12,min_samples_leaf=3,class_weight='balanced',n_jobs=4,random_state=42)}
    scores={}; thresholds={}
    for name,m in models.items():
        m.fit(a[FEATURE_COLS],a.is_anomaly.astype(int))
        probabilities=m.predict_proba(b[FEATURE_COLS])[:,1]
        threshold_scores={t:float(f1_score(b.is_anomaly,probabilities>=t)) for t in [.5,.7,.8,.9,.95,.98]}
        thresholds[name]=max(threshold_scores,key=threshold_scores.get)
        scores[name]=threshold_scores[thresholds[name]]
    best=max(scores,key=scores.get);model=models[best]
    training=df[dates<test_start]
    model.fit(training[FEATURE_COLS],training.is_anomaly.astype(int))
    scorer=PatternScorer(model,thresholds[best])
    pred=scorer.predict(test[FEATURE_COLS])==-1;y=test.is_anomaly.astype(int)
    report={'model':'supervised_synthetic_'+best,'validation_f1':scores,'precision':float(precision_score(y,pred)),'recall':float(recall_score(y,pred)),'f1':float(f1_score(y,pred)),'confusion_matrix':confusion_matrix(y,pred).tolist(),'n_events':len(test),'n_train_events':len(training),'test_start':str(test_start),'feature_cols':FEATURE_COLS,'note':'Supervised random forest trained on labeled synthetic access patterns. Selected on earlier validation days and evaluated on the final 20% of days. These are demo-pattern metrics, not validated accuracy on real security incidents. Unlike the previous unsupervised detector, it learns known labeled patterns and may miss novel threats. Flags require human review.'}
    report['training_distribution']={c:{'mean':float(training[c].mean()),'std':float(training[c].std())} for c in ['hour_of_day','is_business_hours','is_weekend','access_denied','recent_denials_by_employee']}
    report['threshold']=thresholds[best]
    report['threshold_selection']='Maximum validation F1 over a fixed probability grid; final test excluded.'
    (MODEL_DIR/'model_metrics.json').write_text(json.dumps(report,indent=2))
    joblib.dump({'model':scorer,'features':FEATURE_COLS},MODEL_DIR/'anomaly_model.pkl',compress=3)
    print(json.dumps({k:v for k,v in report.items() if k not in ['training_distribution','feature_cols']},indent=2))
if __name__=='__main__':train()
