"""Langkah 7: graf - betweenness eksak, anggota komunitas, late rate komponen kecil,
Gambar 6.2 diperbaiki (label tidak bertumpuk + legenda)."""
import json
from pathlib import Path
import numpy as np, pandas as pd, networkx as nx
from itertools import combinations
from collections import Counter
import matplotlib; matplotlib.use('Agg');import matplotlib.pyplot as plt
R=Path('/Users/rafaelyudianto/Documents/COMP8035041-Assignment-II')
RUN=R/'eksekusi-final-lokal/run-actual';OUT=R/'analisis-lanjutan'
edges=pd.read_csv(RUN/'graph-edges.csv');orders=pd.read_csv(RUN/'orders.csv')
lab=orders.set_index('Order Id')['Late_delivery_risk']
g=nx.Graph();g.add_edges_from(zip(edges['source'],edges['target']))
def wilson(p,n,z=1.96):
    if n==0:return (0.,0.)
    d=1+z*z/n;c=p+z*z/(2*n);h=z*np.sqrt(p*(1-p)/n+z*z/(4*n*n));return ((c-h)/d,(c+h)/d)
# proyeksi kategori
o2c=edges.groupby('order_id')['category_id'].apply(lambda s:sorted(set(map(str,s))))
co=Counter()
for cs in o2c:
    for a,b in combinations(cs,2):co[(a,b)]+=1
proj=nx.Graph()
for (a,b),w in co.items():proj.add_edge('category:'+a,'category:'+b,weight=w)
res={'projection':{'nodes':proj.number_of_nodes(),'edges':proj.number_of_edges()}}
# betweenness EKSAK (33 node -> layak)
bc=nx.betweenness_centrality(proj,weight='weight',normalized=True,k=None)
res['betweenness_exact']={'method':'exact (k=None)','nodes':proj.number_of_nodes(),'weight':'co-occurrence',
  'top10':[{'category':x.replace('category:',''),'betweenness':float(v)} for x,v in sorted(bc.items(),key=lambda t:-t[1])[:10]]}
# komunitas + anggota
comms=list(nx.community.greedy_modularity_communities(proj,weight='weight'))
res['communities']={'algorithm':'greedy_modularity_communities','resolution':1.0,'seed':None,
  'note':'NetworkX greedy modularity deterministik (tanpa RNG)',
  'n':len(comms),'sizes':sorted([len(c) for c in comms],reverse=True),
  'members':[sorted([x.replace('category:','') for x in c],key=lambda s:int(s) if s.isdigit() else 999) for c in comms]}
# late rate 19 komponen
comps=sorted(nx.connected_components(g),key=lambda c:-len(c))
comp_rows=[]
for i,comp in enumerate(comps,1):
    on=[int(n.split(':')[1]) for n in comp if n.startswith('order:')]
    s=lab.reindex(on).dropna();p=float(s.mean()) if len(s) else None;nn=len(s)
    comp_rows.append({'component_id':i,'nodes':len(comp),'orders':nn,'categories':sum(n.startswith('category:') for n in comp),
        'late_rate':p,'ci95':[float(x) for x in wilson(p,nn)] if p is not None else None})
res['components']=comp_rows
# weighted degree & pagerank & eigen (untuk insight kesamaan urutan)
wd={n:proj.degree(n,weight='weight') for n in proj.nodes}
pr=nx.pagerank(proj,weight='weight',alpha=0.85)
ev=nx.eigenvector_centrality(proj,weight='weight',max_iter=1000,tol=1e-12)
rank=lambda d:sorted(d.keys(),key=lambda k:-d[k])
def kendall(a,b):
    from itertools import combinations as C
    ai={x:i for i,x in enumerate(a)};bi={x:i for i,x in enumerate(b)}
    con=dis=0
    for x,y in C(set(a)&set(b),2):
        s=(ai[x]-ai[y])*(bi[x]-bi[y])
        if s>0:con+=1
        elif s<0:dis+=1
    return (con-dis)/(con+dis) if con+dis else None
res['rank_similarity']={'weighted_degree_vs_pagerank':kendall(rank(wd),rank(pr)),
  'weighted_degree_vs_eigenvector':kendall(rank(wd),rank(ev)),
  'note':'Kendall tau pada 33 kategori proyeksi'}
res['n_categories_total']=int(edges['category_id'].nunique())
# Gambar 6.2 diperbaiki: label tidak bertumpuk + legenda
top=[('category:'+x['category']) for x in sorted([{'category':str(k).replace('category:',''),'w':v} for k,v in wd.items()],key=lambda d:-d['w'])[:10]]
comms_color={}
for ci,c in enumerate(comms):
    for n in c:comms_color[n]=ci
pos=nx.spring_layout(proj,weight='weight',seed=42,iterations=300,k=1.4)
fig,ax=plt.subplots(figsize=(12,9))
ws=[proj[u][v]['weight'] for u,v in proj.edges];wmax=max(ws)
nx.draw_networkx_edges(proj,pos,width=[0.4+2.2*(w/wmax) for w in ws],alpha=0.35,edge_color='#8a8a8a',ax=ax)
cmap=plt.cm.Set2
for ci,c in enumerate(comms):
    ns=[n for n in c if n in proj]
    nx.draw_networkx_nodes(proj,pos,nodelist=ns,node_size=[90+wd[n]/140 for n in ns],
        node_color=[cmap(ci%8)],edgecolors='white',linewidths=1.0,label=f'Komunitas {ci+1} ({len(c)} kategori)',ax=ax)
# label dengan offset radial agar tidak bertumpuk
for n in proj.nodes:
    x,y=pos[n];r=np.hypot(x,y) or 1
    ax.annotate(n.replace('category:',''),(x,y),xytext=(x+0.06*x/r,y+0.06*y/r),fontsize=9,
        ha='center',va='center',bbox=dict(boxstyle='round,pad=0.18',fc='white',ec='none',alpha=0.85))
ax.set_title('Proyeksi kategori–kategori (bobot = jumlah pesanan bersama)\n'
             f'{proj.number_of_nodes()} kategori, {proj.number_of_edges()} edge, {len(comms)} komunitas; ukuran node = weighted degree',fontsize=11)
ax.legend(loc='lower left',fontsize=9,framealpha=0.9);ax.axis('off')
fig.tight_layout();fig.savefig(OUT/'H_projection_fixed.png',dpi=200);plt.close(fig)
json.dump(res,open(OUT/'H_graph.json','w'),indent=2)
print(json.dumps({k:res[k] for k in ['betweenness_exact','communities','rank_similarity','n_categories_total']},indent=2)[:2000])
print('components:',[(c['component_id'],c['orders'],round(c['late_rate'],4) if c['late_rate'] else None) for c in comp_rows])
