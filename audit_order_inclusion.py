"""Audit inklusi pesanan baca-saja; tidak mengagregasi fitur atau melatih model."""
import csv
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'audit-gate-unit-features'
RAW = ROOT / 'data/raw/DataCoSupplyChainDataset.csv'
orders = defaultdict(Counter)
item_ids = Counter()
blank_order_rows = 0
blank_item_rows = 0
unexpected_statuses = Counter()
known = {'Shipping canceled', 'Advance shipping', 'Late delivery', 'Shipping on time'}
before = hashlib.sha256(RAW.read_bytes()).hexdigest()
with RAW.open(encoding='latin1', newline='') as f:
    for row in csv.DictReader(f):
        oid = row['Order Id']
        status = row['Delivery Status']
        orders[oid]['canceled' if status == 'Shipping canceled' else 'retained'] += 1
        blank_order_rows += not bool(oid.strip())
        blank_item_rows += not bool(row['Order Item Id'].strip())
        item_ids[row['Order Item Id']] += 1
        if status not in known:
            unexpected_statuses[status] += 1
classes = Counter()
rows_by_class = Counter()
for counts in orders.values():
    cls = ('mixed' if counts['canceled'] and counts['retained'] else
           'all_canceled' if counts['canceled'] else 'all_retained')
    classes[cls] += 1
    rows_by_class[cls] += sum(counts.values())
retained_rows = sum(c['retained'] for c in orders.values())
canceled_rows = sum(c['canceled'] for c in orders.values())
retained_orders = sum(c['retained'] > 0 for c in orders.values())
fully_retained_orders = classes['all_retained']
fully_retained_rows = rows_by_class['all_retained']
assert before == hashlib.sha256(RAW.read_bytes()).hexdigest()
assert sum(classes.values()) == len(orders)
assert sum(rows_by_class.values()) == retained_rows + canceled_rows
prior = json.loads((OUT / 'audit-results.json').read_text())
assert prior['scope_rows'] == retained_rows
assert prior['scope_orders'] == retained_orders
assert prior['mixed_canceled_and_noncanceled_orders'] == classes['mixed']
with (OUT / 'inventaris-kolom.csv').open(encoding='utf-8-sig', newline='') as f:
    inventory = list(csv.DictReader(f))
required = ['source_name', 'source_definition', 'temporal_evidence', 'timing_assessment',
            'possible_later_change', 'leakage_risk', 'audit_status']
assert len(inventory) == 54
assert len({r['source_name'] for r in inventory[:53]}) == 53
assert all(r[k].strip() for r in inventory for k in required)
status_counts = Counter(r['audit_status'] for r in inventory)
summary = {
    'execution_scope': 'Audit Python stdlib lokal; bukan Colab/Spark, bukan pipeline ML',
    'source_sha256': before,
    'raw_orders': len(orders), 'raw_rows': retained_rows + canceled_rows,
    'orders_by_cancellation_class': {k: classes[k] for k in ['all_retained', 'all_canceled', 'mixed']},
    'rows_by_cancellation_class': {k: rows_by_class[k] for k in ['all_retained', 'all_canceled', 'mixed']},
    'historical_item_filter_retained_rows': retained_rows,
    'historical_item_filter_excluded_rows': canceled_rows,
    'historical_item_filter_distinct_orders': retained_orders,
    'whole_order_exclusion_of_any_canceled_retained_orders': fully_retained_orders,
    'whole_order_exclusion_of_any_canceled_retained_rows': fully_retained_rows,
    'equivalent_in_this_snapshot': retained_rows == fully_retained_rows and retained_orders == fully_retained_orders,
    'blank_order_id_rows': blank_order_rows, 'blank_item_id_rows': blank_item_rows,
    'duplicate_item_id_excess_rows': sum(n-1 for n in item_ids.values()),
    'unexpected_delivery_status_counts': dict(unexpected_statuses),
    'inventory_records': len(inventory), 'inventory_source_columns': 53,
    'inventory_derived_audit_columns': 1, 'inventory_status_counts': dict(status_counts),
    'feature_aggregation_created': False, 'final_features_approved': False, 'model_trained': False,
    'interpretation': 'Perbandingan aturan merupakan audit sensitivitas, bukan pengesahan kebijakan untuk pesanan campuran di data masa depan. Filter status akhir bukan bukti lolos pembatalan pada cutoff.'
}
(OUT / 'audit-inklusi-pesanan.json').write_text(json.dumps(summary, indent=2, ensure_ascii=False))
lines = [
    'AUDIT INKLUSI PESANAN DAN INVENTARIS TEMPORAL',
    'Sumber: CSV transaksi dan kamus lokal; hash sumber dicatat dalam JSON pendamping.',
    'Baseline: filter item historis Delivery Status != Shipping canceled; clickstream tidak digunakan.',
    f'Baris sumber: {summary["raw_rows"]}; Order Id unik: {len(orders)}.',
    f'Pesanan seluruh item dipertahankan: {classes["all_retained"]}; item: {rows_by_class["all_retained"]}.',
    f'Pesanan seluruh item dibatalkan: {classes["all_canceled"]}; item: {rows_by_class["all_canceled"]}.',
    f'Pesanan campuran: {classes["mixed"]}; item terdampak: {rows_by_class["mixed"]}.',
    f'Hasil filter item historis: {retained_rows} item dari {retained_orders} Order Id unik.',
    'Dua aturan dibandingkan: mempertahankan item tidak batal versus mengecualikan seluruh pesanan bila ada item batal.',
    f'Kedua aturan ekuivalen pada snapshot ini: {summary["equivalent_in_this_snapshot"]}.',
    'Tidak mengesahkan kebijakan untuk pesanan campuran yang mungkin muncul pada data lain; pipeline harus menandainya sebelum agregasi.',
    'Populasi: pesanan yang seluruh itemnya tidak berstatus Shipping canceled pada snapshot historis akhir; bukan populasi terbukti lolos cancellation-check pada waktu prediksi.',
    'Belum membentuk dataset satu baris per pesanan. Hitungan harus diverifikasi ulang setelah aturan agregasi fitur ditetapkan.',
    'Inventaris: 53 kolom sumber + late_days (turunan audit). Seluruh isian definisi/lineage, bukti temporal, asumsi, risiko dan status terisi.',
    'Tidak ada bukti versi nilai as-of cutoff per atribut; konsistensi dalam Order Id bukan bukti temporal.',
    'Inventaris lengkap: inventaris-kolom.csv dan inventaris-kolom.txt.',
    'Tidak melatih model, mengesahkan fitur final, atau mengubah notebook/laporan asli/data mentah.'
]
(OUT / 'audit-inklusi-pesanan.txt').write_text('\n'.join(lines) + '\n')
print(json.dumps(summary, indent=2, ensure_ascii=False))
print('PASS: rekonsiliasi inklusi, hash sumber, dan kelengkapan inventaris.')
