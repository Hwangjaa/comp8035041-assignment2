# COMP8035041 — Assignment II: DataCo

Sumber kode dan dataset untuk tugas COMP8035041 Assignment II.

## Isi

- `PENGUMPULAN-COMP8035041-Assignment-II/` — paket pengumpulan final (laporan DOCX/PDF, paket artefak ZIP, README pengumpulan).
- `data/` — dataset:
  - `raw/DataCoSupplyChainDataset.csv` (91 MB) dan `raw/DescriptionDataCoSupplyChain.csv` dari Mendeley Data (sumber dan checksum di `data/source-manifest.json`).
  - `raw/tokenized_access_logs.csv` (91 MB).
  - `clean/dataco_clean_items.csv`, `clean/dataco_risk_scope.csv` — hasil pembersihan.
- `eksekusi-final-lokal/` — pipeline final yang dieksekusi lokal: `src/pipeline.py`, notebook `Assignment-II-DataCo-executed-local.ipynb`, tes, dan artefak `run-actual/` + `reproducibility-run/`.
- `colab-final/` — versi pipeline Colab: `src/pipeline_colab.py`, tes, keputusan metodologi, dan bukti eksekusi.
- `implementasi-F4-F8/` — implementasi fitur F4–F8 (`implementation.py`, `test_contract.py`).
- `analisis-lanjutan/` — skrip analisis (ekivalensi, keputusan, ablasion, graf, regresi) dan keluaran JSON/PNG.
- Sisa folder (`output-tahap-AB/`, `revisi-QA-20261020/`, `output-sunting-bahasa-20261022/`, `qa-high-quality/`, `persiapan-teknis-colab/`, `backup-*/`, dsb.) adalah kode audit, koreksi QA, dan riwayat versi.

## Kode inti

| Berkas | Peran |
|---|---|
| `eksekusi-final-lokal/src/pipeline.py` | Pipeline akhir (Spark/sklearn, fitur F1–F8, evaluasi) |
| `colab-final/src/pipeline_colab.py` | Varian pipeline untuk Colab GPU |
| `implementasi-F4-F8/implementation.py` | Implementasi fitur F4–F8 |
| `analisis-lanjutan/*.py` | Analisis lanjutan A–H (ekivalensi, ablasion, graf, regresi) |

Catatan: lingkungan (`.venv`) dan distribusi Spark/Hadoop tidak ikut di repo; versi yang diamati tercantum di `eksekusi-final-lokal/run-actual/requirements-observed.txt` dan `persiapan-teknis-colab/runtime-evidence/requirements-observed.txt`.
