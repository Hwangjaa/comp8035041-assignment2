"""Fase 2A: kesetaraan regularisasi Spark vs scikit-learn + sensitivity.
Reuse make_orders/Features dari pipeline.py. Tidak mengubah artefak run-actual."""
import sys, json, time, hashlib
from pathlib import Path
import numpy as np, pandas as pd
sys.path.insert(0,'/Users/rafaelyudianto/Documents/COMP8035041-Assignment-II/eksekusi-final-lokal/src')
from pipeline import make_orders, Features, threshold
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, roc_auc_score
R=Path('/Users/rafaelyudianto/Documents/COMP8035041-Assignment-II')
OUT=R/'analisis-lanjutan';OUT.mkdir(exist_ok=True)
raw=pd.read_csv(R/'data/raw/DataCoSupplyChainDataset.csv',encoding='latin1',low_memory=False)
orders,items,audit=make_orders(raw);del raw
parts={p:orders.loc[orders.partition==p].copy() for p in ['train','validation','test']}
enc=Features().fit(parts['train'])
X={p:enc.transform(d) for p,d in parts.items()}
y={p:d['Late_delivery_risk'].to_numpy(dtype=int) for p,d in parts.items()}
n=len(y['train'])
res={'n_train':n,'formula':'regParam = 1/(C*n_train)','verified_docs':['spark mllib-linear-methods: lambda*R(w)+1/n*sum L; R=1/2||w||^2','sklearn logistic.py: -sum log + 0.5*alpha*w.w, alpha=1/C'],'sklearn_runs':[],'spark_runs':[]}
def sk(C,label):
    t=time.perf_counter()
    m=LogisticRegression(C=C,solver='lbfgs',max_iter=2000,tol=1e-8,random_state=42,class_weight=None).fit(X['train'],y['train'])
    dt=time.perf_counter()-t
    pv=m.predict_proba(X['validation'])[:,1];pt=m.predict_proba(X['test'])[:,1]
    d={'label':label,'C':C,'equiv_spark_regParam':1.0/(C*n),'seconds':dt,'n_iter':m.n_iter_.tolist(),
       'ap_val':float(average_precision_score(y['validation'],pv)),'ap_test':float(average_precision_score(y['test'],pt)),
       'auc_val':float(roc_auc_score(y['validation'],pv)),'auc_test':float(roc_auc_score(y['test'],pt)),
       'coef_norm':float(np.linalg.norm(m.coef_))}
    res['sklearn_runs'].append(d)
    return m,pv,pt,d
# C=1.0 (asli), C ekuivalen dengan Spark regParam=0.1, dan C lemah (regularisasi lemah)
m1,pv1,pt1,d1=sk(1.0,'C=1.0 (asli, ekuiv spark regParam=2.007e-5)')
m2,pv2,pt2,d2=sk(1.0/(0.1*n),'C=2.007e-4 (ekuiv spark regParam=0.1)')
m3,pv3,pt3,d3=sk(1e6,'C=1e6 (regularisasi lemah/sensitivity)')
np.save(OUT/'probs_sklearn_val.npy',np.vstack([pv1,pv2,pv3]))
np.save(OUT/'probs_sklearn_test.npy',np.vstack([pt1,pt2,pt3]))
# Spark: regParam=0.1 (asli), regParam=1/n (ekuiv C=1.0), regParam=0 (none)
from pyspark.sql import SparkSession, types as T
from pyspark.ml.linalg import Vectors, VectorUDT
from pyspark.ml.classification import LogisticRegression as SparkLR
spark=SparkSession.builder.master('local[2]').appName('equiv').config('spark.driver.bindAddress','127.0.0.1').config('spark.sql.shuffle.partitions','2').config('spark.default.parallelism','2').getOrCreate()
spark.sparkContext.setLogLevel('ERROR')
schema=T.StructType([T.StructField('label',T.DoubleType(),False),T.StructField('features',VectorUDT(),False)])
def sframe(p):
    mat=X[p];lab=y[p]
    return spark.createDataFrame([(float(lab[i]),Vectors.sparse(mat.shape[1],mat[i].indices.tolist(),mat[i].data.tolist())) for i in range(mat.shape[0])],schema)
sftr=sframe('train');sfva=sframe('validation');sfte=sframe('test')
sprobs={}
for rp,label in [(0.1,'regParam=0.1 (asli)'),(1.0/n,'regParam=2.007e-5 (ekuiv C=1.0)'),(0.0,'regParam=0 (none)')]:
    t=time.perf_counter()
    sm=SparkLR(regParam=rp,elasticNetParam=0.,maxIter=1000,tol=1e-8,standardization=False).fit(sftr)
    dt=time.perf_counter()-t
    def gp(sf):
        rows=sm.transform(sf).select('probability').collect();return np.array([float(r[0][1]) for r in rows])
    pv=gp(sfva);pt=gp(sfte);sprobs[rp]=(pv,pt)
    d={'label':label,'regParam':rp,'seconds':dt,'iterations':int(sm.summary.totalIterations),
       'ap_val':float(average_precision_score(y['validation'],pv)),'ap_test':float(average_precision_score(y['test'],pt)),
       'auc_val':float(roc_auc_score(y['validation'],pv)),'auc_test':float(roc_auc_score(y['test'],pt))}
    res['spark_runs'].append(d)
# perbandingan pasangan ekuivalen: sklearn C=1.0 vs spark regParam=1/n ; sklearn C=2.007e-4 vs spark 0.1
sp_v_equiv=pv2  # sklearn C=2.007e-4 vs spark 0.1  -> val
sp_t_equiv=sprobs[0.1][1]
sp_v_c1=sprobs[1.0/n][0];sp_t_c1=sprobs[1.0/n][1]
res['pair_comparison']={
 'A_sklearnC1.0_vs_sparkRegParam2.007e-5':{'corr_prob_val':float(np.corrcoef(pv1,sp_v_c1)[0,1]),'corr_prob_test':float(np.corrcoef(pt1,sp_t_c1)[0,1]),
    'dAP_test':float(average_precision_score(y['test'],pt1)-average_precision_score(y['test'],sp_t_c1)),
    'dAUC_test':float(roc_auc_score(y['test'],pt1)-roc_auc_score(y['test'],sp_t_c1))},
 'B_sklearnC2.007e-4_vs_sparkRegParam0.1':{'corr_prob_val':float(np.corrcoef(pv2,sp_v_equiv)[0,1]),'corr_prob_test':float(np.corrcoef(pt2,sp_t_equiv)[0,1]),
    'dAP_test':float(average_precision_score(y['test'],pt2)-average_precision_score(y['test'],sp_t_equiv)),
    'dAUC_test':float(roc_auc_score(y['test'],pt2)-roc_auc_score(y['test'],sp_t_equiv))},
 'note':'wall-clock bukan bukti skalabilitas; data ~96MB, local[2], filesystem lokal'}
json.dump(res,open(OUT/'A_equivalence.json','w'),indent=2)
np.save(OUT/'probs_spark_val.npy',np.vstack([sprobs[k][0] for k in [0.1,1.0/n,0.0]]))
np.save(OUT/'probs_spark_test.npy',np.vstack([sprobs[k][1] for k in [0.1,1.0/n,0.0]]))
json.dump({'test_labels':y['test'].tolist(),'val_labels':y['validation'].tolist()},open(OUT/'labels.json','w'))
spark.stop()
print(json.dumps(res,indent=2))
