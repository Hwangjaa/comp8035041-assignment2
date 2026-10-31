# Eksekusi Final Lokal — Pipeline Spark Local Mode

Implementasi utama pipeline prediksi risiko keterlambatan pengiriman yang dijalankan di lingkungan lokal dengan Spark mode `local[2]`.

## File

- **`src/pipeline.py`**: Pipeline utama yang mencakup audit data, preprocessing, feature engineering (F4-F8), pelatihan Logistic Regression, threshold selection, evaluasi, dan ekspor hasil.
- **`tests/test_pipeline.py`**: Unit test kontrak fitur dan metode (boundary conditions, missing values, temporal split).
- **`Assignment-II-DataCo-executed-local.ipynb`**: Notebook eksekusi yang memanggil `pipeline.run()`.

## Proses Pipeline

1. **Audit sumber dan environment**: Verifikasi dataset, Spark version, Hadoop configuration
2. **Preprocessing**: Load data, filter cohort (exclude "Shipping canceled"), temporal split
3. **Feature engineering**: Ekstraksi F4-F8, encoding kategorikal, normalisasi
4. **Graph analysis**: Konstruksi bipartite graph (order-category) dengan Spark DataFrame
5. **Training**: Logistic Regression pada training set
6. **Threshold selection**: Binary F1 maximization pada validation set
7. **Evaluation**: ROC-AUC, Precision, Recall, F1 pada test set
8. **Export**: Model (joblib), confusion matrix, metrics JSON

## Output

Hasil eksekusi disimpan di folder output (default: `run-actual/`):
- `config.json`: Konfigurasi eksperimen
- `spark-environment.json`: Spark version dan Hadoop configuration
- `model.pkl`: Trained Logistic Regression model
- `metrics-*.json`: Evaluasi per split (train/validation/test)
- `graph-*.json`: Statistik graph analysis
- `execution.log`: Log eksekusi

## Menjalankan

```python
from pathlib import Path
from pipeline import run

root = Path('/path/to/dataco-assignment2')
output = Path('/path/to/output')
result = run(root, output)
```

Lihat notebook atau laporan untuk detail eksperimen.
