"""Verifikasi teknis tanpa fit/Spark/notebook; seluruh keluaran hanya koreksi-kode."""
import os
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'
import sys
sys.dont_write_bytecode = True
import ast
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import unittest
from unittest.mock import patch
import joblib
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.dummy import DummyClassifier
from dataco_qa_v1.features import Features
from dataco_qa_v1.pipeline import make_orders
from dataco_qa_v1.serialization import load_legacy_preprocessor, convert_preprocessor

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
BASE = ROOT / 'eksekusi-final-lokal'

def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as handle:
        for chunk in iter(lambda: handle.read(1048576), b''):
            h.update(chunk)
    return h.hexdigest()

def dump(path, value):
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False))

def snapshot():
    paths = list((ROOT / 'data').rglob('*')) + list(BASE.rglob('*'))
    paths += list(ROOT.rglob('*.ipynb'))
    return {str(p.relative_to(ROOT)): sha(p) for p in sorted(set(paths))
            if p.is_file() and '__pycache__' not in p.parts and '.venv' not in p.parts
            and not p.is_relative_to(HERE)}

def blocked(*args, **kwargs):
    raise AssertionError('fit dilarang dalam verifikasi ini')

def prediction_worker(run, artifact):
    out = BASE / run
    encoder = joblib.load(artifact)  # loader standar: tidak ada alias/namespace pipeline lama
    assert type(encoder).__module__ == 'dataco_qa_v1.features'
    assert 'pipeline' not in sys.modules and not hasattr(sys.modules['__main__'], 'Features')
    # Tidak ada alias __main__.Features dalam interpreter anak.
    contract = json.loads((out / 'feature-contract.json').read_text())
    assert encoder.names == contract['feature_names'] and encoder.vocab == contract['vocabulary']
    assert hashlib.sha256(json.dumps(encoder.fit_order_ids).encode()).hexdigest() == contract['fit_order_ids_sha256']
    assert len(encoder.names) == contract['n_features'] == 48
    orders = pd.read_csv(out / 'orders.csv', float_precision='round_trip')
    orders['categories'] = orders.categories.map(json.loads)
    frozen = json.loads((out / 'thresholds-frozen.json').read_text())
    results = []
    for part in ['validation', 'test']:
        rows = orders.loc[orders.partition == part]
        matrix = encoder.transform(rows)
        assert list(matrix.shape) == contract['shape'][part]
        for model_name, model_file in [('sklearn_lr', 'sklearn-model.joblib'), ('baseline', 'baseline-model.joblib')]:
            model = joblib.load(out / model_file)
            stored = pd.read_csv(out / f'predictions-{part}-{model_name}.csv', float_precision='round_trip')
            assert rows['Order Id'].tolist() == stored['Order Id'].tolist()
            assert rows.Late_delivery_risk.tolist() == stored.Late_delivery_risk.tolist()
            prob = model.predict_proba(matrix)[:, 1]
            delta = float(np.max(np.abs(prob - stored.probability_1.to_numpy())))
            assert np.allclose(prob, stored.probability_1, rtol=0, atol=1e-14)
            threshold = frozen['thresholds'][model_name]
            assert stored.threshold.eq(threshold).all()
            mismatch = int(np.count_nonzero((prob >= threshold).astype(int) != stored.prediction.to_numpy()))
            assert mismatch == 0
            results.append({'run': run, 'partition': part, 'model': model_name, 'rows': len(rows),
                            'n_features': matrix.shape[1], 'max_abs_probability_error': delta,
                            'prediction_mismatches': mismatch, 'threshold': threshold})
    return {'namespace': type(encoder).__module__, 'plain_joblib_load': True,
            'pid': os.getpid(), 'results': results}

