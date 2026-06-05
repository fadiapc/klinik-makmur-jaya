# Dokumen User Story
**Sistem E-Commerce & POS Klinik Makmur Jaya**

Dokumen ini mendefinisikan *User Story* (Cerita Pengguna) yang merepresentasikan fungsionalitas sistem dari sudut pandang setiap peran (*role*) yang menggunakan aplikasi Klinik Makmur Jaya. Pendekatan ini membantu memastikan bahwa fitur yang dikembangkan benar-benar selaras dengan kebutuhan operasional nyata.

---

## Daftar Aktor (Peran Pengguna)
1. **Pasien / Pelanggan:** Pengguna publik yang berbelanja obat atau produk kesehatan secara daring melalui platform E-Commerce.
2. **Kasir:** Staf klinik yang melayani penjualan langsung di tempat (POS) dan mengonfirmasi masuknya pembayaran dari transaksi daring.
3. **Apoteker:** Staf klinik dengan keahlian medis yang bertugas memverifikasi kelayakan resep dokter, meracik/menyiapkan pesanan, dan mengelola keluar masuknya stok obat di gudang.
4. **Admin:** Pengelola sistem yang memiliki hak akses penuh untuk mengelola master data pengguna, memantau riwayat audit, dan mengawasi operasional secara keseluruhan.

---

## 1. User Story: Pasien / Pelanggan

| ID | Sebagai seorang... | Saya ingin bisa... | Sehingga saya dapat... | Kriteria Penerimaan (Acceptance Criteria) |
|---|---|---|---|---|
| US-P01 | Pasien | Melihat katalog obat dan produk kesehatan | Mencari obat yang saya butuhkan dengan mudah | Katalog menampilkan foto, nama, harga, dan ketersediaan stok produk. |
| US-P02 | Pasien | Memasukkan produk ke dalam keranjang belanja | Membeli beberapa jenis obat sekaligus dalam satu transaksi | Ada indikator jumlah barang di keranjang dan total estimasi harga. |
| US-P03 | Pasien | Mengunggah foto resep dokter saat *checkout* obat keras | Membeli obat resep secara legal dan aman dari rumah | Sistem mewajibkan unggahan foto jika ada item dalam keranjang berlabel "Obat Keras". |
| US-P04 | Pasien | Mengunggah bukti transfer pembayaran | Membayar pesanan daring saya | Status pesanan otomatis berubah menjadi "Menunggu Konfirmasi Kasir". |
| US-P05 | Pasien | Menerima notifikasi perubahan status pesanan secara *real-time* | Mengetahui secara pasti apakah pesanan saya sedang diproses, dikirim, atau ditolak | Lonceng notifikasi menyala saat apoteker menolak resep atau saat barang dikirim. |

## 2. User Story: Kasir

| ID | Sebagai seorang... | Saya ingin bisa... | Sehingga saya dapat... | Kriteria Penerimaan (Acceptance Criteria) |
|---|---|---|---|---|
| US-K01 | Kasir | Menambahkan item belanja menggunakan sistem POS | Melayani pelanggan yang datang langsung ke klinik | Fitur pencarian instan untuk mencari nama/SKU obat dan otomatis menghitung total harga kembalian. |
| US-K02 | Kasir | Menerima notifikasi pesanan daring yang sudah dibayar | Segera memproses konfirmasi dana masuk | Terdapat notifikasi dan menu khusus untuk "Pesanan Online". |
| US-K03 | Kasir | Melihat dan memverifikasi foto bukti transfer dari pelanggan | Memastikan uang benar-benar telah masuk ke rekening klinik | Kasir dapat mengeklik tombol "Konfirmasi Dana" yang mengubah status pesanan menjadi "Diproses". |

## 3. User Story: Apoteker

| ID | Sebagai seorang... | Saya ingin bisa... | Sehingga saya dapat... | Kriteria Penerimaan (Acceptance Criteria) |
|---|---|---|---|---|
| US-A01 | Apoteker | Menerima notifikasi pesanan yang membutuhkan verifikasi resep | Segera memeriksa legalitas dan dosis resep dokter pasien | Menampilkan gambar resep, daftar obat yang dipesan, dan tombol "Setujui" atau "Tolak" (dengan kolom catatan). |
| US-A02 | Apoteker | Mendapatkan notifikasi peringatan jika ada obat yang akan kedaluwarsa (H-30, H-60, H-90) | Menarik obat tersebut dari rak/etalase agar tidak membahayakan pasien | Muncul lonceng notifikasi persisten setiap hari terhadap *batch* yang mendekati kedaluwarsa. |
| US-A03 | Apoteker | Mendapatkan peringatan ketika stok obat menipis | Segera merencanakan pembelian/pengadaan (*restock*) | Notifikasi otomatis terkirim saat transaksi berhasil membuat sisa stok mencapai/di bawah *Minimum Stock*. |
| US-A04 | Apoteker | Mengelola (Tambah/Ubah/Hapus) data master obat dan *batch* | Memastikan etalase *e-commerce* dan POS sinkron dengan ketersediaan fisik | Form untuk memasukkan nama, kategori, harga, jenis obat (Bebas/Keras), tanggal kedaluwarsa, dan kuantitas. |
| US-A05 | Apoteker | Menekan tombol "Selesai Dipacking / Dikirim" | Menginformasikan bagian logistik dan pelanggan bahwa paket siap jalan | Status pesanan diubah ke "Dikirim". |

## 4. User Story: Admin

| ID | Sebagai seorang... | Saya ingin bisa... | Sehingga saya dapat... | Kriteria Penerimaan (Acceptance Criteria) |
|---|---|---|---|---|
| US-AD1 | Admin | Menambah, mengubah, atau menonaktifkan akun staf (Kasir/Apoteker) | Mengelola sumber daya manusia (SDM) klinik secara digital | Ada halaman Manajemen Pengguna (*User Management*) yang hanya bisa diakses peran Admin. |
| US-AD2 | Admin | Melihat sistem *Audit Log* (Log Aktivitas) | Mengawasi dan melacak rekam jejak apabila terjadi manipulasi stok atau persetujuan transaksi yang tidak wajar | Tabel Log mencatat Waktu, *User ID*, Aksi, dan Data Sebelum/Sesudah. |
| US-AD3 | Admin | Menerima seluruh notifikasi stok menipis dan kedaluwarsa | Ikut mengawasi jalannya operasional Apotek | Sama seperti US-A02 dan US-A03, Admin otomatis menerima peringatan yang sama. |

---

*Setiap "User Story" ini menjadi pedoman utama pengembangan fitur (*Feature Backlog*) yang divalidasi kebenaran teknisnya pada tahap *System Integration Testing* (SIT).*
