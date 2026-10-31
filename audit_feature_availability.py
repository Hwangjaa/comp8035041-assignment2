"""Audit baca-saja CSV lokal; tidak membangun matriks fitur atau model."""
import csv
import hashlib
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'audit-gate-unit-features'
OUT.mkdir(exist_ok=True)
RAW = ROOT / 'data/raw/DataCoSupplyChainDataset.csv'
DICT = ROOT / 'data/raw/DescriptionDataCoSupplyChain.csv'
MAPPING = {'order date (DateOrders)': 'order_date', 'shipping date (DateOrders)': 'shipping_date', 'Days for shipping (real)': 'dispatch_real_days', 'Days for shipment (scheduled)': 'dispatch_scheduled_days', 'Late_delivery_risk': 'is_late'}
# Kategori di bawah merupakan penilaian audit, bukan daftar fitur final.
NOTES = {}
def note(cols, timing, changes, risk, status):
    for col in cols:
        assert col not in NOTES
        NOTES[col] = dict(timing_assessment=timing, possible_later_change=changes, leakage_risk=risk, audit_status=status)

note(['Type'], 'Kamus: jenis transaksi. Dugaan diketahui saat pembayaran; kapan nilai snapshot ditetapkan tidak tersedia.', 'Metode/rekonsiliasi pembayaran dapat berubah; riwayat tidak tersedia.', 'Sedang: snapshot pembayaran mungkin sesudah cutoff.', 'BELUM TERVERIFIKASI TEMPORAL')
note(['Days for shipping (real)', 'shipping date (DateOrders)'], 'Kamus: durasi aktual / waktu pengiriman; informasi hasil, bukan bukti waktu handover.', 'Terisi/diperbarui ketika kejadian pengiriman diketahui.', 'Langsung: informasi sesudah cutoff sebelum pengiriman.', 'DILARANG SEBAGAI FITUR')
note(['Days for shipment (scheduled)'], 'Kamus: hari pengiriman terjadwal. Kandidat pra-pengiriman hanya bila jadwal asli tersedia pada cutoff.', 'Janji/jadwal mungkin direvisi; tidak ada versi awal.', 'Sedang-tinggi: jadwal akhir dapat memuat revisi pascapemesanan.', 'KANDIDAT BERSYARAT; BELUM TERVERIFIKASI TEMPORAL')
note(['Benefit per order', 'Order Profit Per Order', 'Order Item Profit Ratio'], 'Kamus menyebut earnings/profit/rasio profit; tidak menjelaskan kapan diakui atau komponen biaya.', 'Biaya aktual, refund, atau penyesuaian mungkin mengubah profit; ini kemungkinan, bukan fakta dataset.', 'Tinggi/tidak pasti: berpotensi memakai biaya atau hasil akhir.', 'TAHAN; PERLU LINEAGE DAN WAKTU PENGAKUAN')
note(['Sales per customer'], 'Kamus menyebut total penjualan pelanggan tetapi tidak menjelaskan jendela agregasi atau cutoff.', 'Jika agregat pelanggan, transaksi masa depan dapat mengubahnya; kesetaraan numerik diperiksa terpisah.', 'Tinggi/tidak pasti: agregat masa depan atau alias nilai item; semantik belum tuntas.', 'TAHAN; PERLU LINEAGE AGREGASI')
note(['Delivery Status'], 'Kamus: status termasuk late/on time/canceled; snapshot hasil.', 'Dapat berubah sepanjang siklus; timestamp perubahan tidak ada.', 'Langsung: mengungkap outcome. Hanya untuk cakupan/audit.', 'DILARANG SEBAGAI FITUR; CAKUPAN RETROSPEKTIF')
note(['Late_delivery_risk'], 'Kamus: indikator sending late 1 / not late 0; label historis.', 'Outcome diketahui setelah proses relevan; versi label tidak tersedia.', 'Langsung bila dipakai sebagai masukan.', 'TARGET SAJA, BUKAN FITUR')
note(['Category Id', 'Category Name', 'Department Id', 'Department Name', 'Product Category Id', 'Product Name'], 'Kamus: identitas/nama kategori, departemen, atau produk. Kandidat dari master saat pesanan, tetapi snapshot historis tidak terbukti.', 'Klasifikasi/nama master dapat direvisi; as-of join tidak tersedia.', 'Sedang: master akhir dapat berbeda dari nilai pada cutoff; bukan otomatis leakage.', 'KANDIDAT BERSYARAT; BELUM TERVERIFIKASI TEMPORAL')
note(['Customer City', 'Customer Country', 'Customer State', 'Customer Street', 'Customer Zipcode'], 'Kamus mencampurkan lokasi pembelian/pelanggan/toko. Belum terbukti alamat pengiriman atau lokasi gudang.', 'Profil/alamat atau master lokasi dapat berubah; tidak ada riwayat.', 'Sedang: snapshot profil akhir; privasi dan salah interpretasi lokasi.', 'TAHAN SEMANTIK/AS-OF; ALAMAT DETAIL PERLU MINIMISASI')
note(['Customer Email', 'Customer Password'], 'Kamus: email / masked customer key. Dihapus dalam Assignment I; waktu snapshot tidak terbukti.', 'Profil/kredensial dapat berubah; tidak diaudit sebagai fitur.', 'Privasi/keamanan tinggi; penghapusan bukan pembuktian leakage.', 'SUDAH DIHAPUS DALAM ASSIGNMENT I; JANGAN PULIHKAN')
note(['Customer Fname', 'Customer Lname'], 'Kamus: nama pelanggan; waktu snapshot tidak tersedia.', 'Nama/profil dapat berubah.', 'Privasi dan memorisasi identitas; bukan otomatis target leakage.', 'TAHAN; BUKAN KANDIDAT DEFAULT')
note(['Customer Id', 'Order Customer Id'], 'Kamus: Customer ID / customer order code; kesetaraan empiris diperiksa, bukan bukti waktu penerbitan.', 'Identitas biasanya stabil sebagai asumsi; mekanisme penerbitan/migrasi tidak didokumentasikan.', 'Memorisasi pelanggan; pelanggan berulang lintas split bukan otomatis leakage, tergantung tujuan generalisasi.', 'KUNCI AUDIT/RELASI; FITUR BELUM DISETUJUI')
note(['Customer Segment'], 'Kamus: Consumer/Corporate/Home Office. Dugaan atribut profil pra-pengiriman; waktu penetapan tidak ada.', 'Segmen dapat diperbarui; tidak ada historisasi.', 'Sedang: segmentasi masa depan berpotensi masuk snapshot.', 'KANDIDAT BERSYARAT; BELUM TERVERIFIKASI TEMPORAL')
note(['Latitude', 'Longitude'], 'Kamus menyebut lokasi toko, bukan koordinat tujuan/gudang. Perlu verifikasi entitas koordinat.', 'Lokasi/master bisa berubah atau dikoreksi; tidak ada waktu efektif.', 'Sedang: salah entitas lokasi, snapshot akhir, presisi lokasi sensitif.', 'TAHAN SEMANTIK LOKASI DAN AS-OF')
note(['Market', 'Order City', 'Order Country', 'Order Region', 'Order State'], 'Kamus: wilayah/tujuan pengiriman. Kandidat jika merupakan tujuan yang sudah disepakati pada cutoff.', 'Tujuan atau klasifikasi wilayah bisa direvisi; tidak ada riwayat.', 'Sedang: tujuan akhir dapat berbeda dari tujuan pada cutoff.', 'KANDIDAT BERSYARAT; BELUM TERVERIFIKASI TEMPORAL')
note(['Order Zipcode'], 'Ada pada header transaksi tetapi TIDAK ADA pada kamus 52 baris. Dugaan kode pos pesanan belum terverifikasi.', 'Kemungkinan revisi alamat; dugaan belum dibuktikan.', 'Tidak pasti: semantik dan temporal belum terverifikasi; detail lokasi.', 'TAHAN; DEFINISI SUMBER TIDAK TERSEDIA')
note(['order date (DateOrders)'], 'Kamus: tanggal pesanan dibuat; satu-satunya penanda awal pesanan yang didokumentasikan, bukan timestamp kesiapan pengiriman.', 'Koreksi/backfill tidak dapat dikesampingkan tanpa log.', 'Rendah-sedang bersyarat: tanggal awal tidak mengungkap outcome, tetapi turunan/pembagian waktu perlu audit.', 'KANDIDAT BERSYARAT; TIDAK MEMBUKTIKAN CUTOFF OPERASIONAL')
note(['Order Id'], 'Kamus: kode pesanan; mengelompokkan item. Timestamp penerbitan tidak didokumentasikan.', 'Stabil dalam snapshot; tidak membuktikan stabilitas sistem sumber.', 'Dapat menjadi proksi waktu/urutan atau memorisasi; wajib dipertahankan sebagai kunci split/audit.', 'KUNCI KELOMPOK/TINDAKAN; BUKAN FITUR DEFAULT')
note(['Order Item Id'], 'Kamus: kode item; keunikan diperiksa pada snapshot.', 'ID dapat terbit ketika item ditambahkan; waktu tepat tidak ada.', 'Memorisasi/proksi urutan; bukan otomatis informasi prediktif sah.', 'KUNCI ITEM; BUKAN FITUR DEFAULT')
note(['Order Item Cardprod Id', 'Product Card Id'], 'Kamus: kode produk (Cardprod disebut kode dari RFID). Tidak membuktikan peristiwa scan atau waktu penerbitan.', 'Master/identitas produk dapat dikoreksi; tidak ada as-of mapping.', 'Memorisasi produk dan ketidakpastian waktu scan; ID produk bukan bukti dispatch.', 'KUNCI RELASI/KANDIDAT BERSYARAT; BELUM DISETUJUI')
note(['Order Item Discount', 'Order Item Discount Rate', 'Order Item Product Price', 'Order Item Quantity', 'Sales', 'Order Item Total'], 'Kamus: diskon, harga, kuantitas, nilai penjualan/total. Dugaan detail transaksi tersedia saat pesanan; basis dan waktu finalisasi tidak didokumentasikan.', 'Perubahan item, diskon, refund atau koreksi mungkin terjadi; tidak ada versi awal.', 'Sedang: angka final mungkin berbeda dari angka pada cutoff; agregasi dapat double-count.', 'KANDIDAT BERSYARAT; PERLU LINEAGE DAN NILAI AS-OF')
note(['Order Status'], 'Kamus: COMPLETE/PENDING/CLOSED/PENDING_PAYMENT/CANCELED/PROCESSING/SUSPECTED_FRAUD/ON_HOLD/PAYMENT_REVIEW. Waktu snapshot tidak ada.', 'Status bersifat lifecycle; tidak ada jejak status pada cutoff.', 'Tinggi: campuran informasi proses/hasil, dapat mengungkap masa depan.', 'TAHAN; STATUS AKHIR DILARANG; TIDAK BOLEH ASUMSI AMAN')
note(['Product Description'], 'Kamus: deskripsi produk. Assignment I menghapus; kosong seluruhnya perlu diperiksa ulang.', 'Master deskripsi dapat direvisi.', 'Tidak ada informasi terisi pada snapshot bila audit cocok; bukan pembuktian temporal.', 'SUDAH DIHAPUS DALAM ASSIGNMENT I; JANGAN PULIHKAN')
note(['Product Image'], 'Header nama image; kamus justru menyebut link visit/purchase produk. Semantik ambigu; dihapus Assignment I.', 'URL/master dapat berubah.', 'Tidak pasti; jangan menganggap URL sebagai fitur kunjungan tervalidasi.', 'SUDAH DIHAPUS DALAM ASSIGNMENT I; JANGAN PULIHKAN')
note(['Product Price'], 'Kamus: harga produk. Belum jelas harga master terkini atau harga saat transaksi; bandingkan harga item secara empiris.', 'Harga master dapat berubah; tidak ada waktu efektif.', 'Sedang: harga master akhir dapat membawa informasi sesudah pesanan.', 'KANDIDAT BERSYARAT; BEDAKAN HARGA MASTER DAN TRANSAKSI')
note(['Product Status'], 'Kamus: stock 1 unavailable / 0 available. Tidak menjelaskan apakah stok saat order atau saat ekspor.', 'Stok berubah sepanjang waktu; snapshot tanpa timestamp.', 'Tinggi/tidak pasti: stok akhir bukan stok saat cutoff.', 'TAHAN; PERLU SNAPSHOT STOK HISTORIS')
note(['Shipping Mode'], 'Kamus: Standard/First/Second Class/Same Day. Kandidat layanan yang dipilih sebelum pengiriman; waktu finalisasi tidak ada.', 'Moda layanan bisa diubah/di-upgrade; riwayat tidak ada.', 'Sedang: moda akhir mungkin merupakan respons atas keterlambatan.', 'KANDIDAT BERSYARAT; BELUM TERVERIFIKASI TEMPORAL')

