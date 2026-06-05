# Skenario Pembaruan Perangkat Lunak & Analisis Dampak
**Sistem E-Commerce & POS Klinik Makmur Jaya**

Seiring bertumbuhnya klinik, penambahan fitur (*update*) pasti akan terjadi. Dokumen ini merumuskan skenario penambahan fitur baru tanpa mematikan sistem, serta menganalisis dampak perubahannya (*impact analysis*) terhadap fungsionalitas lain.

---

## 1. Penggunaan Version Control System (Git)

Proyek ini wajib menggunakan penamaan cabang **Git Flow** standar untuk mencegah kode baru (*untested code*) merusak *Production*.

### Pemisahan Branch Utama:
1. `main` (atau `master`): Cabang suci. Mewakili versi aplikasi yang aktif. TIDAK BOLEH *commit* langsung.
2. `staging`: Cabang pengujian di server uji coba (*Staging Server*).
3. `feature/nama-fitur`: Cabang pengerjaan fitur baru.

### Skenario Alur Kerja:
1. **Inisiasi:** Pengembang menarik kode terbaru: `git checkout -b feature/ekspor-pdf`.
2. **Penggabungan Pengujian:** Lakukan *Pull Request* (PR) ke cabang `staging` untuk diuji oleh QA/Apoteker.
3. **Rilis:** Jika lulus uji coba, kode `staging` di-*merge* ke cabang `main` (*Automated Deployment*).

## 2. Skenario *Zero-Downtime Update*

1. **Pembaruan Backend (FastAPI):**
   - Pembaruan peladen dilakukan dengan metode *Rolling Restart* menggunakan *Gunicorn/Supervisor* agar *worker* dihidupkan ulang bergantian tanpa memutus koneksi API.
2. **Pembaruan Database (Alembic):**
   - **Aturan Emas:** Jangan pernah MENGHAPUS (*DROP*) atau MENGUBAH NAMA (*RENAME*) kolom lama saat pembaruan fitur. Selalu TAMBAHKAN (*ADD*) kolom baru. Ini memastikan versi aplikasi klien yang lama tidak *crash* (*Backward Compatibility*).
3. **Pembaruan Frontend (React/Vite):**
   - Aset statis hasil *build* terbaru diunggah ke server/CDN. Pengguna hanya perlu me-muat ulang (*refresh*) halaman untuk mendapatkan UI terbaru.

---

## 3. Analisis Dampak Perubahan (Impact Analysis)

Aplikasi e-commerce adalah sistem terintegrasi (*tightly coupled*). Berikut adalah analisis dampak pada skenario perubahan umum untuk mencegah regresi kode (*regression bugs*).

### Skenario A: Mengubah Skema Kolom "Data Obat" (Product)
*Contoh Perubahan: Menambahkan satuan_obat atau mengubah format Harga.*

**Dampak Modul Terpengaruh (High Impact):**
1. **Keranjang Belanja:** Perhitungan subtotal bisa menjadi `NaN` jika format harga di-*backend* berubah.
2. **Pesanan (OrderItem):** *Item* pesanan biasanya mereplikasi data produk. Perubahan struktur harus direfleksikan ke skema *snapshot* pesanan.
3. **Peringatan Kedaluwarsa:** Karena terikat `StockBatch` (1:M), perubahan `is_active` bisa merusak kalkulasi stok layanan latar belakang.

**Pencegahan:** Tambahkan *Unit Testing* yang menyimulasikan keranjang belanja (*mock checkout*) setiap kali ada modifikasi model `Product`.

### Skenario B: Mengubah Algoritma "Keranjang / Pembayaran"
*Contoh Perubahan: Menambahkan kupon diskon (Voucher) atau integrasi Payment Gateway.*

**Dampak Modul Terpengaruh (Critical Impact):**
1. **Alur Status Pesanan:** Logika perpindahan `MENUNGGU_PEMBAYARAN` menjadi `DIPROSES` berpotensi otomatis tanpa validasi kasir.
2. **Sistem Notifikasi:** Pemicu *WebSocket* ke pelanggan berpotensi terlewat (*missed trigger*).
3. **Laporan / Keuangan:** Nilai tutup buku Kasir akan selisih (minus) jika tidak mengurangi nominal kupon.

**Pencegahan:** Mengadopsi arsitektur *Observer Pattern* agar modul pesanan, notifikasi, dan pembayaran terisolasi dengan baik.

### Skenario C: Memodifikasi Modul "Autentikasi & Keamanan"
*Contoh Perubahan: Mengubah struktur token JWT atau mengganti algoritma hashing.*

**Dampak Modul Terpengaruh (System-wide Impact):**
1. **Seluruh Endpoint:** Ini akan mengganggu penjagaan akses API. Jika token diubah secara paksa, semua kasir/apoteker yang sedang melayani pasien akan langsung ter-logout (*401 Unauthorized*).

**Pencegahan:** Ubah *hashing* dengan dukungan sistem *legacy* (seperti `Argon2` dan `Bcrypt` bersamaan di `passlib`). Lakukan pembaruan fitur ini hanya di luar jam kerja.
