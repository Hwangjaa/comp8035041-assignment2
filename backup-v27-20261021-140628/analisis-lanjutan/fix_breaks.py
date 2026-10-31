"""Pindahkan page break dari entri TOC terakhir ke heading daftar berikutnya."""
from docx import Document
from docx.oxml.ns import qn
from pathlib import Path
R=Path('/Users/rafaelyudianto/Documents/COMP8035041-Assignment-II')
O=R/'Assignment-II-DataCo-Laporan-Final-High-Quality.docx'
d=Document(O);ps=d.paragraphs
def strip_break(p):
    n=0
    for br in p._p.xpath('.//w:br[@w:type="page"]'):
        run=br.getparent();run.remove(br);n+=1
        if not run.xpath('.//w:t|.//w:br|.//w:drawing|.//m:oMath'):run.getparent().remove(run)
    return n
moved=0
for i,p in enumerate(ps):
    if p._p.xpath('.//w:br[@w:type="page"]') and '\t' in p.text:
        # cari heading berikutnya
        for j in range(i+1,min(i+5,len(ps))):
            if ps[j].style.name.startswith('Heading'):
                strip_break(p);ps[j].paragraph_format.page_break_before=True;moved+=1
                print('moved break from',repr(p.text[:40]),'->',repr(ps[j].text[:40]))
                break
d.save(O)
print('moved:',moved)
