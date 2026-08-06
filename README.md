# BerWisata

Platform pencarian & rekomendasi destinasi wisata **Hidden Gem di Indonesia** berbasis
Artificial Intelligence, Machine Learning, Geolocation, dan Real-Time Location Tracking.

![stack](https://img.shields.io/badge/stack-FastAPI%20%7C%20React%20%7C%20PostgreSQL%20%7C%20ML-blue)

## Fitur Utama

- 🔍 Search engine multi-filter (nama, provinsi, kabupaten, kategori, harga, rating, radius, jam operasional, fasilitas, budget)
- 🤖 Rekomendasi AI berbasis model **Random Forest** (Hidden Gem Score 0–100)
- 📍 Real-time location tracking via HTML5 Geolocation (`watchPosition`) + WebSocket
- 🗺️ Peta **Leaflet + OpenStreetMap**, marker cluster, polyline rute
- 🛣️ Rute & ETA via **OpenRouteService API** (mobil/motor/kaki/sepeda), fallback Haversine
- 🌦️ Cuaca real-time via **Open-Meteo** (suhu, angin, kelembaban, kondisi)
- 🔐 Autentikasi JWT + Refresh Token + role authorization (admin/user)
- ❤️ Favorit, rating & riwayat pencarian per user
- 👨‍💼 Admin: CRUD destinasi/kategori/user/galeri, upload foto, import/export CSV, retrain ML, statistik

## Arsitektur

```
berwisata/
├── docker-compose.yml
├── backend/
│   ├── app/
│   │   ├── api/v1/routers/    # REST + WebSocket endpoints
│   │   ├── controllers/       # request handling & orchestration
│   │   ├── services/          # business logic (auth, ml, map, weather, ...)
│   │   ├── repositories/      # data access layer
│   │   ├── models/            # SQLAlchemy models
│   │   ├── schemas/           # Pydantic schemas
│   │   ├── core/              # config, security, logging, exceptions
│   │   └── ml/                # training pipeline + serialized model
│   ├── alembic/               # database migrations
│   ├── scripts/               # dataset generator + seed
│   ├── tests/                 # pytest (41 tests)
│   └── uploads/               # uploaded images (volume)
├── frontend/
│   └── src/                   # React + Vite + Tailwind
└── .env.example
```

## Quick Start (Docker)

```bash
cp .env.example .env
# isi ORS_API_KEY (OpenRouteService) jika ingin rute/navigasi penuh

docker compose up --build
```

- Frontend: http://localhost:8080
- Backend API: http://localhost:8000
- Swagger docs: http://localhost:8000/docs

Akun admin seed: `admin@berwisata.id` / `Admin@1234`

## Development (tanpa Docker)

Backend dapat berjalan di atas SQLite untuk pengembangan cepat:

```bash
# Backend
cd backend
python -m venv .venv && .venv/Scripts/activate
pip install -r requirements.txt

# (opsional) mode SQLite — buat skema lalu seed
$env:DATABASE_URL="sqlite:///./dev.db"   # PowerShell
python -c "from app.database.session import Base, engine; import app.models; Base.metadata.create_all(engine)"
python scripts/seed.py

# jalankan API
uvicorn app.main:app --reload

# Frontend (terminal terpisah)
cd frontend
npm install
npm run dev
```

Dengan PostgreSQL + Alembic:

```bash
cd backend
alembic upgrade head
python scripts/seed.py
uvicorn app.main:app --reload
```

## Tests

```bash
cd backend
python -m pytest tests -q    # 41 passed
```

## Machine Learning

Dataset realistis ±6.000 destinasi (dibangkitkan dengan pola sebaran 38 provinsi Indonesia).
Model Random Forest dilatih dengan fitur: kategori, rating, jumlah review, harga, popularitas,
latitude, longitude, jumlah pengunjung, fasilitas, keamanan, kebersihan, keindahan, akses jalan,
jam operasional, provinsi, kabupaten → output **Hidden Gem Score (0–100)**.
Hasil latih: R²=0.8185, MAE=2.76, 85% prediksi dalam ±5 poin.

Retrain dari Admin Dashboard atau:

```bash
cd backend
python -m app.ml.train --data app/ml/data/destinations.csv
```
