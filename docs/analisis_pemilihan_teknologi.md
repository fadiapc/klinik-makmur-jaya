# Dokumen Analisis Pemilihan Teknologi
**Sistem E-Commerce & POS Klinik Makmur Jaya**

Dokumen ini mendokumentasikan alat (*tools*), pustaka (*libraries*), komponen, dan kerangka kerja (*frameworks*) yang digunakan dalam pengembangan sistem perangkat lunak Klinik Makmur Jaya, beserta analisis dan alasan logis di balik pemilihan tersebut.

---

## 1. Lapisan Backend (Server-side)

Lapis *Backend* difokuskan pada kecepatan pemrosesan data, konkurensi (menangani banyak permintaan bersamaan), dan keamanan.

### A. FastAPI (Python)
- **Peran:** Kerangka kerja utama untuk membangun REST API dan *WebSocket endpoint*.
- **Alasan Pemilihan:**
  - **Kinerja Tinggi:** Salah satu *framework* Python tercepat berkat dukungan *asynchronous* bawaan (menggunakan *Starlette*).
  - **Dokumentasi Otomatis:** Menghasilkan dokumentasi Swagger UI dan ReDoc secara otomatis dari kode program, sangat memudahkan kolaborasi API dengan pengembang *Frontend*.
  - **Modern dan Ringkas:** Penulisan kode sangat deklaratif dan lebih singkat dibandingkan Django atau Flask.

### B. Uvicorn
- **Peran:** Server *Web Server Gateway Interface* (ASGI).
- **Alasan Pemilihan:** Gunicorn/Uvicorn merupakan standar industri saat ini untuk mengeksekusi aplikasi *asynchronous* Python di lingkungan produksi (*production*).

### C. SQLAlchemy & Alembic
- **Peran:** *Object Relational Mapper* (ORM) dan alat migrasi *database*.
- **Alasan Pemilihan:**
  - **SQLAlchemy:** Menghindarkan penulisan *query* SQL manual (*raw query*) sehingga meminimalisir risiko *SQL Injection*. Sangat stabil dan menangani relasi antar-tabel (*Foreign Keys*) dengan cerdas.
  - **Alembic:** Memungkinkan pelacakan versi skema *database* secara bertahap (*version control* untuk *database*). Jika ada perubahan kolom di masa depan, tidak perlu menghapus *database* lama.

### D. Pydantic
- **Peran:** Validasi data input dan serialisasi *output*.
- **Alasan Pemilihan:** Terintegrasi langsung dengan FastAPI. Secara otomatis akan menolak *payload* permintaan (*request*) yang tipe datanya tidak sesuai atau formatnya salah sebelum masuk ke logika bisnis aplikasi.

### E. PostgreSQL
- **Peran:** Sistem Manajemen Basis Data Relasional (RDBMS) Utama.
- **Alasan Pemilihan:** Berlisensi *open-source*, sepenuhnya memenuhi standar ACID (Atomicity, Consistency, Isolation, Durability) yang mutlak dibutuhkan dalam aplikasi finansial/POS e-commerce. Memiliki fitur pelacakan *JSONB* yang kuat apabila dibutuhkan penyimpanan data dinamis.

### F. PyJWT & Passlib (Bcrypt)
- **Peran:** Autentikasi token dan enkripsi (hashing) sandi.
- **Alasan Pemilihan:** JWT memungkinkan aplikasi berjalan tanpa status (*stateless*), menghemat memori *server*. Passlib dengan Bcrypt memastikan bahwa jika terjadi peretasan *database*, kata sandi pengguna tidak dapat dibaca karena berbentuk teks acak.

---

## 2. Lapisan Frontend (Client-side)

Lapis *Frontend* difokuskan pada pengalaman pengguna (UI/UX) yang responsif, pengelolaan *state* (status aplikasi) yang efisien, dan lingkungan pengembangan yang cepat.

### A. React.js
- **Peran:** Pustaka Antarmuka Pengguna (*User Interface Library*).
- **Alasan Pemilihan:** Memiliki ekosistem terbesar di dunia untuk pengembangan *Single Page Application* (SPA). Komponen berbasis modular memudahkan penggunaan ulang kode (*reusability*) pada halaman yang berbeda (contoh: *layout* navigasi yang sama untuk halaman Kasir dan Apoteker).

### B. TypeScript
- **Peran:** Bahasa pemrograman superset dari JavaScript.
- **Alasan Pemilihan:** Menambahkan pengetikan statis (*static typing*) pada JavaScript. Hal ini secara drastis mengurangi *bug* yang sering terjadi (*runtime error*) akibat tipe data yang keliru, serta memberikan fitur *auto-complete* (*Intellisense*) yang presisi di lingkungan IDE.

### C. Vite
- **Peran:** Alat *Build* dan *Development Server*.
- **Alasan Pemilihan:** Menawarkan *Hot Module Replacement* (HMR) yang sangat cepat. Perubahan kode *Frontend* akan langsung terlihat di peramban pengguna (*browser*) dalam hitungan milidetik. Waktu penyusunan (*bundling*) untuk *production* jauh lebih cepat dibandingkan Webpack atau *Create React App*.

### D. Tailwind CSS
- **Peran:** Kerangka kerja *Styling* (*Utility-first CSS*).
- **Alasan Pemilihan:** Mempercepat penulisan gaya (*styling*) langsung pada struktur HTML (JSX) tanpa harus berpindah-pindah antar *file* CSS terpisah. Menghasilkan ukuran bundel CSS yang sangat kecil dan efisien karena secara otomatis akan membuang *class* yang tidak terpakai saat *build*.

### E. Zustand
- **Peran:** Pengelolaan Status Global (*Global State Management*).
- **Alasan Pemilihan:** Sangat ringan dan meminimalisir penulisan kode berulang (*boilerplate*) dibandingkan Redux. Di aplikasi ini, Zustand digunakan untuk menyimpan Token Autentikasi dan Data Sesi Pengguna di memori peramban secara sinkron.

### F. Lucide React
- **Peran:** Paket Ikon SVG.
- **Alasan Pemilihan:** Kumpulan ikon yang minimalis, modern, dan sangat konsisten secara visual. Ukurannya lebih ringan dari FontAwesome dan dioptimalkan secara khusus untuk ekosistem React.

---

## Ringkasan

Kombinasi antara **Python (FastAPI)** dan **TypeScript (React)** memberikan keseimbangan yang sempurna antara **Kecepatan Pengembangan** (*Developer Velocity*) dan **Kinerja Aplikasi** (*Application Performance*). 

Penggunaan alat praintegrasi seperti ORM, JWT, dan Tailwind CSS memastikan bahwa aplikasi Klinik Makmur Jaya mengikuti praktik industri modern yang tangguh secara keamanan, sekaligus mudah untuk dipertahankan (*maintainable*) dan diperluas skalanya di masa mendatang.
