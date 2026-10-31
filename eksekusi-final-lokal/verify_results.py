"""Verifikasi independen hasil tersimpan, bukan menjalankan ulang training."""
from pathlib import Path
import json,sys,hashlib
import numpy as np
import pandas as pd
import networkx as nx
import nbformat
from sklearn.metrics import average_precision_score,roc_auc_score,precision_score,recall_score,f1_score,confusion_matrix
from fractions import Fraction
root=Path(__file__).resolve().parent;out=root/'run-actual'
metrics=json.loads((out/'metrics.json').read_text());frozen=json.loads((out/'thresholds-frozen.json').read_text())
orders=pd.read_csv(out/'orders.csv');checks=[]
assert orders['Order Id'].is_unique
assert len(metrics)==6
for r in metrics:
    d=pd.read_csv(out/f"predictions-{r['partition']}-{r['model']}.csv",float_precision='round_trip')
    expected=orders.loc[orders.partition==r['partition']]
    assert d['Order Id'].tolist()==expected['Order Id'].tolist()
    assert d.Late_delivery_risk.tolist()==expected.Late_delivery_risk.tolist()
    y=d.Late_delivery_risk.to_numpy();p=d.probability_1.to_numpy();pred=d.prediction.to_numpy();t=frozen['thresholds'][r['model']]
    assert np.array_equal(pred,(p>=t).astype(int)) and (d.threshold==t).all()
    actual={'average_precision':average_precision_score(y,p),'roc_auc':roc_auc_score(y,p),'precision':precision_score(y,pred,zero_division=0),'recall':recall_score(y,pred,zero_division=0),'binary_f1':f1_score(y,pred,zero_division=0)}
    for key,value in actual.items(): assert np.isclose(value,r[key],atol=1e-14,rtol=0),(key,value,r[key])
    cm=confusion_matrix(y,pred,labels=[0,1]).ravel().tolist();assert cm==r['confusion_matrix'] and sum(cm)==r['n']==len(d)
    if r['partition']=='validation':
        # Referensi independen vectorized untuk seluruh threshold unik + all-negative.
        sorted_idx=np.argsort(-p,kind='stable');sp=p[sorted_idx];sy=y[sorted_idx];ends=np.flatnonzero(np.r_[sp[:-1]!=sp[1:],True]);tp=np.cumsum(sy)[ends];den=y.sum()+ends+1
        scores=2*tp/den;best=float(scores.max());best_indices=np.flatnonzero(scores==best)
        candidates=[(Fraction(2*int(tp[i]),int(den[i])),float(sp[ends[i]])) for i in best_indices]
        candidates.append((Fraction(0),float(np.nextafter(p.max(),np.inf))))
        assert max(candidates)[1]==t
    checks.append({'model':r['model'],'partition':r['partition'],'rows':len(d),'metrics_recomputed':True,'threshold_checked':True})
e=pd.read_csv(out/'graph-edges.csv',dtype={'category_id':str});summary=json.loads((out/'graph-summary.json').read_text());assert not e[['order_id','category_id']].duplicated().any();assert set(e.order_id)==set(orders['Order Id'])
assert e.source.tolist()==('order:'+e.order_id.astype(str)).tolist();assert e.target.tolist()==('category:'+e.category_id).tolist()
g=nx.from_pandas_edgelist(e,'source','target');assert g.number_of_nodes()==summary['nodes'] and g.number_of_edges()==summary['edges'];assert nx.number_connected_components(g)==summary['connected_components'];assert nx.number_of_selfloops(g)==0
original=pd.read_csv(Path(__file__).resolve().parents[1]/'data/raw/DataCoSupplyChainDataset.csv',encoding='latin1',usecols=['Order Id','Category Id','Delivery Status']);pairs=original.loc[original['Delivery Status']!='Shipping canceled',['Order Id','Category Id']].drop_duplicates();assert set(map(tuple,pairs.to_numpy()))==set((int(a),int(b)) for a,b in e[['order_id','category_id']].itertuples(index=False,name=None))
degree=pd.read_csv(out/'graph-category-degree.csv');assert all(g.degree['category:'+str(int(a))]==int(b) for a,b in degree.itertuples(index=False,name=None))
comp=pd.read_csv(out/'graph-components.csv');membership=pd.read_csv(out/'graph-component-membership.csv');assert len(membership)==len(g) and membership.node.is_unique
for i,rows in membership.groupby('component_id'):
    ns=set(rows.node);assert nx.is_connected(g.subgraph(ns));row=comp.loc[comp.component_id==i].iloc[0];assert len(ns)==row.nodes and g.subgraph(ns).number_of_edges()==row.edges
notebook=nbformat.read(root/'Assignment-II-DataCo-executed-local.ipynb',as_version=4);code=[c for c in notebook.cells if c.cell_type=='code'];assert code and all(c.execution_count for c in code);assert not any(o.output_type=='error' for c in code for o in c.outputs)
assert json.loads((out/'status.json').read_text())['exit_status']==0
result={'verification':'PASS','prediction_checks':checks,'graph_recomputed_from_edge_csv':True,'edge_pairs_match_original_source':True,'component_membership_verified':True,'notebook_executed_without_error':True,'total_prediction_rows':sum(x['rows'] for x in checks),'full_graph_nodes':len(g),'full_graph_edges':g.number_of_edges()}
(root/'verification.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
