import os
os.environ.setdefault('MPLCONFIGDIR',os.path.join(os.environ.get('TMPDIR','.'),'dataco-mpl'))
import json, sys, hashlib, platform, subprocess, traceback, logging
from pathlib import Path
from datetime import datetime, timezone
from fractions import Fraction
import numpy as np
import pandas as pd
from scipy import sparse
from sklearn.linear_model import LogisticRegression
from sklearn.dummy import DummyClassifier
from sklearn.metrics import average_precision_score, roc_auc_score, precision_score, recall_score, f1_score, confusion_matrix
import networkx as nx

SINGLE=['Days for shipment (scheduled)','Customer Segment','Market','order date (DateOrders)','Late_delivery_risk']
KNOWN_DELIVERY_STATUSES={'Advance shipping','Late delivery','Shipping canceled','Shipping on time'}

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
    if d['Delivery Status'].isna().any():
        raise ValueError('Delivery Status missing: pipeline berhenti')
    unknown_status=sorted(set(d['Delivery Status'].astype(str))-KNOWN_DELIVERY_STATUSES)
    if unknown_status:
        raise ValueError('Delivery Status tidak dikenal: '+str(unknown_status))
    cancel=d['Delivery Status'].eq('Shipping canceled')
    status=cancel.groupby(d['Order Id']).agg(['any','all'])
    mixed=status.index[status['any']!=status['all']].tolist()
    if mixed: raise ValueError('Pesanan campuran batal/nonbatal: '+str(mixed))
    keep=d.loc[~cancel,required].copy()
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

class Features:
    def fit(self,train):
        self.vocab={}
        for c in ['Customer Segment','Market']:
            self.vocab[c]=sorted(set(train[c].dropna().astype(str))|{'MISSING','UNKNOWN'})
        self.vocab['Category Id']=sorted(set(v for row in train.categories for v in row)|{'MISSING','UNKNOWN'})
        self.names=['Days for shipment (scheduled)','unique_Order_Item_Id_count']+[c+'='+v for c,vs in self.vocab.items() for v in vs]
        self.fit_order_ids=train['Order Id'].astype(int).tolist()
        return self
    def transform(self,d):
        rows=[];cols=[];values=[]
        numeric=d[['Days for shipment (scheduled)','item_count']].to_numpy(dtype=float)
        if not np.isfinite(numeric).all(): raise ValueError('Missing/nonfinite numerik')
        for i in range(len(d)):
            for j in range(2): rows.append(i);cols.append(j);values.append(numeric[i,j])
        offset=2
        for c,vs in self.vocab.items():
            lookup={v:j for j,v in enumerate(vs)}
            for i,(_,row) in enumerate(d.iterrows()):
                tokens=row.categories if c=='Category Id' else ['MISSING' if pd.isna(row[c]) else str(row[c])]
                mapped=set(v if v in lookup else 'UNKNOWN' for v in tokens)
                for v in mapped: rows.append(i);cols.append(offset+lookup[v]);values.append(1.)
            offset+=len(vs)
        return sparse.csr_matrix((values,(rows,cols)),shape=(len(d),len(self.names)))

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

