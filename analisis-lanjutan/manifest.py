import hashlib, shutil, json
from pathlib import Path
R=Path('/Users/rafaelyudianto/Documents/COMP8035041-Assignment-II')
# salin PDF deliverable ke root
src=Path('/Users/rafaelyudianto/.hermes/cache/scratch/dataco-hq/Assignment-II-DataCo-Laporan-Final-High-Quality.pdf')
dst=R/'Assignment-II-DataCo-Laporan-Final-High-Quality.pdf';shutil.copy2(src,dst)
targets=[R/'Assignment-II-DataCo-Laporan-Final-High-Quality.docx',dst,
  R/'analisis-lanjutan/A_equivalence.json',R/'analisis-lanjutan/B_decision.json',
  R/'analisis-lanjutan/C_ablation.json',R/'analisis-lanjutan/D_graph.json',
  R/'analisis-lanjutan/LAPORAN-VERIFIKASI-TEKNIS.md',R/'analisis-lanjutan/FINAL-VERIFY.json',
  R/'analisis-lanjutan/B_pr_roc_test.png',R/'analisis-lanjutan/E_projection.png',R/'analisis-lanjutan/D_graph_subset_fixed.png']
lines=[]
for t in targets:
    if t.exists():lines.append(f'{hashlib.sha256(t.read_bytes()).hexdigest()}  {t.relative_to(R)}')
(R/'analisis-lanjutan/SHA256SUMS.txt').write_text('\n'.join(lines)+'\n')
print('\n'.join(lines))
