"""Audit read-only artefak lama; hanya menulis di direktori skrip ini. Tidak melatih model."""
import os
os.environ['PYTHONDONTWRITEBYTECODE']='1'
os.environ.setdefault('MPLCONFIGDIR',os.path.join(os.environ['TMPDIR'],'qa-dataco-mpl'))
import sys,json,hashlib,subprocess,ast,itertools
from pathlib import Path
from fractions import Fraction
import numpy as np
import pandas as pd
import networkx as nx
from sklearn.metrics import average_precision_score,roc_auc_score,precision_score,recall_score,f1_score,confusion_matrix
ROOT=Path('/Users/rafaelyudianto/Documents/COMP8035041-Assignment-II')
QA=Path(__file__).resolve().parent
BASE=ROOT/'eksekusi-final-lokal'
sys.dont_write_bytecode=True
sys.path.insert(0,str(BASE/'src'))
import pipeline
checks=[]
def dump(name,data): (QA/name).write_text(json.dumps(data,indent=2,ensure_ascii=False,allow_nan=False,default=str))
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''): h.update(b)
 return h.hexdigest()
def ck(name,value,detail=None):
 checks.append({'pemeriksaan':name,'lulus':bool(value),'rincian':detail})
def load(p): return json.loads(p.read_text())
def csv(p,**kw): return pd.read_csv(p,float_precision='round_trip',**kw)
def snapshot():
 paths=list((ROOT/'data').rglob('*'))+list(BASE.rglob('*'))+[ROOT/'implementasi-F4-F8/keputusan-final.json',ROOT/'gerbang-keputusan-F1-F3/dokumen-keputusan-F1-F3.html',ROOT/'gerbang-keputusan-F4-F8/paket-keputusan.txt']
 return {str(p.relative_to(ROOT)):sha(p) for p in paths if p.is_file() and '__pycache__' not in str(p) and not p.name.startswith('~$')}
before=snapshot();dump('hash-sebelum.json',before)
manifest=load(ROOT/'data/source-manifest.json');source=[]
for row in manifest['files']:
 p=ROOT/'data/raw'/Path(row['file']).name
 d=pd.read_csv(p,encoding='latin1',low_memory=False)
 observed={'file':str(p),'bytes':p.stat().st_size,'sha256':sha(p),'rows':len(d),'columns':len(d.columns),'schema':{c:str(t) for c,t in d.dtypes.items()}}
 ck('raw manifest '+p.name,observed['sha256']==row['sha256'] and observed['bytes']==row['bytes'])
 source.append(observed)