with DICT.open(encoding='utf-8-sig', newline='') as f:
    definitions = {r['FIELDS'].strip().lower(): r['DESCRIPTION'].strip() for r in csv.DictReader(f)}
with RAW.open(encoding='latin1', newline='') as f:
    reader = csv.DictReader(f)
    columns = reader.fieldnames
    assert set(columns) == set(NOTES), (set(columns)-set(NOTES), set(NOTES)-set(columns))
    n = ns = 0
    blanks = Counter(); unique = {c:set() for c in columns}
    first = {}; variation = {c:set() for c in columns}; sizes = Counter(); labels = Counter(); item_ids = set()
    all_first = {}; all_bad = set(); canceled_by_order = {}; mixed_cancel = set()
    pairs = [('Benefit per order','Order Profit Per Order'), ('Sales per customer','Order Item Total'), ('Customer Id','Order Customer Id'), ('Order Item Cardprod Id','Product Card Id'), ('Category Id','Product Category Id'), ('Product Price','Order Item Product Price')]
    eq = Counter()
    for r in reader:
        n += 1
        for c in columns:
            if not r[c].strip(): blanks[c] += 1
        oid = r['Order Id']; canceled = r['Delivery Status'] == 'Shipping canceled'
        sig = tuple(r[c] for c in ['Late_delivery_risk','order date (DateOrders)','shipping date (DateOrders)'])
        if oid not in all_first: all_first[oid] = sig
        elif all_first[oid] != sig: all_bad.add(oid)
        if oid in canceled_by_order and canceled_by_order[oid] != canceled: mixed_cancel.add(oid)
        canceled_by_order[oid] = canceled
        if canceled: continue
        ns += 1; sizes[oid] += 1; labels[r['Late_delivery_risk']] += 1; item_ids.add(r['Order Item Id'])
        for a,b in pairs:
            if r[a] == r[b]: eq[a+' == '+b] += 1
        if oid not in first: first[oid] = r
        for c in columns:
            unique[c].add(r[c])
            if first[oid][c] != r[c]: variation[c].add(oid)

