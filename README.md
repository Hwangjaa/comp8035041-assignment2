# COMP8035041 Big Data Analytics — DataCo Smart Supply Chain Predictive Analytics & Interactive Dashboard

Repository ini berisi artefak lengkap untuk **Assignment II & Final Project** mata kuliah *COMP8035041 – Big Data Analytics* (BINUS Graduate Program, Magister Teknik Informatika) oleh **Rafael Yudianto (NIM: 2702752495)**. Proyek ini mencakup pemrosesan data berskala besar, pemodelan prediktif risiko keterlambatan pengiriman (*Late Delivery Risk*) menggunakan Apache Spark MLlib dan scikit-learn, analisis topologi jaringan belanja pelanggan (*Graph Analytics*), serta penyajian wawasan bisnis interaktif berbasis web (*Visualisasi Berupa Dashboard*).

---

## 🌐 Live Interactive Dashboard

Dashboard visualisasi analitik interaktif (Bab 7) dapat diakses langsung secara publik melalui GitHub Pages:

🔗 **[https://hwangjaa.github.io/comp8035041-assignment2/](https://hwangjaa.github.io/comp8035041-assignment2/)**

### Fitur Utama Dashboard:
1. **Interactive Scenario Controls**: Slider ambang batas keputusan risiko (*decision threshold* 0,40–0,85) dinamis dengan pemfilteran wilayah pasar (*Market*) dan moda pengiriman (*Shipping Mode*).
2. **KPI Scorecards**: Ringkasan volume pesanan uji (8.043 pesanan), jumlah antrean risiko kritis, metrik performa model (*Average Precision* 0,7364), dan skala jaringan graf (62.948 simpul).
3. **Insight 1 (Machine Learning)**: Histogram distribusi skor probabilitas risiko dengan garis potong dinamis, serta tabel interaktif *Live Dispatch Queue* untuk pemeringkatan pesanan darurat (*Top-K Alert* dengan presisi 78,9% pada kohort kritis).
4. **Insight 2 (Graph Analytics)**: Analisis *bipartite network* pesanan-kategori produk yang mengidentifikasi simpul penghubung (*network hubs*) dengan tingkat keterlambatan >57,6% (Cleats, Men's Footwear, Women's Apparel) untuk panduan penataan ulang slot rak gudang (*warehouse reslotting*).
5. **Insight 3 (Business & Operations Policy)**: Visualisasi paradoks operasional antara janji durasi pengiriman agresif (*Same Day* dan *First Class*) terhadap risiko keterlambatan riil, menjadi dasar kalibrasi batas waktu pesanan (*order cutoff time*) dan estimasi toleransi SLA.

---

## 📁 Struktur Repository

```
├── docs/                          Direktori hosting GitHub Pages (Live Interactive Dashboard)
│   ├── index.html                 Antarmuka mandiri (HTML5, Tailwind CSS, Plotly.js)
│   └── data.js                    Agregasi data masukan JSON (8.043 pesanan uji & metrik graf)
├── dashboard/                     Salinan lokal berkas dashboard interaktif
│   ├── index.html
│   └── data.js
├── data/                          Dataset DataCo Supply Chain
│   ├── raw/                       Dataset mentah (CSV)
│   └── clean/                     Dataset hasil preprocessing
├── eksekusi-final-lokal/          Pipeline eksekusi lokal (Spark local mode)
│   ├── src/pipeline.py            Implementasi utama
│   ├── tests/test_pipeline.py     Unit test kontrak fitur dan metode
│   └── Assignment-II-DataCo-executed-local.ipynb
├── colab-final/                   Pipeline eksekusi Google Colab (Spark 4.0.4)
│   ├── src/pipeline_colab.py      Varian Colab dari pipeline utama
│   └── tests/test_pipeline.py     Unit test Colab
├── implementasi-F4-F8/            Modul threshold selection dan evaluasi
│   ├── implementation.py          Fungsi pemilihan threshold dan evaluator
│   ├── test_contract.py           Unit test
│   └── README.md                  Dokumentasi F4-F8
├── persiapan-teknis-colab/        Smoke test Spark + HDFS
│   └── runtime-evidence/src/spark_smoke.py
├── Assignment-II-DataCo-Revisi-Bahasa.docx   Laporan Resmi Final Project (Bab 1–Bab 7)
├── Assignment-II-DataCo-Revisi-Bahasa.pdf    Dokumen PDF Resmi Final Project (38 halaman)
├── Presentasi-Assignment-II-RafaelYudianto.pptx  Slide Presentasi Eksekutif
└── Presentasi-Assignment-II-RafaelYudianto.pdf   Versi PDF Slide Presentasi
```

---

## ⚙️ Fitur dan Pemodelan (F4–F8)

- **Target Prediksi**: `Late_delivery_risk` (0 = tepat waktu, 1 = terlambat).
- **Kelompok Fitur**:
  - **F4**: *Days for shipment (scheduled)*
  - **F5**: *Customer Segment*
  - **F6**: *Market*
  - **F7**: *Category Id* (*multi-hot encoding*)
  - **F8**: *Order Item Id Count*
- **Pembagian Temporal (Temporal Split)**:
  - *Train*: `order_date` < 2017-07-01 (47.749 pesanan)
  - *Validation*: 2017-07-01 ≤ `order_date` < 2017-10-01 (7.105 pesanan)
  - *Test*: `order_date` ≥ 2017-10-01 (8.043 pesanan)

---

## 💻 Lingkungan Eksekusi

- **Eksekusi Lokal (`eksekusi-final-lokal/`)**:
  - Python 3.12.15, Apache Spark / PySpark 3.5.9, Java 17.0.20.1
  - Spark mode `local[2]`, `fs.defaultFS=file:///`
- **Eksekusi Final Google Colab (`colab-final/`)**:
  - Python 3.13.16, Apache Spark 4.0.4
  - Spark mode `local[2]`, penyimpanan `file:///` pada Google Colab VM
  - Seluruh angka evaluasi resmi pada laporan bersumber dari jalur ini (*Average Precision* = 0,7364, *ROC-AUC* = 0,7242).