def main():
    before = snapshot()
    dump(HERE / 'hash-sebelum.json', before)
    report = {'versi': 'dataco_qa_v1 1.0.0', 'training_baru': False,
              'spark_dijalankan': False, 'notebook_dijalankan_ulang': False,
              'python': sys.version, 'executable': sys.executable, 'joblib': joblib.__version__}
    suite = unittest.defaultTestLoader.discover(str(HERE / 'tests'))
    with (HERE / 'tests-green.log').open('w') as log:
        result = unittest.TextTestRunner(stream=log, verbosity=2).run(suite)
    report['unit_tests'] = {'run': result.testsRun, 'failures': len(result.failures), 'errors': len(result.errors)}
    assert result.wasSuccessful()
    spec = importlib.util.spec_from_file_location('pipeline', BASE / 'src/pipeline.py')
    old = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(old)
    old_ast = ast.parse((BASE / 'src/pipeline.py').read_text())
    new_ast = ast.parse((HERE / 'dataco_qa_v1/features.py').read_text())
    feature_ast = lambda tree: ast.dump(next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == 'Features'), include_attributes=False)
    assert feature_ast(old_ast) == feature_ast(new_ast)
    report['implementasi_features_identik_ast'] = True
    raw = pd.read_csv(ROOT / 'data/raw/DataCoSupplyChainDataset.csv', encoding='latin1', low_memory=False)
    new_orders, new_items, new_audit = make_orders(raw)
    old_orders, old_items, old_audit = old.make_orders(raw)
    pd.testing.assert_frame_equal(new_orders, old_orders)
    pd.testing.assert_frame_equal(new_items, old_items)
    assert new_audit == old_audit
    for run in ['run-actual', 'reproducibility-run']:
        stored = pd.read_csv(BASE / run / 'orders.csv', float_precision='round_trip')
        stored['categories'] = stored.categories.map(json.loads)
        stored['order_date'] = pd.to_datetime(stored.order_date)
        pd.testing.assert_frame_equal(new_orders, stored)
    report['data_aktual_valid'] = {'source_rows': len(raw), 'orders': len(new_orders),
                                 'orders_dan_items_identik_pipeline_lama': True,
                                 'orders_identik_csv_kedua_run': True, 'audit': new_audit}
    states = []
    report['portable_subprocess'] = []
    for run in ['run-actual', 'reproducibility-run']:
        source = BASE / run / 'preprocessor.joblib'
        target = HERE / 'artifacts' / run / 'preprocessor.joblib'
        state = vars(load_legacy_preprocessor(source))
        states.append(state)
        if target.exists():
            assert vars(joblib.load(target)) == state
        else:
            convert_preprocessor(source, target)
        assert vars(joblib.load(target)) == state
        code = ('import sys,json;sys.path.insert(0,' + repr(str(HERE)) + ');'
                'import verify_corrections as v;'
                'v.Features.fit=v.blocked;v.LogisticRegression.fit=v.blocked;v.DummyClassifier.fit=v.blocked;'
                'print(json.dumps(v.prediction_worker(' + repr(run) + ',' + repr(str(target)) + ')))')
        env = dict(os.environ)
        env.pop('PYTHONPATH', None)
        child = subprocess.run([sys.executable, '-B', '-c', code], cwd=HERE, env=env,
                               capture_output=True, text=True, check=True)
        observed = json.loads(child.stdout)
        assert observed['pid'] != os.getpid()
        observed['source'] = str(source)
        observed['converted'] = str(target)
        observed['source_sha256'] = sha(source)
        observed['converted_sha256'] = sha(target)
        report['portable_subprocess'].append(observed)
    assert states[0] == states[1]
    report['state_encoder_antar_run_identik'] = True
    after = snapshot()
    dump(HERE / 'hash-sesudah.json', after)
    changed = sorted(k for k in before.keys() | after.keys() if before.get(k) != after.get(k))
    report['integritas_lama'] = {'files_checked': len(before), 'changed': changed}
    assert not changed
    report['status'] = 'PASS'
    report['batas'] = ['Bukan run penuh baru.', 'Tidak memanggil fit, Spark/JVM, atau notebook.',
                      'Prediksi hanya sklearn dan baseline tersimpan pada validation/test kedua run.',
                      'Portabilitas diuji pada interpreter dan environment lokal ini, bukan lintas versi sklearn/joblib/OS.',
                      'Validasi konflik diterapkan pada item noncanceled sesuai cohort lama; missing Category Id tetap MISSING.',
                      'Joblib/pickle hanya untuk sumber tepercaya; loader bukan sandbox.']
    dump(HERE / 'hasil-verifikasi.json', report)
    print(json.dumps(report, ensure_ascii=False))

if __name__ == '__main__':
    with patch.object(Features, 'fit', blocked), patch.object(LogisticRegression, 'fit', blocked), patch.object(DummyClassifier, 'fit', blocked):
        main()
