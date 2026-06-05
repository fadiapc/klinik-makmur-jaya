# Dokumen Analisis Risiko Keamanan Informasi dan Langkah Mitigasi
**Sistem E-Commerce & POS Klinik Makmur Jaya**

Dokumen ini menguraikan potensi risiko keamanan informasi yang mungkin terjadi pada sistem Klinik Makmur Jaya beserta langkah-langkah mitigasi yang telah dan harus diterapkan untuk meminimalisir dampak dari risiko tersebut.

---

## 1. Risiko Akses Tidak Sah dan Pembajakan Akun (Unauthorized Access & Account Takeover)
**Deskripsi Risiko:**
Pihak tidak berwenang berhasil masuk ke dalam sistem menggunakan kredensial pengguna yang sah (misal: akibat kata sandi lemah, serangan *brute-force*, atau *phishing*), yang dapat menyebabkan manipulasi data pasien, stok obat, atau penyalahgunaan fitur POS.

**Langkah Mitigasi:**
- **Autentikasi Berbasis Token:** Penggunaan JWT (*JSON Web Token*) dengan masa aktif yang terbatas untuk sesi pengguna.
- **Enkripsi Kata Sandi:** Menyimpan kata sandi menggunakan algoritma *hashing* yang kuat (Argon2) dan teknik *salting*, sehingga kata sandi asli tidak pernah tersimpan di *database*.
- **Role-Based Access Control (RBAC):** Membatasi hak akses pengguna secara ketat berdasarkan peran mereka (Admin, Apoteker, Kasir, Pasien). Pengguna hanya dapat mengakses API dan halaman yang diizinkan untuk perannya.
- **Kebijakan Kata Sandi Kuat:** Mewajibkan pengguna menggunakan kombinasi huruf besar, huruf kecil, angka, dan karakter khusus.

## 2. Kebocoran Data Privasi Pasien (Data Breach)
**Deskripsi Risiko:**
Data sensitif seperti riwayat transaksi, unggahan resep dokter, dan informasi pribadi pasien (nama, alamat, telepon) diakses dan dicuri oleh peretas.

**Langkah Mitigasi:**
- **Komunikasi Terenkripsi (HTTPS):** Menggunakan protokol SSL/TLS untuk mengenkripsi semua data yang ditransmisikan antara *frontend* dan *backend*, maupun komunikasi WebSockets.
- **Pengamanan File Unggahan:** Menyimpan file resep dan bukti transfer di direktori yang tidak dapat diakses langsung oleh publik (contoh: *folder* lokal tertutup atau *cloud storage* dengan kebijakan akses ketat) dan memvalidasi ekstensi file yang diunggah (`.jpg`, `.png`, `.webp`) untuk mencegah unggahan *script* berbahaya (*Web Shell*).
- **Pembatasan Paparan Data (Data Exposure Limits):** Memastikan API hanya mengembalikan data yang relevan dengan kebutuhan *frontend* (misal: tidak mengembalikan *hash* kata sandi atau *ID database* internal yang sensitif pada respon API).

## 3. Serangan Injeksi dan Manipulasi Input (SQL Injection, XSS, CSRF)
**Deskripsi Risiko:**
Peretas memasukkan perintah berbahaya melalui *form input* aplikasi atau parameter URL yang dapat dieksekusi oleh *database* (SQLi) atau peramban pengguna lain (XSS).

**Langkah Mitigasi:**
- **Object Relational Mapping (ORM):** Menggunakan *SQLAlchemy ORM* dengan fitur pengikatan parameter (*parameter binding*) yang secara otomatis memfilter input pengguna sehingga mustahil melakukan SQL Injection.
- **Validasi Input Terpusat:** Menggunakan *Pydantic* untuk memvalidasi dan memfilter setiap *payload* JSON yang masuk ke *backend*. Format, tipe data, dan panjang maksimum input dibatasi.
- **Pembersihan Output (Sanitization):** Menggunakan *framework frontend* modern (React/Vite) yang secara bawaan (*by default*) melakukan *escaping* terhadap data dinamis sebelum di-*render* ke DOM, sehingga mencegah serangan XSS (*Cross-Site Scripting*).

## 4. Ancaman dari Dalam (Insider Threats)
**Deskripsi Risiko:**
Karyawan klinik (seperti Kasir atau Apoteker) dengan sengaja atau tidak sengaja menghapus data, memanipulasi stok, atau menyetujui transaksi secara tidak sah.

**Langkah Mitigasi:**
- **Sistem Log Audit (Audit Trail):** Merekam setiap perubahan status pesanan, penambahan stok, dan persetujuan resep di dalam tabel `AuditLog`. Setiap aktivitas dicatat lengkap beserta waktu, aktor yang melakukan (User ID), dan perubahannya (Data Sebelum & Sesudah).
- **Pemisahan Tugas (Segregation of Duties):** Alur verifikasi berlapis. Contoh: Kasir bertugas mengonfirmasi pembayaran, sementara Apoteker bertugas memverifikasi resep. Tidak ada satu peran pun yang dapat melewati kedua proses ini sendirian.
- **Notifikasi Multi-Role:** Setiap aktivitas kritikal (stok menipis, pesanan baru) disiarkan ke berbagai peran terkait (Admin, Apoteker, Kasir) sehingga terjadi fungsi pengawasan silang (*cross-monitoring*).

## 5. Ketersediaan Sistem dan Serangan DDoS (DDoS Attacks & Downtime)
**Deskripsi Risiko:**
Sistem kewalahan karena dibanjiri oleh lalu lintas palsu (*Denial of Service*) atau *server database* mengalami kegagalan (*crash*), menyebabkan layanan klinik dan *e-commerce* lumpuh.

**Langkah Mitigasi:**
- **Pembatasan Laju Akses (Rate Limiting):** Menerapkan pembatasan jumlah *request* dari satu alamat IP dalam waktu tertentu untuk melindungi API endpoints (*login*, *checkout*) dari serangan *brute-force* atau bot DDoS.
- **Penanganan Kesalahan (Error Handling) yang Baik:** Tidak memaparkan pesan kesalahan internal *server* ke publik (*stack trace*). Mengembalikan respon HTTP standar (seperti `400 Bad Request` atau `500 Internal Server Error` dengan pesan generik).
- **Infrastruktur Cadangan (Backup & Disaster Recovery):** Menerapkan pencadangan otomatis pada *database* Klinik secara rutin (harian) dan menyimpan arsip ke server eksternal, sehingga data transaksi tidak hilang apabila server fisik mengalami kerusakan.

## 6. Kekurangan Stok dan Kadaluarsa Obat (Operasional)
**Deskripsi Risiko:**
Klinik kehabisan stok obat yang sangat dibutuhkan pasien atau obat yang diberikan kepada pasien ternyata telah kedaluwarsa.

**Langkah Mitigasi:**
- **Sistem Manajemen Stok Terpadu:** Pengurangan stok otomatis dengan algoritma FIFO (*First-In-First-Out*) pada setiap *checkout* pesanan.
- **Peringatan Otomatis (Automated Alerts):** *Background service* secara konstan memantau stok minimum dan batas kedaluwarsa (30, 60, dan 90 hari sebelum H-Hari), lalu mengirimkan pemberitahuan gigih (*persistent notification*) ke *dashboard* Admin dan Apoteker.

---
**Dokumen ini merupakan pedoman *living document* yang wajib ditinjau dan diperbarui secara berkala seiring dengan penambahan fitur-fitur baru pada sistem Klinik Makmur Jaya.**
