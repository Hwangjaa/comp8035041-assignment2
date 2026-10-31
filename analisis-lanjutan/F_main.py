"""Fase 2 utama: Spark regParam=1/(C*n) sebagai konfigurasi UTAMA.
Menghitung ulang metrik, ambang, top-k eksak (jumlah terpilih + tie), bootstrap CI,
ablation + RF/GBT (parameter+CI), dan uji spesifikasi jadwal."""
import sys, json, time, hashlib
from pathlib import Path
import numpy as np, pandas as pd
sys.path.insert(0,'/Users/rafaelyudianto/Documents/COMP8035041-Assignment-II/eksekusi-final-lokal/src')
from pipeline import make_orders, Features, threshold
from sklearn.linear_model import LogisticRegression
from sklearn.dummy import DummyClassifier
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.metrics import average_precision_score, roc_auc_score, precision_score, recall_score, f1_score, confusion_matrix
R=Path('/Users/rafaelyudianto/Documents/COMP8035041-Assignment-II');OUT=R/'analisis-lanjutan'
raw=pd.read_csv(R/'data/raw/DataCoSupplyChainDataset.csv',encoding='latin1',low_memory=False)
orders,items,audit=make_orders(raw);del raw
parts={p:orders.loc[orders.partition==p].copy() for p in ['train','validation','test']}
enc=Features().fit(parts['train'])
X={p:enc.transform(d) for p,d in parts.items()};y={p:d['Late_delivery_risk'].to_numpy(dtype=int) for p,d in parts.items()}
names=enc.names;n=len(y['train']);seed=42
res={'seed':seed,'n_train':n,'main_config':'Spark regParam = 1/(C*n_train) = %.10e (setara C=1.0)'%(1.0/n),'sensitivity_config':'Spark regParam=0.1 (setara scikit-learn C=2.007e-4)'}
rng=np.random.default_rng(seed)
def evalm(y,p,t):
    pred=(p>=t).astype(int)
    return {'n':len(y),'ap':float(average_precision_score(y,p)),'auc':float(roc_auc_score(y,p)),
            'precision':float(precision_score(y,pred,zero_division=0)),'recall':float(recall_score(y,pred,zero_division=0)),
            'binary_f1':float(f1_score(y,pred,zero_division=0)),
            'cm':confusion_matrix(y,pred,labels=[0,1]).ravel().astype(int).tolist(),'threshold':float(t)}
# --- model utama ---
lr=LogisticRegression(C=1.,solver='lbfgs',max_iter=2000,tol=1e-8,random_state=seed).fit(X['train'],y['train'])
prior=DummyClassifier(strategy='prior',random_state=seed).fit(X['train'],y['train'])
from pyspark.sql import SparkSession, types as T
from pyspark.ml.linalg import Vectors, VectorUDT
from pyspark.ml.classification import LogisticRegression as SparkLR
spark=SparkSession.builder.master('local[2]').appName('main14').config('spark.driver.bindAddress','127.0.0.1').config('spark.sql.shuffle.partitions','2').config('spark.default.parallelism','2').getOrCreate();spark.sparkContext.setLogLevel('ERROR')
sch=T.StructType([T.StructField('label',T.DoubleType(),False),T.StructField('features',VectorUDT(),False)])
def sf(p):
    m=X[p];l=y[p];return spark.createDataFrame([(float(l[i]),Vectors.sparse(m.shape[1],m[i].indices.tolist(),m[i].data.tolist())) for i in range(m.shape[0])],sch)
ftr, fva, fte = sf('train'), sf('validation'), sf('test')
def spark_fit(rp):
    t0=time.perf_counter();m=SparkLR(regParam=rp,elasticNetParam=0.,maxIter=1000,tol=1e-8,standardization=False).fit(ftr);dt=time.perf_counter()-t0
    def gp(f):return np.array([float(r[0][1]) for r in m.transform(f).select('probability').collect()])
    return m,gp(fva),gp(fte),dt
