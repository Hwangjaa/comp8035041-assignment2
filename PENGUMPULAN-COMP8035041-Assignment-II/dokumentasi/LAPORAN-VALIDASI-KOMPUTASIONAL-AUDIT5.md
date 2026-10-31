# Laporan validasi komputasional — Audit 5

Dokumen yang divalidasi: `Assignment-II-DataCo-Laporan-Final-Revisi-Audit5-Final.docx` (32 halaman, 263 paragraf, 25 tabel, 15 entri pustaka).
Tanggal validasi: 31 Oktober 2026. Validasi dilakukan **sebelum** DOCX diubah, dan diulang setelah perubahan.

## 1. Hierarki sumber yang dipakai

| Tingkat | Sumber | Lokasi |
|---|---|---|
| 1 | Data mentah | `data/raw/DataCoSupplyChainDataset.csv` (95.910.149 byte, SHA-256 `fa6d022e…80aa6`), `DescriptionDataCoSupplyChain.csv` |
| 2 | Data olahan | `data/clean/dataco_clean_items.csv`, `dataco_risk_scope.csv`, `eksekusi-final-lokal/run-actual/orders.csv` (62.897 baris) |
| 3 | Kode/konfigurasi | `run-actual/config.json`, `thresholds-frozen.json`, `feature-contract.json`, `environment.json` |
| 4 | Artefak prediksi/metrik | `predictions-{validation,test}-{baseline,sklearn_lr,spark_lr}.csv`, `metrics.json`, `graph-*.csv`, `graph-summary.json` |
| 5 | Bukti eksekusi | `colab-final/evidence-colab-final-2026-10-22.json`, `run-actual/execution.log`, `SHA256SUMS.txt` |
| 6 | Dokumen laporan | DOCX Audit 4 (basis) dan Audit 5 (hasil revisi) |

## 2. Rekalkulasi metrik dari berkas prediksi

Dihitung ulang dari CSV per pesanan (bukan dibaca dari laporan): confusion matrix, precision, recall, binary F1, average precision (aturan step, setara `average_precision_score`), dan ROC-AUC (metode peringkat dengan koreksi ties).

| Model | Bagian | Ambang | AP hitung ulang | AP `metrics.json` | ROC-AUC hitung ulang | ROC-AUC `metrics.json` |
|---|---|---|---|---|---|---|
| baseline | validation | 0,572472 | 0,574383452665 | 0,574383452665 | 0,500000000000 | 0,500000000000 |
| baseline | test | 0,572472 | 0,576401840109 | 0,576401840109 | 0,500000000000 | 0,500000000000 |
| sklearn_lr | validation | 0,307476 | 0,744400470730 | 0,744400470730 | 0,719214458151 | 0,719214458151 |
| sklearn_lr | test | 0,307476 | 0,736424322835 | 0,736424322835 | 0,719781736480 | 0,719781736480 |
| spark_lr | validation | 0,446602 | 0,744406764619 | 0,744406764619 | 0,719908758770 | 0,719908758770 |
| spark_lr | test | 0,446602 | 0,736850734516 | 0,736850734516 | 0,720601054065 | 0,720601054065 |

Confusion matrix hasil hitung ulang identik dengan `metrics.json` untuk keenam kombinasi, termasuk TN=2 pada Spark/validation dan TN=0 pada seluruh baris test.

Angka laporan (Tabel 5.5 dan 5.6) dibandingkan dengan `evidence-colab-final-2026-10-22.json`: **selisih 0,0** pada AP dan ROC-AUC sampai 6 desimal untuk kelima pasangan yang tersedia.

## 3. Replikasi pengujian top-k

Aturan yang terbukti dari data: cutoff = kuantil `1 − k` dari skor test, seleksi memakai `skor ≥ cutoff` (seluruh ties ikut).

| k | Cutoff (sklearn) | Terpilih | TP | Precision | Lift |
|---|---|---|---|---|---|
| 10% | 0,8439506993 | 1.091 | 880 | 0,806599 | 1,3994 |
| 20% | 0,8429472477 | 1.674 | 1.463 | 0,873955 | 1,5162 |
| 30% | 0,7339822687 | 2.496 | 2.128 | 0,852564 | 1,4791 |

Hasil replikasi identik dengan `B_decision.json` sampai 4 desimal pada ketiga cutoff. Implementasi Spark: 1.088 (TP 877, precision 0,8061), 1.671 (TP 1.460, precision 0,8737), 2.488 (TP 2.123, precision 0,8533).

## 4. Distribusi skor terhadap ambang beku

| Bagian | n | Minimum | Median | Maksimum | Skor ≥ ambang |
|---|---|---|---|---|---|
| sklearn validation | 5.028 | 0,307476 | 0,426947 | 0,935811 | 5.028 |
| sklearn test | 8.043 | 0,353159 | 0,420485 | 0,914649 | 8.043 |
| Spark validation | 5.028 | 0,446311 | 0,453239 | 0,865781 | 5.026 |
| Spark test | 8.043 | 0,447789 | 0,453721 | 0,865100 | 8.043 |

Temuan: ambang scikit-learn **sama persis** dengan skor validation minimum (0,307476), dan skor test minimum (0,353159) lebih besar daripada ambang tersebut. Karena itu keputusan semua-positif pada test adalah konsekuensi mekanis dari aturan ambang, bukan kesalahan implementasi, dan bukan akibat pemilihan ambang dari data test.

## 5. UNKNOWN dan kategori baru

| Partisi | Pesanan | Memuat ≥1 kategori baru | Persentase |
|---|---|---|---|
| Training | 49.826 | 0 | 0,00% |
| Validation | 5.028 | 54 | 1,07% |
| Test | 8.043 | 7.972 | 99,12% |

