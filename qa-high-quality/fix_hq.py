from pathlib import Path
from copy import deepcopy
from docx import Document
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
import hashlib
R=Path('/Users/rafaelyudianto/Documents/COMP8035041-Assignment-II')
O=R/'Assignment-II-DataCo-Laporan-Final-High-Quality.docx'
pre=hashlib.sha256(O.read_bytes()).hexdigest()
d=Document(O)
# 1. Convert manual page breaks on Heading paragraphs to page_break_before (idempotent -> no blank pages).
converted=[]
for p in d.paragraphs:
    if not p.style.name.startswith('Heading'):continue
    brs=p._p.xpath('.//w:br[@w:type="page"]')
    if not brs:continue
    for br in brs:
        run=br.getparent()
        # remove br; if run now empty (only had br), remove run
        run.remove(br)
        if not run.xpath('.//w:t|.//w:br|.//w:cr|.//w:drawing|.//m:oMath'):
            run.getparent().remove(run)
    p.paragraph_format.page_break_before=True
    converted.append(p.text[:40])
# 2. Force Word to update all fields on open (fixes stale PAGEREF cache without manual F9).
st=d.settings.element
uf=st.find(qn('w:updateFields'))
if uf is None:
    uf=OxmlElement('w:updateFields');st.insert(0,uf)
uf.set(qn('w:val'),'true')
d.save(O)
post=hashlib.sha256(O.read_bytes()).hexdigest()
print(f'converted_breaks={len(converted)} pages_before={pre[:12]} after={post[:12]}')
print('converted:',converted)