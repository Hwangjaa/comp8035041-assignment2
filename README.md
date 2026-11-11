# COMP8035041 Big Data Analytics — DataCo Smart Supply Chain Predictive Analytics & Interactive Dashboard

Repository ini memuat seluruh artefak teknis dan laporan resmi untuk **Assignment II & Final Project** mata kuliah *COMP8035041 – Big Data Analytics* (BINUS Graduate Program, Magister Teknik Informatika) oleh **Rafael Yudianto (NIM: 2702752495)**.

Proyek ini mencakup pemrosesan data skala besar (*Big Data*), pemodelan prediktif risiko keterlambatan pengiriman (*Late Delivery Risk*) menggunakan Apache Spark MLlib dan scikit-learn, eksplorasi topologi jaringan produk belanja (*Graph Analytics*), serta instrumen pendukung keputusan operasional rantai pasok berbasis web interaktif (*Visualisasi Berupa Dashboard*).

---

## 📊 Dashboard Interaktif Mandiri (*Standalone Interactive Dashboard*)

Dashboard visualisasi analitik (Bab 7) dibangun secara mandiri (*standalone web application*) berbasis HTML5, Tailwind CSS, dan Plotly.js. Seluruh aset data (8.043 pesanan data uji dan metrik topologi graf bipartit) telah dipaketkan langsung dalam berkas `data.js` sehingga **dapat dijalankan dan diuji interaktivitasnya secara instan tanpa membutuhkan instalasi dependensi atau konfigurasi server khusus (*zero-installation*)**.

### Cara Menjalankan & Menguji Dashboard:

1. **Cara Langsung via Peramban (Paling Mudah)**:
   * Buka berkas **`dashboard/index.html`** (atau `docs/index.html`) langsung menggunakan peramban web modern (Google Chrome, Microsoft Edge, Mozilla Firefox, Safari).
   * Seluruh filter pasar (*Market*), filter moda pengiriman (*Shipping Mode*), slider dinamis ambang batas risiko (*decision threshold*), histogram distribusi risiko, dan tabel antrean kerja (*Live Dispatch Queue*) langsung aktif dan responsif secara *in-memory* di sisi klien (*client-side*).

2. **Cara Alternatif via Local HTTP Server (Opsional)**:
   ```bash
   # Jalankan server HTTP lokal sederhana dari root repositori:
   python3 -m http.server 8000

   # Akses melalui peramban:
   # http://localhost:8000/dashboard/
   ```

### Fitur Utama & Tiga Wawasan Bisnis (*Insights*) Dashboard:
1. **Interactive Scenario Controls**: Slider ambang batas keputusan risiko (0,40–0,85) dinamis serta filter wilayah pasar (*Market*) dan moda pengiriman (*Shipping Mode*).
2. **KPI Scorecards**: Ringkasan volume pesanan uji (8.043 pesanan), jumlah antrean risiko kritis terdeteksi, skor performa model (*Average Precision* 0,7364), dan skala jaringan graf (62.948 simpul).
3. **Insight 1 (Machine Learning — Antrean Prioritas Gudang)**: Histogram distribusi probabilitas risiko model Spark MLlib dan tabel interaktif *Live Dispatch Queue* (Top-K Alert). Memprioritaskan pesanan kritis darurat setiap awal shift kerja dengan presisi mencapai **78,9%**, mencegah denda penalti pelanggaran SLA dan melindungi barang bernilai tinggi.
4. **Insight 2 (Graph Analytics — Penataan Ulang Rak Gudang / *Reslotting*)**: Pemetaan graf bipartit pesanan-kategori produk mengidentifikasi simpul penghubung raksasa (*network hubs*) berketerlambatan tinggi >57,6% (Cleats, Men's Footwear, Women's Apparel). Panduan rekomendasi: penataan ulang slot rak gudang (*warehouse reslotting*) di area *Fast-Moving Staging Zone* dekat meja pengepakan (*packing station*), memangkas *picking cycle time* hingga 30%.
5. **Insight 3 (Business & Operations Policy — Kalibrasi SLA Realistis)**: Mengungkap paradoks operasional bahwa moda pengiriman dengan janji durasi paling agresif (*Same Day* jadwal 0 hari dan *First Class* jadwal 1 hari) justru memiliki rata-rata skor keterlambatan tertinggi (0,8647 dan 0,7931). Rekomendasi bisnis: penetapan batas waktu pesanan (*order cutoff time*) pukul 11:00 dan penambahan toleransi estimasi +1 hari pada destinasi transit kepulauan.

---

## 📁 Struktur Lengkap Repositori

