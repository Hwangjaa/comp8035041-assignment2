"""Finalisasi: referensi APA7 alfabetis, TOC 6.6-6.8, insight 6.2, seragamkan desimal, tautan dataset."""
import json
from pathlib import Path
from docx import Document
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
from docx.shared import Pt, Inches
from docx.enum.text import WD_TAB_ALIGNMENT, WD_TAB_LEADER
R=Path('/Users/rafaelyudianto/Documents/COMP8035041-Assignment-II')
OUT=R/'analisis-lanjutan';SRC=R/'Assignment-II-DataCo-Laporan-Final-High-Quality.docx'
d=Document(SRC)
def find_para(t):
    for p in d.paragraphs:
        if p.text.strip().startswith(t) and '\t' not in p.text:return p
    raise KeyError(t[:40])
def find_caption(t):
    for p in d.paragraphs:
        if p.text.strip()==t and 'Caption' in p.style.name:return p
    raise KeyError(t)
# ===== 8. referensi APA 7 alfabetis =====
refs=[
 'Akturk, M. S., Mallipeddi, R. R., & Jia, X. (2022). Estimating impacts of logistics processes on online customer ratings: Consequences of providing technology-enabled order tracking data to customers. Journal of Operations Management, 68(6–7), 775–811. https://doi.org/10.1002/joom.1204',
 'Apache Software Foundation. (n.d.). HDFS Architecture. Diakses 20 Oktober 2026, dari https://hadoop.apache.org/docs/current/hadoop-project-dist/hadoop-hdfs/HdfsDesign.html',
 'Apache Software Foundation. (n.d.). Submitting Applications. Spark 3.5.9 Documentation. Diakses 20 Oktober 2026, dari https://spark.apache.org/docs/3.5.9/submitting-applications.html',
 'Blondel, V. D., Guillaume, J.-L., Lambiotte, R., & Lefebvre, E. (2008). Fast unfolding of communities in large networks. Journal of Statistical Mechanics: Theory and Experiment, 2008(10), P10008. https://doi.org/10.1088/1742-5468/2008/10/P10008',
 'Breiman, L. (2001). Random forests. Machine Learning, 45(1), 5–32. https://doi.org/10.1023/A:1010933404324',
 'Constante, F., Silva, F., & Pereira, A. (2019). DataCo SMART SUPPLY CHAIN FOR BIG DATA ANALYSIS (Version 5) [Data set]. Mendeley Data. https://doi.org/10.17632/8gx2fvg2k6.5',
 'European Parliament and Council of the European Union. (2016). Regulation (EU) 2016/679 (General Data Protection Regulation). Official Journal of the European Union, L 119, 1–88. https://eur-lex.europa.eu/eli/reg/2016/679/oj',
 'Friedman, J. H. (2001). Greedy function approximation: A gradient boosting machine. The Annals of Statistics, 29(5), 1189–1232. https://doi.org/10.1214/aos/1013203451',
 'Hagberg, A. A., Schult, D. A., & Swart, P. J. (2008). Exploring network structure, dynamics, and function using NetworkX. In G. Varoquaux, T. Vaught, & J. Millman (Eds.), Proceedings of the 7th Python in Science Conference (SciPy2008) (pp. 11–15).',
 'Kapoor, S., & Narayanan, A. (2023). Leakage and the reproducibility crisis in machine-learning-based science. Patterns, 4(9), 100804. https://doi.org/10.1016/j.patter.2023.100804',
 'Kaufman, S., Rosset, S., Perlich, C., & Stitelman, O. (2012). Leakage in data mining: Formulation, detection, and avoidance. ACM Transactions on Knowledge Discovery from Data, 6(4), 1–21. https://doi.org/10.1145/2382577.2382579',
 'Meng, X., Bradley, J., Yavuz, B., Sparks, E., Venkataraman, S., Liu, D., Freeman, J., Tsai, D. B., Amde, M., Owen, S., Xin, D., Xin, R., Franklin, M. J., Zadeh, R., Zaharia, M., & Talwalkar, A. (2016). MLlib: Machine learning in Apache Spark. Journal of Machine Learning Research, 17(34), 1–7.',
 'Page, L., Brin, S., Motwani, R., & Winograd, T. (1999). The PageRank citation ranking: Bringing order to the web (Technical Report No. 1999-66). Stanford InfoLab. http://ilpubs.stanford.edu:8090/422/',
 'Pedregosa, F., Varoquaux, G., Gramfort, A., Michel, V., Thirion, B., Grisel, O., Blondel, M., Prettenhofer, P., Weiss, R., Dubourg, V., Vanderplas, J., Passos, A., Cournapeau, D., Brucher, M., Perrot, M., & Duchesnay, É. (2011). Scikit-learn: Machine learning in Python. Journal of Machine Learning Research, 12, 2825–2830.',
 'Zaharia, M., Chowdhury, M., Das, T., Dave, A., Ma, J., McCauley, M., Franklin, M. J., Shenker, S., & Stoica, I. (2012). Resilient distributed datasets: A fault-tolerant abstraction for in-memory cluster computing. In Proceedings of the 9th USENIX Symposium on Networked Systems Design and Implementation (pp. 15–28). USENIX Association.']
