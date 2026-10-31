"""Fase 2B: evaluasi bermakna keputusan - precision@k/recall@k/lift, PR & ROC, bootstrap CI.
Memuat probabilitas dari A (sklearn C=1.0 & spark regParam=0.1 sebagai model primer)."""
import json
from pathlib import Path
import numpy as np
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from sklearn.metrics import average_precision_score, roc_auc_score, precision_recall_curve, roc_curve
R=Path('/Users/rafaelyudianto/Documents/COMP8035041-Assignment-II')
OUT=R/'analisis-lanjutan'
lab=json.load(open(OUT/'labels.json'));yval=np.array(lab['val_labels']);ytest=np.array(lab['test_labels'])
sk=np.load(OUT/'probs_sklearn_test.npy');sp=np.load(OUT/'probs_spark_test.npy')
skv=np.load(OUT/'probs_sklearn_val.npy');spv=np.load(OUT/'probs_spark_val.npy')
models={'sklearn_lr':(sk[0],skv[0]),'spark_lr':(sp[0],spv[0])}
prev=float(ytest.mean())
res={'prevalence_test':prev,'test_n':int(len(ytest)),'test_pos':int(ytest.sum()),'models':{}}
rng=np.random.default_rng(42)
def topk_metrics(y,p,k):
    thr=np.quantile(p,1-k)
    sel=p>=thr
    nsel=int(sel.sum())
    tp=int((sel&(y==1)).sum())
    prec=tp/nsel if nsel else 0.0
    rec=tp/int(y.sum())
    return {'k':k,'threshold':float(thr),'n_selected':nsel,'precision_at_k':prec,'recall_at_k':rec,'lift':prec/prev,'confusion_at_k':{'TP':tp,'FP':nsel-tp,'FN':int(y.sum())-tp,'TN':int((~sel&(y==0)).sum())}}
def boot_ci(y,p,metric,seed=42,B=1000):
    rng=np.random.default_rng(seed);vals=[]
    for _ in range(B):
        idx=rng.integers(0,len(y),len(y))
        yy=y[idx];pp=p[idx]
        if yy.sum()==0 or yy.sum()==len(yy):continue
        vals.append(metric(yy,pp))
    vals=np.array(vals)
    return {'mean':float(vals.mean()),'lo95':float(np.percentile(vals,2.5)),'hi95':float(np.percentile(vals,97.5)),'B':len(vals)}
for name,(p, pv) in models.items():
    ap=float(average_precision_score(ytest,p));auc=float(roc_auc_score(ytest,p))
    d={'ap_test':ap,'auc_test':auc,'topk':[topk_metrics(ytest,p,k) for k in (0.10,0.20,0.30)],
       'bootstrap':{'average_precision':boot_ci(ytest,p,average_precision_score),
                    'roc_auc':boot_ci(ytest,p,roc_auc_score),
                    'precision_at_20pct':boot_ci(ytest,p,lambda yy,pp:topk_metrics(yy,pp,0.20)['precision_at_k'])}}
    # target-recall threshold from VALIDATION (frozen), applied to test
    for target in (0.80,0.90):
        order=np.argsort(-pv);ys=yval[order];cum=np.cumsum(ys)/ys.sum()
        i=int(np.argmax(cum>=target));thr=float(pv[order][i])
        sel=p>=thr;tp=int((sel&(ytest==1)).sum());ns=int(sel.sum())
        d[f'recall{int(target*100)}_threshold_val']={'threshold':thr,'test_precision':tp/ns if ns else 0.0,'test_recall':tp/int(ytest.sum()),'test_selected':ns,'test_lift':(tp/ns)/prev if ns else 0.0}
    res['models'][name]=d
# curves
fig,ax=plt.subplots(1,2,figsize=(11,4.5))
for name,(p,_) in models.items():
    pr,rc,_=precision_recall_curve(ytest,p);ax[0].plot(rc,pr,label=f'{name} (AP={average_precision_score(ytest,p):.3f})')
    fpr,tpr,_=roc_curve(ytest,p);ax[1].plot(fpr,tpr,label=f'{name} (AUC={roc_auc_score(ytest,p):.3f})')
ax[0].axhline(prev,ls='--',c='gray',label=f'prevalensi={prev:.3f}');ax[0].set_xlabel('Recall');ax[0].set_ylabel('Precision');ax[0].set_title('Kurva Precision-Recall (test)');ax[0].legend(fontsize=8)
ax[1].plot([0,1],[0,1],ls='--',c='gray');ax[1].set_xlabel('False Positive Rate');ax[1].set_ylabel('True Positive Rate');ax[1].set_title('Kurva ROC (test)');ax[1].legend(fontsize=8)
fig.tight_layout();fig.savefig(OUT/'B_pr_roc_test.png',dpi=170);plt.close(fig)
json.dump(res,open(OUT/'B_decision.json','w'),indent=2)
print(json.dumps(res,indent=2))
