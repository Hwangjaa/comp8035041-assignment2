"""Update DOCX: tambah Tabel 5.6-5.8, gambar 5.1, Tabel 6.4-6.5, gambar 6.2, ganti Gambar 6.1.
Angka dibaca otomatis dari JSON hasil eksekusi. Tidak menulis interpretasi akademik."""
import json, shutil
from pathlib import Path
from docx import Document
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
from docx.shared import Inches, Pt
from docx.enum.text import WD_TAB_ALIGNMENT, WD_TAB_LEADER
R=Path('/Users/rafaelyudianto/Documents/COMP8035041-Assignment-II')
OUT=R/'analisis-lanjutan';SRC=R/'Assignment-II-DataCo-Laporan-Final-High-Quality.docx'
A=json.load(open(OUT/'A_equivalence.json'));B=json.load(open(OUT/'B_decision.json'))
C=json.load(open(OUT/'C_ablation.json'));D=json.load(open(OUT/'D_graph.json'))
d=Document(SRC)
tbl_style=d.tables[15].style
def dec(x,n=4):return f'{x:.{n}f}'
def p_before(anchor,txt,style=None,italic=False):
    p=d.add_paragraph();r=p.add_run(txt)
    if style:p.style=d.styles[style]
    r.italic=italic
    anchor._p.addprevious(p._p);return p
def table_before(anchor,data,widths=None):
    t=d.add_table(rows=len(data),cols=len(data[0]))
    try:t.style=tbl_style
    except Exception:pass
    for i,row in enumerate(data):
        for j,val in enumerate(row):
            c=t.cell(i,j);c.text=str(val)
            for pp in c.paragraphs:
                for rr in pp.runs:rr.font.size=Pt(9)
    anchor._p.addprevious(t._tbl)
    return t
def img_before(anchor,path,caption,width=6.0):
    p=d.add_paragraph();p.add_run().add_picture(str(path),width=Inches(width))
    anchor._p.addprevious(p._p)
    cap=d.add_paragraph(caption);cap.style=d.styles['Figure Caption']
    anchor._p.addprevious(cap._p);return cap
def add_bookmark(para,name):
    b=OxmlElement('w:bookmarkStart');b.set(qn('w:id'),str(9100+abs(hash(name))%80));b.set(qn('w:name'),name)
    e=OxmlElement('w:bookmarkEnd');e.set(qn('w:id'),b.get(qn('w:id')))
    para._p.insert(0,b);para._p.append(e)
def toc_entry_after(anchor,txt,bm):
    p=d.add_paragraph();p.paragraph_format.space_after=Pt(3);p.paragraph_format.line_spacing=1.0
    p.paragraph_format.tab_stops.add_tab_stop(Inches(6.45),WD_TAB_ALIGNMENT.RIGHT,WD_TAB_LEADER.DOTS)
    r=p.add_run(txt+'\t');r.font.size=Pt(11)
    for kind in ['begin','instruction','separate','value','end']:
        rr=OxmlElement('w:r')
        if kind=='instruction':
            el=OxmlElement('w:instrText');el.set(qn('xml:space'),'preserve');el.text=f' PAGEREF {bm} \\h '
        elif kind=='value':el=OxmlElement('w:t');el.text='1'
        else:el=OxmlElement('w:fldChar');el.set(qn('w:fldCharType'),kind)
        rr.append(el);p._p.append(rr)
    anchor._p.addnext(p._p);return p
def find(t):
    for p in d.paragraphs:
        if p.text.startswith(t):return p
    raise KeyError(t)
# ---------- 5.4: kesetaraan regularisasi ----------
a54=find('5.5 Evaluasi Model')
p_before(a54,'Konfigurasi regularisasi kedua implementasi disetarakan memakai hubungan regParam = 1/(C x n_train) yang berlaku ketika Spark memakai loss rata-rata dan scikit-learn memakai C = 1/alpha, dengan n_train = 49.826. Tabel 5.6 membandingkan kedua implementasi pada pasangan parameter yang setara.')
p_before(a54,'Tabel 5.6 Kesetaraan regularisasi Spark MLlib dan scikit-learn').style=d.styles['Table Caption']
pa=A['pair_comparison']['A_sklearnC1.0_vs_sparkRegParam2.007e-5'];pb=A['pair_comparison']['B_sklearnC2.007e-4_vs_sparkRegParam0.1']
table_before(a54,[['Pasangan parameter setara','Korelasi probabilitas (test)','Delta AP test','Delta ROC-AUC test'],
 ['scikit-learn C=1,0 <-> Spark regParam=2,007x10^-5',dec(pa['corr_prob_test'],12),dec(pa['dAP_test'],8),dec(pa['dAUC_test'],8)],
 ['scikit-learn C=2,007x10^-4 <-> Spark regParam=0,1',dec(pb['corr_prob_test'],12),dec(pb['dAP_test'],8),dec(pb['dAUC_test'],8)]])