def run(root,out):
    root=Path(root).resolve();out=Path(out).resolve();out.mkdir(parents=True,exist_ok=True)
    logging.basicConfig(level=logging.INFO,format='%(asctime)s %(levelname)s %(message)s',handlers=[logging.FileHandler(out/'execution.log'),logging.StreamHandler(sys.stdout)],force=True)
    started=datetime.now(timezone.utc).isoformat()
    config={'started_utc':started,'seed':42,'split':{'train':'order_date < 2017-07-01','validation':'2017-07-01 <= order_date < 2017-10-01','test':'order_date >= 2017-10-01'},'gap':'none; label maturation unknown','benchmark':'not performed','feature_groups':['Days for shipment (scheduled)','Customer Segment','Market','Category Id multi-hot','unique Order Item Id count'],'threshold':'validation binary F1 maximum; ties largest; >=; all-negative candidate included','refit':False,'storage':'Colab VM local file:///; not HDFS','evaluation_scope':'Retrospective conditional cohort: orders known from final status as not Shipping canceled; feature availability as-of prediction time is not established.'}
    dump(out/'config.json',config)
    try:
        logging.info('A: audit sumber dan environment')
        manifest=json.loads((root/'data/source-manifest.json').read_text());data_manifest=[]
        required_name='DataCoSupplyChainDataset.csv'
        selected=[f for f in manifest['files'] if Path(f['file']).name==required_name]
        if len(selected)!=1: raise ValueError('Manifest harus memuat tepat satu '+required_name)
        for f in selected:
            path=root/'data/raw'/Path(f['file']).name
            digest=sha(path)
            if digest!=f['sha256']:raise ValueError('SHA256 mismatch '+str(path))
            parsed=pd.read_csv(path,encoding='latin1',low_memory=False)
            data_manifest.append({'file':str(path),'bytes':path.stat().st_size,'sha256':digest,'matches_prior_manifest':True,'rows':len(parsed),'columns':len(parsed.columns),'schema':{c:str(t) for c,t in parsed.dtypes.items()}})
        dump(out/'data-manifest.json',{'source':manifest['source'],'comparison':'SHA-256 dibandingkan dengan manifest sumber lokal yang telah diverifikasi; retrieval Colab dapat memakai mirror byte-identik','files':data_manifest})
        import sklearn, scipy, pyspark, matplotlib
        env={'python':sys.version,'executable':sys.executable,'platform':platform.platform(),'versions':{m.__name__:m.__version__ for m in [pd,np,sklearn,scipy,pyspark,nx,matplotlib]},'java':subprocess.run([str(Path(os.environ['JAVA_HOME'])/'bin/java'),'-version'],capture_output=True,text=True).stderr,'thread_environment':{k:os.environ.get(k) for k in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS']}}
        dump(out/'environment.json',env)
        (out/'requirements-observed.txt').write_text(subprocess.run([sys.executable,'-m','pip','freeze'],capture_output=True,text=True).stdout)
        raw=pd.read_csv(root/'data/raw/DataCoSupplyChainDataset.csv',encoding='latin1',low_memory=False)
        orders,items,audit=make_orders(raw)
        del raw
        dump(out/'audit-orders.json',audit)
        orders.assign(categories=orders.categories.map(json.dumps)).to_csv(out/'orders.csv',index=False)
        split=orders.groupby(['partition','Late_delivery_risk']).size().unstack(fill_value=0).reindex(['train','validation','test']);split.columns=['label_0','label_1'];split['total']=split.sum(axis=1);split.to_csv(out/'split.csv')
        assert orders['Order Id'].is_unique and int(split.total.sum())==len(orders)
        parts={p:orders.loc[orders.partition==p].copy() for p in ['train','validation','test']}
        enc=Features().fit(parts['train']);X={p:enc.transform(d) for p,d in parts.items()};y={p:d['Late_delivery_risk'].to_numpy(dtype=int) for p,d in parts.items()}
        dump(out/'feature-contract.json',{'vocabulary':enc.vocab,'feature_names':enc.names,'n_features':len(enc.names),'fit_partition':'train','fit_order_ids_sha256':hashlib.sha256(json.dumps(enc.fit_order_ids).encode()).hexdigest(),'shape':{p:list(x.shape) for p,x in X.items()},'forbidden_predictors_present':False,'numeric_units':'original; no scaling/log','source_columns':config['feature_groups']})
        assert X['train'].shape[1]==len(enc.names) and all(x.shape[1]==len(enc.names) for x in X.values())
        logging.info('B: order dan fitur selesai: %s; ukuran %s',audit,{p:x.shape for p,x in X.items()})
        lr=LogisticRegression(C=1.,solver='lbfgs',max_iter=1000,tol=1e-6,random_state=42,class_weight=None,l1_ratio=0.0)
        lr.fit(X['train'],y['train']);assert lr.classes_.tolist()==[0,1]
        prior=DummyClassifier(strategy='prior',random_state=42).fit(X['train'],y['train'])
        import joblib
        joblib.dump(lr,out/'sklearn-model.joblib');joblib.dump(prior,out/'baseline-model.joblib');joblib.dump(enc,out/'preprocessor.joblib')
        loaded_enc=joblib.load(out/'preprocessor.joblib')
        assert loaded_enc.names==enc.names and (loaded_enc.transform(parts['validation'])!=X['validation']).nnz==0
        dump(out/'sklearn-parameters.json',lr.get_params());dump(out/'baseline-parameters.json',{'parameters':prior.get_params(),'classes':prior.classes_.tolist(),'class_prior':prior.class_prior_.tolist(),'majority_class':int(prior.classes_[np.argmax(prior.class_prior_)])})
        from pyspark.sql import SparkSession, functions as F, types as T
        from pyspark.ml.linalg import Vectors, VectorUDT
        from pyspark.ml.classification import LogisticRegression as SparkLR
        spark=SparkSession.builder.master('local[2]').appName('COMP8035041-Assignment-II').config('spark.driver.bindAddress','127.0.0.1').config('spark.sql.shuffle.partitions','2').config('spark.default.parallelism','2').config('spark.driver.memory','2g').getOrCreate()
        spark.sparkContext.setLogLevel('WARN')
        dump(out/'spark-environment.json',{'version':spark.version,'master':spark.sparkContext.master,'conf':dict(spark.sparkContext.getConf().getAll()),'defaultFS':spark.sparkContext._jsc.hadoopConfiguration().get('fs.defaultFS')})
        schema=T.StructType([T.StructField('Order Id',T.LongType(),False),T.StructField('label',T.DoubleType(),False),T.StructField('features',VectorUDT(),False)])
        def spark_frame(p):
            mat=X[p];ids=parts[p]['Order Id'].to_numpy();labels=y[p]
            rows=[(int(ids[i]),float(labels[i]),Vectors.sparse(mat.shape[1],mat[i].indices.tolist(),mat[i].data.tolist())) for i in range(mat.shape[0])]
            return spark.createDataFrame(rows,schema)
        sf=spark_frame('train')
        slr=SparkLR(regParam=.1,elasticNetParam=0.,maxIter=1000,tol=1e-6,standardization=False)
        sm=slr.fit(sf);sm.write().overwrite().save(str(out/'spark-model'))
        dump(out/'spark-parameters.json',{p.name:v for p,v in sm.extractParamMap().items()})
        def sp_prob(p):
            rows=sm.transform(spark_frame(p)).select('Order Id','probability').collect()
            by_id={int(r[0]):float(r[1][1]) for r in rows}
            assert len(by_id)==len(parts[p])
            return np.array([by_id[int(i)] for i in parts[p]['Order Id']])
        pv={'baseline':prior.predict_proba(X['validation'])[:,1],'sklearn_lr':lr.predict_proba(X['validation'])[:,1],'spark_lr':sp_prob('validation')}
        thresholds={m:threshold(y['validation'],p) for m,p in pv.items()}
        dump(out/'thresholds-frozen.json',{'frozen_utc':datetime.now(timezone.utc).isoformat(),'selection_partition':'validation','test_predictions_not_yet_computed':True,'thresholds':thresholds})
        logging.info('C: threshold validation dibekukan %s',thresholds)
        probs={'validation':pv,'test':{'baseline':prior.predict_proba(X['test'])[:,1],'sklearn_lr':lr.predict_proba(X['test'])[:,1],'spark_lr':sp_prob('test')}}
        metrics=[]
        for part,preds in probs.items():
            for model,p in preds.items():
                t=thresholds[model];result=evaluate(y[part],p,t);result.update(model=model,partition=part);metrics.append(result)
                pred=parts[part][['Order Id','order_date','partition','Late_delivery_risk']].copy();pred['model']=model;pred['probability_1']=p;pred['threshold']=t;pred['prediction']=(p>=t).astype(int)
                pred.to_csv(out/f'predictions-{part}-{model}.csv',index=False)
        dump(out/'metrics.json',metrics);pd.DataFrame(metrics).to_csv(out/'metrics.csv',index=False)
        dump(out/'convergence.json',{'sklearn_iterations':lr.n_iter_.tolist(),'sklearn_max_iter':1000,'spark_iterations':sm.summary.totalIterations,'spark_objective_history':sm.summary.objectiveHistory})
        logging.info('C: training dan evaluasi selesai; metrics.json tersimpan')
        graph_rows=[(int(a),'MISSING' if pd.isna(b) else str(int(b))) for a,b in zip(items['Order Id'],items['Category Id'])]
        gs=spark.createDataFrame(graph_rows,['order_id','category_id'])
        edges=gs.select('order_id','category_id').distinct().orderBy('order_id','category_id')
        ep=edges.toPandas();ep['source']='order:'+ep.order_id.astype(str);ep['target']='category:'+ep.category_id.astype(str)
        assert not ep[['order_id','category_id']].duplicated().any() and not (ep.source==ep.target).any()
        ep.to_csv(out/'graph-edges.csv',index=False)
        g=nx.Graph();g.add_edges_from(ep[['source','target']].itertuples(index=False,name=None))
        degree=pd.DataFrame([{'Category Id':c,'degree':g.degree['category:'+c]} for c in sorted(ep.category_id.unique(),key=lambda x:(x=='MISSING',int(x) if x!='MISSING' else 0))])
        degree['sort_id']=degree['Category Id'].map(lambda x:int(x) if x!='MISSING' else 10**9)
        degree=degree.sort_values(['degree','sort_id'],ascending=[False,True]).drop(columns='sort_id');degree.to_csv(out/'graph-category-degree.csv',index=False)
        components=sorted(nx.connected_components(g),key=lambda c:(-len(c),min(c)))
        cr=[];membership=[]
        for i,comp in enumerate(components,1):
            cr.append({'component_id':i,'nodes':len(comp),'orders':sum(n.startswith('order:') for n in comp),'categories':sum(n.startswith('category:') for n in comp),'edges':g.subgraph(comp).number_of_edges()})
            membership.extend({'node':n,'component_id':i} for n in sorted(comp))
        pd.DataFrame(cr).to_csv(out/'graph-components.csv',index=False);pd.DataFrame(membership).to_csv(out/'graph-component-membership.csv',index=False)
        top=['category:'+str(c) for c in degree['Category Id'].iloc[:10]]
        selected=sorted({n for c in top for n in g.neighbors(c)},key=lambda n:int(n.split(':')[1]))[:200]
        view=g.subgraph(top+selected).copy()
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        fig,ax=plt.subplots(figsize=(12,8));pos=nx.spring_layout(view,seed=42,iterations=50)
        nx.draw_networkx_edges(view,pos,alpha=.2,width=.5,ax=ax)
        nx.draw_networkx_nodes(view,pos,nodelist=selected,node_size=12,node_color='#6aaed6',ax=ax)
        nx.draw_networkx_nodes(view,pos,nodelist=top,node_size=250,node_color='#f4a340',ax=ax)
        nx.draw_networkx_labels(view,pos,labels={c:c for c in top},font_size=8,ax=ax)
        ax.set_title('Subset: 10 kategori degree tertinggi, maksimal 200 order');ax.axis('off');fig.tight_layout();fig.savefig(out/'graph-subset.png',dpi=180);plt.close(fig)
        summary={'nodes':g.number_of_nodes(),'orders':len(orders),'categories':len(degree),'edges':g.number_of_edges(),'connected_components':len(components),'self_loops':nx.number_of_selfloops(g),'duplicate_edges':int(ep[['order_id','category_id']].duplicated().sum()),'missing_category_items':audit['missing_category_items'],'edge_construction':'Spark DataFrame distinct; full retained cohort','metric_engine':'NetworkX; single-machine','visualization':{'categories':len(top),'orders':len(selected),'nodes':view.number_of_nodes(),'edges':view.number_of_edges(),'selection':'top-10 degree descending, Category Id ascending ties; neighboring Order Id ascending first 200','seed':42,'iterations':50},'source_sha256':data_manifest[0]['sha256']}
        assert summary['nodes']==summary['orders']+summary['categories'] and sum(degree.degree)==summary['edges'] and sum(x['nodes'] for x in cr)==summary['nodes']
        dump(out/'graph-summary.json',summary)
        spark.stop()
        dump(out/'status.json',{'started_utc':started,'finished_utc':datetime.now(timezone.utc).isoformat(),'exit_status':0,'training_evaluation_graph':'executed','report':'separate deliverable stage'})
        logging.info('D: graph selesai %s',summary)
        return {'output':str(out),'audit':audit,'thresholds':thresholds,'metrics':metrics,'graph':summary}
    except Exception:
        (out/'traceback.log').write_text(traceback.format_exc());dump(out/'status.json',{'started_utc':started,'finished_utc':datetime.now(timezone.utc).isoformat(),'exit_status':1});logging.exception('Eksekusi gagal');raise

if __name__=='__main__':
    import argparse
    a=argparse.ArgumentParser();a.add_argument('--root',required=True);a.add_argument('--output',required=True);args=a.parse_args();run(args.root,args.output)
