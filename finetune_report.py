from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
from docx import Document
from docx.shared import Inches,Pt
from docx.oxml import OxmlElement
from docx.text.paragraph import Paragraph
import re,json
root=Path('/Users/rafaelyudianto/Documents/COMP8035041-Assignment-II');base=Path('/Users/rafaelyudianto/Downloads')
# Diagram berdasarkan komponen dan transformasi yang sudah ditetapkan pada laporan.
w,h=1700,1700
im=Image.new('RGB',(w,h),'white');draw=ImageDraw.Draw(im)
fontpath='/System/Library/Fonts/Supplemental/Arial.ttf'
boldpath='/System/Library/Fonts/Supplemental/Arial Bold.ttf'
font=ImageFont.truetype(fontpath,28);bold=ImageFont.truetype(boldpath,34);small=ImageFont.truetype(fontpath,24)
def center(text,y,f,color='#172b4d'):
 if any(term in text for term in ['Spark','HDFS','CSV','clickstream','Python','hash','Parquet','Structured Streaming','cluster']):
  f=ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial Italic.ttf',f.size)
 box=draw.textbbox((0,0),text,font=f);draw.text(((w-(box[2]-box[0]))/2,y),text,font=f,fill=color)
def box(y,title,lines,done=False):
 color='#276749' if done else '#756025';fill='#edf7ef' if done else '#fff8e8'
 draw.rounded_rectangle((140,y,1560,y+180),radius=18,outline=color,width=4,fill=fill)
 center(title,y+18,bold)
 for i,line in enumerate(lines):center(line,y+70+i*38,font)
def arrow(y):
 draw.line((850,y,850,y+45),fill='#46556b',width=5);draw.polygon([(850,y+58),(837,y+40),(863,y+40)],fill='#46556b')
center('Alur Pemrosesan Apache Spark dengan HDFS',30,bold)
center('Batas pelaksanaan: data historis lokal dan uji integrasi infrastruktur',82,small)
box(145,'1. Sumber historis CSV',['Transaksi dan clickstream diunduh; hash serta struktur diperiksa','Pembersihan transaksi lokal menggunakan Python telah dijalankan'],True);arrow(328)
box(390,'2. Penyimpanan HDFS',['Uji tulis/baca berkas kecil: berhasil','Pemuatan seluruh dataset ke HDFS: belum dijalankan'],True);arrow(573)
box(635,'3. Pembacaan Apache Spark',['Spark local[2] membaca tiga baris uji langsung dari HDFS','Pembacaan dataset transaksi lengkap melalui Spark: belum dijalankan'],True);arrow(818)
box(880,'4. Transformasi dataset dalam Spark',['Pemetaan nama kolom, konversi tanggal, penyaringan nonbatal','Operasi telah dilakukan di Python; belum dieksekusi dalam Spark']);arrow(1063)
box(1125,'5. Agregasi dan keluaran',['Agregasi sesuai kebutuhan analitik; transaksi dalam Parquet','Konversi format dan keluaran analitik Spark: belum dijalankan'])
center('Hijau: terdapat bukti uji pada komponen; bukan seluruh tahap sudah selesai.',1355,small)
center('Kuning: tahap pemrosesan dataset yang belum dieksekusi.',1395,small)
center('Jalur clickstream melalui Structured Streaming belum diuji.',1460,font)
center('Diagram tidak menyatakan model, integrasi clickstream, atau cluster produksi sudah berjalan.',1510,small)
image=root/'gambar-2.2-alur-spark-hdfs.png';im.save(image)
src=base/'COMP8035041 - Assignment I - Gambar dan Halaman Diperbaiki.docx';d=Document(src)
# Tempatkan setelah gambar 2.1, sebelum Bab 3: masih dalam bagian 2.3.
heading=next(p for p in d.paragraphs if p.text=='BAB 3. TATA KELOLA IT')
def before(text=None):
 node=OxmlElement('w:p');heading._p.addprevious(node);p=Paragraph(node,heading._parent)
 if text:p.add_run(text)
 return p
