import re, json
from pathlib import Path
from docx import Document

R = Path(__file__).parent
d = Document(R / "Assignment-II-DataCo-Revisi-Humanizer.docx")
cands = {}
for i, par in enumerate(d.paragraphs):
    for m in re.finditer(r"\b[a-z]{11,}\b", par.text):
        cands.setdefault(m.group(0), []).append(i)
print(json.dumps({w: idx[:4] for w, idx in sorted(cands.items())}, ensure_ascii=False, indent=1))
