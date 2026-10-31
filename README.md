# COMP8035041 Assignment II — DataCo Supply Chain Predictive Analytics

Repository ini berisi implementasi prediksi risiko keterlambatan pengiriman (Late Delivery Risk) menggunakan Logistic Regression dengan Apache Spark dan scikit-learn.

## Struktur Repository

```
├── data/                          Dataset DataCo Supply Chain
│   ├── raw/                       Dataset asli (CSV)
│   └── clean/                     Dataset hasil preprocessing
├── eksekusi-final-lokal/          Pipeline eksekusi lokal (Spark local mode)
│   ├── src/pipeline.py            Implementasi utama
│   ├── tests/test_pipeline.py     Unit test kontrak fitur dan metode
│   └── Assignment-II-DataCo-executed-local.ipynb
├── colab-final/                   Pipeline eksekusi Google Colab
│   ├── src/pipeline_colab.py      Varian Colab dari pipeline utama
│   └── tests/test_pipeline.py     Unit test Colab
├── implementasi-F4-F8/            Modul threshold selection dan evaluasi
│   ├── implementation.py          Fungsi pemilihan threshold dan evaluator
│   ├── test_contract.py           Unit test
│   └── README.md                  Dokumentasi F4-F8
└── persiapan-teknis-colab/        Smoke test Spark + HDFS
    └── runtime-evidence/src/spark_smoke.py
```

## Feature Groups (F4–F8)

- **F4**: Days for shipment (scheduled)
- **F5**: Customer Segment
- **F6**: Market
- **F7**: Category Id (multi-hot encoding)
- **F8**: Order Item Id Count

Target prediksi: `Late_delivery_risk` (0 = on-time, 1 = late)

## Temporal Split

- **Train**: order_date < 2017-07-01
- **Validation**: 2017-07-01 ≤ order_date < 2017-10-01
- **Test**: order_date ≥ 2017-10-01

## Eksekusi

Pipeline membutuhkan:
- Python 3.11+
- Apache Spark 3.5.9
- scikit-learn, pandas, networkx, joblib

Lihat laporan untuk detail eksperimen dan hasil evaluasi.
