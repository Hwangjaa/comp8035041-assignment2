from docx import Document
from pathlib import Path
import hashlib,json,re
p=Path('/Users/rafaelyudianto/Documents/COMP8035041-Assignment-II/output-sunting-bahasa-20261022/rapih-final/Assignment-II-DataCo-Laporan-Final-Rapi-20261022.docx')
d=Document(p)
repls={
'Marketdrivers':'Market drivers','Businessdrivers':'Business drivers','TimOperations/Logistics':'Tim Operations/Logistics','CS Leaddapat':'CS Lead dapat','pesanan.CS':'pesanan. CS','TimData/IT':'Tim Data/IT','Keamanan/privasi':'Keamanan/privasi','pembentukanfitur':'pembentukan fitur','pelatihanLogistic Regression':'pelatihan Logistic Regression','padaruntime':'pada runtime','nilaihash-nya':'nilai hash-nya','training. Customer':'training. Customer','data test':'data test','ambangvalidation':'ambang validation','menghasilkanmodel':'menghasilkan model','darisnapshot':'dari snapshot','kelompokfitur':'kelompok fitur','menggunakanmachine learning':'menggunakan machine learning','darifitur':'dari fitur','antarasumber':'antarsumber','padafilesystem':'pada filesystem','pemrosesanCSV':'pemrosesan CSV','order_date':'order_date',
}
changed=0
def fix(s):
 global changed
 for a,b in repls.items():
  n=s.count(a)
  if n: s=s.replace(a,b); changed+=n
 return s
for p0 in d.paragraphs:
 if p0.text:
  old=p0.text; new=fix(old)
  if new!=old: p0.text=new
for t in d.tables:
 for row in t.rows:
  for c in row.cells:
   for p0 in c.paragraphs:
    old=p0.text; new=fix(old)
    if new!=old: p0.text=new
# Normalize accidental runs where a word boundary was lost by formatting edits.
for p0 in d.paragraphs:
 p0.paragraph_format.widow_control=True

d.save(p)
print(json.dumps({'replacements':changed,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}))
