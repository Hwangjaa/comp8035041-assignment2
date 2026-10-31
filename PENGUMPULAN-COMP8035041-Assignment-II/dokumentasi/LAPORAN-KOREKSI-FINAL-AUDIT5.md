# Laporan koreksi final — Audit 5 Final Correction (putaran 2)

Basis: `Assignment-II-DataCo-Laporan-Final-Revisi-Audit5-Final-Correction.docx` (arsip, tetap utuh).
Hasil: `Assignment-II-DataCo-Laporan-Final-Revisi-Audit5-Final-Correction2.docx` + `.pdf` (33 halaman).
Paket bukti: `PAKET-ARTEFAK-AUDIT5.zip` (52 berkas + README + manifest SHA-256).

## Status checklist (9 butir)

| # | Butir | Prioritas | Status |
|---|---|---|---|
| 1 | Perbandingan baseline AP dan ROC-AUC | P0 | **Selesai** |
| 2 | Interpretasi median dan kalibrasi probabilitas | P0 | **Selesai** |
| 3 | Nomor halaman Tabel 6.1 dan 6.2 | P0 | **Selesai** (akar masalah: bookmark ganda) |
| 4 | Deklarasi AI dan tanda tangan | P0 | **Terbuka** (keputusan Rafael) |
| 5 | Folder artefak eksperimen ikut dikumpulkan | P0 | **Selesai** (ZIP + manifest) |
| 6 | Penggunaan `zero_division=0` | P1 | **Selesai** |
| 7 | Tabel 5.4 dan referensi Breiman | P1 | **Selesai** |
| 8 | Judul bagian 5.4 dan Tabel 5.8 | P1 | **Selesai untuk Tabel 5.8**; judul 5.4 tidak diubah (lihat catatan) |
| 9 | Visualisasi Gambar 6.1 | P2 | **Selesai** (margin putih dipangkas, konten ~20% lebih besar) |

## 1. P0 — AP dan ROC-AUC dibandingkan dengan baseline yang benar

Kalimat lama menyamakan keduanya: "AP 0,736 dan ROC-AUC 0,720 yang jauh di atas 0,576".

Kalimat baru: "Pada data test, kedua implementasi menghasilkan Average Precision sekitar 0,736–0,737, lebih tinggi daripada baseline 0,576, sedangkan ROC-AUC sekitar 0,720 dibandingkan baseline 0,500. Hasil tersebut menunjukkan kemampuan pemeringkatan risiko yang lebih baik daripada baseline, meskipun keputusan klasifikasi pada ambang yang dipakai belum mampu memisahkan kelas secara efektif."

Angka diambil dari Tabel 5.5 (baseline AP 0,576402; ROC-AUC 0,500000) dan bukti Colab.

## 2. P0 — kalibrasi tidak lagi disimpulkan dari median

Kalimat "median … yaitu di sekitar proporsi kelas positif" dan istilah "sebaran menyempit" dihapus. Penggantinya menyatakan bahwa median hanya menggambarkan posisi tengah distribusi; kalibrasi memerlukan calibration curve atau Brier score yang belum dilakukan; karena itu skor dipakai untuk pemeringkatan relatif dan tidak ditafsirkan sebagai probabilitas absolut terkalibrasi.

## 3. P0 — nomor halaman Tabel 6.1 dan 6.2 (akar masalah ditemukan)

Bukan cache field. Ada **bookmark ganda**: caption Tabel 5.7 dan Tabel 6.1 sama-sama memakai `lap_table_17`, dan Tabel 5.8 serta Tabel 6.2 sama-sama memakai `lap_table_18`. Word/LibreOffice menyelesaikan PAGEREF ke kemunculan pertama, sehingga entri Tabel 6.1 menampilkan halaman Tabel 5.7 (23) dan Tabel 6.2 menampilkan halaman Tabel 5.8 (24).

