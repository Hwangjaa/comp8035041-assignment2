import ast, datetime, hashlib, json, pathlib, sys, zipfile
OUT=pathlib.Path(__file__).parent
ROOT=OUT.parent.parent
SPARK=ROOT/'runtime/spark-3.5.9-bin-hadoop3'
records=json.loads((OUT/'command-index.json').read_text())
sources=json.loads((OUT/'source-evidence.json').read_text())
static={}
for rel,names in {'python/pyspark/ml/classification.py':['LogisticRegression','DecisionTreeClassifier','RandomForestClassifier','GBTClassifier'],'python/pyspark/ml/evaluation.py':['BinaryClassificationEvaluator','MulticlassClassificationEvaluator']}.items():
    p=SPARK/rel; tree=ast.parse(p.read_text()); entries={}
    for node in tree.body:
        if isinstance(node,ast.ClassDef) and node.name in names:
            doc=ast.get_docstring(node) or ''
            entries[node.name]={'line':node.lineno,'source_present':True,'metric_documentation_lines':[x.strip() for x in doc.splitlines() if any(y in x for y in ['areaUnder','weightedPrecision','weightedRecall','accuracy','f1','precisionByLabel','recallByLabel'])]}
    static[str(p)]={'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'classes':entries}
jar_classes={}
for jar in (SPARK/'jars').glob('spark-mllib_*.jar'):
    with zipfile.ZipFile(jar) as z:
        all_names=set(z.namelist())
    names=['org/apache/spark/ml/classification/'+x+'.class' for x in ['LogisticRegression','DecisionTreeClassifier','RandomForestClassifier','GBTClassifier']]+['org/apache/spark/ml/evaluation/'+x+'.class' for x in ['BinaryClassificationEvaluator','MulticlassClassificationEvaluator']]
    jar_classes[str(jar)]={x:x in all_names for x in names}
verification={'source_hashes_unchanged':{p:hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()==v['sha256'] for p,v in sources.items()},'command_logs_present':all(pathlib.Path(r[k]).is_file() for r in records for k in ['stdout_path','stderr_path'])}
smoke=next(r for r in records if r['label']=='spark_range_smoke')
historic=sources[str(ROOT/'runtime/logs/smoke-test.log')]
summary={'language':'id','scope':'Pemeriksaan read-only environment dan smoke infrastruktur; bukan pipeline dataset penuh.','command_count':len(records),'interpreters':json.loads((OUT/'interpreters.json').read_text()),'python_probes':[r for r in records if r['label'].startswith('python_')],'spark_smoke':smoke,'hdfs_current':[r for r in records if r['label'] in ['hdfs_ls','hdfs_report']],'historical_smoke':{'source':str(ROOT/'runtime/logs/smoke-test.log'),'mtime_utc':historic['mtime_utc'],'markers':[x for x in historic['content'].splitlines() if x.startswith(('HDFS_WRITE_READ=','SPARK_VERSION=','ROW_COUNT=','SPARK_HDFS_SMOKE='))],'meaning':'Hanya bukti historis smoke tiga baris; bukan kondisi HDFS sekarang atau full dataset.'},'static_api_evidence':static,'jar_class_presence':jar_classes,'algorithm_readiness':'Tidak ada kandidat yang lulus import ML pada interpreter yang diuji. Source Python dan class JVM Spark tersedia, tetapi import PySpark ML/evaluator terhalang numpy; sklearn tidak ditemukan. Tidak ada algoritma dipilih.','metric_readiness':'Fungsi sklearn dan evaluator PySpark gagal import; nama metrik di source hanya bukti API statis, bukan hasil evaluasi.','verification':verification,'changes':'Berkas bukti di output-tahap-AB/environment; temporary Spark/Java di ~/.hermes/cache/scratch/comp8035041-environment; tanpa install, daemon start, training, perubahan source/config/dataset/notebook.'}
(OUT/'environment-summary.json').write_text(json.dumps(summary,indent=2))
text='''# Audit environment lokal (tanpa training)

## Hasil aktual
- macOS arm64; Python sistem 3.9.6 dan Hermes 3.14.7 diuji (termasuk alias interpreter dan pm-runtime).
- numpy, pandas, scikit-learn, scipy, networkx tidak dapat di-import pada interpreter yang diperiksa. Versi tidak diklaim ketika import gagal.
- PySpark tidak tersedia pada jalur native, tetapi bundle Spark 3.5.9 berhasil di-import melalui PYTHONPATH eksplisit.
- Java Corretto 17.0.20.1 dan Hadoop 3.4.3 berhasil menjalankan perintah versi.
- Sesi Spark local[2] berhasil: range(10).count() = 10; stop dipanggil dan proses selesai exit 0. Ini tidak menguji Python worker/UDF, ML atau kompatibilitas pipeline penuh.
- HDFS ls dan report saat pemeriksaan gagal Connection refused pada 127.0.0.1:19000; tidak ada daemon dinyalakan. Tidak dapat memverifikasi isi HDFS atau dataset aktual.
- Log 2026-10-13 menyimpan HDFS_WRITE_READ=PASS dan SPARK_HDFS_SMOKE=PASS dengan ROW_COUNT=3. Ini bukti historis infrastruktur, bukan full dataset.

## Opsi algoritma dan metrik (bukan pemilihan)
- LogisticRegression, DecisionTreeClassifier, RandomForestClassifier, GBTClassifier: source bundle PySpark dan class JVM terverifikasi ada; seluruh import Python ML gagal karena numpy tidak ditemukan.
- LogisticRegression, DecisionTreeClassifier, RandomForestClassifier, GradientBoostingClassifier sklearn: import gagal karena sklearn tidak ditemukan.
- accuracy, precision, recall, F1, ROC-AUC, average precision, confusion matrix dan kurva sklearn: import gagal. BinaryClassificationEvaluator/MulticlassClassificationEvaluator PySpark juga gagal import karena numpy. Bukti nama metrik statis ada di environment-summary.json; tidak dinyatakan siap pakai.
- Tidak ada training, fitur, split, benchmark, pemilihan model atau pembacaan dataset akademik.

## Bukti dan reproduksi
- environment-summary.json: hasil agregat, probe import lengkap, bukti source/JAR dan verifikasi hash source/config/log yang dibaca.
- command-index.json: setiap argv, cwd, environment override, exit code, timeout, path stdout/stderr dan command reproduksi.
- <label>.json, <label>.stdout.log, <label>.stderr.log: bukti per perintah.
- source-evidence.json: isi README/env/config dan log historis beserta SHA256/mtime.
- Jalankan ulang dari direktori ini: python -B audit_environment.py > audit-run.stdout.log 2> audit-run.stderr.log; python -B finalize_evidence.py > finalize.stdout.log 2> finalize.stderr.log
- Java/PATH/PYTHONPATH hanya pada subprocess. TMPDIR, java.io.tmpdir dan spark.local.dir diarahkan ke /Users/rafaelyudianto/.hermes/cache/scratch/comp8035041-environment, bukan runtime/tmp atau system tmp.
- HDFS diberi batas waktu 20 detik; sesi Spark 120 detik. Peringatan native-hadoop macOS tercatat dan bukan bukti dukungan codec native.
'''
(OUT/'README.md').write_text(text)
assert all(verification['source_hashes_unchanged'].values())
assert verification['command_logs_present']
assert smoke['result']['pass'] and smoke['result']['session_stopped'] and smoke['exit_code']==0
print(json.dumps({'verification':verification,'command_count':len(records),'summary':str(OUT/'environment-summary.json'),'report':str(OUT/'README.md'),'static_api_evidence':static,'jar_class_presence':jar_classes},indent=2))
