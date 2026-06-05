# Diagram Kelas (Class Diagram)
**Sistem E-Commerce & POS Klinik Makmur Jaya**

Dokumen ini mendeskripsikan secara teknis Entitas Database (*SQLAlchemy ORM Models*) beserta hubungan kardinalitas antar-entitas (1:1, 1:M, M:M) yang menopang logika bisnis aplikasi.

---

## Diagram Model Data

Berikut adalah visualisasi struktur *Database* menggunakan representasi *Class Diagram*:

```mermaid
classDiagram
    %% =======================
    %% Enumerations
    %% =======================
    class OrderStatus {
        <<enumeration>>
        MENUNGGU_VERIFIKASI_RESEP
        MENUNGGU_PEMBAYARAN
        MENUNGGU_KONFIRMASI_KASIR
        DIPROSES
        DIKIRIM
        SELESAI
        DIBATALKAN
    }

    class OrderType {
        <<enumeration>>
        ONLINE
        COUNTER
    }

    class PaymentMethod {
        <<enumeration>>
        CASH
        TRANSFER
        QRIS
    }

    class PrescriptionStatus {
        <<enumeration>>
        PENDING
        APPROVED
        REJECTED
    }

    %% =======================
    %% Core Entities
    %% =======================
    class Role {
        +Integer id
        +String name
        +String description
        +DateTime created_at
        +DateTime updated_at
    }

    class Category {
        +Integer id
        +String name
        +Text description
        +Boolean is_active
        +DateTime created_at
        +DateTime updated_at
    }

    class Supplier {
        +Integer id
        +String name
        +String contact_person
        +String phone
        +Text address
        +DateTime created_at
        +DateTime updated_at
    }

    class User {
        +UUID id
        +Integer role_id
        +String email
        +String password_hash
        +String name
        +String phone
        +Text address
        +Boolean is_active
        +DateTime created_at
        +DateTime updated_at
    }

    class Product {
        +UUID id
        +Integer category_id
        +Integer supplier_id
        +String sku
        +String name
        +Text description
        +String image_url
        +Numeric base_price
        +Numeric selling_price
        +Integer current_stock
        +Integer min_stock
        +Boolean is_prescription_required
        +Boolean is_active
        +DateTime created_at
        +DateTime updated_at
    }

    class ProductBatch {
        +UUID id
        +UUID product_id
        +String batch_number
        +Date expiration_date
        +Integer initial_quantity
        +Integer remaining_quantity
        +Boolean is_active
        +DateTime created_at
        +DateTime updated_at
    }

    class Order {
        +UUID id
        +String order_number
        +UUID user_id
        +OrderType order_type
        +OrderStatus status
        +PaymentMethod payment_method
        +String payment_status
        +String proof_of_payment_url
        +Numeric total_amount
        +Text notes
        +DateTime created_at
        +DateTime updated_at
    }

    class OrderItem {
        +UUID id
        +UUID order_id
        +UUID product_id
        +Integer quantity
        +Numeric unit_price
        +Numeric subtotal
    }

    class Prescription {
        +UUID id
        +UUID order_id
        +String image_url
        +PrescriptionStatus status
        +Text pharmacist_notes
        +DateTime created_at
        +DateTime updated_at
    }

    class Notification {
        +UUID id
        +UUID user_id
        +String title
        +Text message
        +String level
        +String type
        +String link
        +Boolean is_read
        +DateTime created_at
    }

    class AuditLog {
        +UUID id
        +UUID user_id
        +String action
        +String entity_type
        +String entity_id
        +JSONB old_value
        +JSONB new_value
        +String ip_address
        +DateTime created_at
    }

    %% =======================
    %% Relationships
    %% =======================
    Role "1" -- "*" User : memiliki
    Category "1" -- "*" Product : mengklasifikasikan
    Supplier "1" -- "*" Product : memasok
    
    User "1" -- "*" Order : melakukan
    User "1" -- "*" Notification : menerima
    User "1" -- "*" AuditLog : melakukan aktivitas
    
    Product "1" -- "*" ProductBatch : terdiri dari
    Product "1" -- "*" OrderItem : masuk dalam
    
    Order "1" -- "*" OrderItem : berisi
    Order "1" -- "1" Prescription : wajib melampirkan (jika obat keras)
```

---

## Keterangan Relasi

1. **User (Pengguna) & Role (Peran): `(M:1)`**
   Setiap Pengguna di sistem wajib memiliki persis satu peran (misalnya: *Admin*, *Kasir*, *Pasien*), sedangkan satu peran dapat dimiliki oleh banyak Pengguna.

2. **Product (Produk) & Category/Supplier: `(M:1)`**
   Setiap Produk tergabung dalam satu Kategori dan disuplai oleh satu *Supplier* Utama. Hal ini memudahkan rekapitulasi data barang saat restok.

3. **Product (Produk) & ProductBatch: `(1:M)`**
   Untuk menerapkan sistem peringatan kedaluwarsa secara spesifik, satu jenis Produk (misal: Paracetamol) dapat memiliki banyak *Batch* (dengan nomor *batch* dan tanggal kedaluwarsa yang berbeda-beda). Sisa stok pada `Product` adalah kalkulasi dinamis atau agregasi dari total *remaining quantity* pada seluruh *batch* aktifnya.

4. **Order (Pesanan) & OrderItem: `(1:M)`**
   Sebuah *Order* atau struk belanja dapat berisi banyak baris item belanjaan (*OrderItem*), di mana setiap *OrderItem* mereferensikan satu `Product` spesifik beserta jumlah (*quantity*) dan subtotal harganya.

5. **Order (Pesanan) & Prescription (Resep): `(1:1)`**
   Jika pesanan memuat minimal satu produk berlabel *Obat Keras* (`is_prescription_required = True`), maka pesanan tersebut wajib memiliki tepat 1 entitas *Prescription* terlampir yang berisi foto unggahan resep dokter untuk diverifikasi oleh Apoteker.

6. **AuditLog & Notification**
   Semua log audit dan notifikasi terhubung langsung ke entitas Pengguna (`User`). *Audit Log* menyimpan jejak langkah (sebelum vs sesudah dalam format *JSONB*) dari sebuah aksi untuk akuntabilitas, sedangkan *Notification* menyimpan pesan pemberitahuan persisten.
