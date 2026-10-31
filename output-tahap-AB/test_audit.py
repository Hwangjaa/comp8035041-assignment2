"""Fixture unit-test buatan; bukan hasil dataset atau eksperimen."""
import unittest
from audit_stage_a import summarize_orders

class PopulationTest(unittest.TestCase):
    def test_mixed_orders_excluded_and_conflicting_target_rejected(self):
        def row(o,i,s,y='1',d='1/1/2017 0:00'):
            return {'Order Id':o,'Order Item Id':i,'Delivery Status':s,'Late_delivery_risk':y,'order date (DateOrders)':d,'Category Id':'13','Category Name':'Electronics','Product Category Id':'13'}
        result=summarize_orders([row('1','1','Late delivery'),row('2','2','Shipping canceled'),row('2','3','Late delivery')])
        self.assertEqual(result['population_classes'],{'all_retained':1,'all_canceled':0,'mixed':1})
        self.assertEqual(result['retained_rows'],1)
        self.assertEqual(result['retained_order_labels'],{'1':1})
        with self.assertRaises(ValueError):
            summarize_orders([row('1','1','Late delivery'),row('1','2','Late delivery','0')])
        for bad in [row('1','1','UNKNOWN'),row('','1','Late delivery'),row('1','1','Late delivery','2')]:
            with self.assertRaises(ValueError): summarize_orders([bad])
        with self.assertRaises(ValueError):
            summarize_orders([row('1','1','Late delivery'),row('1','2','Late delivery',d='1/2/2017 0:00')])

if __name__=='__main__': unittest.main()
