"""Migrasi eksplisit joblib lokal tepercaya; tanpa alias global __main__."""
from pathlib import Path
import joblib
from joblib.numpy_pickle import NumpyUnpickler, _validate_fileobject_and_memmap
from .features import Features

class LegacyFeaturesUnpickler(NumpyUnpickler):
    def find_class(self, module, name):
        if (module, name) in {('__main__', 'Features'), ('pipeline', 'Features')}:
            return Features
        return super().find_class(module, name)

def load_legacy_preprocessor(path):
    """Hanya sumber tepercaya; API privat diuji dengan joblib 1.6.0."""
    path = Path(path).resolve()
    with path.open('rb') as handle:
        with _validate_fileobject_and_memmap(handle, str(path), None) as (stream, _):
            if isinstance(stream, str):
                raise ValueError('Format joblib pra-0.10 tidak didukung')
            obj = LegacyFeaturesUnpickler(str(path), stream, True).load()
    if type(obj) is not Features or set(vars(obj)) != {'vocab', 'names', 'fit_order_ids'}:
        raise ValueError('State preprocessor tidak sesuai kontrak yang diaudit')
    return obj

def convert_preprocessor(source, destination):
    """Simpan baru secara eksklusif, hanya di koreksi-kode."""
    source, destination = Path(source).resolve(), Path(destination).resolve()
    allowed = Path(__file__).resolve().parents[1]
    if not destination.is_relative_to(allowed) or source == destination:
        raise ValueError('Tujuan wajib salinan baru di koreksi-kode')
    obj = load_legacy_preprocessor(source)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open('xb') as handle:
        joblib.dump(obj, handle)
    return destination