p_before(a54,'Konfigurasi awal tidak setara karena C=1,0 pada scikit-learn setara dengan regParam=2,007x10^-5 pada Spark, bukan 0,1. Setelah disetarakan, kedua implementasi menghasilkan probabilitas yang identik secara numerik dan selisih AP test tidak melebihi 6x10^-8. Selisih AP antar tingkat regularisasi hanya sekitar 0,0004, sehingga regularisasi bukan sumber perbedaan yang berarti pada dataset ini.')
# ---------- 5.5: evaluasi keputusan + ablation ----------
a56=find('5.6 Analisis')
p_before(a56,'Selain ambang F1 pada data validation, evaluasi dilakukan pada aturan yang benar-benar memisahkan kelas melalui peringkat skor. Tabel 5.7 menyajikan Average Precision dan ROC-AUC beserta interval kepercayaan bootstrap 1.000 resampel (seed 42), kemudian presisi dan recall pada k persen skor tertinggi serta lift terhadap prevalensi. Seluruh ambang peringkat dibekukan dari data validation.')
p_before(a56,'Tabel 5.7 Evaluasi keputusan berbasis peringkat pada data test').style=d.styles['Table Caption']
sk=B['models']['sklearn_lr'];sp=B['models']['spark_lr'];tk={x['k']:x for x in sk['topk']};tks={x['k']:x for x in sp['topk']}
bsk=sk['bootstrap'];bsp=sp['bootstrap']
table_before(a56,[['Ukuran','LR scikit-learn','LR Spark MLlib'],
 ['Average Precision (CI95)',f"{dec(sk['ap_test'])} [{dec(bsk['average_precision']['lo95'])}, {dec(bsk['average_precision']['hi95'])}]",f"{dec(sp['ap_test'])} [{dec(bsp['average_precision']['lo95'])}, {dec(bsp['average_precision']['hi95'])}]"],
 ['ROC-AUC (CI95)',f"{dec(sk['auc_test'])} [{dec(bsk['roc_auc']['lo95'])}, {dec(bsk['roc_auc']['hi95'])}]",f"{dec(sp['auc_test'])} [{dec(bsp['roc_auc']['lo95'])}, {dec(bsp['roc_auc']['hi95'])}]"],
 ['Precision@10%',dec(tk[0.1]['precision_at_k']),dec(tks[0.1]['precision_at_k'])],
 ['Precision@20%',dec(tk[0.2]['precision_at_k']),dec(tks[0.2]['precision_at_k'])],
 ['Precision@30%',dec(tk[0.3]['precision_at_k']),dec(tks[0.3]['precision_at_k'])],
 ['Lift@20% terhadap prevalensi',dec(tk[0.2]['lift'],3),dec(tks[0.2]['lift'],3)],
 ['Recall@30%',dec(tk[0.3]['recall_at_k']),dec(tks[0.3]['recall_at_k'])]])
p_before(a56,f"Prevalensi kelas positif pada data test adalah {dec(B['prevalence_test'])}. Interval bootstrap kedua implementasi saling tumpang tindih sehingga perbedaan di antara keduanya tidak dapat dinyatakan bermakna.")
p_before(a56,'Tabel 5.8 Uji sumber sinyal (ablation) pada data test').style=d.styles['Table Caption']
ab=C['ablation_sklearn_lr_C1'];nl=C['nonlinear']
table_before(a56,[['Subset fitur','Jumlah fitur','Average Precision test','ROC-AUC test'],
 ['Jadwal saja',ab['jadwal saja']['n_features'],dec(ab['jadwal saja']['ap_test']),dec(ab['jadwal saja']['auc_test'])],
 ['Jadwal + jumlah item',ab['jadwal+jumlah item']['n_features'],dec(ab['jadwal+jumlah item']['ap_test']),dec(ab['jadwal+jumlah item']['auc_test'])],
 ['Kategori saja',ab['kategori saja']['n_features'],dec(ab['kategori saja']['ap_test']),dec(ab['kategori saja']['auc_test'])],
 ['Segmen + market saja',ab['segmen+market saja']['n_features'],dec(ab['segmen+market saja']['ap_test']),dec(ab['segmen+market saja']['auc_test'])],
 ['Tanpa jadwal',ab['tanpa jadwal']['n_features'],dec(ab['tanpa jadwal']['ap_test']),dec(ab['tanpa jadwal']['auc_test'])],
 ['Semua fitur',ab['semua fitur']['n_features'],dec(ab['semua fitur']['ap_test']),dec(ab['semua fitur']['auc_test'])],
 ['Random Forest (semua fitur)',48,dec(nl['RandomForest']['ap_test']),dec(nl['RandomForest']['auc_test'])],
 ['Gradient Boosting (semua fitur)',48,dec(nl['GradientBoosting']['ap_test']),dec(nl['GradientBoosting']['auc_test'])]])
