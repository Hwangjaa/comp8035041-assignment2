"""Encoder namespace stabil; kontrak lama tidak berubah."""
import numpy as np
import pandas as pd
from scipy import sparse

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
