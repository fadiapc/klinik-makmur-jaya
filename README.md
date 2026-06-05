# 🏥 Klinik Makmur Jaya

**Klinik Makmur Jaya** adalah sebuah aplikasi web manajemen klinik dan apotek modern yang dirancang untuk mengelola inventaris obat, menangani pemesanan pasien (termasuk obat dengan resep dokter), transaksi Point of Sale (POS) kasir, serta verifikasi obat oleh apoteker secara terintegrasi dan *real-time*.

![Klinik Makmur Jaya Preview](https://placehold.co/1200x600/f8fafc/0f766e?text=Klinik+Makmur+Jaya)

## ✨ Fitur Utama

Aplikasi ini memiliki sistem multi-peran (Multi-Role) dengan alur kerja yang terintegrasi:

*   **👨‍⚕️ Pasien (Customer)**
    *   Melihat katalog produk dan obat.
    *   Keranjang belanja dan sistem *checkout* terpadu (One-Page Checkout).
    *   Mengunggah foto resep dokter untuk obat keras.
    *   Melihat riwayat pesanan dan status secara *real-time*.
*   **💊 Apoteker**
    *   *Dashboard* khusus untuk memverifikasi pesanan yang mengandung obat keras.
    *   Mengecek, menyetujui, atau menolak resep yang diunggah oleh pasien.
*   **💵 Kasir (Point of Sale)**
    *   Antarmuka POS modern untuk memproses pembayaran dan menyelesaikan pesanan.
    *   Memantau antrean pesanan dari pasien.
*   **🛠️ System Admin**
    *   *Dashboard* analitik dan statistik klinik.
    *   Manajemen produk/obat (CRUD), kategori, dan stok.
    *   Manajemen pengguna (Admin, Apoteker, Kasir, Pasien).
    *   Catatan Aktivitas (*Audit Log*) untuk memantau keamanan dan perubahan sistem.
*   **🔔 Notifikasi Real-time**
    *   Menggunakan *WebSockets* untuk memberikan notifikasi instan lintas peran (misal: notifikasi ke apoteker saat ada resep masuk, notifikasi ke pasien saat pesanan disetujui).

## 💻 Tech Stack

### Frontend
*   **Framework:** React 18 (menggunakan Vite)
*   **Bahasa:** TypeScript
*   **Styling:** Tailwind CSS
*   **State Management:** Zustand
*   **Routing:** React Router DOM
*   **Ikon:** Lucide React

### Backend
*   **Framework:** FastAPI (Python 3)
*   **Database:** SQLite (menggunakan SQLAlchemy ORM & Alembic untuk migrasi)
*   **Validasi Data:** Pydantic
*   **Autentikasi:** JWT (JSON Web Tokens) & Passlib (Bcrypt)
*   **Real-time:** WebSockets

## 🚀 Cara Instalasi & Menjalankan Aplikasi

Pastikan Anda telah menginstal **Node.js** dan **Python (3.9+)** di sistem Anda.

### 1. Persiapan Backend (FastAPI)

Buka terminal dan arahkan ke *folder* `backend`:
```bash
cd backend

# Buat virtual environment
python -m venv .venv

# Aktifkan virtual environment (Windows)
.venv\Scripts\activate
# Aktifkan virtual environment (Mac/Linux)
# source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Menjalankan migrasi database
alembic upgrade head

# (Opsional) Mengisi database dengan data awal (Seed Data)
python full_seed.py

# Jalankan server
uvicorn main:app --reload
```
Backend akan berjalan di `http://localhost:8000`.

### 2. Persiapan Frontend (React/Vite)

Buka terminal baru dan arahkan ke *folder* `frontend`:
```bash
cd frontend

# Install dependencies
npm install

# Jalankan server pengembangan
npm run dev
```
Frontend akan berjalan di `http://localhost:5173`.

## 🔐 Akun Default (Testing)

Jika Anda telah menjalankan skrip `full_seed.py`, Anda dapat *login* menggunakan akun berikut:

| Peran | Username | Password |
| :--- | :--- | :--- |
| **System Admin** | `admin` | `password123` |
| **Apoteker** | `apoteker1` | `password123` |
| **Kasir** | `kasir1` | `password123` |
| **Pasien** | `fadia` | `password123` |

## 📂 Struktur Direktori

```text
klinik-makmur-jaya/
├── backend/                  # Kode sumber FastAPI
│   ├── app/
│   │   ├── api/              # Endpoint API (Controllers)
│   │   ├── core/             # Konfigurasi keamanan & environment
│   │   ├── models/           # Skema Database (SQLAlchemy)
│   │   ├── schemas/          # Skema Validasi (Pydantic)
│   │   ├── services/         # Logika Bisnis
│   │   └── repositories/     # Operasi Database
│   ├── alembic/              # Migrasi Database
│   └── main.py               # Entry point FastAPI
│
└── frontend/                 # Kode sumber React (Vite)
    ├── src/
    │   ├── components/       # Komponen UI (Layout, Navbar, dll)
    │   ├── pages/            # Halaman aplikasi per-role
    │   ├── store/            # State Management (Zustand)
    │   ├── hooks/            # Custom Hooks (WebSockets)
    │   └── lib/              # Konfigurasi API Client (Axios)
    └── index.html            # Entry point HTML
```

---
Dibuat untuk Klinik Makmur Jaya. All rights reserved.
