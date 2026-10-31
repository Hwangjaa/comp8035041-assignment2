"""Verifikasi artefak audit; bukan eksperimen model."""
import json
import csv
import hashlib
from pathlib import Path
p=Path(__file__).resolve().parent
a=json.loads((p/'audit-stage-A.json').read_text())
old=json.loads((p.parent/'audit-gate-category-quantity-temporal/audit-results.json').read_text())
assert all(a['protected_hashes_before'][k]==v for k,v in old['source_hashes_before'].items())
assert all(hashlib.sha256(Path(k).read_bytes()).hexdigest()==v for k,v in a['protected_hashes_after'].items())
assert sum(a['population_class_rows'].values())==a['raw_rows']
assert sum(a['population_classes'].values())==a['raw_orders']
assert sum(a['retained_order_labels'].values())==a['retained_orders']
assert all(sum(v['orders'] for v in s['counts'].values())==a['retained_orders'] for s in a['temporal_boundary_options'])
with (p/'inventaris-kolom-terkini.csv').open() as f: rows=list(csv.DictReader(f))
assert len(rows)==54
assert sum(a['inventory_status_counts'].values())==53
text=(p/'paket-keputusan-mahasiswa.txt').read_text()
assert all(s in text for s in ['A. KANDIDAT','B. FEATURE ENGINEERING','C. ALGORITMA','D. VALIDASI','E. EVALUASI','F. GRAPH','G. FORMULIR'])
print('PASS: hashes sumber tetap, rekonsiliasi populasi/target/waktu, 53 kolom sumber + turunan audit, paket keputusan A–F.')
