# BerWisata

Platform pencarian & rekomendasi destinasi wisata **Hidden Gem di Indonesia** berbasis
Artificial Intelligence, Machine Learning, Geolocation, dan Real-Time Location Tracking.

## Fitur Utama

- Search engine multi-filter (nama, provinsi, kabupaten, kategori, harga, rating, radius, jam operasional, fasilitas, budget)
- Rekomendasi AI berbasis model **Random Forest** (Hidden Gem Score 0–100)
- Real-time location tracking via HTML5 Geolocation (`watchPosition`) + WebSocket
- Peta **Leaflet + OpenStreetMap**, marker cluster, polyline rute
- Rute & ETA via **OpenRouteService API** (mobil/motor/kaki/sepeda), fallback Haversine
- Cuaca real-time via **Open-Meteo** (suhu, angin, kelembaban, kondisi)
- Autentikasi JWT + Refresh Token + role authorization (admin/user)
- Favorit, rating & riwayat pencarian per user
- Admin: CRUD destinasi/kategori/user/galeri, upload foto, import/export CSV, retrain ML, statistik
