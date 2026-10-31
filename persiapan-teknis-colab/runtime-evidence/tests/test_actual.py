import unittest, json, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from prep_audit import fingerprint, inspect_csv, audit_transactions, guard_methodology, verify_expected
class ActualDataTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root=Path('/content'); cls.cfg=json.loads((ROOT/'config.json').read_text())
    def test_all_source_fingerprints(self):
        for name, expected in self.cfg['expected_files'].items():
            actual=inspect_csv(self.root/name)
            verify_expected(actual, expected)
    def test_actual_transaction_integrity(self):
        a=audit_transactions(self.root/'DataCoSupplyChainDataset.csv',self.cfg)
        self.assertEqual(a['rows'],180519)
        self.assertEqual(a['raw_orders'],65752)
        self.assertEqual(a['retained_orders'],62897)
        self.assertEqual(a['retained_rows'],172765)
        self.assertEqual(a['mixed_orders'],0)
        self.assertEqual(a['target_conflict_orders'],0)
        self.assertEqual(a['date_conflict_orders'],0)
        self.assertEqual(a['duplicate_item_id_excess'],0)
    def test_model_gate_closed(self):
        with self.assertRaises(PermissionError): guard_methodology(self.cfg)
    def test_manifest_rejects_actual_file_wrong_hash(self):
        actual=fingerprint(self.root/'DataCoSupplyChainDataset.csv')
        with self.assertRaises(ValueError): verify_expected(actual,{'sha256':'0'*64})
    def test_readonly_source_hashes(self):
        before={n:fingerprint(self.root/n)['sha256'] for n in self.cfg['expected_files']}
        inspect_csv(self.root/'DescriptionDataCoSupplyChain.csv')
        after={n:fingerprint(self.root/n)['sha256'] for n in self.cfg['expected_files']}
        self.assertEqual(before,after)
if __name__=='__main__': unittest.main(verbosity=2)
