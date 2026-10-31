# Implementasi Feature Groups F4–F8

Folder ini berisi implementasi pemilihan threshold dan evaluasi model untuk eksperimen Logistic Regression dengan lima kelompok fitur (F4–F8).

## Kelompok Fitur (Feature Groups)

- **F4**: Days for shipment (scheduled) — durasi pengiriman terjadwal
- **F5**: Customer Segment — segmen pelanggan
- **F6**: Market — wilayah pasar
- **F7**: Category Id — kategori produk (multi-hot encoding)
- **F8**: Order Item Id Count — jumlah Order Item Id unik per pesanan

Target prediksi: `Late_delivery_risk` (biner: 0/1)

## File

- `implementation.py` — fungsi pemilihan threshold (validation binary F1 maximum) dan evaluator
- `test_contract.py` — unit test kontrak implementasi (boundary temporal split, threshold exhaustive, precision/recall calculation)

## Penggunaan

Modul ini dipanggil dari pipeline utama (`eksekusi-final-lokal/` atau `colab-final/`) untuk:
1. Memilih threshold optimal dari kandidat skor probabilitas pada data validasi.
2. Mengevaluasi performa model dengan metrik: ROC-AUC, Average Precision, Precision, Recall, Binary F1, Confusion Matrix.
3. Mempartisi data berdasarkan temporal split (train < 2017-07-01, validation < 2017-10-01, test ≥ 2017-10-01).

Lihat Bab 5 laporan untuk detail eksperimen.
