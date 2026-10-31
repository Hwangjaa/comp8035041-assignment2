"""Ablation (verifikasi 5.8) + uji spesifikasi jadwal (langkah 5)."""
import sys, json
from pathlib import Path
import numpy as np, pandas as pd
from scipy import sparse
sys.path.insert(0,'/Users/rafaelyudianto/Documents/COMP8035041-Assignment-II/eksekusi-final-lokal/src')
from pipeline import make_orders, Features
from sklearn.linear_model import LogisticRegression
from sklearn.dummy import DummyClassifier
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.metrics import average_precision_score, roc_auc_score
R=Path('/Users/rafaelyudianto/Documents/COMP8035041-Assignment-II');OUT=R/'analisis-lanjutan'
raw=pd.read_csv(R/'data/raw/DataCoSupplyChainDataset.csv',encoding='latin1',low_memory=False)
orders,items,audit=make_orders(raw);del raw
parts={p:orders.loc[orders.partition==p].copy() for p in ['train','validation','test']}
enc=Features().fit(parts['train']);X={p:enc.transform(d) for p,d in parts.items()}
y={p:d['Late_delivery_risk'].to_numpy(dtype=int) for p,d in parts.items()}
names=enc.names;seed=42
def wilson(p,n,z=1.96):
    if n==0:return (0.,0.)
    d=1+z*z/n;c=p+z*z/(2*n);h=z*np.sqrt(p*(1-p)/n+z*z/(4*n*n));return ((c-h)/d,(c+h)/d)
res={'seed':seed}
# --- ablation ---
idx_s=[names.index('Days for shipment (scheduled)')];idx_c=[names.index('unique_Order_Item_Id_count')]
idx_seg=[i for i,x in enumerate(names) if x.startswith('Customer Segment=')]
idx_mkt=[i for i,x in enumerate(names) if x.startswith('Market=')]
idx_cat=[i for i,x in enumerate(names) if x.startswith('Category Id=')]
allidx=list(range(len(names)))
subs={'jadwal saja':idx_s,'jadwal+jumlah item':idx_s+idx_c,'kategori saja':idx_cat,'segmen+market saja':idx_seg+idx_mkt,'tanpa jadwal':[i for i in allidx if i not in idx_s],'semua fitur':allidx}
def fit(Xtr,ytr,cols):
    m=LogisticRegression(C=1.,solver='lbfgs',max_iter=3000,tol=1e-8,random_state=seed).fit(Xtr[:,cols],ytr)
    return m
abl={}
for lbl,cols in subs.items():
    m=fit(X['train'],y['train'],cols)
    pv=m.predict_proba(X['validation'][:,cols])[:,1];pt=m.predict_proba(X['test'][:,cols])[:,1]
    const=bool(np.allclose(pt,pt[0]))
    abl[lbl]={'n_features':len(cols),'ap_test':float(average_precision_score(y['test'],pt)),'auc_test':float(roc_auc_score(y['test'],pt)),
              'constant_prediction':const,'distinct_prob_test':int(len(np.unique(np.round(pt,12))))}
# baseline + RF/GBT
b=DummyClassifier(strategy='prior',random_state=seed).fit(X['train'],y['train'])
pb=b.predict_proba(X['test'])[:,1]
abl['baseline (prior)']={'n_features':0,'ap_test':float(average_precision_score(y['test'],pb)),'auc_test':float(roc_auc_score(y['test'],pb)),'constant_prediction':True,'distinct_prob_test':1}
rf=RandomForestClassifier(n_estimators=300,max_depth=None,min_samples_leaf=5,max_features='sqrt',random_state=seed,n_jobs=2,warm_start=False).fit(X['train'],y['train'])
gb=GradientBoostingClassifier(n_estimators=200,max_depth=3,learning_rate=0.1,subsample=1.0,random_state=seed).fit(X['train'],y['train'])
for lbl,m in [('Random Forest',rf),('Gradient Boosting',gb)]:
    pt=m.predict_proba(X['test'])[:,1]
    abl[lbl]={'n_features':len(names),'ap_test':float(average_precision_score(y['test'],pt)),'auc_test':float(roc_auc_score(y['test'],pt)),'constant_prediction':bool(np.allclose(pt,pt[0])),'distinct_prob_test':int(len(np.unique(np.round(pt,12))))}
