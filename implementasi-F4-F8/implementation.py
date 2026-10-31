from datetime import datetime
from fractions import Fraction
import numpy as np
from sklearn.metrics import roc_auc_score, average_precision_score, precision_score, recall_score, f1_score, confusion_matrix

def pretraining_guard(config):
    if not config['F1_F3']['exact_payload_recovered']:
        raise ValueError('Payload final F1–F3 belum pulih; training diblokir.')

def select_threshold(y, p):
    y, p = np.asarray(y, dtype=int), np.asarray(p, dtype=float)
    assert len(y) == len(p) and len(y) and np.isfinite(p).all()
    assert set(y) <= {0, 1} and ((p >= 0) & (p <= 1)).all()
    order = np.argsort(-p, kind='stable')
    y, p = y[order], p[order]
    positives, tp, count = int(y.sum()), 0, 0
    best_f, best_t = Fraction(0), float(np.nextafter(p.max(), np.inf))
    while count < len(y):
        end = count + 1
        while end < len(y) and p[end] == p[count]: end += 1
        tp += int(y[count:end].sum())
        score = Fraction(2 * tp, positives + end) if positives + end else Fraction(0)
        threshold = float(p[count])
        if score > best_f or (score == best_f and threshold > best_t):
            best_f, best_t = score, threshold
        count = end
    return best_t

def evaluate(y, p, threshold, predicted=None):
    y, p = np.asarray(y, dtype=int), np.asarray(p, dtype=float)
    assert len(y) == len(p) and len(y) and set(y) <= {0, 1}
    assert np.isfinite(p).all() and ((p >= 0) & (p <= 1)).all()
    pred = (p >= threshold).astype(int) if predicted is None else np.asarray(predicted, dtype=int)
    assert len(pred) == len(y) and set(pred) <= {0, 1}
    undefined = []
    if not pred.sum(): undefined.append('precision')
    if not y.sum(): undefined += ['recall', 'average_precision']
    if not (y.sum() + pred.sum()): undefined.append('binary_f1')
    if len(set(y)) < 2: undefined.append('roc_auc')
    return {'roc_auc': float(roc_auc_score(y,p)) if len(set(y)) == 2 else None,
            'average_precision': float(average_precision_score(y,p)) if y.sum() else None,
            'precision': float(precision_score(y,pred,zero_division=0)),
            'recall': float(recall_score(y,pred,zero_division=0)),
            'binary_f1': float(f1_score(y,pred,zero_division=0)),
            'confusion_matrix': confusion_matrix(y,pred,labels=[0,1]).tolist(),
            'confusion_matrix_order': [["TN", "FP"], ["FN", "TP"]],
            'undefined': undefined, 'threshold': float(threshold)}

def partition(iso_date):
    dt = datetime.fromisoformat(iso_date)
    return 'train' if dt < datetime(2017, 7, 1) else 'validation' if dt < datetime(2017, 10, 1) else 'test'