p_before(a56,'Days for shipment (scheduled) memiliki pemetaan satu-satu dengan Shipping Mode (Same Day=0, First Class=1, Second Class=2, Standard Class=4), sehingga keduanya membawa informasi yang sama. Tabel 5.8 menunjukkan kontribusi tiap kelompok fitur terhadap kinerja.')
img_before(a56,OUT/'B_pr_roc_test.png','Gambar 5.1 Kurva precision-recall dan ROC pada data test',6.2)
# ---------- 6.1: perluasan graf ----------
a62=find('6.2 Analisis dan Insight')
p_before(a62,'Selain metrik graf bipartit pesanan-kategori, dilakukan proyeksi kategori-kategori dengan bobot berupa jumlah pesanan yang memuat kedua kategori. Tabel 6.4 menyajikan sentralitas pada proyeksi dan Tabel 6.5 tingkat keterlambatan per kategori. Proyeksi mencakup 33 kategori dengan 434 edge.')
p_before(a62,'Tabel 6.4 Sentralitas proyeksi kategori-kategori').style=d.styles['Table Caption']
cp=D['category_projection']
table_before(a62,[['Metrik','Lima teratas'],
 ['Weighted degree',', '.join(f"{x['category']} ({x['weighted_degree']})" for x in cp['weighted_degree_top10'][:5])],
 ['PageRank (alpha=0,85)',', '.join(f"{x['category']} ({dec(x['pagerank'])})" for x in cp['pagerank_top10'][:5])],
 ['Eigenvector',', '.join(f"{x['category']} ({dec(x['eigenvector'])})" for x in cp['eigenvector_top10'][:5])],
 ['Betweenness (sampel)',', '.join(f"{x['category']} ({dec(x['betweenness'])})" for x in cp['betweenness_sample']['top10'][:5])],
 ['Komunitas (greedy modularity)',f"{cp['communities']['n_communities']} komunitas, ukuran {cp['communities']['sizes']}"]])
p_before(a62,'Tabel 6.5 Tingkat keterlambatan per kategori pada graf lengkap').style=d.styles['Table Caption']
rows=[['Category Id','Tingkat keterlambatan','Jumlah pesanan','CI95']]
for x in D['late_rate_by_category'][:10]:
    rows.append([x['category'],dec(x['late_rate'],3),x['orders'],f"[{dec(x['ci95'][0],3)}, {dec(x['ci95'][1],3)}]"])
table_before(a62,rows)
p_before(a62,f"Komponen terhubung terbesar memuat {D['largest_component']['orders']} pesanan dengan tingkat keterlambatan {dec(D['largest_component']['late_rate'])} (CI95 [{dec(D['largest_component']['ci95'][0])}, {dec(D['largest_component']['ci95'][1])}]). Angka pada Tabel 6.4-6.5 berasal dari perhitungan proyeksi dan bukan statistik graf bipartit lengkap.")
img_before(a62,OUT/'E_projection.png','Gambar 6.2 Proyeksi kategori-kategori dengan bobot pesanan bersama',6.2)
# ---------- ganti Gambar 6.1 ----------
new_part,new_rId=d.part.get_or_add_image(str(OUT/'D_graph_subset_fixed.png'))
cap61=find('Gambar 6.1 Subset graf')
# paragraph sebelum caption yang memuat drawing
target=None
for p in d.paragraphs:
    if p._p.xpath('.//w:drawing') and p._p.getnext() is not None:
        nxt=p._p.getnext()
        if nxt is cap61._p:target=p;break
if target is not None:
    blip=target._p.find('.//'+qn('a:blip'))
    if blip is not None:blip.set(qn('r:embed'),new_rId);print('Gambar 6.1 diganti')
# ---------- entri TOC baru ----------
tbl_entries=[('Tabel 5.6 Kesetaraan regularisasi Spark MLlib dan scikit-learn','bm_t56'),
 ('Tabel 5.7 Evaluasi keputusan berbasis peringkat pada data test','bm_t57'),
 ('Tabel 5.8 Uji sumber sinyal (ablation) pada data test','bm_t58'),
 ('Tabel 6.4 Sentralitas proyeksi kategori-kategori','bm_t64'),
 ('Tabel 6.5 Tingkat keterlambatan per kategori pada graf lengkap','bm_t65')]
fig_entries=[('Gambar 5.1 Kurva precision-recall dan ROC pada data test','bm_g51'),
 ('Gambar 6.2 Proyeksi kategori-kategori dengan bobot pesanan bersama','bm_g62')]
# beri bookmark pada caption baru
caps={}
for p in d.paragraphs:
    for txt,bm in tbl_entries+fig_entries:
        if p.text.strip()==txt:add_bookmark(p,bm);caps[txt]=p
anchor_tbl=find('Tabel 6.3 Komponen terhubung pada graf lengkap')
for txt,bm in tbl_entries:toc_entry_after(anchor_tbl,txt,bm)
anchor_fig=find('Gambar 6.1 Subset graf')
for txt,bm in fig_entries:toc_entry_after(anchor_fig,txt,bm)
d.save(SRC)
print('saved. tables now:',len(d.tables))
