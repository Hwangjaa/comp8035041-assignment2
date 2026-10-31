# COMP8035041 Assignment II — Analisis Risiko Keterlambatan Pengiriman DataCo

Repositori ini memuat kode sumber dan dataset untuk COMP8035041 Assignment II.
Tugasnya memodelkan `Late_delivery_risk` pada dataset rantai pasok DataCo dengan
unit analisis **pesanan** (*Order Id*), membandingkan tiga pemodel, dan
mempresentasikan hubungan pesanan–kategori sebagai graf bipartit.

Laporan lengkap, interpretasi, dan analisis lanjutan ada di dokumen Word/PDF
(`PENGUMPULAN-COMP8035041-Assignment-II/`). README ini menjelaskan struktur
repo, cara menautkan alur, dan angka hasil yang dikutip langsung dari artefak
`run-actual` (eksekusi 20 Oktober 2026, `exit_status: 0`).

## Alur secara singkat

1. **Pembersihan dan audit** — dataset Mendeley Data v5 (180.519 baris item,
   65.752 pesanan) diaudit: pesanan berstatus `Shipping canceled` dibuang,
   pesanan dengan label atau identitas berkonflik membuat pipeline berhenti.
   Tersisa 62.897 pesanan (172.765 item).
2. **Pembagian temporal** — berbasis `order date (DateOrders)`: train sebelum
   2017-07-01 (49.826), validation 2017-07-01 s.d. sebelum 2017-10-01 (5.028),
   test mulai 2017-10-01 (8.043).
3. **Fitur (48 kolom)** — hari pengiriman terjadwal, jumlah item unik, segmen
   pelanggan, *market*, dan kategori (multi-hot) dengan aturan *MISSING*
   berkode `MISSING` dan nilai tak dikenal `UNKNOWN`.
4. **Tiga pemodel** — baseline prioritas kelas, `LogisticRegression`
   scikit-learn (C=1.0, lbfgs, seed 42), dan `LogisticRegression` PySpark
   (regParam=0.1, seed 42).
5. **Ambang beku** — dipilih dari **validation** (maksimisasi F1 biner, seri
   diputuskan ambang terbesar) sebelum test disentuh; terekam di
   `thresholds-frozen.json`.
6. **Graf** — bipartit pesanan–kategori dari kohort utuh; 62.948 simpul,
   152.676 sisi, 19 komponen terhubung, tanpa sisi ganda atau *self-loop*.

## Hasil utama (partisi test, n = 8.043)

| Model | Average Precision | ROC-AUC | Precision | Recall | F1 |
|---|---|---|---|---|---|
| baseline (prioritas) | 0,5764 | 0,5000 | 0,5764 | 1,0000 | 0,7313 |
| scikit-learn | 0,7364 | 0,7198 | 0,5764 | 1,0000 | 0,7313 |
| PySpark | 0,7369 | 0,7206 | 0,5764 | 1,0000 | 0,7313 |

Detail per partisi (termasuk validation dan matriks kebingungan) ada di
`run-actual/metrics.json`. Seluruh CSV prediksi (6 berkas) memungkinkan
penghitungan ulang semua metrik secara independen; hasilnya identik.

## Struktur repo

| Folder | Isi |
|---|---|
| `PENGUMPULAN-COMP8035041-Assignment-II/` | **Paket penyerahan final**: laporan DOCX/PDF, `PAKET-ARTEFAK-AUDIT5.zip` (52 berkas bukti: metrik, CSV prediksi, model, notebook, bukti eksekusi Colab, `SHA256SUMS-PAKET.txt`), plus `README-PENGUMPULAN.md` dan dokumentasi audit |
| `data/` | Data Mendeley Data (`raw/`, ±91 MB dataset utama; `clean/`, hasil pembersihan tahap awal) dan `source-manifest.json` (nama sumber + SHA-256) |
| `eksekusi-final-lokal/` | **Kode inti**: `src/pipeline.py` (alur A–D), `execute_notebook.py`, tes unit (`tests/test_pipeline.py`), notebook eksekusi 20 Okt 2026 |
| `colab-final/` | Varian pipeline untuk Colab (`src/pipeline_colab.py`) dan bukti eksekusi 22 Okt 2026 |
| `implementasi-F4-F8/` | Implementasi fitur F4–F8 dan tes kontraknya |
| `analisis-lanjutan/` | Skrip analisis A–H (ekivalensi, ablasion, graf, keputusan model) dan keluaran JSON |
| `persiapan-teknis-colab/` | Bukti runtime Colab (smoke test Spark) |
| skrip `audit_*.py` di akar | Audit sumber data, ketersediaan fitur, dan inklusi pesanan |
| `backup-*/`, `output-*/`, `revisi-*/`, `qa-high-quality/` | Riwayat iterasi dan koreksi QA — bukan bagian penyerahan |

## Menjalankan ulang

Lingkungan yang terekam: Python 3.12.15, PySpark 3.5.9, scikit-learn 1.9.1,
NetworkX 3.7, Java 17 (MacOS arm64). Daftar paket lengkap ada di
`run-actual/requirements-observed.txt` dan `environment.json` di dalam paket
ZIP. `.venv` dan distribusi Spark tidak ikut di repo.

```bash
python eksekusi-final-lokal/src/pipeline.py --root . --output eksekusi-final-lokal/run-actual
```

atau lewat notebook: `python eksekusi-final-lokal/execute_notebook.py`.
Lakukan di folder kerja terpisah bila ingin menyimpan `run-actual` aslinya.

## Catatan

- Graf subset untuk visualisasi memakai **10 kategori derajat tertinggi +
  200 pesanan tetangga terdekat** (dipilih deterministik, seed 42) — bukan
  statistik graf utuh; data lengkapnya (sisi, keanggotaan komponen) tersimpan
  sebagai CSV di paket ZIP.
- Ruang lingkup evaluasi bersifat retrospektif: pesanan dievaluasi setelah
  status akhirnya diketahui, dan status `Shipping canceled` tidak termasuk
  kohort. Ketersediaan fitur *as-of* pada waktu prediksi **belum
  tervalidasi** — dicatat sebagai keterbatasan di laporan.
- `tokenized_access_logs.csv` tidak dipakai pada alur final.
- Eksekusi Colab memakai runtime berbeda (Python 3.13.16, Spark 4.0.4); nilai
  metriknya setara dengan eksekusi lokal hingga enam desimal, dan keseluruhan
  artefak terverifikasi lewat `SHA256SUMS.txt`.
