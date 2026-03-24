-- Create ENUMs for common types
CREATE TYPE transaction_type AS ENUM ('income', 'expense');
CREATE TYPE debt_status AS ENUM ('unpaid', 'partially_paid', 'paid');
CREATE TYPE goal_status AS ENUM ('in_progress', 'completed', 'cancelled');
CREATE TYPE notification_status AS ENUM ('unread', 'read');

-- 1. Categories Table
CREATE TABLE categories (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    type transaction_type NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. Transactions Table
CREATE TABLE transactions (
    id SERIAL PRIMARY KEY,
    category_id INT REFERENCES categories(id) ON DELETE SET NULL,
    amount DECIMAL(15, 2) NOT NULL,
    type transaction_type NOT NULL,
    description TEXT,
    transaction_date DATE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 3. Debts Table (Utang - Uang yang kita pinjam dari orang)
CREATE TABLE debts (
    id SERIAL PRIMARY KEY,
    creditor_name VARCHAR(100) NOT NULL,
    amount DECIMAL(15, 2) NOT NULL,
    remaining_amount DECIMAL(15, 2) NOT NULL,
    due_date DATE,
    status debt_status DEFAULT 'unpaid',
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 4. Receivables Table (Piutang - Uang kita yang dipinjam orang)
CREATE TABLE receivables (
    id SERIAL PRIMARY KEY,
    debtor_name VARCHAR(100) NOT NULL,
    amount DECIMAL(15, 2) NOT NULL,
    remaining_amount DECIMAL(15, 2) NOT NULL,
    due_date DATE,
    status debt_status DEFAULT 'unpaid',
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 5. Financial Goals Table (Tujuan Keuangan)
CREATE TABLE financial_goals (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    target_amount DECIMAL(15, 2) NOT NULL,
    current_amount DECIMAL(15, 2) DEFAULT 0,
    target_date DATE,
    status goal_status DEFAULT 'in_progress',
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- INDEXES
CREATE INDEX idx_transactions_date ON transactions(transaction_date);
CREATE INDEX idx_transactions_type ON transactions(type);

-- ==========================================
-- SEED DATA
-- ==========================================

-- Seed Categories
INSERT INTO categories (name, type, description) VALUES
('Gaji', 'income', 'Gaji bulanan dari pekerjaan utama'),
('Bonus', 'income', 'Bonus tahunan atau proyek'),
('Pemberian', 'income', 'Pemberian dari keluarga/teman'),
('Makan & Minum', 'expense', 'Pengeluaran untuk makanan dan minuman sehari-hari'),
('Transportasi', 'expense', 'Bensin, tol, tiket KRL/Bus'),
('Tagihan & Utilitas', 'expense', 'Listrik, Air, Internet, dll'),
('Hiburan', 'expense', 'Nonton, langganan streaming, liburan'),
('Kesehatan', 'expense', 'Obat, dokter, asuransi kesehatan');

-- Seed Transactions
INSERT INTO transactions (category_id, amount, type, description, transaction_date) VALUES
(1, 10000000.00, 'income', 'Gaji Bulan Oktober', CURRENT_DATE - INTERVAL '5 days'),
(4, 50000.00, 'expense', 'Makan Siang Nasi Padang', CURRENT_DATE - INTERVAL '2 days'),
(5, 100000.00, 'expense', 'Isi Bensin Motor', CURRENT_DATE - INTERVAL '1 day'),
(6, 350000.00, 'expense', 'Bayar Listrik Bulanan', CURRENT_DATE);

-- Seed Debts
INSERT INTO debts (creditor_name, amount, remaining_amount, due_date, status, description) VALUES
('Bank ABC', 5000000.00, 4000000.00, CURRENT_DATE + INTERVAL '30 days', 'partially_paid', 'Cicilan Motor'),
('Budi', 500000.00, 500000.00, CURRENT_DATE + INTERVAL '7 days', 'unpaid', 'Pinjam darurat untuk servis laptop');

-- Seed Receivables
INSERT INTO receivables (debtor_name, amount, remaining_amount, due_date, status, description) VALUES
('Andi', 200000.00, 200000.00, CURRENT_DATE + INTERVAL '14 days', 'unpaid', 'Bayarin makan siang yang kurang'),
('Siti', 1000000.00, 500000.00, CURRENT_DATE + INTERVAL '60 days', 'partially_paid', 'Pinjam untuk modal usaha kecil');

-- Seed Financial Goals
INSERT INTO financial_goals (name, target_amount, current_amount, target_date, status, description) VALUES
('Dana Darurat', 30000000.00, 10000000.00, CURRENT_DATE + INTERVAL '365 days', 'in_progress', 'Kumpulkan dana darurat 3x biaya hidup bulanan'),
('Liburan ke Bali', 5000000.00, 1500000.00, CURRENT_DATE + INTERVAL '180 days', 'in_progress', 'Tabungan liburan akhir tahun');
