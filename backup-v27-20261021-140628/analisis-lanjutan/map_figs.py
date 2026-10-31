from pathlib import Path
from docx import Document
from docx.oxml.ns import qn
from docx.shared import Inches
R=Path('/Users/rafaelyudianto/Documents/COMP8035041-Assignment-II')
OUT=R/'analisis-lanjutan';SRC=R/'Assignment-II-DataCo-Laporan-Final-High-Quality.docx'
d=Document(SRC)
# peta drawing -> caption berikutnya
body=list(d.element.body)
for i,el in enumerate(body):
    if el.tag==qn('w:p') and el.findall('.//'+qn('w:drawing')):
        blip=el.find('.//'+qn('a:blip'));rid=blip.get(qn('r:embed')) if blip is not None else None
        nxt=body[i+1] if i+1<len(body) else None
        cap=''
        if nxt is not None and nxt.tag==qn('w:p'):
            cap=''.join(t.text or '' for t in nxt.iter(qn('w:t')))[:50]
        print(f'drawing rId={rid} -> next p: {cap!r}')
