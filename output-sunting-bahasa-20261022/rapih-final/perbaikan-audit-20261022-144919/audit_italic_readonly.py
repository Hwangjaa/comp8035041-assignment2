from pathlib import Path
from zipfile import ZipFile
from lxml import etree as E
import re,json,hashlib
base=Path(__file__).parent
src=base.parent/'Assignment-II-DataCo-Laporan-Final-Rapi-20261022.docx'
sha=lambda:hashlib.sha256(src.read_bytes()).hexdigest()
before=sha()
with ZipFile(src) as z:
 root=E.fromstring(z.read('word/document.xml'))
 styles=E.fromstring(z.read('word/styles.xml'))
ns={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main','m':'http://schemas.openxmlformats.org/officeDocument/2006/math'}
w=lambda s:'{'+ns['w']+'}'+s
def txt(el):return ''.join(el.xpath('.//w:t/text()',namespaces=ns))
def prop(el,name):
 if el is None:return None
 x=el.find(w(name))
 return None if x is None else x.get(w('val'),'1') not in ('0','false','off')
smap={s.get(w('styleId')):s for s in styles.findall(w('style'))}
def inherited(sid,seen=None):
 seen=set() if seen is None else seen
 if not sid or sid in seen:return None
 seen.add(sid); s=smap.get(sid)
 if s is None:return None
 v=prop(s.find(w('rPr')),'i')
 if v is not None:return v
 b=s.find(w('basedOn'))
 return inherited(b.get(w('val')) if b is not None else None,seen)
def ital(r,p):
 v=prop(r.find(w('rPr')),'i')
 if v is not None:return v
 rs=r.find('w:rPr/w:rStyle',ns)
 if rs is not None:
  v=inherited(rs.get(w('val')))
  if v is not None:return v
 ps=p.find('w:pPr/w:pStyle',ns)
 return bool(inherited(ps.get(w('val')) if ps is not None else 'Normal'))
body=root.find(w('body')); allpars=root.xpath('.//w:body//w:p',namespaces=ns)
bodypars=body.findall(w('p')); pindex={p:i+1 for i,p in enumerate(bodypars)}
records=[]; issues=[]; references=[]; caps=[]; headings=[]; tables=[]
for i,p in enumerate(allpars,1):
 t=txt(p); loc={'xml_paragraph':i,'body_paragraph':pindex.get(p),'text':t}
 runs=[]; pos=0
 for ri,r in enumerate(p.findall(w('r')),1):
  rt=txt(r); runs.append({'run':ri,'start':pos,'end':pos+len(rt),'text':rt,'italic':ital(r,p)});pos+=len(rt)
 loc['runs']=runs;records.append(loc)
 for m in re.finditer(r'\b[\w-]+\b',t):
  word=m.group(); a,b=m.span(); seg=[r for r in runs if r['end']>a and r['start']<b]
  partial=[r for r in seg if r['italic'] and (r['start']>a or r['end']<b)]
  if partial and any(not r['italic'] for r in seg):
   issues.append({**{k:v for k,v in loc.items() if k!='runs'},'word':word,'span':[a,b],'segments':seg})
 for m in re.finditer(r'\bTabel\s+(\d+(?:\.\d+)*)',t,re.I):
  references.append({'number':m.group(1),'body_paragraph':loc['body_paragraph'],'xml_paragraph':i,'text':t})
 if re.match(r'^Tabel\s+\d',t):caps.append({k:v for k,v in loc.items() if k!='runs'})
 ps=p.find('w:pPr/w:pStyle',ns)
 if ps is not None and ('Heading' in ps.get(w('val'),'') or t.startswith('BAB ')):
  headings.append({'body_paragraph':loc['body_paragraph'],'text':t,'pPr':E.tostring(p.find(w('pPr')),encoding='unicode')})
for ti,tb in enumerate(body.findall(w('tbl')),1):
 prev=tb.getprevious()
 tables.append({'table':ti,'previous':txt(prev) if prev is not None else None,'first_rows':[txt(r) for r in tb.findall(w('tr'))[:2]],'properties':E.tostring(tb.find(w('tblPr')),encoding='unicode')})
report={'source':str(src),'sha256_before':before,'sha256_after':sha(),'counts':{'body_paragraphs':len(bodypars),'tables':len(tables),'drawings':len(root.xpath('.//w:drawing',namespaces=ns)),'equations':len(root.xpath('.//m:oMath',namespaces=ns))},'partial_italic_words':issues,'table_references':references,'caption_candidates':caps,'headings':headings,'tables':tables,'sections':[E.tostring(s,encoding='unicode') for s in root.xpath('.//w:sectPr',namespaces=ns)],'paragraph_records':records}
(base/'audit_italic_layout_evidence.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
print(json.dumps({k:v for k,v in report.items() if k not in ['paragraph_records','tables','sections','headings']},ensure_ascii=False,indent=2))
