from docx import Document
p='/Users/rafaelyudianto/Documents/COMP8035041-Assignment-II/Assignment-II-DataCo-Laporan-Final-High-Quality.docx'
d=Document(p)
for x in d.paragraphs:
 if any(k in x.text for k in ['Eksperimen dijalankan pada macOS','Eksperimen final dijalankan','Average Precision']): print(repr(x.text))
