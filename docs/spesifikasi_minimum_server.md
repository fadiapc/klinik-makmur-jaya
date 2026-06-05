# Dokumen Spesifikasi Minimum Server (E-Commerce)
**Sistem E-Commerce & POS Klinik Makmur Jaya**

Dokumen ini merinci spesifikasi *server* yang direkomendasikan berdasarkan perkiraan lalu lintas kunjungan (*traffic*) pada *platform e-commerce* Klinik. Aplikasi dibangun menggunakan arsitektur modern yang efisien: **FastAPI (Python, Asynchronous)** untuk *Backend* dan **React/Vite** untuk *Frontend*.

Walaupun aplikasi ini relatif ringan, pengelolaan *database* transaksional (*PostgreSQL*) membutuhkan *resource* yang stabil agar performa tidak menurun saat terjadi transaksi secara bersamaan (*concurrent transactions*).

---

## 1. Skala Minimum (Fase Awal / Startup)
**Cocok untuk:**
- Kunjungan: < 500 pengunjung per hari
- Transaksi: < 20 pesanan per hari
- Lingkungan: VPS *All-in-One* (Aplikasi *Frontend*, API *Backend*, dan *Database* disatukan dalam satu server).

**Spesifikasi Server Utama (Minimum Mutlak):**
- **Prosesor (CPU):** 2 vCore (contoh: Intel Xeon Gold atau AMD EPYC generasi terbaru).
- **RAM:** 4 GB DDR4 (Disarankan 2 GB didedikasikan sepenuhnya untuk PostgreSQL *shared_buffers*).
- **Penyimpanan (Storage):** 40 GB NVMe SSD (Penting menggunakan SSD/NVMe agar proses baca/tulis *database* cepat).
- **Jaringan (Bandwidth):** Kecepatan port 1 Gbps, dengan kuota transfer data minimal 1 TB / Bulan.

---

## 2. Skala Menengah (Rekomendasi Standar)
**Cocok untuk:**
- Kunjungan: 1.000 - 5.000 pengunjung per hari
- Transaksi: 50 - 200 pesanan per hari
- Lingkungan: Arsitektur *Tiered* dengan pemisahan antara *Server Aplikasi* dan *Server Database* (sesuai dokumen Arsitektur Perangkat Keras).

**A. Server Aplikasi (Web/API Node):**
- **Prosesor (CPU):** 4 vCore
- **RAM:** 8 GB DDR4
- **Penyimpanan (Storage):** 50 GB NVMe SSD
- **Jaringan (Bandwidth):** Port 1 Gbps. Server ini melayani konten langsung ke peramban pengguna, sehingga *bandwidth outbound* cukup signifikan.

**B. Server Database (PostgreSQL Node):**
- **Prosesor (CPU):** 4 vCore
- **RAM:** 16 GB (Sangat krusial untuk menyimpan *query cache* dan *table indexing* agar akses POS dan Etalase E-Commerce berjalan dalam hitungan milidetik).
- **Penyimpanan (Storage):** 80 GB NVMe SSD.
- **Jaringan (Bandwidth):** Terhubung ke *Aplication Server* melalui jaringan internal (*Private Network*) minimal 1 Gbps.

---

## 3. Skala Tinggi (High Traffic / Promo Event)
**Cocok untuk:**
- Kunjungan: > 10.000 pengunjung per hari secara konstan atau memiliki lonjakan (*spike*) saat ada promo diskon obat-obatan.
- Lingkungan: Arsitektur terdistribusi (*Micro-services-ready* / *Load Balanced*).

**Kebutuhan Infrastruktur:**
- **Load Balancer:** 2 vCPU, 4GB RAM (NGINX/HAProxy) khusus untuk mendistribusikan lalu lintas koneksi.
- **Server Aplikasi (Multi-Node):** Menggunakan minimal 2 hingga 3 VM/Node Server Aplikasi (masing-masing 4 vCPU, 8 GB RAM) yang melayani secara paralel (*Horizontal Scaling*).
- **Server Database Utama:** 8 vCore, 32 GB RAM, 200 GB NVMe SSD.
- **Server Database Replika:** (Spesifikasi sama dengan DB Utama) khusus untuk melayani transaksi *Read-Only* seperti menampilkan halaman "Katalog Produk", sehingga beban utama hanya digunakan untuk transaksi *checkout* atau *update* stok.
- **Object Storage Eksternal:** Menggunakan Amazon S3 atau penyedia lokal setara untuk melayani unggahan gambar produk, bukti transfer, dan foto resep (sehingga menghemat beban penyimpanan di *Server Aplikasi*).
- **Bandwidth:** *Unlimited* Bandwidth dengan tambahan layanan mitigasi DDoS (seperti Cloudflare Pro/Business).

---

## Kesimpulan Teknis

Karena *backend* menggunakan algoritma *asynchronous* (Uvicorn/FastAPI), aplikasi dapat menangani ratusan koneksi secara konkuren (misalnya fitur Notifikasi WebSocket) dengan efisiensi penggunaan CPU dan RAM yang sangat tinggi pada *Aplication Node*. 

Satu-satunya **potensi penyempitan (bottleneck)** pada sistem E-commerce ini terletak pada proses pembaruan stok obat dan penambahan entri log audit, yang sangat bergantung pada kinerja penyimpanan. **Oleh karena itu, prioritas investasi perangkat keras sebaiknya dialokasikan pada penggunaan *Storage NVMe SSD* yang cepat dan kapasitas *RAM yang besar* untuk server *Database*.**