manifest = {p.name: {'bytes':p.stat().st_size, 'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in [RAW,DICT]}
old = json.loads((ROOT/'data/audit-results.json').read_text())
for item in old['files']:
    if item['file'] in manifest:
        assert manifest[item['file']]['sha256'] == item['sha256']
order_labels = Counter(r['Late_delivery_risk'] for r in first.values())
summary = dict(execution_scope='Python stdlib lokal, audit baca-saja; bukan Colab/Spark/HDFS/model', source_manifest=manifest, source_hash_matches_historical_manifest=True, raw_rows=n, source_columns=len(columns), dictionary_rows=len(definitions), scope_rows=ns, scope_orders=len(first), unique_scope_item_ids=len(item_ids), scope_item_labels=dict(labels), scope_order_labels=dict(order_labels), scope_items_per_order_mean=ns/len(first), scope_order_size_distribution=dict(sorted(Counter(sizes.values()).items())), scope_multi_item_orders=sum(v>1 for v in sizes.values()), raw_orders=len(all_first), raw_orders_inconsistent_label_or_timestamps=len(all_bad), mixed_canceled_and_noncanceled_orders=len(mixed_cancel), scope_columns_varying_within_order={c:len(variation[c]) for c in columns}, scope_exact_string_equality_counts=dict(eq), note='Kesetaraan dalam snapshot bukan bukti lineage, asal informasi, atau waktu ketersediaan.')
(OUT/'audit-results.json').write_text(json.dumps(summary,indent=2,ensure_ascii=False))
records = []
for i,c in enumerate(columns,1):
    rec = dict(number=i, source_name=c, mapped_name=MAPPING.get(c,c), source_definition=definitions.get(c.lower(),'TIDAK ADA DALAM KAMUS'), temporal_evidence='Tidak ada timestamp pencatatan/pembaruan per atribut atau riwayat versi; definisi kamus bukan bukti nilai tersedia pada cutoff.', **NOTES[c], raw_blank_rows=blanks[c], scope_unique_values=len(unique[c]), scope_orders_with_multiple_values=len(variation[c]))
    records.append(rec)
# late_days dicatat terpisah; bukan kolom sumber ke-54.
records.append(dict(number=54, source_name='(turunan audit)', mapped_name='late_days', source_definition='Days for shipping (real) - Days for shipment (scheduled); audit_data.py baris 36', temporal_evidence='Lineage memakai durasi aktual sesudah cutoff.', timing_assessment='Informasi hasil pengiriman.', possible_later_change='Mengikuti perubahan durasi sumber.', leakage_risk='Langsung: turunan outcome; jangan dipakai sebagai fitur.', audit_status='DILARANG SEBAGAI FITUR; AUDIT SAJA', raw_blank_rows='', scope_unique_values='', scope_orders_with_multiple_values=''))
with (OUT/'inventaris-kolom.csv').open('w',encoding='utf-8-sig',newline='') as f:
    writer=csv.DictWriter(f,fieldnames=list(records[0]));writer.writeheader();writer.writerows(records)
with (OUT/'inventaris-kolom.txt').open('w',encoding='utf-8') as f:
    f.write('INVENTARIS 53 KOLOM SUMBER + 1 TURUNAN AUDIT\nBukan daftar fitur final. Tidak ada kolom kandidat yang disahkan aman secara operasional.\nDefinisi kamus dikutip apa adanya; penilaian kemungkinan perubahan adalah hipotesis audit, bukan kejadian yang terbukti.\nStatistik dihitung ulang dari CSV lokal; tidak menampilkan nilai identitas pribadi.\n\n')
    for r in records:
        f.write(f"{r['number']}. {r['source_name']} -> {r['mapped_name']}\n")
        for k,label in [('source_definition','Bukti kamus/lineage'),('timing_assessment','Waktu/ketersediaan'),('possible_later_change','Potensi perubahan (belum terbukti)'),('leakage_risk','Risiko'),('audit_status','Status')]: f.write(f'   {label}: {r[k]}\n')
        f.write(f"   Bukti snapshot: kosong mentah={r['raw_blank_rows']}; nilai unik cakupan={r['scope_unique_values']}; pesanan dengan >1 nilai={r['scope_orders_with_multiple_values']}.\n\n")
assert len(records)==54 and len({r['source_name'] for r in records[:53]})==53
print(json.dumps(summary,ensure_ascii=False,indent=2))
print('INVENTORY_SOURCE_COLUMNS=53; DERIVED_AUDIT_COLUMNS=1; MODEL_TRAINED=False')
