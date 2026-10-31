"""Bukti kegagalan loader lama dan regresi loader stabil dalam proses baru."""
import json
import os
from pathlib import Path
import subprocess
import sys
import unittest

HERE = Path(__file__).resolve().parents[1]
ROOT = HERE.parents[1]
LEGACY = ROOT / 'eksekusi-final-lokal/reproducibility-run/preprocessor.joblib'

class PortabilityTests(unittest.TestCase):
    def test_legacy_load_in_fresh_process(self):
        loader = os.environ.get('PREPROCESSOR_LOADER', 'stable')
        code = ('import joblib; obj=joblib.load(path)' if loader == 'legacy' else
                'from dataco_qa_v1.serialization import load_legacy_preprocessor; obj=load_legacy_preprocessor(path)')
        command = 'path=' + repr(str(LEGACY)) + ';' + code + ';assert len(obj.names)==48'
        child = subprocess.run([sys.executable, '-B', '-c', command], cwd=HERE,
                               capture_output=True, text=True)
        self.assertEqual(child.returncode, 0, child.stderr)

if __name__ == '__main__':
    unittest.main()
