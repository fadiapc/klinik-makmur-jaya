# Dokumen Skenario Migrasi Data
**Sistem E-Commerce & POS Klinik Makmur Jaya**

Dokumen ini menjelaskan strategi dan langkah-langkah perpindahan (migrasi) data dari pencatatan manual/spreadsheet lama ke dalam basis data PostgreSQL sistem e-commerce baru.

---

## 1. Strategi Migrasi Data Obat
Pendekatan migrasi yang digunakan adalah **"Big Bang Migration"** (berpindah serentak) yang dilakukan pada luar jam operasional klinik (misalnya pukul 23:00 - 02:00) untuk mencegah adanya pencatatan transaksi yang tumpang tindih.

### Langkah Persiapan:
1. **Data Cleansing (Pembersihan Data):** Data Excel lama dibersihkan dari duplikasi, spasi berlebih, atau ketidaksesuaian format tanggal (misal: penyeragaman format kedaluwarsa menjadi `YYYY-MM-DD`).
2. **Transformasi Format:** Menyimpan *(Export)* file Spreadsheet menjadi format *Comma Separated Values* (`.csv`) berstandar UTF-8.

---

## 2. Pemetaan Kolom (Mapping Field)

Pemetaan atribut dari dokumen Excel/Manual ke dalam *Tabel Product* dan *ProductBatch* di Database PostgreSQL.

| Kolom Spreadsheet (Lama) | Tipe Data | Tabel & Kolom PostgreSQL (Baru) | Tipe Data |
| :--- | :--- | :--- | :--- |
| Kode Barang / Barcode | Text | `products.sku` | String (Unique) |
| Nama Obat | Text | `products.name` | String |
| Kategori (Resep/Bebas) | Text | `categories.id` (Relasi) | Integer (Foreign Key) |
| Harga Beli | Angka | `products.base_price` | Numeric(12,2) |
| Harga Jual | Angka | `products.selling_price` | Numeric(12,2) |
| Peringatan Minim | Angka | `products.min_stock` | Integer |
| No. Batch / Produksi | Text | `product_batches.batch_number`| String |
| Tgl Kedaluwarsa | Teks/Date | `product_batches.expiration_date`| Date |
| Sisa Stok Aktif | Angka | `product_batches.remaining_quantity`| Integer |

---

## 3. Validasi Data Pasca-Migrasi

Setelah skrip *import* CSV dijalankan dan data masuk ke PostgreSQL, verifikasi dilakukan dengan:
1. **Data Count Validation:** Memastikan jumlah baris di tabel `products` sama dengan total baris valid di file Excel (`SELECT COUNT(*) FROM products`).
2. **Data Integrity Check:** Memastikan stok tidak ada yang bernilai minus.
3. **Random Sampling:** Tim operasional (Apoteker) memeriksa 20 obat secara acak di UI Aplikasi apakah nama, harga, dan sisa stok sudah persis sama dengan pencatatan manual terakhir.

---

## 4. Rencana Pemulihan (Rollback Plan)

Jika pada masa validasi ditemukan kegagalan struktural (misalnya: salah *mapping* harga jual menjadi harga beli, atau data terpotong):
1. **Hentikan Sistem:** Tutup akses pengguna ke aplikasi web baru.
2. **Truncate Tables:** Jalankan kueri `TRUNCATE TABLE product_batches, products CASCADE;` untuk mengosongkan seluruh data yang cacat masuk.
3. **Revert ke Manual:** Klinik kembali beroperasi menggunakan *Spreadsheet* keesokan harinya sembari tim TI (*IT*) memperbaiki skrip migrasi (parser CSV). Tidak ada *downtime* pada sisi bisnis klinik.
