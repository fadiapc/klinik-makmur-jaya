# Dokumen Manajemen Proyek Komprehensif
**Sistem E-Commerce & POS Klinik Makmur Jaya**

Dokumen ini merangkum *Project Charter*, *Work Breakdown Structure* (WBS), penjadwalan, daftar periksa kualitas, log perubahan, panduan, dan bukti integrasi yang digunakan selama pengembangan sistem.

---

## 1. Project Charter (Piagam Proyek)
- **Nama Proyek:** Pengembangan Platform E-Commerce dan POS Terintegrasi Klinik Makmur Jaya.
- **Latar Belakang:** Operasional penjualan obat masih manual, memicu ketidakpastian stok, kesulitan pelacakan pesanan, dan nihilnya layanan penjualan *online* untuk memfasilitasi pasien dari luar klinik.
- **Tujuan Proyek:** Mengotomatisasi sistem inventori farmasi berbasis FIFO, menghadirkan portal *e-commerce* dengan validasi resep elektronik, dan mendigitalisasi kasir (POS) dalam satu pangkalan data pusat (*centralized database*).
- **Pemangku Kepentingan (Stakeholders):** Manajemen Klinik Makmur Jaya (Sponsor Proyek), Apoteker, Kasir, Admin (Pengguna Internal), dan Pasien (Pengguna Akhir).

---

## 2. WBS (Work Breakdown Structure) & Scope
Ruang lingkup pekerjaan (Scope) dipecah menjadi beberapa fase terukur:

**1.0 Inisiasi & Perancangan Sistem**
  - 1.1 Analisis Kebutuhan Fungsional & Non-Fungsional
  - 1.2 Perancangan *Entity Relationship Diagram* (ERD)
  - 1.3 Pemilihan Tumpukan Teknologi (*Tech Stack*)

**2.0 Pengembangan Backend (API & Logika Bisnis)**
  - 2.1 Modul Autentikasi (JWT) & Keamanan RBAC
  - 2.2 Modul Katalog Produk & Sistem *Batch* FIFO
  - 2.3 Modul Transaksi (Order) & Validasi Resep
  - 2.4 Modul *WebSocket* untuk Notifikasi *Real-Time*

**3.0 Pengembangan Frontend (Antarmuka Pengguna)**
  - 3.1 Portal Pasien (Katalog E-Commerce, Keranjang Belanja, *Checkout*)
  - 3.2 Dasbor Kasir (POS, Konfirmasi Pembayaran)
  - 3.3 Dasbor Apoteker (Verifikasi Resep, Laporan Kedaluwarsa)

**4.0 Pengujian, Dokumentasi, & Migrasi**
  - 4.1 Pembuatan *Cutover Plan* & *Impact Analysis*
  - 4.2 Pelaksanaan *System Integration Testing* (SIT)
  - 4.3 Penyusunan *User Guide* dan *Troubleshooting*

---

## 3. Jadwal Proyek (Timeline)
Estimasi penyelesaian adalah 4 Minggu (1 Bulan/Sprint).
- **Minggu 1:** Finalisasi *Project Charter*, penyusunan dokumen arsitektur, dan inisialisasi basis data *PostgreSQL / SQLite*.
- **Minggu 2:** Pengerjaan *Backend* API (FastAPI) untuk pengelolaan Pengguna, Produk, dan Keranjang Belanja.
- **Minggu 3:** Integrasi *Frontend* (React), perakitan tampilan POS, dan halaman *Checkout*.
- **Minggu 4:** Pemasangan *WebSocket*, penyelesaian *Bug*, dan pengesahan dokumen Manajemen (termasuk *Cutover* & Skenario *Update*).

---

## 4. Quality Checklist (Daftar Periksa Kualitas)
| Fitur / Modul | Kriteria Penerimaan (*Acceptance Criteria*) | Status |
| :--- | :--- | :---: |
| Keamanan Akun | Kata sandi di-*hash* dengan `bcrypt`, token JWT aktif | ✅ Lulus |
| Manajemen Stok | Stok berkurang dari *batch* paling lama terlebih dahulu (FIFO) | ✅ Lulus |
| Verifikasi Resep | Transaksi obat keras mewajibkan pasien mengunggah gambar | ✅ Lulus |
| Kinerja UI | Dasbor tidak *freeze* saat mengambil data; *loading spinner* berfungsi | ✅ Lulus |
| Notifikasi | Klien menerima peringatan stok tanpa harus menyegarkan (*refresh*) halaman | ✅ Lulus |
| Responsivitas | UI dapat diakses dengan baik di layar Komputer Kasir maupun Tablet | ✅ Lulus |

---

## 5. Change Log (Riwayat Perubahan)
Melacak modifikasi signifikan pada sistem selama iterasi pengembangan:
- **v1.0.0:** Rilis inisial; mencakup keranjang belanja dasar dan manajemen produk.
- **v1.1.0:** *Fix* - Perbaikan alur verifikasi resep di dasbor Apoteker (`test_approve.py`).
- **v1.2.0:** *Update* - Penggabungan (*merge*) modul `notification_routes` dengan *WebSocket* persisten yang tersambung ke `app/models`.
- **v1.3.0:** *Update* - Penambahan rutin asinkron (`expiry_service.py`) untuk mengecek kedaluwarsa H-30/60/90 saat *startup* aplikasi.
- **v1.4.0:** *Documentation* - Melengkapi seluruh dokumen administratif sesuai studi kasus (Migrasi, FAQ, Impact Analysis).

---

## 6. Panduan Teknis Pelanggan (Rangkuman)
Pelanggan dapat memanfaatkan platform ini secara *mandiri* dengan cara:
1. Mengunjungi beranda web untuk mendaftar akun menggunakan nama dan email asli.
2. Memasukkan obat yang diperlukan ke dalam *Cart* (Keranjang).
3. Jika membeli obat berlabel resep, pelanggan wajib mengunggah pindaian/foto resep dokter sebelum memproses *Checkout*.
4. Pembayaran dilakukan via transfer rekening, dengan pengunggahan bukti bayar melalui menu Dasbor Pasien.
*(Versi rinci lengkap terdapat dalam dokumen `docs/user_guide.md` dan `docs/faq.md`)*.

---

## 7. Bukti Integrasi Seluruh Pekerjaan
Aplikasi Klinik Makmur Jaya telah mengimplementasikan arsitektur *Monorepo* yang terintegrasi secara utuh (*End-to-End*), dibuktikan dengan parameter berikut:
1. **Frontend-Backend Handshake:** Layanan Axios pada *Frontend* (`api.ts`) dipasang dengan *Interceptor* yang secara otomatis melampirkan Token JWT ke *Backend* FastAPI di port 8000.
2. **Event-Driven Integration:** Modul Transaksi (POS) tidak bekerja sendiri. Ketika Kasir menekan tombol "Setujui Transaksi", pemicu *trigger* otomatis mengirim instruksi ke modul Notifikasi (*WebSocket*), lalu diteruskan memperbarui angka pada Dasbor Admin secara *Real-Time*.
3. **Database Concurrency:** Skema ORM `SQLAlchemy` menjamin transaksi asinkron sehingga pasien yang melakukan *checkout online* dan Kasir yang melakukan transaksi POS dapat mengakses inventori di saat bersamaan tanpa risiko ganda (*Race Condition*).
4. **Version Control Git:** Seluruh komponen antarmuka, *routing* peladen, *library*, dan naskah dokumen didorong (*pushed*) secara kolektif ke dalam cabang pelacakan terpadu (GitHub), memastikan siklus *CI/CD* yang bersih.