first=find_para('Akturk, M. S.')
# hapus semua paragraf referensi lama
on=False;removed=[]
for p in list(d.paragraphs):
    if p.text.strip()=='DAFTAR PUSTAKA':on=True;continue
    if on and p.style.name.startswith('Heading'):break
    if on and p.text.strip():
        removed.append(p.text[:40]);p._p.getparent().remove(p._p)
anchor=find_para('DAFTAR PUSTAKA')
refs2=list(reversed(refs));prev=anchor
for r in refs2:
    p=d.add_paragraph();p.add_run(r)
    p.paragraph_format.space_after=Pt(6);p.paragraph_format.left_indent=Pt(24);p.paragraph_format.first_line_indent=Pt(-24)
    anchor._p.addnext(p._p)
print('refs removed',len(removed),'written',len(refs))
# ===== 9. Tabel 5.4 desimal koma =====
from docx.table import Table
def tbl_by_caption(cap):
    p=find_caption(cap) if False else find_para(cap);nxt=p._p.getnext()
    while nxt is not None and nxt.tag!=qn('w:tbl'):nxt=nxt.getnext()
    return Table(nxt,d)
t54=tbl_by_caption('Tabel 5.4 Kesetaraan regularisasi')
for row in t54.rows[1:]:
    for c in row.cells[1:]:
        c.text=c.text.replace('.',',')
print('Tabel 5.4 desimal diseragamkan')
# ===== TOC entri Tabel 6.6-6.8 =====
def add_bookmark(para,name,i):
    b=OxmlElement('w:bookmarkStart');b.set(qn('w:id'),str(i));b.set(qn('w:name'),name)
    e=OxmlElement('w:bookmarkEnd');e.set(qn('w:id'),str(i));para._p.insert(0,b);para._p.append(e)
def toc_entry_after(anchor,txt,bm):
    p=d.add_paragraph();p.paragraph_format.space_after=Pt(0.5);p.paragraph_format.line_spacing=0.92
    p.paragraph_format.tab_stops.add_tab_stop(Inches(6.45),WD_TAB_ALIGNMENT.RIGHT,WD_TAB_LEADER.DOTS)
    p.add_run(txt+'\t').font.size=Pt(10.5)
    for kind in ['begin','instruction','separate','value','end']:
        rr=OxmlElement('w:r')
        if kind=='instruction':
            el=OxmlElement('w:instrText');el.set(qn('xml:space'),'preserve');el.text=f' PAGEREF {bm} \\h '
        elif kind=='value':el=OxmlElement('w:t');el.text='1'
        else:el=OxmlElement('w:fldChar');el.set(qn('w:fldCharType'),kind)
        rr.append(el);p._p.append(rr)
    anchor._p.addnext(p._p);return p
new=[('Tabel 6.6 Anggota dua komunitas pada proyeksi kategori','bm_t66',9811),
     ('Tabel 6.7 Tingkat keterlambatan komponen terhubung','bm_t67',9812),
     ('Tabel 6.8 Tingkat keterlambatan menurut Days for shipment (scheduled) dan Shipping Mode','bm_t68',9813)]
for txt,bm,i in new:add_bookmark(find_caption(txt),bm,i)
anchor_toc=None
for p in d.paragraphs:
    if p.text.startswith('Tabel 6.5 Tingkat keterlambatan per kategori') and '\t' in p.text:anchor_toc=p;break
assert anchor_toc is not None,'entri TOC Tabel 6.5 tidak ditemukan'
for txt,bm,i in new:anchor_toc=toc_entry_after(anchor_toc,txt,bm)
# ===== tautan dataset di Bab 1 =====
p1=find_para('Penelitian menggunakan DataCo Smart Supply Chain')
from copy import deepcopy
def append_sentence(p,sent):
    r=p.add_run(sent);r.font.size=Pt(11)
append_sentence(p1,' Dataset yang digunakan tersedia pada DOI https://doi.org/10.17632/8gx2fvg2k6.5, sedangkan kode yang dieksekusi dan berkas hasil disertakan pada tautan repositori yang disediakan penulis.')
d.save(SRC)
print('selesai; total tabel:',len(d.tables))
