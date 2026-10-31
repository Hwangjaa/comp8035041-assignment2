"""Generate gambar proyeksi kategori-kategori (Fase 2D) untuk Bab 6."""
import json
from pathlib import Path
import pandas as pd, networkx as nx
from itertools import combinations
from collections import Counter
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
R=Path('/Users/rafaelyudianto/Documents/COMP8035041-Assignment-II')
RUN=R/'eksekusi-final-lokal/run-actual';OUT=R/'analisis-lanjutan'
edges=pd.read_csv(RUN/'graph-edges.csv')
o2c=edges.groupby('order_id')['category_id'].apply(lambda s:sorted(set(map(str,s))))
co=Counter()
for cs in o2c:
    for a,b in combinations(cs,2):co[(a,b)]+=1
proj=nx.Graph()
for (a,b),w in co.items():proj.add_edge('category:'+a,'category:'+b,weight=w)
comms=list(nx.community.greedy_modularity_communities(proj,weight='weight'))
cmap={n:i for i,c in enumerate(comms) for n in c}
pos=nx.spring_layout(proj,weight='weight',seed=42,iterations=200)
fig,ax=plt.subplots(figsize=(11,8.5))
ws=[proj[u][v]['weight'] for u,v in proj.edges]
wmax=max(ws);norm=[0.4+3.5*(w/wmax) for w in ws]
nx.draw_networkx_edges(proj,pos,width=norm,alpha=0.35,edge_color='#888',ax=ax)
colors=plt.cm.tab20([cmap[n]%20 for n in proj.nodes])
sizes=[120+proj.degree(n,weight='weight')/120 for n in proj.nodes]
nx.draw_networkx_nodes(proj,pos,node_size=sizes,node_color=colors,edgecolors='white',linewidths=0.8,ax=ax)
nx.draw_networkx_labels(proj,pos,labels={n:n.split(':')[1] for n in proj.nodes},font_size=9,ax=ax)
ax.set_title(f'Proyeksi kategori–kategori (bobot = jumlah pesanan bersama)\n{proj.number_of_nodes()} node, {proj.number_of_edges()} edge, {len(comms)} komunitas (greedy modularity)')
ax.axis('off');fig.tight_layout();fig.savefig(OUT/'E_projection.png',dpi=180);plt.close(fig)
print('saved E_projection.png',proj.number_of_nodes(),proj.number_of_edges(),len(comms))
print('images:',[p.name for p in OUT.glob('*.png')])
