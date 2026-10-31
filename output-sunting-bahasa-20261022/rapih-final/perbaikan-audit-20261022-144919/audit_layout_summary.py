from pathlib import Path
from zipfile import ZipFile
from lxml import etree as E
import json,re,collections,hashlib
b=Path(__file__).parent;d=json.loads((b/'audit_italic_layout_evidence.json').read_text());ns={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main'};w=lambda n:'{'+ns['w']+'}'+n
with ZipFile(d['source']) as z:
 root=E.fromstring(z.read('word/document.xml'));styles=E.fromstring(z.read('word/styles.xml'))
body=root.find(w('body')); ps=body.findall(w('p'))
def text(e):return ''.join(e.xpath('.//w:t/text()',namespaces=ns))
def tags(e):return [(E.QName(x).localname,dict((E.QName(k).localname,v) for k,v in x.attrib.items())) for x in e] if e is not None else []
layout={'style_heading1':tags(styles.find("w:style[@w:styleId='Heading1']/w:pPr",ns)), 'chapters':[], 'navigation':[], 'caption_keep':[], 'table_widths':[], 'drawings':[]}
for i,p in enumerate(ps,1):
 t=text(p)
 if t.startswith('BAB '):layout['chapters'].append({'p':i,'text':t,'props':tags(p.find(w('pPr'))),'preceding_page_break':bool(i>1 and ps[i-2].xpath('.//w:br[@w:type="page"]',namespaces=ns))})
 if 17<=i<=75 and t:layout['navigation'].append({'p':i,'text':t,'props':tags(p.find(w('pPr')))})
 if re.match(r'Tabel \d',t) and i>75:layout['caption_keep'].append({'p':i,'text':t,'props':tags(p.find(w('pPr')))})
sect=root.find('.//'+w('sectPr'));sz=sect.find(w('pgSz'));mar=sect.find(w('pgMar'));width=int(sz.get(w('w')))-int(mar.get(w('left')))-int(mar.get(w('right')))
layout['text_width_twips']=width
for i,t in enumerate(body.findall(w('tbl')),1):
 grid=[int(x.get(w('w'))) for x in t.findall('w:tblGrid/w:gridCol',ns)];hdr=t.find('w:tr/w:trPr/w:tblHeader',ns)
 layout['table_widths'].append({'table':i,'grid_width':sum(grid),'exceeds_text_width':sum(grid)>width,'header_repeat':hdr is not None})
confirmed=[]
for x in d['partial_italic_words']:
 for r in x['segments']:
  v=r['text'].lower()
  if not r['italic']:continue
  word=x['word'].lower()
  bad=(v=='fit' and ('fitur' in word or word in ('profit','refit'))) or (v=='run' and word in ('penurunan','turunannya','turunan')) or (v=='log' and any(s in word for s in ['teknologi','kronologi','logistics','technology','tokenized_access_logs'])) or (v=='edge' and 'knowledge' in word)
  if bad:confirmed.append({'body_paragraph':x['body_paragraph'],'xml_paragraph':x['xml_paragraph'],'word':x['word'],'run':r['run'],'italic_substring':r['text']})
layout['confirmed_substring_false_positives']=confirmed
(b/'audit_layout_summary.json').write_text(json.dumps(layout,ensure_ascii=False,indent=2))
print(json.dumps({'false_positive_count':len(confirmed),'false_positive_by_substring':dict(collections.Counter(x['italic_substring'] for x in confirmed)),'chapters':layout['chapters'],'heading1':layout['style_heading1'],'table_widths':layout['table_widths'],'missing_caption_keepNext':[x['p'] for x in layout['caption_keep'] if not any(y[0]=='keepNext' and y[1].get('val','1') not in ('0','false') for y in x['props'])],'navigation_styles':collections.Counter(str(x['props']) for x in layout['navigation'])},ensure_ascii=False,indent=2))
