"""Read-only raw-data audit. No feature/model/graph implementation."""
import csv, json, hashlib, logging, sys
from pathlib import Path
from collections import Counter, defaultdict
from datetime import datetime, timezone

def fingerprint(path):
    path=Path(path); h=hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda:f.read(1024*1024), b''): h.update(block)
    return {'path':str(path.resolve()),'bytes':path.stat().st_size,'sha256':h.hexdigest()}

def verify_expected(actual, expected):
    for k,v in expected.items():
        if k not in actual or actual[k]!=v:
            raise ValueError('Manifest mismatch: '+k+' actual='+str(actual.get(k))+' expected='+str(v))

def read_raw(path):
    # Explicit encoding; retain literal strings, leading zeros and missing values.
    with Path(path).open(encoding='latin1',newline='') as f:
        reader=csv.DictReader(f)
        if not reader.fieldnames or len(set(reader.fieldnames))!=len(reader.fieldnames):
            raise ValueError('Missing/duplicate schema names')
        for row in reader:
            if None in row or any(v is None for v in row.values()):
                raise ValueError('Malformed CSV record')
            yield row

def inspect_csv(path):
    info=fingerprint(path)
    with Path(path).open(encoding='latin1',newline='') as f:
        r=csv.reader(f); header=next(r)
        if len(set(header))!=len(header): raise ValueError('Duplicate columns')
        n=0; seen=set(); duplicate=0; missing=Counter(); numeric=set(header)
        for row in r:
            n+=1
            if len(row)!=len(header): raise ValueError('CSV width mismatch at '+str(n))
            # Store row hashes only: do not log PII or source row contents.
            key=hashlib.sha256(json.dumps(row,ensure_ascii=False,separators=(',',':')).encode()).digest()
            duplicate+=key in seen; seen.add(key)
            for col,value in zip(header,row):
                if value.strip()=='': missing[col]+=1
                elif col in numeric:
                    try: float(value)
                    except ValueError: numeric.remove(col)
    info.update(rows=n,columns=len(header),schema=header,blank_cells=dict(missing),duplicate_row_excess=duplicate,parseable_numeric_columns=sorted(numeric),encoding='latin1',schema_types='Raw strings; numeric parseability is audit only, not conversion.')
    return info

def audit_transactions(path, config):
    required={'Order Id','Order Item Id','Late_delivery_risk','Delivery Status','order date (DateOrders)','shipping date (DateOrders)','Category Id','Category Name','Product Category Id'}
    orders={}; item_ids=set(); n=0; dup=0; status=Counter(); y_rows=Counter(); mapping=defaultdict(set); alias=0
    with Path(path).open(encoding='latin1',newline='') as f:
        headers=csv.DictReader(f).fieldnames
    if not required.issubset(headers): raise ValueError('Missing required columns: '+str(required-set(headers)))
    for row in read_raw(path):
        n+=1
        if not row['Order Id'].strip() or not row['Order Item Id'].strip(): raise ValueError('Missing key')
        y=row['Late_delivery_risk']
        if y not in ('0','1'): raise ValueError('Target not binary 0/1')
        st=row['Delivery Status']; status[st]+=1; y_rows[y]+=1
        if st not in ('Late delivery','Advance shipping','Shipping on time','Shipping canceled'): raise ValueError('Unknown status')
        dt=datetime.strptime(row['order date (DateOrders)'],config['date_format'])
        ship=datetime.strptime(row['shipping date (DateOrders)'],config['date_format'])
        item=row['Order Item Id']; dup+=item in item_ids; item_ids.add(item)
        o=orders.setdefault(row['Order Id'],{'y':set(),'date':set(),'ship':set(),'n':0,'cancel':0})
        o['y'].add(y); o['date'].add(dt); o['ship'].add(ship); o['n']+=1; o['cancel']+=st=='Shipping canceled'
        mapping[row['Category Id']].add(row['Category Name']); alias+=row['Category Id']!=row['Product Category Id']
    label_conf=sum(len(o['y'])!=1 for o in orders.values()); date_conf=sum(len(o['date'])!=1 for o in orders.values()); ship_conf=sum(len(o['ship'])!=1 for o in orders.values())
    if label_conf or date_conf: raise ValueError('Non-singleton order target/date')
    retained=[o for o in orders.values() if not o['cancel']]
    canceled=[o for o in orders.values() if o['cancel']==o['n']]
    mixed=[o for o in orders.values() if 0<o['cancel']<o['n']]
    months=defaultdict(Counter)
    for o in retained: months[next(iter(o['date'])).strftime('%Y-%m')][next(iter(o['y']))]+=1
    return {'rows':n,'raw_orders':len(orders),'duplicate_item_id_excess':dup,'target_row_counts':dict(y_rows),'status_row_counts':dict(status),'target_conflict_orders':label_conf,'date_conflict_orders':date_conf,'shipping_date_conflict_orders':ship_conf,'retained_orders':len(retained),'retained_rows':sum(o['n'] for o in retained),'canceled_orders':len(canceled),'canceled_rows':sum(o['n'] for o in canceled),'mixed_orders':len(mixed),'retained_order_labels':dict(Counter(next(iter(o['y'])) for o in retained)),'retained_order_date_min':min(next(iter(o['date'])) for o in retained).isoformat(),'retained_order_date_max':max(next(iter(o['date'])) for o in retained).isoformat(),'monthly_order_label_counts':{m:dict(c) for m,c in sorted(months.items())},'category_ids':len(mapping),'category_names':len(set.union(*mapping.values())),'category_mapping_conflicts':sum(len(v)!=1 for v in mapping.values()),'category_alias_mismatch_rows':alias,'note':'Raw snapshot metadata only; no order feature table, transformation, split or model.'}

def guard_methodology(config):
    m=config['methodology']
    if not m['approved'] or any(m[k] is None for k in ('features','algorithms','split','metrics','threshold','graph')):
        raise PermissionError('Methodology decisions incomplete; implementation gate closed')

def run(root, out):
    out=Path(out); root=Path(root); cfg=json.loads((out/'config.json').read_text())
    logging.basicConfig(filename=out/'execution.log',level=logging.INFO,format='%(asctime)sZ %(levelname)s %(message)s',force=True)
    logging.Formatter.converter=__import__('time').gmtime
    before={name:fingerprint(root/name) for name in cfg['expected_files']}
    report={'timestamp_utc':datetime.now(timezone.utc).isoformat(),'files':[]}
    for name,expected in cfg['expected_files'].items():
        logging.info('Reading source %s',name)
        actual=inspect_csv(root/name); verify_expected(actual,expected)
        actual['manifest_match']=True; report['files'].append(actual)
    report['transactions']=audit_transactions(root/'DataCoSupplyChainDataset.csv',cfg)
    after={name:fingerprint(root/name) for name in cfg['expected_files']}
    if before!=after: raise RuntimeError('Source changed during audit')
    report.update(source_hashes_before=before,source_hashes_after=after,source_unchanged=True,feature_matrix_created=False,split_created=False,training_executed=False,graph_created=False)
    (out/'audit.json').write_text(json.dumps(report,indent=2))
    logging.info('Audit complete; source hashes unchanged; no features, split, graph or fit')
    return report

if __name__=='__main__':
    report=run(sys.argv[1],sys.argv[2]); print(json.dumps(report,indent=2))
