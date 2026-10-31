"""Bangun ulang isi DOCX sesuai 10 instruksi pemilik. Angka dari F/G/H JSON."""
import json, re
from pathlib import Path
from docx import Document
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
from docx.shared import Inches, Pt
from docx.enum.text import WD_TAB_ALIGNMENT, WD_TAB_LEADER
R=Path('/Users/rafaelyudianto/Documents/COMP8035041-Assignment-II')
OUT=R/'analisis-lanjutan';SRC=R/'Assignment-II-DataCo-Laporan-Final-High-Quality.docx'
F=json.load(open(OUT/'F_main.json'));G=json.load(open(OUT/'G_ablation_schedule.json'));H=json.load(open(OUT/'H_graph.json'))
d=Document(SRC)
def f(x,n=6):return f'{x:.{n}f}'
def idn(x,n=6):
    s=f'{x:.{n}f}';return s.replace('.',',')
def n2(x):return f'{x:,}'.replace(',','.')
def find_heading(t):
    for p in d.paragraphs:
        if p.text.strip()==t and p.style.name.startswith('Heading'):return p
    raise KeyError(t)
def find_para(t):
    for p in d.paragraphs:
        if p.text.strip().startswith(t) and '\t' not in p.text:return p
    raise KeyError(t[:40])
def set_text(p,new,italic=False):
    first=next((r for r in p.runs if r.text),None)
    props=None
    if first is not None and first._r.rPr is not None:
        from copy import deepcopy;props=deepcopy(first._r.rPr)
    p.clear();r=p.add_run(new)
    if props is not None:r._r.insert(0,props)
    r.italic=italic
def cell_set(cell,text,bold=False):
    cell.text=str(text)
    for p in cell.paragraphs:
        for r in p.runs:
            r.font.size=Pt(8.5);r.bold=bold
def rebuild_table(tbl,rows,widths=None):
    while len(tbl.rows)>len(rows):tbl._tbl.remove(tbl.rows[-1]._tr)
    while len(tbl.rows)<len(rows):tbl.add_row()
    for i,row in enumerate(rows):
        for j,val in enumerate(row):
            if j<len(tbl.columns):cell_set(tbl.cell(i,j),val,bold=(i==0))
def tbl_by_caption(cap):
    from docx.table import Table
    p=find_para(cap);nxt=p._p.getnext()
    while nxt is not None and nxt.tag!=qn('w:tbl'):nxt=nxt.getnext()
    assert nxt is not None,'tabel setelah '+cap+' tidak ditemukan'
    return Table(nxt,d)
# ============ 1. Tabel 5.2 parameter ============
T=json.load(open(OUT/'F_main.json'))
rebuild_table(tbl_by_caption('Tabel 5.2 Parameter Logistic Regression'),[
 ['Implementasi','Parameter'],
 ['scikit-learn','C=1,0; solver=lbfgs; max_iter=1000; tol=0,000001; random_state=42; class_weight=None'],
 ['Spark MLlib (utama)','regParam=2,0069843x10^-5; elasticNetParam=0,0; maxIter=1000; tol=0,000001; standardization=False'],
 ['Hubungan parameter','regParam = 1/(C x n_train) dengan n_train = 49.826; setara dengan C=1,0 pada scikit-learn'],
 ['Spark MLlib (sensitivity)','regParam=0,1; setara dengan C=2,007x10^-4 pada scikit-learn'],
 ['Refit','Tidak melatih ulang menggunakan gabungan training dan validation']])
# ============ 2. Tabel 5.5 test (utama) ============
t=F['main']['test']
rebuild_table(tbl_by_caption('Tabel 5.5 Hasil evaluasi pada data test'),[
 ['Ukuran','Baseline','LR scikit-learn','LR Spark MLlib'],
 ['Average precision',idn(t['baseline']['ap']),idn(t['sklearn_lr']['ap']),idn(t['spark_lr']['ap'])],
 ['ROC-AUC',idn(t['baseline']['auc']),idn(t['sklearn_lr']['auc']),idn(t['spark_lr']['auc'])],
 ['Precision kelas 1',idn(t['baseline']['precision']),idn(t['sklearn_lr']['precision']),idn(t['spark_lr']['precision'])],
 ['Recall kelas 1',idn(t['baseline']['recall']),idn(t['sklearn_lr']['recall']),idn(t['spark_lr']['recall'])],
 ['Binary F1',idn(t['baseline']['binary_f1']),idn(t['sklearn_lr']['binary_f1']),idn(t['spark_lr']['binary_f1'])],
 ['Confusion matrix (TN, FP, FN, TP)','0, 3.407, 0, 4.636','0, 3.407, 0, 4.636','0, 3.407, 0, 4.636'],
 ['Threshold validation',idn(F['thresholds_validation']['baseline']),idn(F['thresholds_validation']['sklearn_lr']),idn(F['thresholds_validation']['spark_lr'])]])
