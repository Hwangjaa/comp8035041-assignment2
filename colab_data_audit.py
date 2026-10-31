# Bantuan teknis: unduh dan verifikasi data yang sudah digunakan pada Assignment I.
# Tidak memilih fitur, algoritma, strategi evaluasi, atau menginterpretasikan hasil.
from pathlib import Path
import csv, hashlib, json, platform, sys
import requests

ROOT = Path('/content/COMP8035041-Assignment-II')
RAW = ROOT / 'data' / 'raw'
RAW.mkdir(parents=True, exist_ok=True)
api = 'https://data.mendeley.com/public-api/datasets/8gx2fvg2k6/files?folder_id=root&version=5'
# Metadata resmi sudah diverifikasi; hindari endpoint API yang menolak runtime Colab.
specs = [
    ('DataCoSupplyChainDataset.csv', '72784be5-36d3-44fe-b75d-0edbf1999f65', 'fa6d022ed437155e1a2f0378710602848703c8a7f203f7ff5d77805bf8480aa6', 95910149),
    ('DescriptionDataCoSupplyChain.csv', '29dc7b05-dda6-4834-8354-5b5cc44430df', '9828e34669bd6d77e3b4463364cc44a5d52446b5e246fc258758cfe592566c4b', 3444),
    ('tokenized_access_logs.csv', '66751ed1-e1c4-4a37-b759-d1e38d3f36c1', '7a4372df63a1e87f5add68bc036bb6064db09069998f25a679aec39f1a8d7765', 95446364),
]
items = [{'filename': name, 'content_details': {'sha256_hash': digest, 'size': size, 'download_url': f'https://data.mendeley.com/public-files/datasets/8gx2fvg2k6/files/{fid}/file_downloaded'}} for name, fid, digest, size in specs]
manifest = []
for item in items:
    details = item['content_details']
    path = RAW / item['filename']
    expected = details['sha256_hash']
    def sha256_file(p):
        h = hashlib.sha256()
        with p.open('rb') as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b''):
                h.update(chunk)
        return h.hexdigest()
    if not path.exists() or sha256_file(path) != expected:
        temporary = path.with_suffix('.download')
        with requests.get(details['download_url'], stream=True, timeout=(30, 180)) as download:
            download.raise_for_status()
            with temporary.open('wb') as output:
                for chunk in download.iter_content(1024 * 1024):
                    output.write(chunk)
        assert sha256_file(temporary) == expected, f'Hash gagal: {path.name}'
        temporary.replace(path)
    assert path.stat().st_size == details['size']
    manifest.append({'file': path.name, 'bytes': path.stat().st_size, 'sha256': sha256_file(path)})
    print('HASH_PASS:', path.name, flush=True)

counts = {}
for name, encoding in [('DataCoSupplyChainDataset.csv', 'latin1'), ('tokenized_access_logs.csv', 'utf-8')]:
    with (RAW / name).open(encoding=encoding, newline='') as stream:
        reader = csv.reader(stream)
        header = next(reader)
        count = 0
        malformed = 0
        for row in reader:
            count += 1
            malformed += len(row) != len(header)
    counts[name] = {'rows': count, 'columns': len(header), 'malformed_rows': malformed}
assert counts['DataCoSupplyChainDataset.csv'] == {'rows': 180519, 'columns': 53, 'malformed_rows': 0}
assert counts['tokenized_access_logs.csv'] == {'rows': 469977, 'columns': 8, 'malformed_rows': 0}
result = {'python': sys.version.split()[0], 'platform': platform.system(), 'source': 'https://data.mendeley.com/datasets/8gx2fvg2k6/5', 'files': manifest, 'structure': counts, 'status': 'COLAB_DATACO_AUDIT=PASS'}
(ROOT / 'colab_data_audit_results.json').write_text(json.dumps(result, indent=2))
print(json.dumps(result, indent=2))
print('Belum menjalankan model ML, graph analytics, Spark, atau HDFS.')
