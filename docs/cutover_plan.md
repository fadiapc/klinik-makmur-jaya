# Dokumen Cutover Plan (Rencana Peralihan)
**Sistem E-Commerce & POS Klinik Makmur Jaya**

*Cutover Plan* adalah panduan yang mengatur transisi (*switch*) dari sistem manual ke sistem perangkat lunak baru secara langsung pada lingkungan operasional (*Production*).

---

## 1. Timeline (Garis Waktu) Pelaksanaan

*Target Hari Peralihan (Cutover Date) diasumsikan pada hari **Minggu, pukul 23:00 WIB**.*

| Waktu | Fase | Penanggung Jawab | Aktivitas |
| :--- | :--- | :--- | :--- |
| **H - 3 Hari** | Persiapan | Tim TI & Admin | Pengaturan *server cloud*, instalasi sertifikat SSL/HTTPS, dan *User Acceptance Testing* (UAT) akhir. |
| **H - 1 Hari** | Sosialiasi | Manajemen Klinik | Menginformasikan seluruh staf (Apoteker/Kasir) bahwa besok adalah hari terakhir menggunakan catatan manual. |
| **H-0 (21:00)** | Data Freeze | Seluruh Staf | Operasional klinik ditutup. DILARANG ada transaksi keluar/masuk barang. |
| **H-0 (22:00)** | Ekstraksi | Tim TI | Mengunduh rekapan Excel (stok final) untuk dipersiapkan proses migrasi. |
| **H-0 (23:00)** | **CUTOVER** | Tim TI | Menjalankan *script batch import* data Excel ke basis data PostgreSQL *Production*. |
| **H-0 (00:30)** | Verifikasi | Tim TI & Apoteker | Pengujian acak (Cek harga, stok, coba *login* pakai akun staf). |
| **H+1 (06:00)** | Go-Live | Seluruh Staf | Sistem resmi digunakan melayani pasien. Buku manual disimpan sebagai arsip mati. |

---

## 2. Checklist Pra-Cutover

Sebelum eksekusi dimulai (H-0 23:00), pastikan:
- [ ] Server Web/API dan Database menyala (*Up and Running*) tanpa hambatan.
- [ ] *Domain* utama `klinikmakmurjaya.id` sudah terhubung (*pointing*) ke alamat IP Load Balancer.
- [ ] Lingkungan sudah berada dalam mode `production` (Debug=False di berkas *config*).
- [ ] File migrasi CSV terakhir sudah disetujui (divalidasi) oleh Kepala Apoteker.
- [ ] Seluruh staf sudah memiliki nama pengguna (*username*) dan kata sandi (*password*) awal.

---

## 3. Langkah-Langkah Cutover (Eksekusi)

1. Tampilkan halaman pemeliharaan (*Maintenance Page*) pada antarmuka *Frontend* melalui perutean peladen (NGINX).
2. Bersihkan (*Flush*) status *cache* yang tidak relevan di peladen.
3. Eksekusi skrip `python seed_migration.py data_final.csv` untuk mengimpor seluruh basis data obat, pengguna, dan pemasok.
4. Matikan mode *Maintenance Page* dari NGINX.
5. Umumkan status **GO-LIVE** kepada grup internal staf klinik Makmur Jaya.

---

## 4. Verifikasi Pasca-Cutover (Post-Go-Live Validation)

Pengecekan minimal (Sanity Check) yang harus dilakukan dalam 30 menit pertama:
1. **Login Check:** Admin mencoba *login*.
2. **Role Check:** Pastikan tampilan dasbor Kasir dan Apoteker berbeda.
3. **Transaction Check:** Lakukan 1 transaksi pesanan boneka (Dummy Order) di antarmuka POS dan pastikan struk tercetak normal, lalu batalkan pesanannya (Void).
4. **Integration Check:** Uji unggah 1 foto untuk mengecek apakah integrasi direktori penyimpanan / *Object Storage* bekerja dengan baik.