p=before('Gambar 2.2 memperlihatkan hubungan HDFS dan Apache Spark serta batas pelaksanaan tiap tahap. Transformasi transaksi sudah dijalankan menggunakan Python; pelaksanaan transformasi yang sama melalui Spark belum dilakukan.');p.paragraph_format.keep_with_next=True
p=before();p.alignment=1;p.paragraph_format.keep_with_next=True;p.add_run().add_picture(str(image),width=Inches(6.0))
p=before('Gambar 2.2 Alur pemrosesan Apache Spark dengan HDFS dan status pelaksanaan');p.style=d.styles['Figure Caption'];p.paragraph_format.keep_with_next=False
# Tambahkan daftar gambar, jangan salah memilih caption badan.
idx=next(i for i,p in enumerate(d.paragraphs) if p.text=='DAFTAR GAMBAR')
anchor=d.paragraphs[idx+1]
node=OxmlElement('w:p');anchor._p.addnext(node);Paragraph(node,anchor._parent).add_run('Gambar 2.2 Alur pemrosesan Apache Spark dengan HDFS dan status pelaksanaan')
# Italic istilah asing, identifier, judul referensi, serta deklarasi berbahasa Inggris.
terms=['Apache Spark','Apache Hadoop','Spark Structured Streaming','Structured Streaming','Spark MLlib','Processing Framework','Data Ingestion','Market dan Business Drivers','Market drivers','Business drivers','market drivers','business drivers','Market','Business','Security','Compliance','DataCo Smart Supply Chain','DataCo','Big Data Analytics','Big Data','Operations / Logistics','Operations/Logistics','Operations','Logistics','CS Lead','Data/IT','data lake','framework','backend','single-node','multi-mesin','local[2]','loopback','batch','streaming','near-real-time','clickstream','dispatch','last-mile','real-time','snapshot','feed','cluster','benchmark','throughput','timestamp','join','pipeline','Python','pandas','CSV','JSON','Parquet','HDFS','Hadoop','Spark','Java','GDPR','SHA-256','ISO','MAX','IP','script','hash','role-based access control','Order Id','Order Item Id','Late_delivery_risk','Shipping canceled','Shipping Mode','Product Description','Product Image','Customer Email','Customer Password','Days for shipping (real)','Days for shipment (scheduled)','Delivery Status','Feature Engineering','Data Preprocessing','Machine Learning','Graph','Insight','graph','is_late','late_days','dispatch_real_days','dispatch_scheduled_days','shipping_date','order_date','t_order','t_event']
terms=sorted(set(terms),key=len,reverse=True)
pattern=re.compile('|'.join(re.escape(s) for s in terms)+r'|\b[A-Za-z][A-Za-z0-9_\-]*\.(?:csv|py|json)\b',re.I)
paras=list(d.paragraphs)
for table in d.tables:
 for row in table.rows:
  for cell in row.cells:paras.extend(cell.paragraphs)
foreign_form=False;refs=False;changes=0
for p in paras:
 if p.text=='DAFTAR PUSTAKA':refs=True
 if p.text=='BINUS UNIVERSITY ARTIFICIAL INTELLIGENCE USE DECLARATION FORM':refs=False;foreign_form=True
 # Bibliography entries retain citation metadata; italic foreign titles uniformly.
 full_english=(refs and not p.text.startswith('Video presentasi:')) or (foreign_form and p.text.startswith(('BINUS UNIVERSITY','Name:','Student ID:','Course Code:','Course Title:','Assignment Title:','Assignment Type:')))
 for run in list(p.runs):
  if run._r.xpath('.//w:drawing|.//w:fldChar|.//w:instrText'):continue
  text=run.text
  if not text:continue
  if full_english:
   run.italic=True;changes+=1;continue
  spans=list(pattern.finditer(text))
  # Form table cells in English.
  if p.text.startswith(('Discussed ','Drafted ','Assisted ','Grammar,','Data validation,','Idea and content','Text/Script','Image/Video','Translation,','Others','Yes /')):
   run.italic=True;changes+=1;continue
  if not spans:continue
  from copy import deepcopy
  anchor=run._r;pos=0
  for m in spans:
   for chunk,it in [(text[pos:m.start()],False),(m.group(),True)]:
    if chunk:
     rr=deepcopy(run._r)
     for child in list(rr):
      if child.tag!= '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}rPr':rr.remove(child)
     tt=OxmlElement('w:t');tt.set('{http://www.w3.org/XML/1998/namespace}space','preserve');tt.text=chunk;rr.append(tt);anchor.addprevious(rr)
     from docx.text.run import Run
     if it:Run(rr,p).italic=True;changes+=1
   pos=m.end()
  if text[pos:]:
   rr=deepcopy(run._r)
   for child in list(rr):
    if child.tag!='{http://schemas.openxmlformats.org/wordprocessingml/2006/main}rPr':rr.remove(child)
   tt=OxmlElement('w:t');tt.set('{http://www.w3.org/XML/1998/namespace}space','preserve');tt.text=text[pos:];rr.append(tt);anchor.addprevious(rr)
  anchor.getparent().remove(anchor)
for p in d.paragraphs:
 if p.text.startswith('BAB '):p.paragraph_format.page_break_before=True
out=base/'COMP8035041 - Assignment I - Finetune Gambar 2.2 dan Italic.docx';d.save(out)
c=Document(out)
assert len(c.inline_shapes)==2
assert len(c.element.xpath('.//m:oMath'))==5
assert all(p.paragraph_format.page_break_before for p in c.paragraphs if p.text.startswith('BAB '))
ps=c.paragraphs;g=next(i for i,p in enumerate(ps) if p.text.startswith('Gambar 2.2 Alur') and p.style.name=='Figure Caption');a=next(i for i,p in enumerate(ps) if p.text=='2.3 Processing Framework');b=next(i for i,p in enumerate(ps) if p.text=='BAB 3. TATA KELOLA IT');assert a<g<b
print(json.dumps({'file':str(out),'diagram':str(image),'images':2,'equations':5,'foreign_runs_formatted':changes,'placement_2_3':'PASS','chapter_breaks':'PASS'},indent=2))
