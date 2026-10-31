"""Audit read-only Tahap A. Tidak membangun fitur, split aktual, graph, atau model."""
import csv
import json
import hashlib
import sys
import platform
from pathlib import Path
from collections import Counter, defaultdict
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parent.parent
OUT = Path(__file__).resolve().parent

def summarize_orders(rows):
    orders = {}
    item_ids = set()
    duplicate_items = 0
    mapping = defaultdict(Counter)
    blanks = Counter()
    statuses = Counter()
    alias_mismatch = 0
    n = 0
    for row in rows:
        n += 1
        for key in ('Order Id','Order Item Id','Category Id','Category Name'):
            if not row[key].strip(): blanks[key] += 1
        if not row['Order Id'].strip() or not row['Order Item Id'].strip():
            raise ValueError('Missing grouping/item key')
        if row['Late_delivery_risk'] not in ('0','1'): raise ValueError('Invalid target')
        status = row['Delivery Status']
        if status not in ('Late delivery','Advance shipping','Shipping on time','Shipping canceled'):
            raise ValueError('Unknown delivery status: '+status)
        statuses[status] += 1
        if row['Order Item Id'] in item_ids: duplicate_items += 1
        item_ids.add(row['Order Item Id'])
        dt = datetime.strptime(row['order date (DateOrders)'], '%m/%d/%Y %H:%M')
        obj = orders.setdefault(row['Order Id'], {'labels':set(),'dates':set(),'n':0,'canceled':0})
        obj['labels'].add(row['Late_delivery_risk'])
        obj['dates'].add(dt)
        obj['n'] += 1
        obj['canceled'] += status == 'Shipping canceled'
        mapping[row['Category Id']][row['Category Name']] += 1
        alias_mismatch += row['Category Id'] != row['Product Category Id']
    if any(len(o['labels']) != 1 for o in orders.values()): raise ValueError('Inconsistent target per Order Id')
    if any(len(o['dates']) != 1 for o in orders.values()): raise ValueError('Inconsistent order date')
    classes = Counter({'all_retained':0,'all_canceled':0,'mixed':0})
    class_rows = Counter()
    retained = []
    retained_rows = 0
    for obj in orders.values():
        kind = 'all_retained' if obj['canceled']==0 else ('all_canceled' if obj['canceled']==obj['n'] else 'mixed')
        classes[kind] += 1
        class_rows[kind] += obj['n']
        if kind == 'all_retained':
            # Singleton extraction only after assertions; never voting/MAX target.
            retained.append((next(iter(obj['dates'])), next(iter(obj['labels']))))
            retained_rows += obj['n']
    months = defaultdict(Counter)
    for dt,y in retained: months[dt.strftime('%Y-%m')][y] += 1
    candidates = []
    # Diagnostic counts for alternative boundaries only. No rows assigned/saved as splits.
    for a,b in [('2017-01-01','2017-07-01'),('2017-07-01','2017-10-01'),('2017-09-01','2017-12-01')]:
        da,db = datetime.fromisoformat(a),datetime.fromisoformat(b)
        c = {x:Counter() for x in ('train','validation','test')}
        for dt,y in retained: c['train' if dt<da else 'validation' if dt<db else 'test'][y] += 1
        candidates.append({'train_before':a,'validation_before':b,'test_from':b,'counts':{k:{'orders':sum(v.values()),'label_0':v['0'],'label_1':v['1'],'positive_rate':v['1']/sum(v.values()) if v else None} for k,v in c.items()}})
    return {'raw_rows':n,'raw_orders':len(orders),'distinct_item_ids':len(item_ids),'duplicate_item_id_excess_rows':duplicate_items,'blank_key_category_rows':dict(blanks),'delivery_status_row_counts':dict(statuses),'population_classes':dict(classes),'population_class_rows':dict(class_rows),'retained_rows':retained_rows,'retained_orders':len(retained),'retained_order_labels':dict(Counter(y for _,y in retained)),'label_inconsistent_orders':0,'order_date_inconsistent_orders':0,'order_date_min':min(dt for dt,_ in retained).isoformat(),'order_date_max':max(dt for dt,_ in retained).isoformat(),'monthly_order_counts':{k:dict(v) for k,v in sorted(months.items())},'temporal_boundary_options':candidates,'category_mapping':{k:dict(v) for k,v in mapping.items()},'category_alias_mismatch_rows':alias_mismatch,'note':'Hanya metadata hitungan; tidak menyimpan observasi order, fitur, atau partisi aktual.'}

