"""Perbarui gambar (5.1, 6.2), teks kontradiktif, tabel graf + tabel jadwal."""
import json
from pathlib import Path
from copy import deepcopy
import numpy as np
import matplotlib; matplotlib.use('Agg');import matplotlib.pyplot as plt
from sklearn.metrics import precision_recall_curve, roc_curve, average_precision_score, roc_auc_score
from docx import Document
from docx.oxml.ns import qn
from docx.shared import Inches, Pt
R=Path('/Users/rafaelyudianto/Documents/COMP8035041-Assignment-II')
OUT=R/'analisis-lanjutan';SRC=R/'Assignment-II-DataCo-Laporan-Final-High-Quality.docx'
F=json.load(open(OUT/'F_main.json'));G=json.load(open(OUT/'G_ablation_schedule.json'));H=json.load(open(OUT/'H_graph.json'))
lab=json.load(open(OUT/'labels.json'));yte=np.array(lab['test_labels'])
P=np.load(OUT/'F_pt_main.npy')  # [sklearn_lr, spark_lr, baseline]
def idn(x,n=6):return f'{x:.{n}f}'.replace('.',',')
def n2(x):return f'{x:,}'.replace(',','.')
prev=float(yte.mean())
# Gambar 5.1 konfigurasi utama
fig,ax=plt.subplots(1,2,figsize=(11,4.4))
for nm,p in [('LR scikit-learn (C=1,0)',P[0]),('LR Spark MLlib (regParam=1/(C n))',P[1])]:
    pr,rc,_=precision_recall_curve(yte,p);ax[0].plot(rc,pr,label=f'{nm}; AP={average_precision_score(yte,p):.4f}')
    fpr,tpr,_=roc_curve(yte,p);ax[1].plot(fpr,tpr,label=f'{nm}; AUC={roc_auc_score(yte,p):.4f}')
ax[0].axhline(prev,ls='--',c='gray',label=f'prevalensi={prev:.4f}');ax[0].set_xlabel('Recall');ax[0].set_ylabel('Precision')
ax[0].set_title('Kurva precision-recall (data test)');ax[0].legend(fontsize=8)
ax[1].plot([0,1],[0,1],ls='--',c='gray',label='acak');ax[1].set_xlabel('False positive rate');ax[1].set_ylabel('True positive rate')
ax[1].set_title('Kurva ROC (data test)');ax[1].legend(fontsize=8)
fig.tight_layout();fig.savefig(OUT/'I_pr_roc_main.png',dpi=180);plt.close(fig)
d=Document(SRC)
def find_para(t):
    for p in d.paragraphs:
        if p.text.strip().startswith(t) and '\t' not in p.text:return p
    raise KeyError(t[:40])
def set_text(p,new):
    first=next((r for r in p.runs if r.text),None);props=deepcopy(first._r.rPr) if (first is not None and first._r.rPr is not None) else None
    p.clear();r=p.add_run(new)
    if props is not None:r._r.insert(0,props)
    r.italic=False
# ---- teks kontradiktif 5.3 ----
set_text(find_para('Parameter diterapkan tanpa tuning.'),'Parameter diterapkan tanpa tuning. Kekuatan regularisasi kedua implementasi disetarakan melalui hubungan regParam = 1/(C x n_train) sehingga pada konfigurasi utama scikit-learn memakai C=1,0 dan Spark MLlib memakai regParam=2,0069843x10^-5, dengan n_train = 49.826. Konfigurasi Spark regParam=0,1 diuji pula sebagai sensitivity check, bukan sebagai konfigurasi utama. Kedua implementasi memakai fitur, urutan kolom, dan seed yang sama.')
# ---- 5.5 ambang ----
set_text(find_para('Ambang klasifikasi dipilih berdasarkan binary F1'),'Ambang klasifikasi dipilih dari data validation berdasarkan binary F1 tertinggi. Kandidatnya adalah probabilitas unik validation dan satu ambang di atas probabilitas maksimum yang menghasilkan seluruh prediksi negatif. Jika beberapa kandidat menghasilkan F1 yang sama, dipilih ambang terbesar. Suatu pesanan diprediksi sebagai kelas 1 jika probabilitasnya lebih besar daripada atau sama dengan ambang. Ambang kemudian dibekukan sebelum evaluasi test: baseline 0,572472, scikit-learn 0,307467, dan Spark MLlib 0,307461. Karena regularisasi kedua implementasi setara, ambang keduanya hampir identik.')
set_text(find_para('Tabel 5.5–5.6 menyajikan'),'Tabel 5.5–5.6 menyajikan metrik dengan enam angka desimal. Probabilitas digunakan untuk menghitung AP dan ROC-AUC, sedangkan prediksi kelas mengikuti aturan probabilitas lebih besar atau sama dengan ambang. Pembulatan ambang dalam tabel hanya untuk penyajian. Metrik AP, ROC-AUC, dan precision@20% disertai interval kepercayaan 95% dari 1.000 resampel bootstrap pesanan (seed 42).')
# ---- 5.5 top-k ----
set_text(find_para('Selain ambang F1 pada data validation'),'Selain ambang F1, evaluasi dilakukan dengan aturan peringkat berbasis jumlah: n pesanan dengan skor probabilitas tertinggi ditandai berisiko, dengan n ditetapkan sebagai persentase tetap dari jumlah pesanan test (10%, 20%, dan 30%). Aturan ini berbasis hitungan, bukan ambang probabilitas dari validation; skor batas hanya dilaporkan sebagai konsekuensinya dan skor kembar pada batas ditangani dengan urutan stabil sehingga jumlah terpilih tepat sama dengan n. Tabel 5.7 menyajikan hasilnya beserta interval kepercayaan bootstrap.')
set_text(find_para('Prevalensi kelas positif pada data test adalah'),f"Prevalensi kelas positif pada data test adalah {idn(prev,4)}. Interval kepercayaan bootstrap kedua implementasi identik karena keduanya menghasilkan probabilitas yang sama.")
d.save(SRC)
print('teks 5.3 dan 5.5 diperbarui; gambar 5.1 utama dibuat')
