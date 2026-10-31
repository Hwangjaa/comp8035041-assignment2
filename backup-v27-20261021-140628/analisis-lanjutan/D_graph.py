"""Fase 2D: perluasan graph analytics - proyeksi kategori, sentralitas, komunitas, late-rate.
Semua dari output eksekusi (graph-edges.csv, orders.csv). Single-machine NetworkX."""
import json, time
from pathlib import Path
import numpy as np, pandas as pd
import networkx as nx
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
R=Path('/Users/rafaelyudianto/Documents/COMP8035041-Assignment-II')
RUN=R/'eksekusi-final-lokal/run-actual';OUT=R/'analisis-lanjutan'
edges=pd.read_csv(RUN/'graph-edges.csv')
orders=pd.read_csv(RUN/'orders.csv')
nodes_expected=62948;edges_expected=152676
g=nx.Graph();g.add_edges_from(zip(edges['source'],edges['target']))
res={'full_graph':{'nodes':g.number_of_nodes(),'edges':g.number_of_edges(),
   'matches_expected':bool(g.number_of_nodes()==nodes_expected and g.number_of_edges()==edges_expected),
   'self_loops':nx.number_of_selfloops(g)}}
# degree kategorial (bobot 1)
cat_nodes=[n for n in g.nodes if n.startswith('category:')]
deg1=pd.Series({n:g.degree[n] for n in cat_nodes}).sort_values(ascending=False)
res['category_degree_unweighted_top10']=[{'category':k.replace('category:',''),'degree':int(v)} for k,v in deg1.head(10).items()]
# proyeksi kategori-kategori: bobot = jumlah order bersama
t0=time.perf_counter()
proj=nx.Graph()
order_to_cats=edges.groupby('order_id')['category_id'].apply(list)
from itertools import combinations
from collections import Counter
co=Counter()
for cats in order_to_cats:
    cs=sorted(set(cats))
    for a,b in combinations(cs,2):co[(str(a),str(b))]+=1
for (a,b),w in co.items():proj.add_edge('category:'+a,'category:'+b,weight=w)
res['category_projection']={'nodes':proj.number_of_nodes(),'edges':proj.number_of_edges(),'seconds':time.perf_counter()-t0,
  'weight_note':'weight = jumlah pesanan yang memuat kedua kategori'}
wdeg=pd.Series({n:proj.degree(n,weight='weight') for n in proj.nodes}).sort_values(ascending=False)
res['category_projection']['weighted_degree_top10']=[{'category':k.replace('category:',''),'weighted_degree':int(v)} for k,v in wdeg.head(10).items()]
# PageRank & eigenvector pada proyeksi (parameter dinyatakan)
pr=nx.pagerank(proj,weight='weight',alpha=0.85);ev=nx.eigenvector_centrality(proj,weight='weight',max_iter=500,tol=1e-10)
res['category_projection']['pagerank_top10']=[{'category':k.replace('category:',''),'pagerank':float(v)} for k,v in sorted(pr.items(),key=lambda x:-x[1])[:10]]
res['category_projection']['eigenvector_top10']=[{'category':k.replace('category:',''),'eigenvector':float(v)} for k,v in sorted(ev.items(),key=lambda x:-x[1])[:10]]
res['category_projection']['pagerank_params']={'alpha':0.85,'weight':'co_occurrence','implementation':'networkx'}
# betweenness: sampel (graf 63k node tidak layak exact)
k=min(500,proj.number_of_nodes())
t0=time.perf_counter();bc=nx.betweenness_centrality(proj,k=k,weight=None,seed=42,normalized=True)
res['category_projection']['betweenness_sample']={'k_samples':k,'seconds':time.perf_counter()-t0,
  'top10':[{'category':x.replace('category:',''),'betweenness':float(v)} for x,v in sorted(bc.items(),key=lambda x:-x[1])[:10]],
  'note':'aproksimasi sampel; bukan nilai eksak'}
# komunitas pada proyeksi (greedy modularity, seed)
comms=nx.community.greedy_modularity_communities(proj,weight='weight')
res['category_projection']['communities']={'algorithm':'greedy_modularity','resolution':1.0,'seed':42,'n_communities':len(comms),
  'sizes':sorted([len(c) for c in comms],reverse=True),
  'members':[sorted([x.replace('category:','') for x in c]) for c in comms]}
# late-rate per kategori & per komponen dengan interval (Wilson)
lab=orders.set_index('Order Id')['Late_delivery_risk']
edges2=edges.copy();edges2['late']=edges2['order_id'].map(lab)
def wilson(p,n,z=1.96):
    if n==0:return (0.0,0.0)
    d=1+z*z/n;c=p+z*z/(2*n);h=z*np.sqrt(p*(1-p)/n+z*z/(4*n*n))
    return ((c-h)/d,(c+h)/d)
per_cat=edges2.groupby('category_id')['late'].agg(['mean','count']).sort_values('mean',ascending=False)
res['late_rate_by_category']=[{'category':str(k),'late_rate':float(r['mean']),'orders':int(r['count']),
   'ci95':[float(x) for x in wilson(r['mean'],r['count'])]} for k,r in per_cat.head(10).iterrows()]
# komponen
comps=sorted(nx.connected_components(g),key=lambda c:-len(c))
big=comps[0]
sub=g.subgraph(big)
order_nodes=[n for n in sub.nodes if n.startswith('order:')]
sub_lab=lab.reindex([int(n.split(':')[1]) for n in order_nodes])
rate=float(sub_lab.mean());n=len(sub_lab)
res['largest_component']={'nodes':len(big),'orders':len(order_nodes),'late_rate':rate,'ci95':[float(x) for x in wilson(rate,n)]}
res['caveat']='asosiasi deskriptif, bukan sebab-akibat; metrik graf belum diuji sebagai fitur model'
json.dump(res,open(OUT/'D_graph.json','w'),indent=2)
# gambar subset diperbaiki (label tidak bertumpuk)
top=[('category:'+d['category']) for d in res['category_degree_unweighted_top10']]
sel=sorted({n for c in top for n in g.neighbors(c)},key=lambda n:int(n.split(':')[1]))[:200]
view=g.subgraph(top+sel).copy()
fig,ax=plt.subplots(figsize=(13,9));pos=nx.spring_layout(view,seed=42,iterations=80)
nx.draw_networkx_edges(view,pos,alpha=.15,width=.4,ax=ax)
nx.draw_networkx_nodes(view,pos,nodelist=sel,node_size=10,node_color='#6aaed6',ax=ax)
nx.draw_networkx_nodes(view,pos,nodelist=top,node_size=420,node_color='#f4a340',ax=ax)
lbl={n:n.replace('category:','') for n in top if n in set(view.nodes)}
texts=nx.draw_networkx_labels(view,pos,labels=lbl,font_size=9,ax=ax)
# hindari tumpang tindih: geser label sedikit keluar + kotak latar
for t in texts.values():
    t.set_bbox(dict(boxstyle='round,pad=0.25',fc='white',ec='#f4a340',alpha=0.9))
ax.set_title('Subset tampilan: 10 kategori degree tertinggi; maksimal 200 order\nBukan statistik graf lengkap');ax.axis('off')
fig.tight_layout();fig.savefig(OUT/'D_graph_subset_fixed.png',dpi=180);plt.close(fig)
print(json.dumps({k:res[k] for k in ['full_graph','category_projection','largest_component']},indent=2)[:2500])