if __name__ == '__main__':
    started = datetime.now(timezone.utc).isoformat()
    protected = list((ROOT/'data/raw').glob('*.csv')) + [ROOT/'baseline-mahasiswa-assignment-II.txt',ROOT/'audit-gate-feature-decision/lembar-keputusan-fitur.txt',ROOT/'audit-gate-category-quantity-temporal/laporan-bukti.txt',ROOT/'audit-gate-category-quantity-temporal/audit-results.json',ROOT/'audit-gate-category-quantity-temporal/category-id-name-audit.csv',Path('/Users/rafaelyudianto/Downloads/Assignment I - Big Data Architecture Revised - Italic Corrected.docx'),Path('/Users/rafaelyudianto/Downloads/COMP8035041 - Personal - Assignment II.pdf')]
    before = {str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in protected}
    manifest = json.loads((ROOT/'data/source-manifest.json').read_text())
    matches = {e['file']:before[e['file']]==e['sha256'] for e in manifest['files']}
    assert all(matches.values()), 'Source integrity mismatch'
    with (ROOT/'data/raw/DataCoSupplyChainDataset.csv').open(encoding='latin1',newline='') as f:
        reader=csv.DictReader(f)
        headers=reader.fieldnames
        results=summarize_orders(reader)
    old=json.loads((ROOT/'audit-gate-category-quantity-temporal/audit-results.json').read_text())
    assert results['raw_rows']==old['raw']['rows']
    assert results['raw_orders']==old['raw']['orders']
    assert results['retained_rows']==old['historical_noncanceled']['rows']
    assert results['retained_orders']==old['historical_noncanceled']['orders']
    prior_map={r['Category Id']:{r['Category Name']:r['source_rows']} for r in old['raw']['category_mapping']}
    assert results['category_mapping']==prior_map
    with (ROOT/'audit-gate-unit-features/inventaris-kolom.csv').open(newline='') as f:
        inventory=list(csv.DictReader(f))
    financial={'Order Item Product Price','Product Price','Order Item Discount','Order Item Discount Rate','Sales','Order Item Total','Sales per customer','Benefit per order','Order Profit Per Order','Order Item Profit Ratio'}
    banned={'Late_delivery_risk','Delivery Status','Days for shipping (real)','shipping date (DateOrders)','Customer Email','Customer Password','Product Description','Product Image','Order Status'}|financial
    candidates={'Type','Shipping Mode','Days for shipment (scheduled)','order date (DateOrders)','Customer Segment','Market','Order City','Order Country','Order Region','Order State','Category Id'}
    unknown={'Customer City','Customer Country','Customer State','Customer Street','Customer Zipcode','Latitude','Longitude','Order Zipcode'}
    for r in inventory:
        c=r['source_name']
        r['current_status']='dikecualikan' if c in banned or c=='(turunan audit)' else 'kandidat' if c in candidates else 'belum diketahui' if c in unknown else 'menunggu keputusan mahasiswa'
        r['current_reason']='Batas baseline/master prompt: target/outcome/status akhir/privasi/keuangan; bukan seluruhnya leakage.' if c in banned else 'Semantik lokasi atau definisi belum cukup.' if c in unknown else 'Belum disetujui sebagai fitur; bukti as-of tidak tersedia.'
        r['lineage']='raw:'+c if c!='(turunan audit)' else 'Days for shipping (real) - Days for shipment (scheduled); audit-only'
        r['evidence_source']='audit-gate-unit-features/inventaris-kolom.csv; keputusan terbaru master prompt; laporan-bukti.txt'
        if c in financial: r['audit_status']='DIKECUALIKAN; TERMASUK TURUNAN DAN BOBOT'
        if c=='Category Name': r['current_reason']='Hanya label deskriptif Category Id; bukan identitas alternatif atau kandidat prediktor otomatis.'
        if c in ('Order Id','Order Item Id','Customer Id','Order Customer Id'): r['current_reason']='Kunci grouping/audit/relasi; nilai ID bukan fitur default; count item masih perlu persetujuan.'
    src=[r['source_name'] for r in inventory if r['source_name']!='(turunan audit)']
    assert src==headers and len(set(src))==len(headers)
    assert all(r['source_definition'] and r['temporal_evidence'] and r['current_status'] and r['lineage'] for r in inventory)
    with (OUT/'inventaris-kolom-terkini.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(inventory[0])); w.writeheader(); w.writerows(inventory)
    with (OUT/'distribusi-bulanan-pesanan.csv').open('w',newline='') as f:
        w=csv.writer(f); w.writerow(['month','orders','label_0','label_1'])
        for month,c in results['monthly_order_counts'].items():w.writerow([month,sum(c.values()),c.get('0',0),c.get('1',0)])
    root_expected=[ROOT/'Assignment I - Big Data Architecture Revised - Italic Corrected.docx',ROOT/'COMP8035041 - Personal - Assignment II.pdf']
    after={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in protected}
    assert before==after
    results.update({'run_id':started,'python':sys.version,'executable':sys.executable,'platform':platform.platform(),'protected_hashes_before':before,'protected_hashes_after':after,'protected_unchanged':before==after,'manifest_matches':matches,'missing_exact_root_paths':[str(p) for p in root_expected if not p.exists()],'actual_document_paths':[str(p) for p in protected if p.suffix in ('.docx','.pdf')],'source_columns':len(headers),'inventory_source_columns':len(src),'inventory_derived_audit_rows':1,'inventory_status_counts':dict(Counter(r['current_status'] for r in inventory if r['source_name']!='(turunan audit)')),'reuse':'Audit lama Quantity/variasi/temporal dirujuk, tidak dijalankan ulang; scan ini diperlukan rekonsiliasi dan distribusi waktu aktual baru.','feature_matrix_created':False,'training_executed':False,'graph_created':False})
    (OUT/'audit-stage-A.json').write_text(json.dumps(results,indent=2,ensure_ascii=False))
    paths=[p for p in ROOT.rglob('*') if p.is_file() and 'output-tahap-AB' not in p.parts]
    (OUT/'struktur-direktori.txt').write_text('\n'.join(str(p.relative_to(ROOT)) for p in paths))
    print(json.dumps({k:results[k] for k in ['run_id','raw_rows','raw_orders','population_classes','retained_rows','retained_orders','retained_order_labels','temporal_boundary_options','inventory_status_counts','protected_unchanged','manifest_matches','missing_exact_root_paths']},indent=2))
