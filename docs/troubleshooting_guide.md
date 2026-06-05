# Panduan Penanganan Masalah (Troubleshooting Guide)
**Sistem E-Commerce & POS Klinik Makmur Jaya**

Dokumen ini berisi panduan untuk mengatasi berbagai kendala umum yang sering dilaporkan oleh Pasien atau Staf Klinik saat menggunakan aplikasi.

---

## Masalah pada Pelanggan / Pasien

### 1. Masalah: Gagal Mengunggah Foto Resep atau Bukti Transfer
- **Gejala:** Tampil notifikasi gagal saat menekan tombol "Unggah".
- **Penyebab:** Ukuran berkas foto terlalu besar (lebih dari batas 5MB) atau format tidak didukung (harus berupa JPG atau PNG).
- **Solusi:**
  - Pastikan memotret dengan kamera ponsel biasa (bukan mode Resolusi Tinggi/RAW).
  - Coba tangkap layar (*Screenshot*) ulang foto resep tersebut untuk memperkecil ukurannya, lalu unggah hasil tangkapan layarnya.

### 2. Masalah: Barang di Keranjang Tiba-Tiba Kosong / Berubah
- **Gejala:** Saat menekan tombol Lanjut Pembayaran, aplikasi mengabarkan "Stok tidak mencukupi".
- **Penyebab:** Ada pasien lain / pengunjung luring (di meja kasir fisik) yang lebih dulu menyelesaikan pembayaran untuk obat tersebut (sistem membaca data inventaris *real-time* paralel).
- **Solusi:** Hapus barang yang habis dari keranjang belanja dan coba periksa ulang etalase untuk mencari alternatif merk lain.

### 3. Masalah: Pesanan Terhenti di Status "Menunggu Verifikasi Resep"
- **Gejala:** Sudah memesan sejak kemarin tapi belum disuruh membayar.
- **Penyebab:** Apoteker belum sempat membuka panel verifikasi karena kepadatan pasien di klinik (atau memesan di luar jam praktik Apoteker).
- **Solusi:** Hubungi nomor WhatsApp resmi Klinik Makmur Jaya dengan mencantumkan Kode Pesanan (Contoh: `ORD-XXX`) agar Apoteker segera membuka dasbor daring.

---

## Masalah pada Internal Staf Klinik

### 1. Masalah: Layar POS / Halaman Apoteker Blank Putih atau Mutar Terus
- **Gejala:** Aplikasi memuat tanpa henti saat menekan tombol *refresh*.
- **Penyebab:** Koneksi internet di meja kasir klinik terputus atau sesi keamanan (*JWT Token*) sudah habis/basi (*expired*).
- **Solusi:**
  - Tekan tombol **Keluar (Logout)** di sisi kanan atas, lalu masuk (*Login*) kembali dengan kata sandi kasir.
  - Periksa *router* WiFi di area klinik. Jika listrik sempat padam, tunggu beberapa menit untuk koneksi stabil.

### 2. Masalah: Notifikasi Lonceng (Stok/Pesanan) Tidak Bunyi atau Telat Masuk
- **Gejala:** Kasir tidak tahu ada pesanan masuk padahal pasien sudah mengabari via pesan teks bahwa uang sudah ditransfer.
- **Penyebab:** Sambungan protokol *WebSocket* aplikasi terputus otomatis oleh peramban web (*Browser*) karena tab tertidur (*Sleeping Tab* fitur penghemat memori di Chrome).
- **Solusi:**
  - Muat ulang (Tekan tombol **F5**) halaman Dasbor Kasir untuk memicu sambungan *WebSocket* kembali (Re-connect).
  - Untuk mencegah ini, matikan fitur *Memory Saver* di setelan Google Chrome untuk situs web `klinikmakmurjaya.id`.
