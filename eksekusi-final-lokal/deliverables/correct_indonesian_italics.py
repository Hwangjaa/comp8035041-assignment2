from pathlib import Path
from copy import deepcopy
import re, json, hashlib, zipfile
from lxml import etree
from docx import Document
from docx.text.paragraph import Paragraph
from docx.oxml.ns import qn

ROOT = Path(__file__).resolve().parent
SRC = ROOT / 'Assignment-II-DataCo-Laporan-Hasil-Aktual.docx'
DST = ROOT / 'Assignment-II-DataCo-Laporan-Hasil-Aktual-Italic-Corrected.docx'
doc = Document(SRC)
# Only repair the erroneous mixed-language runs, not foreign-only terms,
# bibliographic entries, mathematics or document content.
indonesian = re.compile(r'\b(sebelumnya|terpisah|berlangsung|kelompok|memilih|menghitung|tetangga|berisi|tersimpan|keberadaan|sebelum)\b', re.I)
paragraphs = [Paragraph(e, doc) for e in doc.element.iter(qn('w:p'))]
terms = set()
for p in paragraphs:
    for r in p.runs:
        if r.italic and r.text.strip() and len(r.text) < 65 and not indonesian.search(r.text):
            terms.add(r.text.strip())
terms.update(['macOS', 'Spark/PySpark', 'Java', 'local[2]', 'fs.defaultFS=file:///', 'environment.json', 'spark-environment.json', 'market', 'multi-hot', 'threshold', 'F1', 'all-negative', 'ties', 'scikit-learn', 'Spark', 'U0', 'H1', 'Degree', 'node', 'edge', 'spring layout', 'seed=42', 'iterations=50', 'graph-edges.csv', 'graph-category-degree.csv', 'graph-components.csv', 'graph-component-membership.csv', 'ID'])
pattern = re.compile(r'(?<![\w])(?:' + '|'.join(re.escape(t) for t in sorted(terms,key=len,reverse=True)) + r')(?![\w])', re.I)
before_text = [p.text for p in paragraphs]
changes=[]
for index,p in enumerate(paragraphs):
    for r in list(p.runs):
        if not (r.italic and indonesian.search(r.text) and len(r.text)>65):
            continue
        if any(c.tag not in (qn('w:rPr'), qn('w:t')) for c in r._r):
            raise RuntimeError('Unexpected non-text content in candidate')
        text=r.text
        spans=[]; pos=0
        for m in pattern.finditer(text):
            if m.start()>pos: spans.append((text[pos:m.start()],False))
            spans.append((m.group(),True)); pos=m.end()
        if pos<len(text): spans.append((text[pos:],False))
        for value, italic in spans:
            clone=deepcopy(r._r)
            from docx.text.run import Run
            new=Run(clone,p); new.text=value; new.italic=italic
            new.font.complex_script = r.font.complex_script
            # Word's complex-script italic flag is distinct.
            ip=new._r.get_or_add_rPr()
            old=ip.find(qn('w:iCs'))
            if old is not None: ip.remove(old)
            r._r.addprevious(clone)
        r._r.getparent().remove(r._r)
        changes.append({'paragraph_xml_index':index,'text':text,'retained_italic':[t for t,i in spans if i]})
doc.save(DST)
out=Document(DST)
after_text=[Paragraph(e,out).text for e in out.element.iter(qn('w:p'))]
assert before_text == after_text, 'Text changed'
with zipfile.ZipFile(SRC) as a,zipfile.ZipFile(DST) as b:
    media=[n for n in a.namelist() if n.startswith('word/media/')]
    assert all(a.read(n)==b.read(n) for n in media)
    ns={'m':'http://schemas.openxmlformats.org/officeDocument/2006/math'}
    ax=etree.fromstring(a.read('word/document.xml')); bx=etree.fromstring(b.read('word/document.xml'))
    eq_a=[etree.tostring(x) for x in ax.findall('.//m:oMath',ns)]
    eq_b=[etree.tostring(x) for x in bx.findall('.//m:oMath',ns)]
    assert eq_a==eq_b, 'Math changed'
remaining=[r.text for e in out.element.iter(qn('w:p')) for p in [Paragraph(e,out)] for r in p.runs if r.italic and indonesian.search(r.text) and len(r.text)>65]
assert not remaining
report={'source':str(SRC),'output':str(DST),'changed_runs':len(changes),'changes':changes,'text_identical':True,'media_identical':True,'equations_identical':True,'remaining_long_indonesian_italic_runs':remaining,'output_sha256':hashlib.sha256(DST.read_bytes()).hexdigest()}
(ROOT/'italic-correction-audit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
print(json.dumps(report,ensure_ascii=False,indent=2))
