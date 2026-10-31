import fitz
from pathlib import Path
PDF=Path('/Users/rafaelyudianto/.hermes/cache/scratch/dataco-hq/Assignment-II-DataCo-Laporan-Final-High-Quality.pdf')
pdf=fitz.open(PDF)
print('pages:',len(pdf))
for i,pg in enumerate(pdf):
    txt=pg.get_text().strip()
    lines=[l.strip() for l in txt.splitlines() if l.strip()]
    # hitung rasio isi: jarak vertikal blok terakhir vs tinggi halaman
    blocks=pg.get_text('dict')['blocks']
    ymax=max((b['bbox'][3] for b in blocks),default=0)
    imgs=sum(1 for b in blocks if b.get('type')==1)
    print(f'--- p{i+1}: chars={len(txt)} blocks={len(blocks)} imgs={imgs} last_y={ymax:.0f}/{pg.rect.height:.0f} ({ymax/pg.rect.height*100:.0f}%)')
    print('   head:', ' | '.join(lines[:3])[:110])
    if len(txt)<400:print('   ALL:', ' | '.join(lines)[:200])
