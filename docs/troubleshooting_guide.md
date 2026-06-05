# Troubleshooting Guide (Panduan Pemecahan Masalah)

Dokumen ini berisi panduan untuk mengatasi *error* teknis atau operasional yang sering terjadi pada Sistem Klinik Makmur Jaya.

---

## Masalah pada Frontend (React / Web)

### 1. Layar Berubah Menjadi Putih Berisi Teks Merah (React Render Error)
*   **Penyebab:** Terjadi kegagalan *render* (bug UI) yang ditangkap oleh komponen `ErrorBoundary`.
*   **Solusi:**
    1.  Coba **Refresh (F5)** halaman browser Anda. Terkadang ini hanya kendala jaringan sesaat.
    2.  Jika terus berulang, silakan kirimkan tangkapan layar (screenshot) teks merah tersebut ke staf IT agar mereka bisa melihat detail `stack trace` penyebabnya.

### 2. Peringatan "Sesi Anda Telah Berakhir" (Unauthorized)
*   **Penyebab:** Token akses (JWT) sudah kedaluwarsa.
*   **Solusi:** Klik tombol "Kembali ke Login" dan masukkan kembali Email serta Password Anda.

### 3. Keranjang Belanja Kosong Sendiri Saat Halaman Direfresh
*   **Penyebab:** Terjadi pembersihan *Cache/LocalStorage* secara tidak sengaja pada browser, atau Anda menggunakan *Incognito Mode* dan browser ditutup.
*   **Solusi:** Anda perlu memasukkan kembali barang ke keranjang. Aplikasi menyimpan keranjang belanja di dalam `LocalStorage` browser.

---

## Masalah pada Backend & Server (Admin/IT)

### 1. Server Error (500 Internal Server Error)
*   **Penyebab:** Bisa disebabkan karena database *down*, *query* bermasalah, atau *library* tidak ditemukan.
*   **Solusi (Untuk IT):** 
    1. Cek *log terminal* Uvicorn di server backend.
    2. Pastikan file konfigurasi `.env` sudah memuat kredensial PostgreSQL yang benar.
    3. Pastikan tidak ada *script migration* Alembic yang tertinggal (`alembic upgrade head`).

### 2. Notifikasi Real-Time (WebSocket) Tidak Muncul
*   **Penyebab:** Koneksi `ws://` terputus.
*   **Solusi:** 
    1. Sistem frontend secara otomatis akan mencoba melakukan *reconnect* setelah beberapa detik.
    2. Jika masih tidak masuk, pastikan alamat `FRONTEND_URL` di server dan `VITE_API_URL` di klien tidak diblokir oleh *Firewall* atau *Proxy* jaringan (Nginx harus dikonfigurasi untuk meneruskan `Upgrade: websocket`).

### 3. Error Koneksi Database: "asyncpg.exceptions.CannotConnectNowError"
*   **Penyebab:** Layanan PostgreSQL tidak berjalan di server.
*   **Solusi:** Masuk ke server, lalu `systemctl restart postgresql` (Linux) atau hidupkan PostgreSQL Service dari *Task Manager* (Windows).
