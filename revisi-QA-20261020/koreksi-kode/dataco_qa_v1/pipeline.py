"""Kontrak lama + validasi item; tidak menyediakan runner training."""
import json, hashlib
from pathlib import Path
from fractions import Fraction
import numpy as np
import pandas as pd
from sklearn.metrics import average_precision_score, roc_auc_score, precision_score, recall_score, f1_score, confusion_matrix
from .features import Features

SINGLE=['Days for shipment (scheduled)','Customer Segment','Market','order date (DateOrders)','Late_delivery_risk']

def dump(p,obj):
    Path(p).parent.mkdir(parents=True,exist_ok=True)
    Path(p).write_text(json.dumps(obj,indent=2,ensure_ascii=False,default=str,allow_nan=False))

def sha(p):
    h=hashlib.sha256()
    with open(p,'rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''): h.update(b)
    return h.hexdigest()

def make_orders(d):
    required=SINGLE+['Order Id','Order Item Id','Category Id','Delivery Status']
    if set(required)-set(d): raise ValueError('Kolom wajib tidak tersedia')
    if d[['Order Id','Order Item Id','Days for shipment (scheduled)','Late_delivery_risk']].isna().any().any():
        raise ValueError('Missing numerik/identitas/target wajib: pipeline berhenti')
    cancel=d['Delivery Status'].eq('Shipping canceled')
    status=cancel.groupby(d['Order Id']).agg(['any','all'])
    mixed=status.index[status['any']!=status['all']].tolist()
    if mixed: raise ValueError('Pesanan campuran batal/nonbatal: '+str(mixed))
    keep=d.loc[~cancel,required].copy()
    item_categories=keep.groupby('Order Item Id')['Category Id'].nunique(dropna=False)
    bad_items=item_categories[item_categories>1].index.tolist()
    if bad_items:
        raise ValueError('Konflik Order Item Id ke Category Id: '+str(bad_items))
    conflicts=keep.groupby('Order Id')[SINGLE].nunique(dropna=False)
    bad=conflicts.loc[(conflicts>1).any(axis=1)]
    if len(bad): raise ValueError('Konflik singleton/target Order Id: '+bad.to_json())
    if not set(keep['Late_delivery_risk'].unique()) <= {0,1}: raise ValueError('Target bukan binary 0/1')
    for col in ['Days for shipment (scheduled)','Order Id','Order Item Id']:
        if not np.isfinite(keep[col].to_numpy(dtype=float)).all(): raise ValueError('Numerik nonfinite: '+col)
    orders=keep.groupby('Order Id',sort=True)[SINGLE].first()
    orders['item_count']=keep.groupby('Order Id')['Order Item Id'].nunique()
    orders['categories']=keep.groupby('Order Id')['Category Id'].apply(lambda s:sorted(set('MISSING' if pd.isna(v) else str(int(v)) for v in s)))
    orders['order_date']=pd.to_datetime(orders.pop('order date (DateOrders)'),format='%m/%d/%Y %H:%M',errors='raise')
    if orders['order_date'].isna().any(): raise ValueError('Tanggal pesanan missing')
    orders['partition']=np.where(orders.order_date<pd.Timestamp('2017-07-01'),'train',np.where(orders.order_date<pd.Timestamp('2017-10-01'),'validation','test'))
    return orders.reset_index(),keep,{'source_rows':len(d),'source_orders':int(d['Order Id'].nunique()),'excluded_items':int(cancel.sum()),'excluded_orders':int(status['all'].sum()),'mixed_orders':len(mixed),'retained_items':len(keep),'retained_orders':len(orders),'singleton_conflicts':0,'label_conflicts':0,'missing_category_items':int(keep['Category Id'].isna().sum())}

def threshold(y,p):
    y=np.asarray(y,dtype=int);p=np.asarray(p,dtype=float)
    order=np.argsort(-p,kind='stable');y=y[order];p=p[order]
    best=Fraction(0);t=float(np.nextafter(p.max(),np.inf));positive=int(y.sum());tp=0;start=0
    while start<len(y):
        end=start+1
        while end<len(y) and p[end]==p[start]:end+=1
        tp+=int(y[start:end].sum());f=Fraction(2*tp,positive+end) if positive+end else Fraction(0)
        if f>best or (f==best and p[start]>t):best=f;t=float(p[start])
        start=end
    return t

def evaluate(y,p,t):
    y=np.asarray(y,dtype=int);p=np.asarray(p,dtype=float);pred=(p>=t).astype(int)
    assert len(y)==len(p) and np.isfinite(p).all() and ((p>=0)&(p<=1)).all()
    cm=confusion_matrix(y,pred,labels=[0,1]).ravel().astype(int).tolist()
    assert sum(cm)==len(y)
    return dict(n=len(y),average_precision=float(average_precision_score(y,p)),roc_auc=float(roc_auc_score(y,p)),precision=float(precision_score(y,pred,zero_division=0)),recall=float(recall_score(y,pred,zero_division=0)),binary_f1=float(f1_score(y,pred,zero_division=0)),confusion_matrix=cm,confusion_matrix_order=['TN','FP','FN','TP'],threshold=float(t),undefined=['precision'] if not pred.sum() else [])
