import csv,json,hashlib
from pathlib import Path
from collections import Counter,defaultdict
from datetime import datetime
root=Path(__file__).parent
raw=root/'data/raw'
rows=list(csv.DictReader((raw/'DataCoSupplyChainDataset.csv').open(encoding='latin1',newline='')))
cols=list(rows[0]); scope=[r for r in rows if r['Delivery Status']!='Shipping canceled']
parse=lambda s:datetime.strptime(s,'%m/%d/%Y %H:%M')
equal=0;invalid=0;dates=[];labels=Counter();same_order=defaultdict(set);mismatch=0
for r in rows:
 try:
  a=parse(r['order date (DateOrders)']);b=parse(r['shipping date (DateOrders)']);dates.append(a)
  equal+=((b-a).total_seconds()/86400==float(r['Days for shipping (real)']))
 except ValueError:invalid+=1
 if r['Delivery Status']!='Shipping canceled':
  labels[r['Late_delivery_risk']]+=1
  mismatch+=(int(r['Late_delivery_risk']) != int(float(r['Days for shipping (real)'])>float(r['Days for shipment (scheduled)'])))
 same_order[r['Order Id']].add((r['Late_delivery_risk'],r['order date (DateOrders)'],r['shipping date (DateOrders)']))
logs=list(csv.DictReader((raw/'tokenized_access_logs.csv').open(encoding='utf-8',newline='')))
logcols=list(logs[0]); dup=len(logs)-len(set(tuple(r[c] for c in logcols) for r in logs))
manifest=[]
for f in sorted(raw.glob('*.csv')):manifest.append({'file':f.name,'bytes':f.stat().st_size,'sha256':hashlib.sha256(f.read_bytes()).hexdigest()})
result={'transaction_rows':len(rows),'transaction_columns':len(cols),'unique_item_ids':len(set(r['Order Item Id'] for r in rows)),'unique_order_ids':len(same_order),'scope_rows':len(scope),'scope_order_ids':len(set(r['Order Id'] for r in scope)),'cancelled_rows':len(rows)-len(scope),'scope_labels':dict(labels),'transaction_duplicate_rows':len(rows)-len(set(tuple(r[c] for c in cols) for r in rows)),'order_date_min':str(min(dates)),'order_date_max':str(max(dates)),'invalid_dates':invalid,'duration_exact_match_rows':equal,'noncancelled_label_vs_duration_mismatch_rows':mismatch,'orders_with_inconsistent_label_or_timestamps':sum(len(v)>1 for v in same_order.values()),'empty_product_description_rows':sum(not r['Product Description'].strip() for r in rows),'clickstream_rows':len(logs),'clickstream_columns':logcols,'clickstream_duplicate_rows':dup,'clickstream_empty_cells':sum(not v.strip() for r in logs for v in r.values()),'clickstream_date_samples':[r['Date'] for r in logs[:3]],'clickstream_date_min_lexical':min(r['Date'] for r in logs),'clickstream_date_max_lexical':max(r['Date'] for r in logs),'files':manifest}
# Reproduire uniquement les règles déjà présentes dans Assignment I.
mapping={'order date (DateOrders)':'order_date','shipping date (DateOrders)':'shipping_date','Days for shipping (real)':'dispatch_real_days','Days for shipment (scheduled)':'dispatch_scheduled_days','Late_delivery_risk':'is_late'}
drop={'Customer Email','Customer Password','Product Description','Product Image'}
fields=[mapping.get(c,c) for c in cols if c not in drop]+['late_days']
clean=root/'data/clean';clean.mkdir(parents=True,exist_ok=True)
for name,selected in [('dataco_clean_items.csv',rows),('dataco_risk_scope.csv',scope)]:
 with (clean/name).open('w',encoding='utf-8',newline='') as f:
  w=csv.DictWriter(f,fieldnames=fields);w.writeheader()
  for r in selected:
   item={mapping.get(c,c):v for c,v in r.items() if c not in drop}
   item['order_date']=parse(item['order_date']).isoformat(sep=' ');item['shipping_date']=parse(item['shipping_date']).isoformat(sep=' ')
   item['late_days']=int(r['Days for shipping (real)'])-int(r['Days for shipment (scheduled)']);w.writerow(item)
result['clean_columns']=len(fields)
ldates=[parse(r['Date']) for r in logs]
result['clickstream_date_min']=str(min(ldates));result['clickstream_date_max']=str(max(ldates))
diffs=Counter();floormatch=0
for r in rows:
 delta=(parse(r['shipping date (DateOrders)'])-parse(r['order date (DateOrders)'])).total_seconds()/86400
 real=float(r['Days for shipping (real)'])
 diffs[round(delta-real,6)]+=1
 floormatch+=(int(delta)==real)
result['duration_floor_match_rows']=floormatch
result['duration_difference_days']=dict(diffs)
result['late_percentage']=len([r for r in scope if r['Late_delivery_risk']=='1'])/len(scope)*100
(root/'data/audit-results.json').write_text(json.dumps(result,ensure_ascii=False,indent=2))
print(json.dumps(result,ensure_ascii=False,indent=2))
