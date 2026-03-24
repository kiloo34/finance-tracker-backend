# 🚀 Finance Tracker Backend (FinancePro API)

Ini adalah repositori backend untuk aplikasi **Finance Tracker**. Dibangun dengan arsitektur modern menggunakan Python dan framework **FastAPI**, backend ini menyediakan API yang cepat, aman, dan asinkron untuk mengelola keuangan pribadi, mulai dari pencatatan transaksi sehari-hari, transfer antar saku (pocket), pengelolaan hutang/piutang (obligations), hingga evaluasi kesehatan finansial.

---

## ✨ Fitur Utama

- **Otentikasi Aman**: Registrasi & login menggunakan JWT Bearer Token dengan hashing password menggunakan `passlib` & `bcrypt`.
- **Manajemen Akun & Saku (Pockets)**: Mendukung multi-akun bank dan pembuatan banyak "Saku" (pockets) di dalam satu akun (misal: Saku Tabungan, Saku Pengeluaran), lengkap dengan fitur transfer antar saku.
- **Pencatatan Transaksi**: Mencatat pemasukan (income) dan pengeluaran (expense), serta eksport data ke bentuk `CSV`.
- **Manajemen Anggaran (Budgets)**: Pembuatan batas pengeluaran bulanan berdasarkan kategori.
- **Tujuan Finansial (Goals)**: Menabung untuk target tertentu (misal: Dana Darurat, Beli Kendaraan) dengan sistem pelacakan progress.
- **Hutang & Piutang (Obligations)**: Mencatat uang yang dipinjamkan ke orang lain (receivable) dan hutang ke pihak lain (debt) beserta cicilannya.
- **Evaluasi Kesehatan Finansial**: Endpoint khusus untuk mengkalkulasi rasio tabungan (saving rate) dan debt-to-income ratio (DTI).
- **Notifikasi & Log Audit**: Mengingatkan jatuh tempo cicilan otomatis (background jobs) dan log lengkap untuk memonitor seluruh aksi user di dalam sistem.

---

## 🛠️ Teknologi yang Digunakan

- **Framework**: [FastAPI](https://fastapi.tiangolo.com/) (Python 3.11+)
- **Database**: PostgreSQL 15
- **ORM & Database Toolkit**: SQLAlchemy (Async) & Alembic (untuk Auto-Migrations)
- **Validation & Settings**: Pydantic v2
- **Keamanan & Rate Limiting**: SlowAPI, Python-JOSE (JWT)
- **Deployment**: Docker & Docker Compose

---

## 🚀 Instalasi & Persiapan (Local Development)

### 1. Prasyarat
Pastikan Anda sudah menginstal:
- Python 3.11 atau lebih baru
- PostgreSQL 14 atau lebih baru

### 2. Kloning & Virtual Environment
```bash
git clone git@github.com:kiloo34/finance-tracker-backend.git
cd finance-tracker-backend

# Buat virtual environment
python -m venv venv
source venv/bin/activate  # Untuk Windows: venv\Scripts\activate

# Instal semua dependensi
pip install -r requirements.txt
```

### 3. Konfigurasi Environment
Buat file `.env` di direktori root dengan menyalin format dari `.env.example`:
```env
DATABASE_URL=postgresql+asyncpg://postgres:password@localhost:5432/fintrack
SECRET_KEY=kunci_rahasia_anda
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
```

### 4. Setup Database
Jalankan migrasi Alembic untuk membuat semua tabel ke dalam database:
```bash
alembic upgrade head
```
*(Opsional)* Anda dapat mengisi database dengan kategori dan user default (Admin: `admin`/`admin123`, User: `user1`/`user123`) dengan cara:
```bash
python seed_categories.py
python seed_users.py
```

### 5. Menjalankan Aplikasi
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```
API akan berjalan pada `http://localhost:8000`.

---

## 🐳 Menggunakan Docker


Gunakan Docker untuk menjalankan aplikasi dan database PostgreSQL sekaligus tanpa harus konfigurasi manual:

```bash
docker-compose up --build -d
```
Service akan langsung berjalan, dan Anda dapat mengakses API di port `8000`.

---

## 📖 Dokumentasi API Lengkap

- **Swagger UI (Interaktif)**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

Untuk panduan penggunaan dari setiap endpoint (Auth, Transaksi, Budgets, dll), silakan baca file:
👉 **[USER_MANUAL.md](./USER_MANUAL.md)**

---

## 🧪 Testing

Jalankan serangkaian pengujian unit menggunakan pytest:
```bash
pytest
```
Untuk menjalankan beserta laporan *coverage*:
```bash
pytest --cov=app tests/
```
