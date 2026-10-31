"""Regression kontrak item; dapat diarahkan ke pipeline lama untuk bukti RED."""
import importlib
import os
import unittest
import pandas as pd

mod = importlib.import_module(os.environ.get('ORDERS_MODULE', 'dataco_qa_v1.pipeline'))

def fixture():
    return pd.DataFrame({
        'Order Id': [1, 1], 'Order Item Id': [10, 10], 'Category Id': [73, 999],
        'Delivery Status': ['Late delivery'] * 2,
        'Days for shipment (scheduled)': [4, 4], 'Customer Segment': ['Consumer'] * 2,
        'Market': ['Pacific Asia'] * 2, 'order date (DateOrders)': ['6/1/2017 0:00'] * 2,
        'Late_delivery_risk': [1, 1]})

class OrdersTests(unittest.TestCase):
    def test_conflicting_item_categories_rejected(self):
        with self.assertRaisesRegex(ValueError, 'Order Item Id.*Category Id'):
            mod.make_orders(fixture())

    def test_cross_order_item_conflict_rejected(self):
        d = fixture(); d.loc[1, 'Order Id'] = 2
        with self.assertRaisesRegex(ValueError, 'Order Item Id.*Category Id'):
            mod.make_orders(d)

    def test_missing_vs_present_category_conflict_rejected(self):
        d = fixture(); d.loc[1, 'Category Id'] = float('nan')
        with self.assertRaisesRegex(ValueError, 'Order Item Id.*Category Id'):
            mod.make_orders(d)

    def test_valid_distinct_items_accepted(self):
        d = fixture(); d.loc[1, 'Order Item Id'] = 11
        orders, items, audit = mod.make_orders(d)
        self.assertEqual(orders.item_count.tolist(), [2])
        self.assertEqual(orders.categories.tolist(), [['73', '999']])
        self.assertEqual(audit['retained_items'], 2)

    def test_repeated_consistent_item_accepted(self):
        d = fixture(); d.loc[1, 'Category Id'] = 73
        orders, _, _ = mod.make_orders(d)
        self.assertEqual(orders.item_count.tolist(), [1])
        self.assertEqual(orders.categories.tolist(), [['73']])

if __name__ == '__main__':
    unittest.main()