res['ablation']=abl;res['ablation_params']={'RandomForest':{'n_estimators':300,'min_samples_leaf':5,'max_features':'sqrt','max_depth':None,'seed':seed},
  'GradientBoosting':{'n_estimators':200,'max_depth':3,'learning_rate':0.1,'subsample':1.0,'seed':seed},'no_test_tuning':True}
# bootstrap CI untuk ablation (sklearn LR saja untuk hemat waktu)
def boot(y,p,B=1000):
    r=np.random.default_rng(seed);v=[]
    for _ in range(B):
        i=r.integers(0,len(y),len(y));yy=y[i];pp=p[i]
        if yy.sum() in (0,len(yy)):continue
        v.append(average_precision_score(yy,pp))
    v=np.array(v);return {'lo95':float(np.percentile(v,2.5)),'hi95':float(np.percentile(v,97.5))}
res['ablation_ci']={}
for lbl,cols in list(subs.items()):
    m=fit(X['train'],y['train'],cols);pt=m.predict_proba(X['test'][:,cols])[:,1]
    res['ablation_ci'][lbl]=boot(y['test'],pt)
# --- uji spesifikasi jadwal ---
tr=parts['train']
sched=tr['Days for shipment (scheduled)'].to_numpy()
res['schedule_rate']={}
for v in sorted(set(orders['Days for shipment (scheduled)'].dropna().astype(int))):
    sub=orders[orders['Days for shipment (scheduled)']==v]
    p=float(sub['Late_delivery_risk'].mean());nn=len(sub)
    res['schedule_rate'][f'scheduled={v}']={'n':int(nn),'late_rate':p,'ci95':[float(x) for x in wilson(p,nn)]}
res['mode_rate']={}
_raw=pd.read_csv(R/'data/raw/DataCoSupplyChainDataset.csv',encoding='latin1',low_memory=False,usecols=['Order Id','Shipping Mode','Delivery Status'])
_raw=_raw[_raw['Delivery Status'].astype(str).str.strip().str.lower()!='shipping canceled']
_mode=_raw.groupby('Order Id')['Shipping Mode'].first()
orders['Shipping Mode']=orders['Order Id'].map(_mode)
del _raw
for v in sorted(orders['Shipping Mode'].dropna().unique()):
    sub=orders[orders['Shipping Mode']==v];p=float(sub['Late_delivery_risk'].mean());nn=len(sub)
    res['mode_rate'][v]={'n':int(nn),'late_rate':p,'ci95':[float(x) for x in wilson(p,nn)],
        'scheduled_value':int(sub['Days for shipment (scheduled)'].iloc[0])}
# LR dengan jadwal sebagai one-hot (varian eksplisit)
vals=[0,1,2,4]
def onehot(part):
    s=X[part][:,0].toarray().ravel()
    cols=[(s==v).astype(float) for v in vals]
    return sparse.hstack([sparse.csr_matrix(np.column_stack(cols)),X[part][:,1:]]).tocsr()
Xoh={p:onehot(p) for p in X}
moh=LogisticRegression(C=1.,solver='lbfgs',max_iter=3000,tol=1e-8,random_state=seed).fit(Xoh['train'],y['train'])
poh=moh.predict_proba(Xoh['test'])[:,1]
res['schedule_onehot_variant']={'features':'jadwal one-hot (0/1/2/4) menggantikan jadwal numerik + fitur lain',
  'ap_test':float(average_precision_score(y['test'],poh)),'auc_test':float(roc_auc_score(y['test'],poh)),
  'ap_ci':boot(y['test'],poh),'decision':'perlu keputusan pemilik: ganti desain utama atau tetap sebagai eksperimen tambahan'}
json.dump(res,open(OUT/'G_ablation_schedule.json','w'),indent=2)
print(json.dumps({k:res[k] for k in ['ablation','schedule_rate','mode_rate','schedule_onehot_variant']},indent=2))
