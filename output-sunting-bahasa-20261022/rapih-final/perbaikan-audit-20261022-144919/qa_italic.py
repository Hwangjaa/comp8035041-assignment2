import json
from pathlib import Path
from docx import Document

R = Path(__file__).parent
d = Document(R / "Assignment-II-DataCo-Revisi-Humanizer.docx")
terms = {}
ratios = []
for i, p in enumerate(d.paragraphs):
    if not p.runs or not p.text.strip():
        continue
    total = sum(len(r.text) for r in p.runs) or 1
    it = sum(len(r.text) for r in p.runs if r.italic)
    if 76 <= i < 210:
        ratios.append((round(it / total, 2), i))
    for r in p.runs:
        if r.italic:
            terms[r.text.strip()] = terms.get(r.text.strip(), 0) + 1
ratios.sort(reverse=True)
print(json.dumps({
    "italic_tertinggi": ratios[:8],
    "median_italic": ratios[len(ratios) // 2],
    "jumlah_istilah_miring": len(terms),
    "contoh": sorted(terms.items(), key=lambda x: -x[1])[:35],
}, ensure_ascii=False, indent=1))
