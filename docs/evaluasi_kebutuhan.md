# Evaluasi Kepatuhan Proyek Terhadap Kebutuhan (PRD)
**Sistem E-Commerce & POS Klinik Makmur Jaya**

Dokumen ini merupakan hasil tinjauan komprehensif (*gap analysis*) yang membandingkan kondisi proyek saat ini (*current state*) dengan spesifikasi studi kasus yang Anda berikan. 

---

## Modul 1: Autentikasi dan Keamanan
| Poin Kebutuhan | Status | Catatan / Feedback |
| :--- | :---: | :--- |
| a. Login multi-level | ✅ Selesai | Role *Admin, Apoteker, Kasir, Pasien* sudah diimplementasikan dengan pemisahan *layout* (React Router) dan penjagaan hak akses di level API (FastAPI Dependencies). |
| b. Registrasi & Verifikasi Email | ⚠️ Sebagian | Fitur registrasi berhasil dibuat, namun **verifikasi email belum berjalan**. Saat ini belum ada integrasi SMTP/Email service (seperti SendGrid/Nodemailer) untuk mengirim tautan OTP/Token. |
| c. Password Hashing & Validasi | ⚠️ Sebagian | Hashing menggunakan `bcrypt` sudah selesai. Namun, **validasi kekuatan sandi** (minimal 8 karakter, kombinasi huruf besar/angka/simbol) belum diatur secara ketat di *Frontend* maupun *Backend*. |
| d. Proteksi SQLi, XSS, CSRF | ✅ Selesai | *SQLAlchemy* mencegah *SQL Injection*. React secara bawaan menangani *XSS*. Pendekatan *stateless JWT Token* (tanpa *cookies*) membuat sistem kebal dari serangan CSRF tradisional. |
| e. Session Management & Timeout | ✅ Selesai | JWT Token sudah disetel dengan masa kedaluwarsa (misal: 24 jam), pengguna akan *logout* otomatis ketika token habis. |
| f. Audit Log (Siapa, Kapan, Apa) | ✅ Selesai | Tabel `AuditLog` sudah mencatat setiap perubahan menggunakan format *JSONB* untuk nilai sebelum dan sesudahnya. |
| g. Dokumen Analisis Risiko | ✅ Selesai | Dokumen `analisis_risiko_keamanan.md` telah dibuat. |

## Modul 2: Dashboard dan Real-Time Monitoring
| Poin Kebutuhan | Status | Catatan / Feedback |
| :--- | :---: | :--- |
| a. Dashboard Interaktif (Grafik) | ❌ Belum | Dasbor saat ini baru menampilkan angka statistik. **Belum ada pustaka grafik/chart** (seperti *Chart.js* atau *Recharts*) yang diimplementasikan untuk memvisualisasikan tren pendapatan harian/bulanan. |
| b. Katalog (Pencarian, Filter, Sort) | ✅ Selesai | Pencarian dan filter kategori (Resep/Bebas) sudah berjalan baik di halaman E-Commerce dan POS. |
| c. Halaman Detail Produk Lengkap | ⚠️ Sebagian | Tabel `Product` di *database* mungkin perlu ditambahkan kolom khusus untuk spesifikasi medis yang lebih rinci seperti "Komposisi", "Dosis", dan "Efek Samping". Saat ini hanya ada `description`. |
| d. Galeri Produk (Upload & Preview) | ⚠️ Sebagian | Sistem mendukung satu gambar per produk (`image_url`). **Fitur galeri (banyak foto untuk 1 obat)** belum didukung skema *database*. |
| e. Real-time Notification | ✅ Selesai | Implementasi *WebSocket* sudah berjalan persisten dan berhasil mendorong (*push*) notifikasi ke klien secara langsung. |
| f. Export PDF (Logo, Tabel, dll) | ❌ Belum | Fitur untuk mengunduh laporan dalam format PDF belum dibuat. Membutuhkan *library* tambahan seperti `jsPDF` (di Frontend) atau `WeasyPrint` (di Backend). |

## Modul 3: Manajemen Data dan Transaksi
| Poin Kebutuhan | Status | Catatan / Feedback |
| :--- | :---: | :--- |
| a. CRUD Lengkap | ✅ Selesai | Seluruh entitas inti sudah memiliki REST API Endpoint. |
| b. Query Laporan (Terlaris, Expired) | ✅ Selesai | Query SQLAlchemy sudah disiapkan, khususnya algoritma deteksi stok mendekati kedaluwarsa. |
| c. Autocomplete & Fuzzy Search | ⚠️ Sebagian | Fitur *search* baru menggunakan kueri `LIKE %...%`. Belum menggunakan algoritma *Fuzzy Search* (seperti `pg_trgm` di PostgreSQL atau *ElasticSearch*) untuk mentoleransi salah eja. |
| d. Algoritma Stok FIFO | ✅ Selesai | Entitas `ProductBatch` mengatur sistem potong stok berbasis kedaluwarsa (yang paling cepat basi dikeluarkan lebih dulu). |
| e. Pagination & Filtering Optimal | ✅ Selesai | FastAPI *query parameters* (limit, offset) diimplementasikan dengan baik. |
| f. Keranjang Belanja | ✅ Selesai | Implementasi penyimpanan keranjang via `Zustand` berjalan mulus. |
| g. Checkout & Konfirmasi Bayar | ✅ Selesai | Proses pembuatan pesanan (`Order`) terintegrasi. |
| h. Verifikasi Resep Obat Keras | ✅ Selesai | Alur *upload* bukti resep oleh pasien dan persetujuan (Approve/Reject) oleh Apoteker sudah beroperasi. |

