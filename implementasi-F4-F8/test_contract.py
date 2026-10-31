import unittest
from pathlib import Path

class ContractTest(unittest.TestCase):
    def test_d2_boundaries(self):
        import implementation as m
        self.assertEqual(m.partition('2017-06-30T23:59:00'), 'train')
        self.assertEqual(m.partition('2017-07-01T00:00:00'), 'validation')
        self.assertEqual(m.partition('2017-09-30T23:59:00'), 'validation')
        self.assertEqual(m.partition('2017-10-01T00:00:00'), 'test')

class EvaluatorTest(unittest.TestCase):
    def test_threshold_exhaustive_reference(self):
        import implementation as m
        import numpy as np
        from sklearn.metrics import f1_score
        # Data uji unit saja, bukan hasil eksperimen atau benchmark.
        y = np.array([1, 0, 1, 0, 1, 0])
        p = np.array([0.9, 0.8, 0.6, 0.6, 0.3, 0.1])
        candidates = list(np.unique(p)) + [np.nextafter(p.max(), np.inf)]
        expected = max(candidates, key=lambda t: (f1_score(y, p >= t, zero_division=0), t))
        self.assertEqual(m.select_threshold(y, p), expected)
    def test_constant_prior_and_undefined_precision(self):
        import implementation as m
        self.assertGreater(m.select_threshold([0, 0], [0.2, 0.2]), 0.2)
        r = m.evaluate([0, 1], [0.3, 0.3], 0.5)
        self.assertEqual(r['confusion_matrix'], [[1, 0], [1, 0]])
        self.assertIn('precision', r['undefined'])
    def test_recall_uses_binary_predictions(self):
        import implementation as m
        r = m.evaluate([0, 1, 1], [0.1, 0.7, 0.3], 0.5)
        self.assertEqual(r['recall'], 0.5)
    def test_missing_feature_contract_blocks_training(self):
        import implementation as m
        with self.assertRaisesRegex(ValueError, 'F1'):
            m.pretraining_guard({'F1_F3': {'exact_payload_recovered': False}})

if __name__ == '__main__': unittest.main()
