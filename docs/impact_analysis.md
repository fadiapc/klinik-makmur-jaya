# Analisis Dampak Perubahan (Impact Analysis)
**Sistem E-Commerce & POS Klinik Makmur Jaya**

Aplikasi e-commerce adalah sistem terintegrasi yang saling mengait (*tightly coupled*). Dokumen ini menguraikan analisis dampak pada modul lain jika ada modifikasi pada salah satu modul inti, agar pengembang mewaspadai *efek domino* / regresi kode (*regression bugs*).

---

## Skenario 1: Mengubah Skema Kolom Entitas "Data Obat" (Product)
*Contoh Perubahan: Menambahkan kolom `satuan_obat` (Box/Botol/Strip/Tablet) atau mengubah format Harga.*

**Dampak Modul Terpengaruh (High Impact):**
1. **Modul Keranjang Belanja (Cart):** UI harus diperbarui agar menampilkan satuan beli. Jika format harga di *backend* diubah, perhitungan total subtotal di keranjang bisa *error* (NaN).
2. **Modul Manajemen Pesanan (Order & OrderItem):** *Item* pesanan (`OrderItem`) biasanya mereplika (menyalin) data produk saat di-*checkout*. Perubahan struktur harus direfleksikan ke skema *snapshot* riwayat pesanan.
3. **Peringatan Kedaluwarsa:** Karena terikat dengan entitas *ProductBatch* (relasi 1:M). Jika ID atau status `is_active` produk berubah, logika penipisan stok di layanan latar belakang (*Background Task*) dapat rusak.

**Tindakan Pencegahan:**
Menambahkan *Unit Testing* yang menjalankan *mock checkout* keranjang setiap kali ada modifikasi model `Product`.

---

## Skenario 2: Mengubah Algoritma Modul "Keranjang / Pembayaran"
*Contoh Perubahan: Menambahkan dukungan fitur kupon diskon (Voucher) atau integrasi *Payment Gateway* otomatis.*

**Dampak Modul Terpengaruh (Critical Impact):**
1. **Alur Status Pesanan (Order Status):** Sangat kritis. Logika perpindahan dari status `MENUNGGU_PEMBAYARAN` menjadi `DIPROSES` yang tadinya ditekan manual oleh Kasir akan menjadi otomatis. Kasir tidak lagi perlu melakukan validasi.
2. **Sistem Notifikasi:** Jika ada pembaruan status otomatis, pemicu notifikasi *WebSocket* ke pelanggan juga berpotensi gagal meledak (*trigger*) apabila diletakkan di tempat yang salah.
3. **Modul Laporan / Keuangan:** Nilai akhir omzet penjualan harus dikurangi nominal kupon agar tutup buku Kasir tidak selisih (minus).

**Tindakan Pencegahan:**
Arsitektur harus mengadopsi struktur *Observer Pattern* atau pemisahan *Domain Driven Design (DDD)* untuk modul diskon.

---

## Skenario 3: Memodifikasi Modul "Autentikasi & Keamanan"
*Contoh Perubahan: Mengganti struktur token JWT (menambahkan ID peran khusus) atau menambahkan validasi email pada pengguna.*

**Dampak Modul Terpengaruh (System-wide Impact):**
1. **Seluruh Endpoint Aplikasi:** Hal ini akan mengganggu fungsi penjagaan akses (*Dependency Injection* `get_current_user`). Jika token diubah secara paksa, semua pengguna, kasir, dan apoteker yang sedang bekerja (token lama belum basi) akan tertendang paksa (mendapat peringatan *401 Unauthorized*).

**Tindakan Pencegahan:**
Jika ada perubahan model token autentikasi, jadwalkan saat masa pemeliharaan (luar jam kerja) untuk meminimalkan keterkejutan pada staf klinik yang tiba-tiba "ter-*logout*" saat sedang melayani pasien.
