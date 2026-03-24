"""
Seed script for transaction categories with EN/ID localization.
Run with: source venv/bin/activate && python seed_categories.py
"""
import asyncio
import os
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://root:password@localhost/fintrack")

# (id_name, en_name, [subcategories as (id_name, en_name)])
SEED_DATA = [
    ("acara sosial", "Social Events", [
        ("amal dan donasi", "Charity & Donations"),
        ("hadiah", "Gifts"),
        ("pemakaman", "Funeral"),
        ("pernikahan", "Wedding"),
    ]),
    ("belanja", "Shopping", [
        ("belanja bulanan", "Monthly Groceries"),
        ("fashion", "Fashion"),
        ("gadget & elektronik", "Gadgets & Electronics"),
    ]),
    ("cicilan", "Installments", [
        ("kendaraan", "Vehicle"),
        ("pinjaman", "Loan"),
        ("rumah", "House"),
    ]),
    ("hiburan", "Entertainment", [
        ("film/musk", "Movies/Music"),
        ("games", "Games"),
        ("hobi", "Hobbies"),
        ("konser", "Concert"),
        ("layanan streaming", "Streaming Services"),
        ("liburan", "Vacation"),
        ("nogkrong", "Hangout"),
    ]),
    ("keluarga", "Family", [
        ("asisten rumah tangga", "Household Assistant"),
        ("kebutuhan anak", "Children's Needs"),
        ("kebutuhan orang tua", "Parents' Needs"),
        ("laundry", "Laundry"),
        ("peliharaan", "Pets"),
        ("renovasi", "Home Renovation"),
    ]),
    ("kesehatan", "Health", [
        ("biaya dokter", "Doctor's Fee"),
        ("gym/fitnes", "Gym/Fitness"),
        ("obat", "Medicine"),
        ("olahraga", "Sports"),
        ("perawatan diri", "Personal Care"),
    ]),
    ("makanan & minuman", "Food & Beverages", [
        ("kafe", "Cafe"),
        ("pesanan makanan", "Food Delivery"),
        ("restoran", "Restaurant"),
    ]),
    ("pembayaran pinjaman", "Loan Payment", []),
    ("pendidikan", "Education", [
        ("buku", "Books"),
        ("uang sekolah/kuliah", "Tuition Fees"),
    ]),
    ("tabungan", "Savings", [
        ("dana darurat", "Emergency Fund"),
        ("investasi", "Investment"),
        ("liburan", "Vacation Fund"),
        ("pendidikan", "Education Fund"),
        ("pensiun", "Retirement"),
        ("rumah/apartemen", "House/Apartment"),
    ]),
    ("tagihan", "Bills", [
        ("air", "Water Bill"),
        ("asuransi", "Insurance"),
        ("biaya pemeliharaan", "Maintenance Fee"),
        ("gas", "Gas Bill"),
        ("internet", "Internet"),
        ("kartu kredit", "Credit Card"),
        ("langganan", "Subscription"),
        ("listrik", "Electricity"),
        ("pulsa & data", "Mobile Data"),
        ("sewa", "Rent"),
        ("tv kabel", "Cable TV"),
        ("telepon rumah", "Home Phone"),
    ]),
    ("titipan pembayaran pinjaman", "Loan Payment Escrow", []),
    ("top up", "Top Up", [
        ("Brizzi BRI", "Brizzi BRI"),
        ("Dana", "Dana"),
        ("Flazz BCA", "Flazz BCA"),
        ("GoPay", "GoPay"),
        ("LinkAja", "LinkAja"),
        ("Mandiri E-money", "Mandiri E-money"),
        ("ovo", "OVO"),
        ("shopeepay", "ShopeePay"),
        ("tapcash", "TapCash"),
    ]),
    ("transportasi", "Transportation", [
        ("bensin", "Fuel"),
        ("biaya parkir", "Parking Fee"),
        ("servis kendaraan", "Vehicle Service"),
        ("taksi ojol", "Ride-Hailing"),
        ("tiket perjalanan", "Travel Ticket"),
        ("transportasi publik", "Public Transport"),
    ]),
    ("lainnya", "Others", [
        ("biaya", "Fee"),
        ("pajak", "Tax"),
        ("pelunasan", "Settlement"),
        ("tarik tunai", "Cash Withdrawal"),
        ("top up kartu", "Card Top-Up"),
        ("uang keluar", "Outgoing Money"),
    ]),
]


async def add_name_en_column():
    """Add name_en column if not exists"""
    engine = create_async_engine(DATABASE_URL, echo=False)
    async with engine.begin() as conn:
        await conn.execute(text(
            "ALTER TABLE categories ADD COLUMN IF NOT EXISTS name_en VARCHAR(100)"
        ))
    print("✓ name_en column ensured.")


async def seed():
    engine = create_async_engine(DATABASE_URL, echo=False)
    system_user_id = 1

    async with engine.begin() as conn:
        for (cat_id_name, cat_en_name, subs) in SEED_DATA:
            # Upsert parent category
            res = await conn.execute(text(
                "SELECT id FROM categories WHERE name = :name AND user_id = :uid AND parent_id IS NULL LIMIT 1"
            ), {"name": cat_id_name, "uid": system_user_id})
            row = res.fetchone()

            if row:
                parent_id = row[0]
                await conn.execute(text(
                    "UPDATE categories SET name_en = :en WHERE id = :id"
                ), {"en": cat_en_name, "id": parent_id})
            else:
                res = await conn.execute(text(
                    "INSERT INTO categories (user_id, name, name_en, type, created_at, updated_at) "
                    "VALUES (:uid, :name, :name_en, 'expense', NOW(), NOW()) RETURNING id"
                ), {"uid": system_user_id, "name": cat_id_name, "name_en": cat_en_name})
                parent_id = res.fetchone()[0]

            # Upsert subcategories
            for (sub_id_name, sub_en_name) in subs:
                res = await conn.execute(text(
                    "SELECT id FROM categories WHERE name = :name AND parent_id = :pid LIMIT 1"
                ), {"name": sub_id_name, "pid": parent_id})
                row = res.fetchone()

                if row:
                    await conn.execute(text(
                        "UPDATE categories SET name_en = :en WHERE id = :id"
                    ), {"en": sub_en_name, "id": row[0]})
                else:
                    await conn.execute(text(
                        "INSERT INTO categories (user_id, parent_id, name, name_en, type, created_at, updated_at) "
                        "VALUES (:uid, :pid, :name, :name_en, 'expense', NOW(), NOW())"
                    ), {"uid": system_user_id, "pid": parent_id,
                        "name": sub_id_name, "name_en": sub_en_name})

    print(f"✓ Seeded {len(SEED_DATA)} categories with EN/ID translations.")


if __name__ == "__main__":
    asyncio.run(add_name_en_column())
    asyncio.run(seed())