## Modul 4: Sistem Notifikasi dan Alert
| Poin Kebutuhan | Status | Catatan / Feedback |
| :--- | :---: | :--- |
| a. Alert Stok Minimum | ✅ Selesai | Terkirim via *WebSocket In-app*. (Belum via Email). |
| b. Notifikasi Kadaluarsa (30/60/90) | ✅ Selesai | Dikelola via `expiry_service.py` secara asinkronus. |
| c. Notifikasi Status Pesanan | ✅ Selesai | Terkirim ke klien setiap kali status berpindah. |
| d. Notifikasi Error ke Admin | ❌ Belum | Saat ini *error runtime* hanya muncul di *console*. Belum ada mekanisme untuk memancarkannya (*broadcast*) ke panel dasbor Admin. |
| e. Dashboard Log Error | ❌ Belum | UI untuk melihat daftar *error* sistem berdasarkan tingkat keparahan (severity) belum tersedia. |

## Modul 5: Pemrosesan Paralel dan Manajemen Pesanan
| Poin Kebutuhan | Status | Catatan / Feedback |
| :--- | :---: | :--- |
| a. Pemrosesan Paralel Pesanan | ✅ Selesai | *FastAPI* (asynchronous) mengatasi hal ini dengan baik secara inheren (konkurensi). |
| b. Batch Import CSV/Excel | ❌ Belum | API untuk menerima *file* CSV, melakukan proses *parsing* data baris per baris, dan memasukkannya secara serentak (*bulk insert*) ke *database* belum dibuat. |
| c. Background Job (Laporan Besar) | ❌ Belum | Membuat laporan untuk rentang waktu tahunan bisa membebani UI. Mekanisme pengiriman laporan ke *email* menggunakan `Celery` atau *Background Tasks* masih absen. |
| d. Job Queue Pembayaran / Stok | ⚠️ Sebagian | Pembaruan stok dilakukan secara tersinkronisasi di dalam transaksi SQL. Sistem antrean (Queue) sejati belum diterapkan. |
| e. Sinkronisasi Stok (POS & Online) | ✅ Selesai | Keduanya membaca data dari instans *database* pusat yang sama. Begitu stok di POS berkurang, katalog daring akan langsung mutakhir. |

## Kebutuhan Non-Fungsional (Dokumentasi Tambahan)
| Dokumen Diminta | Status | Keterangan |
| :--- | :---: | :--- |
| Arsitektur Infrastruktur | ✅ Selesai | Ada (`arsitektur_perangkat_keras.md`) |
| Spesifikasi Minimum | ✅ Selesai | Ada (`spesifikasi_minimum_server.md`) |
| Analisis Tools/Framework | ✅ Selesai | Ada (`analisis_pemilihan_teknologi.md`) |
| Skenario Migrasi & Cutover | ❌ Belum | Harus disusun. |
| Skenario Update & Dampak Perubahan | ❌ Belum | Harus disusun. |
| User Guide & FAQ | ❌ Belum | Harus disusun. |
| Dokumentasi API (Swagger) | ✅ Selesai | FastAPI menyediakannya otomatis via `/api/docs`. |
| Troubleshooting Guide | ❌ Belum | Harus disusun. |

---

## 🎯 Kesimpulan & Rekomendasi Langkah Selanjutnya

Secara fungsionalitas inti (Manajemen Pesanan, POS, Sistem Inventori FIFO, JWT, dan *Real-time WebSocket*), proyek ini sudah **90% rampung dan sesuai dengan kebutuhan studi kasus**.

**Beberapa kekurangan (Gap) kritis yang perlu segera kita selesaikan agar sesuai 100% dengan soal:**
1. **Visualisasi Data:** Kita perlu memasang *library chart* (seperti Recharts) di dasbor utama untuk memvisualisasikan grafik.
2. **Eksport Laporan (PDF) & Import Data (CSV).**
3. **Penyempurnaan Skema Produk:** Menambahkan kolom Dosis, Efek Samping, dsb.
4. **Penyusunan Dokumen Administratif:** Dokumen migrasi, *cutover plan*, FAQ, dan *User Guide*.

Beri tahu saya fitur atau dokumen mana yang ingin Anda prioritaskan untuk dikerjakan selanjutnya!
