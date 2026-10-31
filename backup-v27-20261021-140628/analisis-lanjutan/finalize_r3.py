from pathlib import Path
import zipfile, shutil, re, hashlib
RF=Path('/Users/rafaelyudianto/.hermes/cache/scratch/dataco-hq/r3/Assignment-II-DataCo-Laporan-Final-High-Quality.docx')
OUT=Path('/Users/rafaelyudianto/Documents/COMP8035041-Assignment-II/Assignment-II-DataCo-Laporan-Final-High-Quality.docx')
tmp=OUT.with_suffix('.tmp.docx')
with zipfile.ZipFile(RF) as zin, zipfile.ZipFile(tmp,'w',zipfile.ZIP_DEFLATED) as zout:
    for item in zin.infolist():
        data=zin.read(item.filename)
        if item.filename=='word/settings.xml':
            xml=data.decode('utf-8')
            if '<w:updateFields' not in xml:
                xml=re.sub(r'(<w:settings\b[^>]*>)',r'\1<w:updateFields w:val="true"/>',xml,count=1)
            data=xml.encode('utf-8')
        zout.writestr(item,data)
shutil.move(tmp,OUT)
print('sha256:',hashlib.sha256(OUT.read_bytes()).hexdigest())