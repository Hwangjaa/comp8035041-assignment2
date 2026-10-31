import json, re
from pathlib import Path
from docx import Document

R = Path(__file__).parent
SRC = R.parent / "Assignment-II-DataCo-Laporan-Final-Rapi-20261022.docx"
doc = Document(SRC)

# Rentang paragraf prosa per bab (indeks paragraf body)
BAB = {
    "bab1": range(76, 91),
    "bab2": range(91, 109),
    "bab3": range(109, 122),
    "bab4": range(122, 156),
    "bab5": range(156, 192),
    "bab6": range(192, 210),
}

out = {}
for name, rng in BAB.items():
    paras = []
    for i in rng:
        p = doc.paragraphs[i]
        if p.style.name.startswith("Heading") or "Caption" in p.style.name:
            continue
        if p.text.strip():
            paras.append(p.text.strip())
    out[name] = "\n\n".join(paras)
    (R / f"metrik-{name}-before.md").write_text(out[name], encoding="utf-8")

# Contoh run untuk melihat konvensi italic
for idx in (77, 180, 194):
    p = doc.paragraphs[idx]
    print(f"--- p{idx} style={p.style.name}")
    for r in p.runs[:14]:
        print(f"   italic={r.italic} bold={r.bold} text={r.text!r}")
print("paragraf prosa:", {k: len(v) for k, v in out.items()})
