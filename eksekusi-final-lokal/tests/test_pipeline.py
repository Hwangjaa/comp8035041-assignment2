"""Kontrak fitur dan metode pipeline."""
import unittest
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
import pandas as pd

class OrderContract(unittest.TestCase):
    def test_conflicting_singleton_stops(self):
        import pipeline
        d=pd.DataFrame({'Order Id':[1,1], 'Order Item Id':[1,2], 'Category Id':[13,37], 'Days for shipment (scheduled)':[2,3], 'Customer Segment':['Consumer']*2,'Market':['Europe']*2,'order date (DateOrders)':['1/1/2017 0:00']*2,'Late_delivery_risk':[1,1],'Delivery Status':['Late delivery']*2})
        with self.assertRaisesRegex(ValueError,'singleton'):
            pipeline.make_orders(d)

class FeatureContract(unittest.TestCase):
    def test_unknown_and_missing_and_distinct_category_ids(self):
        import pipeline
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
        import pipeline
        import numpy as np
        from sklearn.metrics import f1_score
        y=np.array([1,0,1,0,1,0]);p=np.array([.9,.8,.6,.6,.3,.1])
        candidates=list(np.unique(p))+[np.nextafter(p.max(),np.inf)]
        expected=max(candidates,key=lambda t:(f1_score(y,p>=t,zero_division=0),t))
        self.assertEqual(pipeline.threshold(y,p),expected)
        self.assertGreater(pipeline.threshold([0,0],[.2,.2]),.2)

if __name__=='__main__': unittest.main()
