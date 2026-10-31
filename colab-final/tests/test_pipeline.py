"""Fixture kecil hanya untuk unit test; bukan hasil eksperimen."""
import unittest
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
import pandas as pd

class OrderContract(unittest.TestCase):
    def test_conflicting_singleton_stops(self):
        import pipeline_colab as pipeline
        d=pd.DataFrame({'Order Id':[1,1], 'Order Item Id':[1,2], 'Category Id':[13,37], 'Days for shipment (scheduled)':[2,3], 'Customer Segment':['Consumer']*2,'Market':['Europe']*2,'order date (DateOrders)':['1/1/2017 0:00']*2,'Late_delivery_risk':[1,1],'Delivery Status':['Late delivery']*2})
        with self.assertRaisesRegex(ValueError,'singleton'):
            pipeline.make_orders(d)

class FeatureContract(unittest.TestCase):
    def test_unknown_and_missing_and_distinct_category_ids(self):
        import pipeline_colab as pipeline
        train=pd.DataFrame({'Order Id':[1,2], 'Days for shipment (scheduled)':[2,3], 'item_count':[1,2], 'Customer Segment':['Consumer','Corporate'], 'Market':['Europe','LATAM'], 'categories':[['13'],['37']]})
        f=pipeline.Features().fit(train)
        unseen=train.iloc[:1].copy();unseen['Customer Segment']='new';unseen['Market']=None;unseen['categories']=[['99']]
        x=f.transform(unseen).toarray()[0]
        self.assertEqual(x[f.names.index('Customer Segment=UNKNOWN')],1)
        self.assertEqual(x[f.names.index('Market=MISSING')],1)
        self.assertEqual(x[f.names.index('Category Id=UNKNOWN')],1)
        self.assertNotEqual(f.names.index('Category Id=13'),f.names.index('Category Id=37'))
        self.assertNotIn('99',f.vocab['Category Id'])
    def test_all_negative_and_tied_threshold(self):
        import pipeline_colab as pipeline
        import numpy as np
        from sklearn.metrics import f1_score
        y=np.array([1,0,1,0,1,0]);p=np.array([.9,.8,.6,.6,.3,.1])
        candidates=list(np.unique(p))+[np.nextafter(p.max(),np.inf)]
        expected=max(candidates,key=lambda t:(f1_score(y,p>=t,zero_division=0),t))
        self.assertEqual(pipeline.threshold(y,p),expected)
        self.assertGreater(pipeline.threshold([0,0],[.2,.2]),.2)

class MethodContract(unittest.TestCase):
    @staticmethod
    def base_rows():
        return pd.DataFrame({
            'Order Id':[1,2,3], 'Order Item Id':[11,21,31], 'Category Id':[13,37,13],
            'Days for shipment (scheduled)':[2,3,4], 'Customer Segment':['Consumer']*3,
            'Market':['Europe']*3,
            'order date (DateOrders)':['6/30/2017 23:59','7/1/2017 0:00','10/1/2017 0:00'],
            'Late_delivery_risk':[0,1,0], 'Delivery Status':['Shipping on time','Late delivery','Advance shipping']
        })

    def test_temporal_boundaries_and_unique_orders(self):
        import pipeline_colab as pipeline
        orders,_,_=pipeline.make_orders(self.base_rows())
        self.assertEqual(orders['partition'].tolist(),['train','validation','test'])
        self.assertTrue(orders['Order Id'].is_unique)
        parts={p:set(orders.loc[orders.partition.eq(p),'Order Id']) for p in ['train','validation','test']}
        self.assertFalse(parts['train'] & parts['validation'])
        self.assertFalse(parts['train'] & parts['test'])
        self.assertFalse(parts['validation'] & parts['test'])

    def test_unknown_or_missing_delivery_status_stops(self):
        import pipeline_colab as pipeline
        bad=self.base_rows();bad.loc[0,'Delivery Status']='Typo status'
        with self.assertRaisesRegex(ValueError,'tidak dikenal'): pipeline.make_orders(bad)
        missing=self.base_rows();missing.loc[0,'Delivery Status']=None
        with self.assertRaisesRegex(ValueError,'missing'): pipeline.make_orders(missing)

    def test_train_only_vocabulary(self):
        import pipeline_colab as pipeline
        orders,_,_=pipeline.make_orders(self.base_rows())
        f=pipeline.Features().fit(orders.loc[orders.partition.eq('train')])
        self.assertNotIn('37',f.vocab['Category Id'])
        x=f.transform(orders.loc[orders.partition.eq('validation')]).toarray()[0]
        self.assertEqual(x[f.names.index('Category Id=UNKNOWN')],1)

if __name__=='__main__': unittest.main()