# ============ Tabel 5.6 validation ============
v=F['main']['validation']
rebuild_table(tbl_by_caption('Tabel 5.6 Hasil evaluasi pada data validation'),[
 ['Ukuran','Baseline','LR scikit-learn','LR Spark MLlib'],
 ['Average precision',idn(v['baseline']['ap']),idn(v['sklearn_lr']['ap']),idn(v['spark_lr']['ap'])],
 ['ROC-AUC',idn(v['baseline']['auc']),idn(v['sklearn_lr']['auc']),idn(v['spark_lr']['auc'])],
 ['Precision kelas 1',idn(v['baseline']['precision']),idn(v['sklearn_lr']['precision']),idn(v['spark_lr']['precision'])],
 ['Recall kelas 1',idn(v['baseline']['recall']),idn(v['sklearn_lr']['recall']),idn(v['spark_lr']['recall'])],
 ['Binary F1',idn(v['baseline']['binary_f1']),idn(v['sklearn_lr']['binary_f1']),idn(v['spark_lr']['binary_f1'])],
 ['Confusion matrix (TN, FP, FN, TP)','0, 2.140, 0, 2.888','0, 2.140, 0, 2.888','0, 2.140, 0, 2.888'],
 ['Threshold validation',idn(F['thresholds_validation']['baseline']),idn(F['thresholds_validation']['sklearn_lr']),idn(F['thresholds_validation']['spark_lr'])]])
# ============ 3. Tabel 5.7 top-k eksak ============
sk=F['topk_exact']['sklearn_lr'];sp=F['topk_exact']['spark_lr']
bs=F['bootstrap']['sklearn_lr'];bp=F['bootstrap']['spark_lr']
def ci(b):return f"[{idn(b['lo95'])}, {idn(b['hi95'])}]"
rebuild_table(tbl_by_caption('Tabel 5.7 Evaluasi keputusan berbasis peringkat pada data test'),[
 ['Ukuran','LR scikit-learn','LR Spark MLlib'],
 ['Average Precision (CI95 bootstrap)',f"{idn(F['main']['test']['sklearn_lr']['ap'])} {ci(bs['ap'])}",f"{idn(F['main']['test']['spark_lr']['ap'])} {ci(bp['ap'])}"],
 ['ROC-AUC (CI95 bootstrap)',f"{idn(F['main']['test']['sklearn_lr']['auc'])} {ci(bs['auc'])}",f"{idn(F['main']['test']['spark_lr']['auc'])} {ci(bp['auc'])}"],
 [f"Precision@10% (n={n2(sk[0]['n_selected'])})",idn(sk[0]['precision_at_k']),idn(sp[0]['precision_at_k'])],
 [f"Recall@10%",idn(sk[0]['recall_at_k']),idn(sp[0]['recall_at_k'])],
 [f"Precision@20% (n={n2(sk[1]['n_selected'])})",idn(sk[1]['precision_at_k']),idn(sp[1]['precision_at_k'])],
 [f"Recall@20%",idn(sk[1]['recall_at_k']),idn(sp[1]['recall_at_k'])],
 [f"Precision@30% (n={n2(sk[2]['n_selected'])})",idn(sk[2]['precision_at_k']),idn(sp[2]['precision_at_k'])],
 [f"Recall@30%",idn(sk[2]['recall_at_k']),idn(sp[2]['recall_at_k'])],
 ['Lift@20% terhadap prevalensi',idn(sk[1]['lift'],3),idn(sp[1]['lift'],3)],
 ['Skor batas @20% (tie pada batas)',f"{idn(sk[1]['threshold_score'])} ({sk[1]['ties_at_boundary']} skor kembar)",f"{idn(sp[1]['threshold_score'])} ({sp[1]['ties_at_boundary']} skor kembar)"],
 ['Precision@20% (CI95 bootstrap)',ci(bs['precision_at_20']),ci(bp['precision_at_20'])]])
# ============ 4. Tabel 5.8 ablation ============
ab=G['ablation'];ci_=G['ablation_ci']
rows=[['Subset fitur / model','Fitur','AP test','ROC-AUC test','AP CI95','Prediksi konstan?']]
order=['baseline (prior)','jadwal saja','jadwal+jumlah item','kategori saja','segmen+market saja','tanpa jadwal','semua fitur','Random Forest','Gradient Boosting']
for k in order:
    x=ab[k];c=ci_.get(k)
    rows.append([k,str(x['n_features']),idn(x['ap_test']),idn(x['auc_test']),
        (f"[{idn(c['lo95'])}, {idn(c['hi95'])}]" if c else '-'),('ya' if x['constant_prediction'] else 'tidak')])
rebuild_table(tbl_by_caption('Tabel 5.8 Uji sumber sinyal (ablation) pada data test'),rows)
d.save(SRC)
print('tabel 5.2, 5.5, 5.6, 5.7, 5.8 diperbarui')