Perbaikan: bookmark caption baru diganti menjadi `lap_table_5_7` dan `lap_table_5_8`, dan instrText kedua entri daftar diarahkan ke nama tersebut. Setelah render ulang: **Tabel 6.1 = 26**, **Tabel 6.2 = 26**, Tabel 6.3 = 27, Tabel 6.4 = 29 — dan seluruh **60/60** baris daftar cocok dengan halaman aktual PDF.

## 4. P0 — deklarasi AI (masih terbuka)

Tidak diubah: Type 1–5 masih `Pending course-specific definition`, tanda tangan kosong, kontribusi AI 40%, dan daftar tool baru memuat Hermes Agent. Pencantuman ChatGPT, pemilihan Type, dan tanda tangan adalah keputusan pemilik laporan sesuai pedoman mata kuliah; saya tidak mengisinya secara fiktif.

## 5. P0 — paket artefak eksperimen

Dibuat `PAKET-ARTEFAK-AUDIT5.zip` (3,5 MB, 52 berkas):
- `analisis-lanjutan/` — `B_decision.json`, `C_ablation.json`, `F_main.json`, `G_ablation_schedule.json`, `H_graph.json`, larik `probs_*_{val,test}.npy`, `labels.json`, gambar, `SHA256SUMS.txt`.
- `eksekusi-final-lokal/run-actual/` — konfigurasi, `thresholds-frozen.json`, `feature-contract.json`, `environment.json`, `metrics.json/csv`, enam berkas `predictions-*.csv`, `split.csv`, `orders.csv`, `audit-orders.json`, statistik graf, parameter model, `convergence.json`, `execution.log`, model (`sklearn-model.joblib`, `spark-model/`).
- `colab-final/evidence-colab-final-2026-10-22.json`.
- `notebook/Assignment-II-DataCo-executed-local.ipynb`.
- `README-PAKET.md` + `SHA256SUMS-PAKET.txt` (checksum 52 berkas, diverifikasi ulang setelah ZIP dibuat: 0 ketidakcocokan).

## 6. P1 — `zero_division=0`

Klausul dipindahkan dari paragraf AP/ROC-AUC ke paragraf precision/recall/F1: "Untuk precision, recall, dan F1, perhitungan memakai parameter zero_division=0, yaitu kesepakatan bahwa hasil yang tidak terdefinisi akibat pembagian dengan nol ditetapkan menjadi nol."

## 7. P1 — Tabel 5.4 dan referensi Breiman

- Tabel 5.4: seluruh sel rata kiri, termasuk kolom terakhir (sebelumnya rata tengah sehingga jarak kata tidak rata).
- Daftar pustaka: 15 entri disetel rata kiri untuk menghilangkan spasi melar akibat perataan justify; entri Breiman dirapikan (tanpa tab/spasi berlebih) dan dirender ulang sebagai satu teks utuh.

## 8. P1 — judul Tabel 5.8 dan bagian 5.4

- Tabel 5.8 kini berjudul "Distribusi skor peluang: test (Colab dan eksekusi lokal) serta validation (eksekusi lokal 20 Oktober 2026)", sesuai isi tabel yang memuat baris test lokal. Entri daftar tabel disesuaikan.
- Judul bagian 5.4 ("Proses Pengembangan Model dengan dan tanpa Spark MLlib") **tidak diubah** karena isinya masih akurat dan tidak ditemukan cacat padanya. Bila yang dimaksud adalah frasa lain, perlu penunjukan spesifik.

## 9. P2 — Gambar 6.1

Citra asli `graph-subset.png` (2160×1440) memiliki margin putih lebar. Margin dipangkas ke kotak konten (menjadi 1798×1322, 83,2% lebar asli), lalu citra diganti di dalam dokumen pada lebar 16,0 cm dengan rasio tetap (16,00 × 11,76 cm). Efeknya konten graf tampil sekitar 20% lebih besar pada lebar halaman yang sama; isi graf tidak berubah (210 node, 495 edge). Berkas hasil pangkas disimpan sebagai `analisis-lanjutan/graph-subset-crop.png` dan ikut di dalam paket artefak.

## 10. Regression test akhir

