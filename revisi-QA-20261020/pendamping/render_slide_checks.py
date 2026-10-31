from pathlib import Path
import json
import pymupdf
from PIL import Image, ImageOps, ImageDraw
root = Path(__file__).parent / 'render-slide'
pdf = root / 'Assignment-II-DataCo-Hasil-Aktual-QA-Visual.pdf'
doc = pymupdf.open(pdf)
checks = []
thumbs = []
for i, page in enumerate(doc, 1):
    image_path = root / f'slide-{i:02}.png'
    page.get_pixmap(matrix=pymupdf.Matrix(1.5, 1.5)).save(image_path)
    outside = []
    for block in page.get_text('dict')['blocks']:
        if block['type'] != 0:
            continue
        for line in block['lines']:
            for span in line['spans']:
                if not page.rect.contains(pymupdf.Rect(span['bbox'])):
                    outside.append({'text': span['text'], 'bbox': span['bbox']})
    checks.append({'slide': i, 'characters': len(page.get_text()), 'outside_page': outside, 'image': str(image_path)})
    im = Image.open(image_path).convert('RGB')
    im.thumbnail((640, 360))
    tile = Image.new('RGB', (660, 400), 'white')
    tile.paste(im, (10, 30))
    ImageDraw.Draw(tile).text((10, 8), f'Slide {i}', fill='black')
    thumbs.append(tile)
for start in range(0, len(thumbs), 6):
    chunk = thumbs[start:start+6]
    sheet = Image.new('RGB', (1320, ((len(chunk)+1)//2)*400), '#bbbbbb')
    for j, im in enumerate(chunk):
        sheet.paste(im, ((j%2)*660, (j//2)*400))
    sheet.save(root / f'kontak-{start+1:02}-{start+len(chunk):02}.png')
result = {'pdf': str(pdf), 'slides': len(doc), 'checks': checks, 'visual_review': 'PENDING; text bounds alone do not prove visual correctness'}
(root / 'render-checks.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
print(json.dumps(result, indent=2))
