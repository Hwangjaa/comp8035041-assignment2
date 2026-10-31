# Colab Final — Pipeline Google Colab

Varian pipeline untuk eksekusi di Google Colab VM dengan Spark mode `local[2]`.

## File

- **`src/pipeline_colab.py`**: Pipeline utama (varian Colab dari `eksekusi-final-lokal/src/pipeline.py`)
- **`src/__init__.py`**: Modul marker
- **`tests/test_pipeline.py`**: Unit test kontrak fitur dan metode

## Perbedaan dengan Eksekusi Lokal

- Storage: `Colab VM local file:///` (bukan HDFS)
- Evaluation scope: Retrospective conditional cohort (orders known from final status as not "Shipping canceled")
- Path handling: Disesuaikan untuk Colab environment (`/content/`)

## Proses Pipeline

Sama dengan `eksekusi-final-lokal/`:
1. Audit data dan environment
2. Preprocessing dan temporal split
3. Feature engineering F4-F8
4. Graph analysis (order-category bipartite)
5. Training Logistic Regression
6. Threshold selection (validation binary F1 max)
7. Evaluation (train/validation/test)
8. Export model dan metrics

## Output

Struktur output identik dengan eksekusi lokal:
- `config.json`, `spark-environment.json`
- `model.pkl`, `metrics-*.json`
- `graph-*.json`, `execution.log`

Lihat laporan untuk detail eksperimen Colab.