dump('data-mentah.json',source)
raw=pd.read_csv(ROOT/'data/raw/DataCoSupplyChainDataset.csv',encoding='latin1',low_memory=False)
keep=raw[raw['Delivery Status']!='Shipping canceled'].copy()
cols=pipeline.SINGLE
conflicts=keep.groupby('Order Id')[cols].nunique(dropna=False)
ck('singleton label dan fitur',not (conflicts>1).any().any())
ck('Order Item Id unik dan nonmissing',keep['Order Item Id'].is_unique and not keep['Order Item Id'].isna().any())
ck('Category Id per item konsisten',keep.groupby('Order Item Id')['Category Id'].nunique(dropna=False).max()==1)
ck('Category Id -> nama singleton',keep.groupby('Category Id')['Category Name'].nunique(dropna=False).max()==1)
orders=keep.groupby('Order Id',sort=True)[cols].first().reset_index()
orders['item_count']=orders['Order Id'].map(keep.groupby('Order Id')['Order Item Id'].nunique())
orders['categories']=orders['Order Id'].map(keep.groupby('Order Id')['Category Id'].agg(lambda s:sorted(set(str(int(v)) if pd.notna(v) else 'MISSING' for v in s))))
orders['order_date']=pd.to_datetime(orders.pop('order date (DateOrders)'),format='%m/%d/%Y %H:%M')
orders['partition']=np.select([orders.order_date<pd.Timestamp('2017-07-01'),orders.order_date<pd.Timestamp('2017-10-01')],['train','validation'],default='test')
po,pi,pa=pipeline.make_orders(raw)
ck('pipeline.make_orders vs rekonstruksi independen',orders.equals(po[orders.columns]))
train=orders[orders.partition=='train'];encoder=pipeline.Features().fit(train)
expected_pairs={(int(a),str(int(b)) if pd.notna(b) else 'MISSING') for a,b in keep[['Order Id','Category Id']].itertuples(index=False,name=None)}
threshold_results=[];graph_results=[];run_results={};precision_notes=[]
for run_name in ['run-actual','reproducibility-run']:
 out=BASE/run_name;prefix=run_name+' '
 stored=csv(out/'orders.csv');stored['categories']=stored.categories.map(json.loads);stored.order_date=pd.to_datetime(stored.order_date)
 ck(prefix+'orders semua nilai',orders.equals(stored[orders.columns]))
 ck(prefix+'audit-orders',load(out/'audit-orders.json')==pa)
 split=orders.groupby(['partition','Late_delivery_risk']).size().unstack(fill_value=0).reindex(['train','validation','test']);split.columns=['label_0','label_1'];split['total']=split.sum(axis=1)
 ck(prefix+'split.csv',split.equals(csv(out/'split.csv',index_col=0)))
 for actual in load(out/'data-manifest.json')['files']:
  expected=next(x for x in source if Path(x['file']).name==Path(actual['file']).name)
  ck(prefix+'data-manifest '+Path(actual['file']).name,all(actual[k]==expected[k] for k in ['sha256','bytes','rows','columns','schema']))
 contract=load(out/'feature-contract.json')
 ck(prefix+'vocabulary train-only',contract['vocabulary']==encoder.vocab and contract['feature_names']==encoder.names and contract['fit_partition']=='train')
 ck(prefix+'fit IDs hash',contract['fit_order_ids_sha256']==hashlib.sha256(json.dumps(encoder.fit_order_ids).encode()).hexdigest())
 ck(prefix+'48 fitur dan ukuran matriks',contract['n_features']==len(encoder.names) and contract['shape']=={p:[int((orders.partition==p).sum()),len(encoder.names)] for p in ['train','validation','test']})
 metrics=load(out/'metrics.json');mcsv=csv(out/'metrics.csv');frozen=load(out/'thresholds-frozen.json')
 ck(prefix+'6 metrics rows',len(metrics)==len(mcsv)==6 and len({(r['partition'],r['model']) for r in metrics})==6)
 ck(prefix+'freeze validation',frozen['selection_partition']=='validation' and frozen['test_predictions_not_yet_computed'])
 pr={}
 for r in metrics:
  pth=out/f"predictions-{r['partition']}-{r['model']}.csv";d=csv(pth);expected=orders[orders.partition==r['partition']]
  ck(prefix+pth.name+' identitas dan target',d['Order Id'].is_unique and d['Order Id'].tolist()==expected['Order Id'].tolist() and d.Late_delivery_risk.tolist()==expected.Late_delivery_risk.tolist() and d.partition.eq(r['partition']).all() and d.model.eq(r['model']).all() and pd.to_datetime(d.order_date).tolist()==expected.order_date.tolist())
  y=d.Late_delivery_risk.to_numpy(dtype=int);p=d.probability_1.to_numpy();t=frozen['thresholds'][r['model']];pred=(p>=t).astype(int)
  ck(prefix+pth.name+' probability/prediction/threshold',np.isfinite(p).all() and ((p>=0)&(p<=1)).all() and np.array_equal(pred,d.prediction) and d.threshold.eq(t).all())
  actual={'average_precision':float(average_precision_score(y,p)),'roc_auc':float(roc_auc_score(y,p)),'precision':float(precision_score(y,pred,zero_division=0)),'recall':float(recall_score(y,pred,zero_division=0)),'binary_f1':float(f1_score(y,pred,zero_division=0))}
  cm=confusion_matrix(y,pred,labels=[0,1]).ravel().tolist()
  mr=mcsv[(mcsv.model==r['model'])&(mcsv.partition==r['partition'])].iloc[0]
  ck(prefix+pth.name+' metrics JSON dan CSV',all(abs(v-r[k])<1e-14 and abs(v-mr[k])<1e-14 for k,v in actual.items()) and cm==r['confusion_matrix']==ast.literal_eval(mr.confusion_matrix) and r['n']==mr['n']==len(d) and r['threshold']==mr.threshold==t)
  default=pd.read_csv(pth);ndiff=int(((default.probability_1.to_numpy()>=t)!=pred).sum())
  precision_notes.append({'run':run_name,'file':pth.name,'beda_prediksi_parser_default_vs_round_trip':ndiff})
  pr[pth.name]={'rows':len(d),'all_positive':bool(pred.all()),'cm':cm,'metrics':actual,'sha256':sha(pth)}
  if r['partition']=='validation':
   idx=np.argsort(-p,kind='stable');sp=p[idx];sy=y[idx];ends=np.flatnonzero(np.r_[sp[:-1]!=sp[1:],True]);tp=np.cumsum(sy)[ends]
   candidates=[(Fraction(0),float(np.nextafter(p.max(),np.inf)),0,0)]
   candidates.extend((Fraction(2*int(a),int(y.sum())+int(b)+1),float(sp[b]),int(b)+1,int(a)) for a,b in zip(tp,ends))
   best=max(candidates,key=lambda x:(x[0],x[1]));ties=[x for x in candidates if x[0]==best[0]]
   ck(prefix+r['model']+' H1 exact semua kandidat',best[1]==t==pipeline.threshold(y,p))
   threshold_results.append({'run':run_name,'model':r['model'],'n_validation':len(y),'positif':int(y.sum()),'kandidat':len(candidates),'probabilitas_unik':len(np.unique(p)),'threshold_tersimpan':t,'threshold_referensi':best[1],'F1_maksimum_exact':str(best[0]),'F1_maksimum':float(best[0]),'jumlah_tie':len(ties),'prediksi_positif':best[2],'TP':best[3],'all_positive':best[2]==len(y),'all_negative_boundary':candidates[0][1],'minimum_probability':float(p.min()),'maximum_probability':float(p.max())})
 e=csv(out/'graph-edges.csv',dtype={'category_id':str});pairs=set(e[['order_id','category_id']].itertuples(index=False,name=None));g=nx.Graph();g.add_edges_from(e[['source','target']].itertuples(index=False,name=None))
 ck(prefix+'graph edge raw lengkap',pairs==expected_pairs and len(pairs)==len(e))
 ck(prefix+'graph namespace bipartit',e.source.tolist()==('order:'+e.order_id.astype(str)).tolist() and e.target.tolist()==('category:'+e.category_id).tolist() and nx.is_bipartite(g) and nx.number_of_selfloops(g)==0)
 deg=csv(out/'graph-category-degree.csv',dtype={'Category Id':str});edeg=sorted([(str(c),g.degree['category:'+str(c)]) for c in e.category_id.unique()],key=lambda x:(-x[1],int(x[0])))
 ck(prefix+'degree dan urutan tie',list(deg.itertuples(index=False,name=None))==edeg)
 comps=sorted(nx.connected_components(g),key=lambda c:(-len(c),min(c)));rows=[];mem={}
 for i,c in enumerate(comps,1):
  rows.append({'component_id':i,'nodes':len(c),'orders':sum(n.startswith('order:') for n in c),'categories':sum(n.startswith('category:') for n in c),'edges':g.subgraph(c).number_of_edges()});mem.update({n:i for n in c})
 cmem=csv(out/'graph-component-membership.csv');ck(prefix+'components semua kolom',pd.DataFrame(rows).equals(csv(out/'graph-components.csv')))
 ck(prefix+'membership seluruh node',len(cmem)==len(g) and cmem.node.is_unique and dict(cmem.itertuples(index=False,name=None))==mem)
 top=['category:'+x[0] for x in edeg[:10]];selected=sorted({n for c in top for n in g.neighbors(c)},key=lambda n:int(n.split(':')[1]))[:200];view=g.subgraph(top+selected).copy();summary=load(out/'graph-summary.json')
 observed={'nodes':len(g),'orders':len(orders),'categories':len(edeg),'edges':len(e),'connected_components':len(comps),'self_loops':nx.number_of_selfloops(g),'duplicate_edges':len(e)-len(pairs),'missing_category_items':int(keep['Category Id'].isna().sum())}
 ck(prefix+'summary graph lengkap',all(summary[k]==v for k,v in observed.items()) and summary['source_sha256']==source[0]['sha256'])
 v={'categories':len(top),'orders':len(selected),'nodes':len(view),'edges':view.number_of_edges()}
 ck(prefix+'summary subset',all(summary['visualization'][k]==z for k,z in v.items()))
 pd.DataFrame(sorted(view.edges()),columns=['source','target']).to_csv(QA/f'graph-subset-edges-{run_name}.csv',index=False)
 dump(f'graph-subset-nodes-{run_name}.json',{'categories':top,'orders':selected})
 graph_results.append({'run':run_name,'full':observed,'subset':v,'top_categories':top,'subset_image_sha256':sha(out/'graph-subset.png'),'bukti_subset_edges':f'graph-subset-edges-{run_name}.csv'})
 status=load(out/'status.json');log=(out/'execution.log').read_text()
 ck(prefix+'status selesai dan log D',status['exit_status']==0 and 'D: graph selesai' in log)
 conv=load(out/'convergence.json');ck(prefix+'iteration di bawah max',max(conv['sklearn_iterations'])<conv['sklearn_max_iter'] and conv['spark_iterations']<1000)
 pars=load(out/'sklearn-parameters.json');spars=load(out/'spark-parameters.json');decision=load(ROOT/'implementasi-F4-F8/keputusan-final.json')
 ck(prefix+'F4 sklearn parameter',all(pars[k]==v for k,v in decision['F4']['sklearn'].items()))
 ck(prefix+'F4 spark parameter',all(spars[k]==v for k,v in decision['F4']['spark'].items()))
 bp=load(out/'baseline-parameters.json');prior=float(train.Late_delivery_risk.mean());ck(prefix+'baseline prior train',bp['class_prior'][1]==prior and all(csv(out/f'predictions-{part}-baseline.csv').probability_1.eq(prior).all() for part in ['validation','test']))
 run_results[run_name]={'predictions':pr,'status':status,'convergence':conv,'environment':load(out/'environment.json'),'spark_environment':load(out/'spark-environment.json')}
