from docx import Document
from docx.shared import Pt
from docx.enum.text import WD_BREAK
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from copy import deepcopy
from pathlib import Path
import re, json, hashlib

base=Path('/Users/rafaelyudianto/Documents/COMP8035041-Assignment-II/output-sunting-bahasa-20261022')
src=base/'Assignment-II-DataCo-Laporan-Final-Sunting-Bahasa-20261022.docx'
out=base/'rapih-final/Assignment-II-DataCo-Laporan-Final-Rapi-20261022.docx'
doc=Document(src)

def delete_paragraph(p):
    el=p._element
    el.getparent().remove(el)
    p._p=None

def insert_before(anchor, text='', style=None, page_break=False):
    # Build isolated paragraph then move its XML directly before anchor.
    holder=Document()
    p=holder.add_paragraph(style=style) if style else holder.add_paragraph()
    if page_break: p.add_run().add_break(WD_BREAK.PAGE)
    if text: p.add_run(text)
    anchor._p.addprevious(deepcopy(p._p))

# Remove broken, manually generated lists from the prior document (everything from
# DAFTAR ISI through the paragraph immediately preceding BAB 1).
paras=list(doc.paragraphs)
start=next(i for i,p in enumerate(paras) if p.text.strip()=='DAFTAR ISI')
end=next(i for i,p in enumerate(paras) if p.text.strip()=='BAB 1. PENDAHULUAN')
for p in paras[start:end]: delete_paragraph(p)
anchor=next(p for p in doc.paragraphs if p.text.strip()=='BAB 1. PENDAHULUAN')

# Insert clean static navigation. Deliberately omit volatile page references;
# the former fields rendered 'Error: Reference source not found'.
toc=[
('DAFTAR ISI','Heading 1'),
('BAB 1. PENDAHULUAN','Normal'),('    1.1 Latar Belakang Masalah','Normal'),('    1.2 Market dan Business Drivers','Normal'),('    1.3 Pemangku Kepentingan yang Terlibat','Normal'),
('BAB 2. RANCANGAN SOLUSI BIG DATA','Normal'),('    2.1 Metode Pengumpulan Data (Data Ingestion)','Normal'),('    2.2 Teknologi Penyimpanan Data','Normal'),('    2.3 Processing Framework','Normal'),
('BAB 3. TATA KELOLA IT','Normal'),('    3.1 Security','Normal'),('    3.2 Compliance','Normal'),('    3.3 Privasi Data','Normal'),('    3.4 Kualitas Data','Normal'),
('BAB 4. DATA','Normal'),('    4.1 Deskripsi Data','Normal'),('        4.1.1 Pembersihan Data Transaksi','Normal'),('        4.1.2 Organisasi Data','Normal'),('    4.2 Model Data dan Operasi Data','Normal'),('    4.3 Dataset untuk Diolah Menggunakan Machine Learning','Normal'),
('BAB 5. MACHINE LEARNING','Normal'),('    5.1 Data Preprocessing','Normal'),('    5.2 Feature Engineering','Normal'),('    5.3 Algoritma','Normal'),('    5.4 Proses Pengembangan Model dengan dan tanpa Spark MLlib','Normal'),('    5.5 Evaluasi Model','Normal'),('    5.6 Analisis','Normal'),
('BAB 6. GRAPH ANALYTICS','Normal'),('    6.1 Pengembangan Graph','Normal'),('    6.2 Analisis dan Insight yang Diperoleh','Normal'),('DAFTAR PUSTAKA','Normal'),('FORMULIR PENGUNGKAPAN PENGGUNAAN AI','Normal'),
('', 'Normal'),('DAFTAR TABEL','Heading 1')]
tables=[p.text.strip() for p in doc.paragraphs if p.style.name=='Table Caption']
figures=[p.text.strip() for p in doc.paragraphs if p.style.name=='Figure Caption']
listing=toc+[(x,'Normal') for x in tables]+[('', 'Normal'),('DAFTAR GAMBAR','Heading 1')]+[(x,'Normal') for x in figures]
for n,(text,style) in enumerate(listing):
    insert_before(anchor,text,style,page_break=(n==0))

# Replace literal Markdown asterisks by actual italics. Preserve text and no
# formatting mutation outside matched emphasis spans.
italic_fixes=0
for p in list(doc.paragraphs):
    if not p.text or '*' not in p.text: continue
    # avoid mangling mathematical asterisks: only pair surrounding word content
    s=p.text
    if not re.search(r'\*[^*\\n]{1,80}\*',s): continue
    matches=list(re.finditer(r'\*([^*\\n]{1,80})\*',s))
    if not matches: continue
    # reconstruct this paragraph only where literal emphasis exists.
    for r in list(p.runs): r._element.getparent().remove(r._element)
    pos=0
    for m in matches:
        if m.start()>pos: p.add_run(s[pos:m.start()])
        rr=p.add_run(m.group(1)); rr.italic=True
        pos=m.end()
    if pos<len(s): p.add_run(s[pos:])
    italic_fixes+=len(matches)

# Remove stale visible reference-error tokens wherever they survived.
reference_errors=0
for p in list(doc.paragraphs):
    if 'Error: Reference source not found' in p.text:
        p.text=p.text.replace('Error: Reference source not found','').strip()
        reference_errors+=1
for tbl in doc.tables:
    for row in tbl.rows:
        for cell in row.cells:
            for p in cell.paragraphs:
                if 'Error: Reference source not found' in p.text:
                    p.text=p.text.replace('Error: Reference source not found','').strip(); reference_errors+=1

# Ensure chapter-level sections do not start in the tail of prior pages.
for p in doc.paragraphs:
    if p.style.name=='Heading 1' and p.text.strip().startswith(('BAB ','DAFTAR PUSTAKA','BINUS UNIVERSITY')):
        pf=p.paragraph_format
        pf.page_break_before=True
        pf.keep_with_next=True
    elif p.style.name.startswith('Heading'):
        p.paragraph_format.keep_with_next=True

# Typography cleanup: no superfluous spacing around list entries; preserve body
# formatting inherited from source.
for p in doc.paragraphs:
    t=p.text.strip()
    if t.startswith(('Tabel ', 'Gambar ')) and p.style.name=='Normal':
        p.paragraph_format.space_after=Pt(0)
    if t in ('DAFTAR ISI','DAFTAR TABEL','DAFTAR GAMBAR'):
        p.paragraph_format.space_after=Pt(8)

doc.save(out)
text='\\n'.join(p.text for p in doc.paragraphs)
report={'source':str(src),'output':str(out),'removed_broken_navigation_paragraphs':end-start,'clean_navigation_entries':len(listing),'markdown_emphasis_converted':italic_fixes,'visible_reference_errors_removed':reference_errors,'remaining_literal_asterisks':text.count('*'),'remaining_reference_errors':text.count('Error: Reference source not found'),'paragraphs':len(doc.paragraphs),'tables':len(doc.tables),'sha256':hashlib.sha256(out.read_bytes()).hexdigest()}
(base/'rapih-final/report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print(json.dumps(report,indent=2))