```
.
├── Assignment-II-DataCo-Revisi-Bahasa.pdf    Dokumen PDF Resmi Final Project (Bab 1–7, 36 halaman, bertanda tangan)
├── Assignment-II-DataCo-Revisi-Bahasa.docx   Dokumen Word Resmi Final Project (Bab 1–7, terjustifikasi rapi)
├── Presentasi-Assignment-II-RafaelYudianto.pdf   Slide Presentasi Eksekutif (PDF)
├── Presentasi-Assignment-II-RafaelYudianto.pptx  Slide Presentasi Eksekutif (PPTX)
├── README.md                                 Dokumentasi proyek dan panduan eksekusi
│
├── dashboard/                                Direktori Utama Dashboard Visualisasi (Bab 7)
│   ├── index.html                            Antarmuka visual interaktif (HTML5, Tailwind, Plotly.js)
│   └── data.js                               Data masukan 8.043 pesanan uji & metrik graf bipartit
│
├── docs/                                     Salinan Mandiri Dashboard Visualisasi
│   ├── index.html                            Antarmuka visual mandiri
│   └── data.js                               Data masukan analitik mandiri
│
├── data/                                     Dataset Penelitian DataCo Smart Supply Chain
│   ├── raw/
│   │   ├── DataCoSupplyChainDataset.csv      Dataset mentah transaksi (180.519 baris, 53 kolom)
│   │   ├── DescriptionDataCoSupplyChain.csv  Kamus data resmi (52 baris)
│   │   └── tokenized_access_logs.csv         Data catatan kunjungan web / clickstream (469.977 baris)
│   └── clean/
│       ├── dataco_clean_items.csv            Dataset transaksi nonbatal bersih (172.765 baris, 50 kolom)
│       └── dataco_risk_scope.csv             Dataset agregasi tingkat pesanan (62.897 pesanan, 48 fitur)
│
├── eksekusi-final-lokal/                     Pipeline Eksekusi Lokal (Apache Spark 3.5.9 Local Mode)
│   ├── src/pipeline.py                       Skrip implementasi pipeline utama
│   ├── tests/test_pipeline.py                Unit test kontrak data dan transformasi fitur
│   ├── Assignment-II-DataCo-executed-local.ipynb  Jupyter Notebook eksekusi lokal lengkap
│   └── README.md                             Dokumentasi teknis eksekusi lokal
│
├── colab-final/                              Pipeline Eksekusi Google Colab (Spark 4.0.4)
│   ├── src/pipeline_colab.py                 Varian Colab dari pipeline analitik
│   ├── tests/test_pipeline.py                Unit test eksekusi Colab
│   └── README.md                             Dokumentasi teknis lingkungan Colab
│
├── implementasi-F4-F8/                       Modul Evaluasi dan Pemilihan Ambang Batas
│   ├── implementation.py                     Fungsi threshold selector, metrik PR/ROC, dan evaluator
│   ├── test_contract.py                      Unit test pemisahan temporal dan metrik evaluasi
│   └── README.md                             Dokumentasi teknis modul F4–F8
│
├── persiapan-teknis-colab/                   Verifikasi Kesiapan Teknis
│   └── runtime-evidence/src/spark_smoke.py  Skrip smoke test Apache Spark & HDFS
│
├── gambar_7_1_dashboard.png                  Tangkapan layar resolusi tinggi Gambar 7.1 pada laporan
├── gambar_7_2_insights.png                   Tangkapan layar resolusi tinggi Gambar 7.2 pada laporan
├── dashboard_full.png                        Tangkapan layar penuh antarmuka dashboard
└── extracted_signature.png                   Goresan tanda tangan resmi pada lembar kepatuhan AI
```

---

## ⚙️ Fitur dan Pemodelan (F4–F8)

- **Target Prediksi**: `Late_delivery_risk` (0 = tepat waktu, 1 = berisiko terlambat).
- **Kelompok Fitur Model**:
  - **F4**: *Days for shipment (scheduled)* — durasi janji pengiriman terjadwal.
  - **F5**: *Customer Segment* — segmen konsumen (Consumer, Corporate, Home Office).
  - **F6**: *Market* — kawasan pasar geografis (Europe, Pacific Asia, LATAM, dll.).
  - **F7**: *Category Id* (*multi-hot encoding*) — representasi biner multi-kategori belanja per pesanan.
  - **F8**: *Order Item Id Count* — total baris item pesanan unik.
- **Pemisahan Temporal (*Temporal Split*)**:
  - *Train*: `order_date` < 2017-07-01 (47.749 pesanan; 21.302 tepat waktu, 28.524 terlambat)
  - *Validation*: 2017-07-01 ≤ `order_date` < 2017-10-01 (7.105 pesanan; 2.140 tepat waktu, 2.888 terlambat)
  - *Test*: `order_date` ≥ 2017-10-01 (8.043 pesanan; 3.407 tepat waktu, 4.636 terlambat)

---

## 💻 Hasil Evaluasi Utama yang Dilaporkan

| Model | Average Precision (AP) | ROC-AUC | Catatan Performa |
| :--- | :---: | :---: | :--- |
| **Baseline (Prior)** | 0,5764 | 0,5000 | Garis dasar proporsi kelas mayoritas data uji |
| **Logistic Regression (scikit-learn)** | **0,7364** | **0,7198** | Regularisasi L2 ($C=1,0$, solver *lbfgs*) |
| **Logistic Regression (Spark MLlib)** | **0,7368** | **0,7206** | Regularisasi L2 (`regParam=0,1`, *standardization=False*) |

*Seluruh angka resmi berasal dari eksekusi final pada Google Colab VM (Python 3.13.16, Apache Spark 4.0.4).*
