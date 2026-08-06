"""Seed the BerWisata database: admin user, categories, destinations from CSV.

Usage:
    python scripts/seed.py                 # full seed
    python scripts/seed.py --if-empty      # only seed when destinations table is empty
    python scripts/seed.py --data path/to/destinations.csv
"""
import argparse
import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import func, select  # noqa: E402

from app.core.security import hash_password  # noqa: E402
from app.database.session import SessionLocal  # noqa: E402
from app.models import Category, Destination, User  # noqa: E402
from app.controllers import admin_controller  # noqa: E402

CATEGORIES = [
    ("Gunung", "gunung", "Pendakian dan pemandangan dari puncak", "mountain"),
    ("Bukit", "bukit", "Bukit dengan panorama indah", "hill"),
    ("Pantai", "pantai", "Pantai pasir putih dan laut", "beach"),
    ("Pulau", "pulau", "Pulau eksotis dengan laut jernih", "island"),
    ("Air Terjun", "air-terjun", "Air terjun yang menyegarkan", "waterfall"),
    ("Curug", "curug", "Curug dan air terjun kecil", "waterfall"),
    ("Danau", "danau", "Danau dan telaga yang tenang", "lake"),
    ("Camping", "camping", "Area camping dan glamping", "tent"),
    ("Tracking", "tracking", "Jalur trekking dan hiking", "trail"),
    ("Sunrise", "sunrise", "Spot pemandangan matahari terbit", "sunrise"),
    ("Sunset", "sunset", "Spot pemandangan matahari terbenam", "sunset"),
    ("Gua", "gua", "Gua dan karst yang menakjubkan", "cave"),
    ("Taman", "taman", "Taman dan kebun wisata", "park"),
    ("Desa Wisata", "desa-wisata", "Desa dengan budaya dan alam", "village"),
    ("Pemandian", "pemandian", "Pemandian air alami", "bath"),
]

ADMIN_EMAIL = "admin@berwisata.id"
ADMIN_PASSWORD = "Admin@1234"


def seed_categories(db) -> None:
    existing = {c.slug for c in db.scalars(select(Category)).all()}
    count = 0
    for name, slug, desc, icon in CATEGORIES:
        if slug not in existing:
            db.add(Category(name=name, slug=slug, description=desc, icon=icon, sort_order=len(existing) + count))
            count += 1
    db.commit()
    print(f"Categories: {count} added")


def seed_admin(db) -> None:
    user = db.scalars(select(User).where(User.email == ADMIN_EMAIL)).first()
    if not user:
        db.add(User(
            email=ADMIN_EMAIL,
            username="admin",
            full_name="Administrator BerWisata",
            password_hash=hash_password(ADMIN_PASSWORD),
            role="admin",
            is_active=True,
            is_verified=True,
        ))
        db.commit()
        print(f"Admin created: {ADMIN_EMAIL} / {ADMIN_PASSWORD}")
    else:
        print("Admin already exists")


def seed_destinations(db, data_path: Path, force: bool = False) -> None:
    total = int(db.scalar(select(func.count(Destination.id))) or 0)
    if total > 0 and not force:
        print(f"Destinations already seeded ({total} rows), skipping (use --force to re-import)")
        return
    if not data_path.exists():
        print(f"Dataset not found at {data_path}")
        print("Generate it first: python scripts/generate_dataset.py")
        raise SystemExit(1)

    if force and total > 0:
        db.query(Destination).delete(synchronize_session=False)
        db.commit()
        print(f"Cleared {total} old destinations (favorites/ratings/images follow via FK cascade)")

    content = data_path.read_text(encoding="utf-8")
    result = admin_controller.import_csv(db, content)
    print(f"Destinations imported: {result['imported']} (skipped {result['skipped']})")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--if-empty", action="store_true", help="Only seed when DB is empty")
    parser.add_argument("--force", action="store_true", help="Force re-import destinations")
    parser.add_argument("--data", default="app/ml/data/destinations.csv")
    args = parser.parse_args()

    db = SessionLocal()
    try:
        total = int(db.scalar(select(func.count(Destination.id))) or 0)
        if args.if_empty and total > 0:
            print("Database already has destinations, seeding skipped")
            return

        seed_categories(db)
        seed_admin(db)
        seed_destinations(db, Path(args.data), force=args.force)
        print("Seeding complete.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
