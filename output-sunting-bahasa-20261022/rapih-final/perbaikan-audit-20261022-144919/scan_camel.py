import re, json
from pathlib import Path
from docx import Document

R = Path(__file__).parent
d = Document(R / "Assignment-II-DataCo-Revisi-Humanizer.docx")
allow = {"DataCo", "DateOrders", "DescriptionDataCoSupplyChain", "DataCoSupplyChainDataset",
         "Late_delivery_risk", "Order", "Customer", "Product", "Shipping", "Category",
         "Market", "Segment", "Days", "Delivery", "Status", "MISSING", "UNKNOWN",
         "PageRank", "NetworkX", "NumPy", "PySpark", "JavaScript", "GitHub", "MacBook"}
hits = {}
for i, p in enumerate(d.paragraphs):
    for m in re.finditer(r"\b[A-Za-z]{2,}\b", p.text):
        w = m.group(0)
        if w in allow:
            continue
        if re.search(r"[a-z][A-Z]", w) and not w.isupper():
            hits.setdefault(w, []).append(i)
print(json.dumps({k: v[:3] for k, v in sorted(hits.items())}, ensure_ascii=False, indent=1))