# Bandingkan seluruh artefak tabular dan model tersimpan antar-run; tidak menjalankan fit.
a=BASE/'run-actual';b=BASE/'reproducibility-run';comparisons=[]
for p in sorted(a.glob('*.csv')):
 q=b/p.name;equal=q.exists() and sha(p)==sha(q)
 comparisons.append({'file':p.name,'byte_identik':equal});ck('reproducibility CSV '+p.name,equal)
for name in ['metrics.json','feature-contract.json','thresholds-frozen.json','graph-summary.json','audit-orders.json','sklearn-parameters.json','spark-parameters.json','baseline-parameters.json','preprocessor.joblib','sklearn-model.joblib','baseline-model.joblib']:
 if name.endswith('.json'):
  x=load(a/name);y=load(b/name)
  if name=='thresholds-frozen.json':x.pop('frozen_utc');y.pop('frozen_utc')
  equal=x==y
 else:equal=sha(a/name)==sha(b/name)
 comparisons.append({'file':name,'nilai_identik_kecuali_timestamp':equal});ck('reproducibility '+name,equal)
dump('reproducibility.json',comparisons)
# Perbedaan namespace pickle dari notebook import vs CLI __main__ diperiksa eksplisit.
import joblib
serialization=[]
loaded={}
for run_name in ['run-actual','reproducibility-run']:
 p=BASE/run_name/'preprocessor.joblib'
 try:
  loaded[run_name]=joblib.load(p);serialization.append({'run':run_name,'load_standar':True,'class_module':type(loaded[run_name]).__module__})
 except AttributeError as exc:
  serialization.append({'run':run_name,'load_standar':False,'error':str(exc),'alias_audit_saja':'__main__.Features = pipeline.Features'})
  setattr(sys.modules['__main__'],'Features',pipeline.Features)
  loaded[run_name]=joblib.load(p)
