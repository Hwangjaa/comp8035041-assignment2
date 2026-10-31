from pathlib import Path
import json,re
import fitz
from PIL import Image,ImageDraw
OUT=Path(__file__).resolve().parent
import sys
pdf=Path(sys.argv[1])
doc=fitz.open(pdf)
page_dir=OUT/'halaman';page_dir.mkdir(exist_ok=True)
checks=[];thumbs=[]
for i,p in enumerate(doc):
    text=p.get_text();pix=p.get_pixmap(matrix=fitz.Matrix(1.2,1.2),alpha=False)
    dest=page_dir/f'halaman-{i+1:02}.png';pix.save(dest)
    bad=[]
    for block in p.get_text('dict')['blocks']:
        if block['type']!=0:continue
        for line in block['lines']:
            for s in line['spans']:
                x0,y0,x1,y1=s['bbox']
                if x0<0 or y0<0 or x1>p.rect.width+1 or y1>p.rect.height+1:bad.append(s['text'])
    checks.append({'page':i+1,'characters':len(text),'images':len(p.get_images()),'outside_page':bad,'empty_list_error':'No table of contents entries found' in text,'text':text})
    im=Image.open(dest).convert('RGB');im.thumbnail((306,420));tile=Image.new('RGB',(326,450),'#dddddd');tile.paste(im,((326-im.width)//2,20));ImageDraw.Draw(tile).text((10,430),f'Halaman {i+1}',fill='black');thumbs.append(tile)
for start in range(0,len(thumbs),6):
    group=thumbs[start:start+6];sheet=Image.new('RGB',(326*3,450*2),'white')
    for j,im in enumerate(group):sheet.paste(im,((j%3)*326,(j//3)*450))
    sheet.save(OUT/f'kontak-{start+1:02}-{start+len(group):02}.png')
(OUT/'render-page-checks.json').write_text(json.dumps({'pdf':str(pdf),'pages':len(doc),'within_40_pages':len(doc)<=40,'page_checks':checks},indent=2,ensure_ascii=False))
(OUT/'rendered-text.txt').write_text('\n\n'.join(f'HALAMAN {i+1}\n'+p.get_text() for i,p in enumerate(doc)))
print(json.dumps({'pages':len(doc),'list_errors':[x['page'] for x in checks if x['empty_list_error']],'outside_page':[x['page'] for x in checks if x['outside_page']],'page_images':str(page_dir)},indent=2))