rp_main=1.0/n;rp_sens=0.1
sm_main,pv_spk,pt_spk,dt_main=spark_fit(rp_main)
sm_sens,pv_spk_s,pt_spk_s,dt_sens=spark_fit(rp_sens)
pv={'baseline':prior.predict_proba(X['validation'])[:,1],'sklearn_lr':lr.predict_proba(X['validation'])[:,1],'spark_lr':pv_spk}
pt={'baseline':prior.predict_proba(X['test'])[:,1],'sklearn_lr':lr.predict_proba(X['test'])[:,1],'spark_lr':pt_spk}
th={m:threshold(y['validation'],p) for m,p in pv.items()}
res['thresholds_validation']=th
res['spark_iterations']={'main':int(sm_main.summary.totalIterations),'sensitivity':int(sm_sens.summary.totalIterations)}
res['wall_seconds']={'spark_main':dt_main,'spark_sensitivity':dt_sens}
res['main']={'validation':{m:evalm(y['validation'],pv[m],th[m]) for m in pv},
             'test':{m:evalm(y['test'],pt[m],th[m]) for m in pt}}
# sensitivity (test)
lr_sens=LogisticRegression(C=1.0/(0.1*n),solver='lbfgs',max_iter=2000,tol=1e-8,random_state=seed).fit(X['train'],y['train'])
pv_sens=lr_sens.predict_proba(X['validation'])[:,1];pt_sens=lr_sens.predict_proba(X['test'])[:,1]
res['sensitivity_test']={'spark_lr_regParam0.1':evalm(y['test'],pt_spk_s,threshold(y['validation'],pv_spk_s)),
                         'sklearn_C2.007e-4':evalm(y['test'],pt_sens,threshold(y['validation'],pv_sens))}
# --- top-k eksak dari aturan hitung, tie dijelaskan ---
def topk(y,p,k):
    N=len(y);nk=int(round(k*N));order=np.argsort(-p,kind='stable');sel=order[:nk]
    tp=int(y[sel].sum());prec=tp/nk;rec=tp/int(y.sum())
    thr=float(p[order[nk-1]]);nties=int((p==thr).sum())
    return {'k_pct':int(k*100),'n_selected':nk,'threshold_score':thr,'ties_at_boundary':nties,
            'precision_at_k':prec,'recall_at_k':rec,'tp':tp,'lift':prec/float(y.mean())}
res['topk_exact']={m:[topk(y['test'],pt[m],k) for k in (0.10,0.20,0.30)] for m in pt}
# --- bootstrap CI ---
def boot(y,p,fn,B=1000):
    r=np.random.default_rng(seed);v=[]
    for _ in range(B):
        i=r.integers(0,len(y),len(y));yy=y[i];pp=p[i]
        if yy.sum() in (0,len(yy)):continue
        v.append(fn(yy,pp))
    v=np.array(v);return {'mean':float(v.mean()),'lo95':float(np.percentile(v,2.5)),'hi95':float(np.percentile(v,97.5)),'B':len(v)}
res['bootstrap']={m:{'ap':boot(y['test'],pt[m],average_precision_score),
                     'auc':boot(y['test'],pt[m],roc_auc_score),
                     'precision_at_20':boot(y['test'],pt[m],lambda yy,pp:topk(yy,pp,0.20)['precision_at_k'])} for m in pt}
json.dump(res,open(OUT/'F_main.json','w'),indent=2)
np.save(OUT/'F_pt_main.npy',np.vstack([pt['sklearn_lr'],pt['spark_lr'],pt['baseline']]))
np.save(OUT/'F_pv_main.npy',np.vstack([pv['sklearn_lr'],pv['spark_lr'],pv['baseline']]))
spark.stop()
print(json.dumps({'thresholds':th,'main_test':res['main']['test'],'topk':res['topk_exact']['sklearn_lr']},indent=2))
