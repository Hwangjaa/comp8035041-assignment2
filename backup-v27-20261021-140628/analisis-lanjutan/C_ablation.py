"""Fase 2C: uji sumber sinyal (ablation) + leakage + model non-linear + importance.
sklearn saja untuk non-linear (waktu); Spark MLlib non-linear dicatat sebagai tidak dijalankan."""
import sys, json, time
from pathlib import Path
import numpy as np, pandas as pd
sys.path.insert(0,'/Users/rafaelyudianto/Documents/COMP8035041-Assignment-II/eksekusi-final-lokal/src')
from pipeline import make_orders, Features
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.metrics import average_precision_score, roc_auc_score
R=Path('/Users/rafaelyudianto/Documents/COMP8035041-Assignment-II')
OUT=R/'analisis-lanjutan'
raw=pd.read_csv(R/'data/raw/DataCoSupplyChainDataset.csv',encoding='latin1',low_memory=False)
orders,items,audit=make_orders(raw);del raw
parts={p:orders.loc[orders.partition==p].copy() for p in ['train','validation','test']}
enc=Features().fit(parts['train'])
X={p:enc.transform(d) for p,d in parts.items()};y={p:d['Late_delivery_risk'].to_numpy(dtype=int) for p,d in parts.items()}
names=enc.names
idx_sched=[names.index('Days for shipment (scheduled)')]
idx_cnt=[names.index('unique_Order_Item_Id_count')]
idx_seg=[i for i,n in enumerate(names) if n.startswith('Customer Segment=')]
idx_mkt=[i for i,n in enumerate(names) if n.startswith('Market=')]
idx_cat=[i for i,n in enumerate(names) if n.startswith('Category Id=')]
allidx=list(range(len(names)))
subsets={'jadwal saja':idx_sched,'tanpa jadwal':[i for i in allidx if i not in idx_sched],
         'kategori saja':idx_cat,'segmen+market saja':idx_seg+idx_mkt,'semua fitur':allidx,
         'jadwal+jumlah item':idx_sched+idx_cnt}
res={'feature_groups':{'schedule':idx_sched,'count':idx_cnt,'segment':idx_seg,'market':idx_mkt,'category':idx_cat},
     'leakage_signal':{'scheduled_unique_values':sorted(set(orders['Days for shipment (scheduled)'].dropna().astype(int))),
        'shipping_mode_known_at_order_time':True,
        'note':'Days for shipment (scheduled) deterministik oleh Shipping Mode (dicek di fase0); bukan outcome/durasi aktual'},
     'ablation_sklearn_lr_C1':{},'nonlinear':{}}
def fit_eval(Xtr,Xva,Xte,name,C=1.0):
    t=time.perf_counter()
    m=LogisticRegression(C=C,solver='lbfgs',max_iter=2000,tol=1e-8,random_state=42).fit(Xtr,y['train'])
    dt=time.perf_counter()-t
    pv=m.predict_proba(Xva)[:,1];pt=m.predict_proba(Xte)[:,1]
    return {'n_features':int(Xtr.shape[1]),'seconds':dt,
            'ap_val':float(average_precision_score(y['validation'],pv)),'ap_test':float(average_precision_score(y['test'],pt)),
            'auc_test':float(roc_auc_score(y['test'],pt))},m
for label,cols in subsets.items():
    d,_=fit_eval(X['train'][:,cols],X['validation'][:,cols],X['test'][:,cols],label)
    res['ablation_sklearn_lr_C1'][label]=d
# non-linear pada semua fitur
for label,mdl in [('RandomForest',RandomForestClassifier(n_estimators=300,max_depth=None,min_samples_leaf=5,random_state=42,n_jobs=2)),
                  ('GradientBoosting',GradientBoostingClassifier(n_estimators=200,max_depth=3,learning_rate=0.1,random_state=42))]:
    t=time.perf_counter();mdl.fit(X['train'],y['train']);dt=time.perf_counter()-t
    pv=mdl.predict_proba(X['validation'])[:,1];pt=mdl.predict_proba(X['test'])[:,1]
    res['nonlinear'][label]={'seconds':dt,'ap_val':float(average_precision_score(y['validation'],pv)),'ap_test':float(average_precision_score(y['test'],pt)),'auc_test':float(roc_auc_score(y['test'],pt))}
    imp=mdl.feature_importances_
    res['nonlinear'][label]['top10_importance']=sorted([{'feature':names[i],'importance':float(imp[i])} for i in np.argsort(-imp)[:10]],key=lambda x:-x['importance'])
# koefisien LR pada semua fitur
m=LogisticRegression(C=1.0,solver='lbfgs',max_iter=2000,tol=1e-8,random_state=42).fit(X['train'],y['train'])
coef=m.coef_[0]
res['lr_coefficients_top10']=sorted([{'feature':names[i],'coef':float(coef[i])} for i in np.argsort(-np.abs(coef))[:10]],key=lambda x:-abs(x['coef']))
res['nonlinear_note']='Spark MLlib GBT/RF tidak dijalankan (waktu); dicatat sebagai keterbatasan'
json.dump(res,open(OUT/'C_ablation.json','w'),indent=2)
print(json.dumps(res,indent=2))