semantic_equal=loaded['run-actual'].__dict__==loaded['reproducibility-run'].__dict__
ck('reproducibility preprocessor semantik',semantic_equal)
dump('serialisasi-preprocessor.json',{'hasil':serialization,'state_identik':semantic_equal,'catatan':'Hash biner berbeda; alias hanya di proses audit, tidak mengubah file lama.'})
# Exercise model lokal tersimpan: predict_proba saja, tanpa fit.
for run_name in ['run-actual','reproducibility-run']:
 out=BASE/run_name
 for part in ['validation','test']:
  x=loaded[run_name].transform(orders[orders.partition==part])
  for model,name in [('sklearn_lr','sklearn-model.joblib'),('baseline','baseline-model.joblib')]:
   predicted=joblib.load(out/name).predict_proba(x)[:,1]
   persisted=csv(out/f'predictions-{part}-{model}.csv').probability_1.to_numpy()
   ck(run_name+' saved predict_proba '+part+' '+model,np.allclose(predicted,persisted,atol=1e-14,rtol=0),{'max_absolute_difference':float(np.max(np.abs(predicted-persisted)))})
 config=load(out/'config.json');spark_env=load(out/'spark-environment.json')
 ck(run_name+' F5/F8 config',config['seed']==42 and config['refit'] is False and config['gap'].startswith('M0') and config['benchmark'].startswith('B0') and config['storage']=='local file:///; not HDFS')
 ck(run_name+' local Spark bukan HDFS',spark_env['master']=='local[2]' and spark_env['defaultFS']=='file:///')
# Notebook tersimpan, log berhasil dan jejak gagal historis dipisahkan.
notebooks=[];logs=[]
for p in BASE.rglob('*.ipynb'):
 n=load(p);code=[c for c in n['cells'] if c['cell_type']=='code'];errors=[{'ename':o.get('ename'),'evalue':o.get('evalue')} for c in code for o in c.get('outputs',[]) if o['output_type']=='error']
 notebooks.append({'file':str(p.relative_to(ROOT)),'code_cells':len(code),'execution_counts':[c.get('execution_count') for c in code],'errors':errors,'historis':'diagnostics' in p.parts})
 if 'diagnostics' not in p.parts:ck('notebook final tereksekusi tanpa error',bool(code) and all(c.get('execution_count') for c in code) and not errors)
