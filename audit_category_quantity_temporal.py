"""Audit bukti baca-saja; bukan agregasi fitur, encoding, atau model."""
import csv
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'audit-gate-category-quantity-temporal'
OUT.mkdir(exist_ok=True)
RAW = ROOT / 'data/raw/DataCoSupplyChainDataset.csv'
DICT = ROOT / 'data/raw/DescriptionDataCoSupplyChain.csv'
protected = [RAW, DICT, ROOT/'baseline-mahasiswa-assignment-II.txt',
             ROOT/'audit-gate-feature-decision/lembar-keputusan-fitur.txt',
             Path.home()/'Downloads/Assignment I - Big Data Architecture Revised - Italic Corrected.docx',
             Path.home()/'Downloads/COMP8035041 - Personal - Assignment II.pdf']
def hashes():
    return {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in protected}
before = hashes()
with RAW.open(encoding='latin1', newline='') as f:
    reader = csv.DictReader(f)
    header = reader.fieldnames
    rows = list(reader)
assert all(None not in r and all(v is not None for v in r.values()) for r in rows)

def audit(rs):
    id_names = defaultdict(set)
    name_ids = defaultdict(set)
    pair_counts = Counter()
    ids = Counter()
    orders = defaultdict(list)
    product_categories = defaultdict(set)
    item_links = defaultdict(set)
    signatures = Counter()
    missing = Counter()
    quantities = Counter()
    for r in rs:
        cid, name = r['Category Id'], r['Category Name']
        id_names[cid].add(name)
        name_ids[name].add(cid)
        pair_counts[cid, name] += 1
        ids[r['Order Item Id']] += 1
        orders[r['Order Id']].append(r)
        product_categories[r['Product Card Id']].add(cid)
        item_links[r['Order Item Id']].add((r['Order Id'], r['Product Card Id'], r['Order Item Quantity'], cid))
        signatures[tuple(r[k] for k in header if k != 'Order Item Id')] += 1
        quantities[r['Order Item Quantity']] += 1
        for k in ['Category Id','Category Name','Order Item Id','Order Id','Order Item Quantity','Product Card Id']:
            missing[k] += not r[k].strip()
    multi = [v for v in orders.values() if len(v)>1]
    repeated = []
    for oid, rr in orders.items():
        prods = Counter(r['Product Card Id'] for r in rr)
        if any(n>1 for n in prods.values()):
            repeated.append(oid)
    example = next((rr for rr in multi if len({r['Order Item Quantity'] for r in rr})>1), [])
    return {
        'rows':len(rs), 'orders':len(orders), 'columns':len(header),
        'category_ids':len(id_names), 'category_names':len(name_ids),
        'missing_or_whitespace_rows':dict(missing),
        'ids_without_nonblank_name':sorted(k for k,v in id_names.items() if not any(x.strip() for x in v)),
        'id_to_multiple_raw_names':{k:sorted(v) for k,v in id_names.items() if len(v)>1},
        'name_to_multiple_ids':{k:sorted(v, key=int) for k,v in name_ids.items() if len(v)>1},
        'names_with_surrounding_whitespace':sorted(k for k in name_ids if k != k.strip()),
        'category_alias_mismatch_rows':sum(r['Category Id']!=r['Product Category Id'] for r in rs),
        'product_to_multiple_category_ids':{k:sorted(v) for k,v in product_categories.items() if len(v)>1},
        'category_mapping':[{'Category Id':k,'Category Name':n,'source_rows':v} for (k,n),v in sorted(pair_counts.items(), key=lambda x:int(x[0][0]))],
        'distinct_item_ids':len(ids),
        'duplicate_item_id_excess_rows':sum(n-1 for n in ids.values()),
        'item_ids_with_conflicting_order_product_quantity_category':sum(len(v)>1 for v in item_links.values()),
        'full_duplicate_excess_rows':len(rs)-len({tuple(r[k] for k in header) for r in rs}),
        'duplicate_except_item_id_excess_rows':sum(n-1 for n in signatures.values()),
        'quantity_value_row_counts':dict(sorted(quantities.items())),
        'non_positive_or_non_integer_quantity_rows':sum(not q.isdigit() or int(q)<=0 for q in (r['Order Item Quantity'] for r in rs)),
        'rows_per_order_distribution':dict(sorted(Counter(len(v) for v in orders.values()).items())),
        'multirow_orders':len(multi),
        'orders_with_quantity_variation':sum(len({r['Order Item Quantity'] for r in v})>1 for v in multi),
        'orders_with_repeated_product_id':len(repeated),
        'minimal_quantity_variation_example':[{k:r[k] for k in ['Order Id','Order Item Id','Product Card Id','Category Id','Order Item Quantity']} for r in example]
    }
result = {'method':'Python stdlib lokal, CSV latin1; diagnostik struktur dan pemetaan saja; tidak menjumlah Quantity',
          'source_headers':header,
          'raw':audit(rows),
          'historical_noncanceled':audit([r for r in rows if r['Delivery Status']!='Shipping canceled']),
          'reused_prior_evidence':'laporan-gerbang-fitur-agregasi.txt bagian 6: hubungan Sales dengan harga x Quantity; tidak diuji ulang dan bukan kandidat fitur',
          'temporal_header_candidates':[k for k in header if any(t in k.lower() for t in ['date','time','version','created','updated','effective'])],
          'source_hashes_before':before}
assert hashes() == before
manifest=json.loads((ROOT/'data/source-manifest.json').read_text())
for entry in manifest['files']:
    if entry['file'] in before:
        assert entry['sha256']==before[entry['file']]
result['protected_hashes_unchanged']=True
result['raw_and_dictionary_match_manifest']=True
result['quantity_sum_computed']=False
result['feature_aggregation_encoding_matrix_or_model_created']=False
(OUT/'audit-results.json').write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n')
with (OUT/'category-id-name-audit.csv').open('w', encoding='utf-8', newline='') as f:
    w=csv.DictWriter(f,fieldnames=['Category Id','Category Name','source_rows'])
    w.writeheader()
    w.writerows(result['raw']['category_mapping'])
for scope in ['raw','historical_noncanceled']:
    print(scope, json.dumps({k:v for k,v in result[scope].items() if k!='category_mapping'},ensure_ascii=False,indent=2))
print('temporal_header_candidates',result['temporal_header_candidates'])
print('PASS: hash sumber tetap; cocok manifest; tidak menghitung total Quantity atau fitur.')
