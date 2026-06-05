# Skenario Migrasi & Cutover Plan
**Sistem E-Commerce & POS Klinik Makmur Jaya**

Dokumen ini menjelaskan strategi pemindahan (migrasi) data dari pencatatan manual/spreadsheet lama ke sistem E-Commerce baru, serta panduan transisi operasional (*Cutover*) secara langsung.

---

## 1. Strategi Migrasi Data Obat
Pendekatan migrasi yang digunakan adalah **"Big Bang Migration"** (berpindah serentak) yang dilakukan pada luar jam operasional klinik (misalnya pukul 23:00 - 02:00) untuk mencegah pencatatan transaksi yang tumpang tindih.

### Langkah Persiapan:
1. **Data Cleansing:** Data Excel lama dibersihkan dari duplikasi, spasi berlebih, atau ketidaksesuaian format tanggal (misal: penyeragaman kedaluwarsa menjadi `YYYY-MM-DD`).
2. **Transformasi Format:** Menyimpan *(Export)* file Spreadsheet menjadi format *Comma Separated Values* (`.csv`) berstandar UTF-8.

## 2. Pemetaan Kolom (Mapping Field)

Pemetaan atribut dari dokumen Excel/Manual ke dalam *Tabel Product* dan *ProductBatch* di Database PostgreSQL.

| Kolom Spreadsheet (Lama) | Tipe Data | Tabel & Kolom PostgreSQL (Baru) | Tipe Data |
| :--- | :--- | :--- | :--- |
| Kode Barang / Barcode | Text | `products.sku` | String (Unique) |
| Nama Obat | Text | `products.name` | String |
| Kategori (Resep/Bebas) | Text | `categories.id` (Relasi) | Integer (Foreign Key) |
| Harga Beli | Angka | `products.base_price` | Numeric(12,2) |
| Harga Jual | Angka | `products.selling_price` | Numeric(12,2) |
| Peringatan Minim | Angka | `products.min_stock_threshold` | Integer |
| No. Batch / Produksi | Text | `stock_batches.batch_number`| String |
| Tgl Kedaluwarsa | Teks/Date | `stock_batches.expiry_date`| Date |
| Sisa Stok Aktif | Angka | `stock_batches.quantity`| Integer |

## 3. Rencana Peralihan (Cutover Plan)

*Target Hari Peralihan (Cutover Date) diasumsikan pada hari **Minggu, pukul 23:00 WIB**.*

| Waktu | Fase | Penanggung Jawab | Aktivitas |
| :--- | :--- | :--- | :--- |
| **H - 3 Hari** | Persiapan | Tim TI & Admin | Pengaturan *server cloud*, instalasi SSL/HTTPS, dan *User Acceptance Testing* (UAT) akhir. |
| **H - 1 Hari** | Sosialiasi | Manajemen Klinik | Menginformasikan seluruh staf (Apoteker/Kasir) bahwa besok adalah hari terakhir menggunakan catatan manual. |
| **H-0 (21:00)** | Data Freeze | Seluruh Staf | Operasional klinik ditutup. DILARANG ada transaksi keluar/masuk barang. |
| **H-0 (22:00)** | Ekstraksi | Tim TI | Mengunduh rekapan Excel (stok final) untuk dipersiapkan proses migrasi. |
| **H-0 (23:00)** | **CUTOVER** | Tim TI | Menjalankan *script batch import* data Excel ke basis data PostgreSQL *Production*. |
| **H-0 (00:30)** | Verifikasi | Tim TI & Apoteker | Pengujian acak (Cek harga, stok, coba *login* pakai akun staf). |
| **H+1 (06:00)** | Go-Live | Seluruh Staf | Sistem resmi digunakan melayani pasien. Buku manual disimpan sebagai arsip mati. |

## 4. Checklist Pra-Cutover
Sebelum eksekusi dimulai (H-0 23:00), pastikan:
- [ ] Server Web/API dan Database menyala (*Up and Running*).
- [ ] *Domain* `klinikmakmurjaya.id` sudah terhubung ke alamat IP server.
- [ ] Lingkungan sudah berada dalam mode `production`.
- [ ] File migrasi CSV terakhir sudah divalidasi oleh Kepala Apoteker.
- [ ] Seluruh staf sudah memiliki *username* dan *password* awal.

## 5. Rencana Pemulihan Darurat (Rollback Plan)

Jika pada masa validasi ditemukan kegagalan struktural fatal (salah *mapping* harga, data terpotong, aplikasi *crash*):
1. **Hentikan Sistem:** Tutup akses pengguna ke aplikasi web baru dan kembalikan *Maintenance Page*.
2. **Truncate Tables:** Kosongkan seluruh data baru dengan kueri `TRUNCATE TABLE stock_batches, products CASCADE;`.
3. **Revert ke Manual:** Klinik kembali beroperasi menggunakan *Spreadsheet* keesokan harinya sembari tim TI memperbaiki *script* migrasi. Tidak ada *downtime* operasional.