- 19 kategori baru: **4 dan 59–76**; 32 kategori ada di training; total 51.
- 7.964 dari 7.972 pesanan test hanya memuat kategori baru.
- Skor rata-rata test: 0,5731 (memuat kategori baru, n=7.972, tingkat terlambat 0,5773) vs 0,5247 (tanpa kategori baru, n=71, tingkat terlambat 0,4789).

## 6. Rumus toleransi 0,5 hari

Dihitung langsung dari 180.519 baris data mentah: Δ = (shipping date − order date) dalam hari; nilai **Δ − Days for shipping (real)** hanya mengambil tiga nilai.

| Residu | Baris |
|---|---|
| 0 hari | 170.782 |
| +0,5 hari | 5.080 |
| −0,5 hari | 4.657 |
| Total | 180.519 |

Tidak ada baris dengan residu di luar ±0,5 hari. Kalimat lama "lebih besar 0,5 hari / lebih kecil 0,5 hari" ambigu (bisa dibaca sebagai ambang, bukan tanda), sehingga dokumen direvisi memakai notasi bertanda.

## 7. Angka graf

| Pemeriksaan | Hasil hitung | Nilai dokumen |
|---|---|---|
| Node | 62.948 | 62.948 |
| Node pesanan | 62.897 | 62.897 |
| Node kategori | 51 | 51 |
| Edge | 152.676 | 152.676 |
| Komponen terhubung | 19 | 19 |
| Komponen terbesar (node/pesanan/kategori/edge) | 54.966 / 54.933 / 33 / 144.712 | sama |
| Pasangan pesanan–kategori | 152.676 | 152.676 |
| Total pesanan terlambat per baris kategori | 87.551 | 87.551 |
| Tingkat keterlambatan seluruh pesanan | 36.048 / 62.897 = 0,573127 → 0,5731 | 0,5731 |
| Rate terendah | kategori 30 = 0,496324 | 0,4963 |
| Rate tertinggi | kategori 34 = 0,688525 (61 pesanan) | 0,6885 |
| Degree tertinggi | 17 = 19.534 | 19.534 |

Sepuluh nilai degree teratas pada Tabel 6.2 cocok seluruhnya dengan `graph-category-degree.csv`.

## 8. Kohort dan checksum

- `audit-orders.json`: 180.519 baris, 65.752 pesanan, 7.754 item batal, 2.855 pesanan batal, 172.765 item, 62.897 pesanan, 0 konflik.
- `DataCoSupplyChainDataset.csv`: ukuran dan SHA-256 sama dengan yang tercatat pada bukti eksekusi Colab.
- `SHA256SUMS.txt` sebelum revisi: 7 entri, **2 entri tidak cocok** (`…High-Quality.docx` dan `.pdf`, keduanya berkas laporan versi lama) dan 5 entri artefak cocok. Tindakan: dua entri laporan dikeluarkan dari manifest, sehingga manifest hanya memuat artefak eksperimen (5 entri, semuanya terverifikasi).
- `run-actual/environment.json` (eksekusi lokal 20 Okt): Python 3.12.15, pandas 3.0.6, NumPy 2.5.4, scikit-learn 1.9.1, SciPy 1.18.1, PySpark 3.5.9, NetworkX 3.7, matplotlib 3.11.2, Java 17.0.20.1, macOS 27.0.1, `OMP/OPENBLAS/MKL_NUM_THREADS=2`.

## 9. Konflik sumber yang ditemukan (dicatat, tidak ditutupi)

1. **`B_decision.json` vs bukti eksekusi Colab.** `B_decision.json` mencatat AP Spark test 0,7368441; bukti eksekusi mencatat 0,7368507 (selisih 6,6×10⁻⁶). Laporan memakai 0,736851, yaitu **bukti eksekusi**. Tindakan: angka laporan dipertahankan; tidak ada perubahan.
2. **Larik probabilitas pada `analisis-lanjutan/` bukan eksekusi final.** Untuk test, satu baris `probs_sklearn_test.npy` cocok tepat dengan AP sklearn (selisih 0,0), tetapi larik validation tidak mereproduksi AP validation bukti eksekusi (selisih 2×10⁻⁵ sampai 9,9×10⁻⁴). Karena itu distribusi skor yang dilaporkan pada Tabel 5.8 diambil dari **artefak eksekusi lokal** yang lengkap dan dapat direproduksi, bukan dari larik tersebut.
3. **Ambang lokal vs Colab.** Lokal: 0,307476 / 0,446602. Colab: 0,307694 / 0,446602. Selisih ini sudah diakui pada dokumen (Bab 5) dan tidak diubah; laporan tetap memakai angka Colab untuk hasil utama dan menyajikan distribusi lokal sebagai pemeriksaan reproduktibilitas.
4. **Versi library Colab.** Bukti eksekusi hanya merekam Python 3.13.16 dan Spark 4.0.4. Versi scikit-learn, NetworkX, NumPy, dan pandas pada eksekusi Colab **tidak tercatat**; dokumen sekarang menyatakan hal itu secara eksplisit, bukan menggantinya dengan versi eksekusi lokal.

## 10. Yang tidak dapat diverifikasi dari artefak

- Prediksi per pesanan untuk eksekusi Colab tidak tersimpan sebagai CSV; hanya larik probabilitas pada `analisis-lanjutan/` (dengan keterbatasan pada butir 9.2).
- Tidak ada benchmark waktu, memori, throughput, atau multi-node; klaim skalabilitas terdistribusi tidak dapat diuji.
- Validasi prospektif dan ketersediaan fitur *as-of* tidak dapat diuji dari potret data historis.
- Definisi Assignment Type 1–5, persentase kontribusi AI, dan tanda tangan adalah keputusan pemilik laporan; tidak diisi.