| Pemeriksaan | Hasil |
|---|---|
| Halaman / paragraf / tabel | 33 / 267 / 25 |
| Baris daftar ber-nomor cocok dengan halaman aktual | **60/60** |
| "Reference source not found" | **0** |
| Typo `,,` | 0 |
| Angka kunci utuh (180.519 · 62.897 · 8.043 · 0,736424 · 0,736851 · 0,719782 · 0,576402 · 0,8066 · 0,8740 · 0,8526 · 62.948 · 152.676 · 87.551 · 0,5731 · 48 dimensi) | utuh di DOCX dan PDF |
| Halaman dengan < 400 karakter | hanya DAFTAR GAMBAR (halaman 4) |
| Bookmark ganda | 0 |

## 11. Yang tetap terbuka

1. Deklarasi AI: Type 1–5, tanda tangan, kontribusi AI, pencantuman ChatGPT.
2. Versi scikit-learn/NetworkX/NumPy/pandas pada eksekusi Colab tetap tidak tercatat (tidak ada artefak yang memuatnya).
3. Dua paragraf > 1.500 karakter (Bab 5.1 UNKNOWN 1.698; Bab 6.2 1.623) tidak diubah karena tidak termasuk butir audit ini.


## 12. Putaran 3 — audit atas PDF `Assignment-II-DataCo-Laporan-Final-Revisi-Audit5-Final(1).pdf`

Audit terakhir memeriksa PDF **Audit5-Final (32 halaman)**, bukan `Correction2` (33 halaman). Karena itu sebagian besar butirnya sudah berstatus beres sebelum audit itu ditulis; berikut pemetaannya.

| Butir audit | Kondisi di Correction2 |
|---|---|
| AP 0,736 / ROC-AUC 0,720 "jauh di atas 0,576" | Kalimat itu sudah tidak ada; paragraf diganti dengan angka baseline per metrik (AP 0,576402; ROC-AUC 0,500000) dan nilai scikit-learn/Spark (0,736424/0,736851; 0,719782/0,720601) pada putaran ini |
| Istilah "sebaran sempit" | Sudah dihapus; kini hanya menyebut rentang 0,30–0,94 dan median 0,42–0,45 |
| Median disamakan dengan prevalensi | Sudah tidak; paragraf menyatakan median **di bawah** 0,5764 dan median saja tidak menentukan kalibrasi |
| Provenance Colab vs lokal tidak konsisten | Sudah dipisah: Tabel 5.5/5.6 = Colab; Tabel 5.8 memakai kolom Sumber; paragraf penyebab semua-positif memakai skor minimum **Colab** 0,353144 / 0,447808 |
| `zero_division=0` setelah AP/ROC-AUC | Sudah dipindah ke paragraf precision/recall/F1 |
| Typo `(0,5764),,` | Sudah dihapus |
| Tabel 6.1 / 6.2 di daftar | Sudah benar: keduanya 26 (bukan 23/24) setelah bookmark ganda diperbaiki |
| Entri Tabel 5.4 tanpa titik pemimpin | Sudah memakai tab dan titik pengisi |
| Klaim "model berguna" (Bab 7) | Sudah diganti kalimat potensi retrospektif + syarat pengujian prospektif |
| Referensi Breiman berspasi berlebih | Sudah dirapikan; seluruh pustaka rata kiri |
| Gambar 6.1 kecil dan pucat | Margin dipangkas, ukuran 16,00 × 11,76 cm, kontras dinaikkan 1,35× dan ketajaman 1,15× pada putaran ini |
| Deklarasi AI | **Tetap terbuka** — keputusan Rafael |

Perubahan yang benar-benar baru pada putaran ini: angka AP/ROC-AUC ditulis eksplisit per model, provenance Tabel 5.8 ditegaskan di awal paragraf (bukan di akhir), dan kontras Gambar 6.1 dinaikkan.

Verifikasi setelah perubahan: 33 halaman · 267 paragraf · 25 tabel · 60/60 baris daftar cocok · 0 "Reference source not found" · angka kunci utuh.