for p in BASE.rglob('*.log'):
 text=p.read_text(errors='replace');logs.append({'file':str(p.relative_to(ROOT)),'bytes':p.stat().st_size,'sha256':sha(p),'traceback_count':text.count('Traceback (most recent call last)'),'error_lines':[line[:500] for line in text.splitlines() if any(w in line for w in ['Traceback','Error:','Exception:','FAILED','Eksekusi gagal'])][:30],'mtime_ns':p.stat().st_mtime_ns,'tail':text[-2000:]})
dump('notebook-dan-log.json',{'notebooks':notebooks,'logs':logs,'catatan':'Traceback/log lama tidak membatalkan status run terakhir; tidak ada training ulang pada audit.'})
# Existing tests dijalankan tanpa menulis pycache lama.
env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1')
r=subprocess.run([sys.executable,'-B','-m','unittest','discover','-s',str(BASE/'tests'),'-v'],cwd=QA,env=env,capture_output=True,text=True)
(QA/'tests-existing.log').write_text(r.stdout+r.stderr);ck('unit tests lama',r.returncode==0)
# Exhaustive reference H1 untuk seluruh label biner/probabilitas ternary hingga panjang 5.
count=0
for n in range(1,6):
 for yy in itertools.product([0,1],repeat=n):
  for pp in itertools.product([.1,.5,.9],repeat=n):
   probs=np.array(pp);labels=np.array(yy);cand=list(np.unique(probs))+[float(np.nextafter(max(pp),np.inf))]
   def key(t):
    predicted=probs>=t;tp=int(labels[predicted].sum());den=int(labels.sum())+int(predicted.sum());return (Fraction(2*tp,den) if den else Fraction(0),t)
   expected=max(cand,key=key)
   if pipeline.threshold(yy,pp)!=expected:raise AssertionError((yy,pp,expected))
   count+=1
ck('H1 exhaustive fixture',True,{'cases':count,'maksimal_panjang':5,'probabilitas':[.1,.5,.9],'referensi':'Fraction, kandidat unik plus nextafter(max,+inf), tie terbesar'})
# Probe kontrak item duplikat/konflik: dokumentasi, bukan perubahan kode.
fixture=raw.loc[raw['Delivery Status']!='Shipping canceled'].iloc[:1].copy();conflict=pd.concat([fixture,fixture.assign(**{'Category Id':999})],ignore_index=True)
try:
 answer,_,_=pipeline.make_orders(conflict)
 probe={'ditolak':False,'item_count':int(answer.item_count.iloc[0]),'categories':answer.categories.iloc[0],'fakta':'Order Item Id identik dengan Category Id berbeda diterima make_orders; data aktual telah diperiksa terpisah.'}
except ValueError as exc:probe={'ditolak':True,'error':str(exc)}
dump('probe-kontrak-item.json',probe)
after=snapshot();changed=[p for p,h in before.items() if after.get(p)!=h];ck('artefak lama tidak berubah',not changed,changed);dump('hash-sesudah.json',after)
dump('threshold-audit.json',threshold_results);dump('graph-bukti.json',graph_results);dump('parser-float.json',precision_notes)
result={'status':'LULUS_PEMERIKSAAN_ARTEFAK' if all(c['lulus'] for c in checks) else 'ADA_PEMERIKSAAN_TIDAK_LULUS','jumlah_pemeriksaan':len(checks),'lulus':sum(c['lulus'] for c in checks),'gagal':[c for c in checks if not c['lulus']],'checks':checks,'raw_order_audit':pa,'runs':run_results,'thresholds':threshold_results,'graphs':graph_results,'probe_item':probe,'tests_exit_code':r.returncode,'h1_exhaustive_cases':count,'artefak_lama_berubah':changed,'batas':'Audit file hasil dua run tersimpan dan pengujian fungsi; tidak menjalankan ulang training, Spark fit, notebook atau HDFS. Metadata penerbit tidak diambil ulang. Final F1-F3 verbatim belum ditemukan pada artefak lokal yang diperiksa.'}
dump('hasil-audit.json',result)
print(json.dumps({k:result[k] for k in ['status','jumlah_pemeriksaan','lulus','gagal','raw_order_audit','h1_exhaustive_cases','artefak_lama_berubah']},indent=2))
