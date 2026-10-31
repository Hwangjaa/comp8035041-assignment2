import json
from pathlib import Path
from docx import Document

R = Path(__file__).parent
d = Document(R / "Assignment-II-DataCo-Revisi-Humanizer.docx")
out = [(i, p.style.name, p.text) for i, p in enumerate(d.paragraphs)
       if "Caption" in p.style.name or p.text.strip().startswith(("Tabel ", "Gambar "))]
print(json.dumps(out, ensure_ascii=False, indent=1))
