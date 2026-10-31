from pathlib import Path
import re,json,hashlib
from docx import Document
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches,Pt
ROOT=Path(__file__).parent
SOURCE=ROOT.parent/'Assignment-II-DataCo-Laporan-Final-Rapi-20261022.docx'
OUT=ROOT/'Assignment-II-DataCo-Revisi-Audit.docx'
assert hashlib.sha256(SOURCE.read_bytes()).hexdigest()=='0d6f9095ba5489cf575afaab8a18bae9ab77181452db142ece8136adc68bc8cb'
d=Document(SOURCE)
terms=['Logistic Regression','Random Forest','Gradient Boosting','Shipping canceled','Journal of Machine Learning Research','Machine Learning','Knowledge Discovery','in-memory','connected components','connected component','community detection','eigenvector centrality','confusion matrix','binary F1','CS Lead','Data/IT','clickstream','filesystem','multi-node','benchmark','deployment','snapshot','timestamp','validation','precision','baseline','training','recall','cluster','pipeline','runtime','encoding','resampling','tuning','degree','market','hash','fitur','node','edge','test','run','event','as-of']
# Longest phrases first; spacing repairs only literal known terms, not arbitrary run boundaries.
terms.sort(key=len,reverse=True)
changes=[]
allp=list(d.paragraphs)
for t in d.tables:
 for row in t.rows:
  for c in row.cells: allp.extend(c.paragraphs)
for p in allp:
 old=p.text
 if not old or p._p.xpath('.//m:oMath|.//w:drawing'): continue
 s=old.replace('Journal ofMachine LearningResearch','Journal of Machine Learning Research').replace('KnowledgeDiscovery','Knowledge Discovery').replace('Averageprecision','Average precision').replace('pesanan.CS','pesanan. CS')
 s=s.replace('local\\[2]','local[2]').replace('zero\\_division','zero_division')
 terms_safe=[x for x in terms if x not in ('run','fitur','market','test','event')]
 for a,b in {'sebagaifitur':'sebagai fitur','bukanfitur':'bukan fitur','representasifitur':'representasi fitur','kelompokfitur':'kelompok fitur','ketersediaanfitur':'ketersediaan fitur','rekonstruksifitur':'rekonstruksi fitur','menjadifitur':'menjadi fitur','memilikitimestamp':'memiliki timestamp','memilikidegree':'memiliki degree','dengandegree':'dengan degree','darirun':'dari run','runfinal':'run final','runkonfirmatori':'run konfirmatori','datatest':'data test','pesanantest':'pesanan test','matrixtest':'matrix test','prediksitest':'prediksi test','definisievent':'definisi event'}.items(): s=s.replace(a,b)
 for term in terms_safe:
  # Never split identifiers: only spacing problems proved by literal wording.
  s=re.sub(r'(?<=[A-Za-z])('+re.escape(term)+r')',r' \1',s)
  s=re.sub(r'('+re.escape(term)+r')(?=[A-Za-z])',r'\1 ',s)
 for a,b in {'connected component s':'connected components','Knowl edge':'Knowledge','pembentukanfitur':'pembentukan fitur','Ketersediaanfitur':'Ketersediaan fitur','dijadikanfitur':'dijadikan fitur','danmachine learningdalam':'dan machine learning dalam','=Shipping':'= Shipping','testdihitung':'test dihitung','testdiprediksi':'test diprediksi','testadalah':'test adalah','eventprediksi':'event prediksi',':baseline0':': baseline 0',';precision0':'; precision 0',',recall1':', recall 1','binary F10,':'binary F1 0,',',recall,':', recall,',',binary F1':', binary F1','kelas,resampling':'kelas, resampling',';benchmark':'; benchmark','.Logistic':'. Logistic','.Random':'. Random',',Gradient':', Gradient',',ablation':', ablation',',market':', market',',degree':', degree',',eigenvector':', eigenvector',',betweenness':', betweenness','hash-nyatelah':'hash-nya telah','forests.Machine':'forests. Machine'}.items(): s=s.replace(a,b)
 # Avoid reformatting headings, navigation or cover; only repair strings there.
 body=p in d.paragraphs and d.paragraphs.index(p)>=75 if False else False
 if s!=old: changes.append({'old':old,'new':s})
 # Retain paragraph properties and equation/image objects; plain prose only.
 style=p.style.name
 is_heading=style.startswith('Heading')
 if s!=old or (not is_heading and len(s)>100):
  for child in list(p._p):
   if child.tag!=qn('w:pPr'): p._p.remove(child)
  # Rebuild mixed-language emphasis on whole terms only, never Indonesian fragments.
  foreign=['market drivers','business drivers','data ingestion','feature engineering','training','validation','baseline','clickstream','graph analytics','degree','connected components','connected component','runtime','hash','filesystem','machine learning','cluster','node','edge','preprocessing','one-hot encoding','multi-hot encoding','encoding','resampling','tuning','test','precision','recall','binary F1','confusion matrix','benchmark','multi-node','ablation','run','snapshot','market','timestamp','as-of','deployment','event','pipeline','spring layout','self-loop']
  pattern=re.compile(r'(?<![\w])(?:'+ '|'.join(re.escape(x) for x in sorted(foreign,key=len,reverse=True))+r')(?![\w])',re.I)
  pos=0
  for m in pattern.finditer(s):
   if m.start()>pos: p.add_run(s[pos:m.start()]).italic=False
   p.add_run(m.group()).italic=True
   pos=m.end()
  if pos<len(s): p.add_run(s[pos:]).italic=False
 p.paragraph_format.widow_control=True
# Header repeat and no row splitting; keep metric tables intact.
for ti,t in enumerate(d.tables):
 for ri,row in enumerate(t.rows):
  pr=row._tr.get_or_add_trPr()
  if not pr.find(qn('w:cantSplit')) is not None: pr.append(OxmlElement('w:cantSplit'))
  if ri==0 and pr.find(qn('w:tblHeader')) is None: pr.append(OxmlElement('w:tblHeader'))
  if ti in (15,16,17):
   for c in row.cells:
    for p in c.paragraphs:
     p.paragraph_format.keep_with_next=ri<len(t.rows)-1
     for r in p.runs:r.font.size=Pt(9)
 if ti in (16,17):
  for c in t.rows[6].cells:
   # Explicit ordered labels avoid ambiguity when values wrap.
   if c is not t.rows[6].cells[0]: pass
  t.autofit=False
  for row in t.rows:
   for ci,c in enumerate(row.cells): c.width=Inches(1.7 if ci==0 else 1.25)
# Keep caption with table immediately following.
for p in d.paragraphs:
 if re.match(r'^Tabel \d+\.\d+ ',p.text) and p.style.name.startswith('Heading') is False:
  p.paragraph_format.keep_with_next=True
# Set explicit chapter breaks only for real headings, never navigation entries.
for p in d.paragraphs:
 if p.style.name=='Heading 1':p.paragraph_format.page_break_before=True
d.save(OUT)
(ROOT/'editorial_changes.json').write_text(json.dumps({'output':str(OUT),'changes':changes,'count':len(changes)},ensure_ascii=False,indent=2))
print(json.dumps({'output':str(OUT),'changes':len(changes),'source_unchanged':hashlib.sha256(SOURCE.read_bytes()).hexdigest()=='0d6f9095ba5489cf575afaab8a18bae9ab77181452db142ece8136adc68bc8cb'}))
