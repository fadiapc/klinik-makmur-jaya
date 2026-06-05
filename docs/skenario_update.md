# Skenario Pembaruan Perangkat Lunak & Kontrol Versi
**Sistem E-Commerce & POS Klinik Makmur Jaya**

Seiring bertumbuhnya klinik, penambahan fitur (*update*) perangkat lunak pasti akan terjadi. Dokumen ini merumuskan skenario penambahan fitur baru tanpa mematikan atau mengganggu fungsi yang sudah berjalan stabil.

---

## 1. Penggunaan Version Control System (Git)

Proyek ini wajib menggunakan metodologi penamaan cabang **Git Flow** standar untuk mencegah kode baru (*untested code*) tumpah ruah merusak lingkungan *Production*.

### Pemisahan Branch Utama:
1. `main` (atau `master`): Cabang suci. Kode di cabang ini merepresentasikan versi aplikasi yang sedang aktif dipakai klinik saat ini. TIDAK BOLEH ditambahkan baris kode apa pun secara langsung.
2. `staging`: Cabang pengujian. Kode di cabang ini berjalan di server uji coba (*Staging Server*) tempat fitur baru dicoba secara internal sebelum dirilis.
3. `feature/nama-fitur`: Cabang pengerjaan. Pengembang menulis kode penambahan fitur di cabang ini.

### Skenario Alur Kerja (Workflow):
1. **Inisiasi:** Pengembang menarik kode terbaru: `git checkout -b feature/ekspor-pdf`.
2. **Pengembangan:** Menginstal modul HTML ke PDF dan membuat antarmuka pengunduhan laporan.
3. **Penggabungan Pengujian (Merge to Staging):** Jika selesai, lakukan *Pull Request* (PR) ke cabang `staging`. Tim QA/Apoteker akan mencoba menekan tombol PDF di server uji coba.
4. **Rilis (Release to Main):** Jika lulus uji coba, kode `staging` di-gabungkan (*merge*) ke cabang `main`. Server produksi akan secara otomatis menarik kode terbaru (*Automated Deployment/CI-CD*).

---

## 2. Skenario *Zero-Downtime Update*

Untuk menghindari sistem POS Kasir macet akibat *restart* peladen, proses pembaruan dijalankan dengan strategi berikut:

1. **Pembaruan Backend (FastAPI):**
   - Jika ada fitur baru (contoh: *Endpoint* Laporan PDF), pembaruan peladen dilakukan dengan metode *Rolling Restart* menggunakan manajer proses seperti **Gunicorn/Supervisor**. 
   - *Worker* yang menangani API akan dihidupkan ulang satu-persatu tanpa memutus keseluruhan koneksi.
2. **Pembaruan Database (Alembic Migrations):**
   - **Aturan Emas (Golden Rule):** Jangan pernah MENGHAPUS (*DROP*) kolom lama atau MENGUBAH NAMA (*RENAME*) kolom saat pembaruan fitur. Selalu TAMBAHKAN (*ADD*) kolom baru.
   - Hal ini memastikan bahwa kode aplikasi versi lama (*Frontend* klien yang belum me-*refresh* *browser*) tidak *crash* karena kolom tiba-tiba hilang. Kolom lama yang sudah usang baru dihapus pada siklus pembaruan beberapa minggu berikutnya (*Backward Compatibility*).
3. **Pembaruan Frontend (React/Vite):**
   - Aset statis hasil *build* (JavaScript/CSS) yang baru diunggah ke peladen/CDN. Pengguna hanya perlu me-muat ulang (*refresh*) halaman (atau menekan f5) untuk mendapatkan versi UI terbaru secara instan. Tidak ada interupsi di sisi pangkalan data.
