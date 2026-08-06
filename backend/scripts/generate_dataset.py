"""
Realistic dataset generator for BerWisata.

Generates ~6000 Indonesian tourism destinations across all provinces with
realistic features, coordinates and ground-truth Hidden Gem Score used to
supervise the Random Forest model.

Locations are geographically coherent: every destination is placed in a real
kabupaten/kota of the right province, addresses use the correct Kabupaten /
Kota / Kota Administrasi prefix, coastal categories (pantai, pulau, sunset)
only appear in coastal regencies, and generated names never borrow a specific
place word from another region (e.g. "Dieng" is only ever Jawa Tengah).

Usage:
    python scripts/generate_dataset.py --output app/ml/data/destinations.csv --rows 6000 --seed 42
"""
import argparse
import csv
import random
import sys
import zlib
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# ---------------------------------------------------------------------------
# Geography
# ---------------------------------------------------------------------------
# province: {
#   "bbox": (lat_min, lat_max, lon_min, lon_max),
#   "coastal": [regencies on the sea / islands ...],
#   "inland":   [...],
# }
# All names are real kabupaten / kota (current 2022 administrative division).
COASTAL_CATEGORIES = {"pantai", "pulau", "sunset"}

PROVINCES = {
    "Aceh": {
        "bbox": (1.5, 5.8, 95.0, 98.5),
        "coastal": [
            "Kota Banda Aceh", "Kota Sabang", "Kota Lhokseumawe", "Kota Langsa",
            "Aceh Besar", "Pidie", "Pidie Jaya", "Bireuen", "Aceh Utara", "Aceh Timur",
            "Aceh Tamiang", "Aceh Jaya", "Aceh Barat", "Nagan Raya", "Aceh Barat Daya",
            "Aceh Selatan", "Aceh Singkil", "Simeulue",
        ],
        "inland": [
            "Aceh Tengah", "Aceh Tenggara", "Gayo Lues", "Bener Meriah", "Kota Subulussalam",
        ],
    },
    "Sumatera Utara": {
        "bbox": (0.0, 4.2, 97.0, 100.6),
        "coastal": [
            "Kota Medan", "Kota Tebing Tinggi", "Kota Sibolga", "Kota Tanjungbalai",
            "Kota Gunungsitoli", "Deli Serdang", "Serdang Bedagai", "Langkat", "Batu Bara",
            "Asahan", "Labuhanbatu", "Labuhanbatu Utara", "Labuhanbatu Selatan",
            "Tapanuli Tengah", "Tapanuli Selatan", "Mandailing Natal",
            "Nias", "Nias Barat", "Nias Utara", "Nias Selatan",
        ],
        "inland": [
            "Kota Binjai", "Kota Pematangsiantar", "Kota Padangsidimpuan",
            "Karo", "Dairi", "Pakpak Bharat", "Simalungun", "Toba", "Tapanuli Utara",
            "Samosir", "Humbang Hasundutan", "Padang Lawas", "Padang Lawas Utara",
        ],
    },
    "Sumatera Barat": {
        "bbox": (-3.3, 0.9, 98.0, 101.8),
        "coastal": [
            "Kota Padang", "Kota Pariaman", "Padang Pariaman", "Pasaman Barat",
            "Pesisir Selatan", "Kepulauan Mentawai",
        ],
        "inland": [
            "Kota Bukittinggi", "Kota Padangpanjang", "Kota Payakumbuh", "Kota Solok",
            "Kota Sawahlunto", "Agam", "Tanah Datar", "Solok", "Sijunjung",
            "Dharmasraya", "Pasaman", "Lima Puluh Kota",
        ],
    },
    "Riau": {
        "bbox": (-1.5, 2.0, 100.0, 104.0),
        "coastal": [
            "Kota Dumai", "Bengkalis", "Siak", "Pelalawan", "Rokan Hilir",
            "Indragiri Hilir", "Kepulauan Meranti",
        ],
        "inland": [
            "Kota Pekanbaru", "Kampar", "Kuantan Singingi", "Rokan Hulu", "Indragiri Hulu",
        ],
    },
    "Kepulauan Riau": {
        "bbox": (-1.5, 5.0, 103.0, 110.0),
        "coastal": [
            "Kota Batam", "Kota Tanjungpinang", "Bintan", "Karimun", "Natuna",
            "Kepulauan Anambas", "Lingga",
        ],
        "inland": [],
    },
    "Jambi": {
        "bbox": (-3.0, -0.5, 101.0, 104.8),
        "coastal": ["Tanjung Jabung Timur", "Tanjung Jabung Barat", "Muaro Jambi"],
        "inland": [
            "Kota Jambi", "Kerinci", "Merangin", "Sarolangun", "Batanghari", "Tebo", "Bungo",
        ],
    },
    "Sumatera Selatan": {
        "bbox": (-5.2, -1.0, 102.0, 107.0),
        "coastal": ["Kota Palembang", "Banyuasin", "Ogan Komering Ilir", "Ogan Ilir", "Musi Banyuasin"],
        "inland": [
            "Kota Prabumulih", "Kota Pagar Alam", "Kota Lubuklinggau", "Muara Enim", "Lahat",
            "Ogan Komering Ulu", "Ogan Komering Ulu Timur", "Ogan Komering Ulu Selatan",
            "Musi Rawas", "Musi Rawas Utara", "Empat Lawang", "Penukal Abab Lematang Ilir",
        ],
    },
    "Bengkulu": {
        "bbox": (-6.0, -2.0, 101.0, 104.0),
        "coastal": [
            "Kota Bengkulu", "Bengkulu Selatan", "Seluma", "Kaur",
            "Bengkulu Utara", "Mukomuko",
        ],
        "inland": ["Rejang Lebong", "Kepahiang", "Lebong", "Bengkulu Tengah"],
    },
    "Lampung": {
        "bbox": (-6.5, -3.5, 103.0, 106.0),
        "coastal": [
            "Kota Bandar Lampung", "Lampung Selatan", "Pesawaran", "Tanggamus",
            "Pesisir Barat", "Lampung Barat", "Lampung Timur", "Tulang Bawang", "Mesuji",
        ],
        "inland": [
            "Kota Metro", "Lampung Tengah", "Lampung Utara", "Pringsewu", "Way Kanan",
            "Tulang Bawang Barat",
        ],
    },
    "Kepulauan Bangka Belitung": {
        "bbox": (-4.5, -1.0, 105.0, 108.5),
        "coastal": [
            "Kota Pangkalpinang", "Bangka", "Bangka Barat", "Bangka Tengah",
            "Bangka Selatan", "Belitung", "Belitung Timur",
        ],
        "inland": [],
    },
    "DKI Jakarta": {
        "bbox": (-6.4, -6.0, 106.7, 107.0),
        "coastal": ["Kepulauan Seribu", "Jakarta Utara"],
        "inland": ["Jakarta Pusat", "Jakarta Barat", "Jakarta Timur", "Jakarta Selatan"],
    },
    "Banten": {
        "bbox": (-7.2, -5.8, 105.0, 106.8),
        "coastal": [
            "Kota Cilegon", "Kota Serang", "Kota Tangerang", "Serang",
            "Pandeglang", "Lebak", "Tangerang",
        ],
        "inland": ["Kota Tangerang Selatan"],
    },
    "Jawa Barat": {
        "bbox": (-7.9, -5.8, 105.8, 108.7),
        "coastal": [
            "Kota Cirebon", "Kota Bekasi", "Cirebon", "Indramayu", "Subang",
            "Karawang", "Bekasi", "Sukabumi", "Garut", "Tasikmalaya", "Pangandaran",
        ],
        "inland": [
            "Kota Bogor", "Kota Bandung", "Kota Cimahi", "Kota Depok", "Kota Sukabumi",
            "Kota Tasikmalaya", "Kota Banjar", "Bogor", "Bandung", "Bandung Barat",
            "Cianjur", "Purwakarta", "Sumedang", "Majalengka", "Kuningan", "Ciamis",
        ],
    },
    "Jawa Tengah": {
        "bbox": (-8.2, -6.0, 108.5, 111.9),
        "coastal": [
            "Kota Semarang", "Kota Tegal", "Kota Pekalongan", "Semarang", "Kendal",
            "Batang", "Pekalongan", "Pemalang", "Tegal", "Brebes", "Cilacap",
            "Kebumen", "Rembang", "Pati", "Jepara", "Demak",
        ],
        "inland": [
            "Kota Surakarta", "Kota Salatiga", "Kota Magelang", "Magelang", "Temanggung",
            "Wonosobo", "Boyolali", "Karanganyar", "Sragen", "Klaten", "Sukoharjo",
            "Wonogiri", "Banjarnegara", "Purworejo", "Blora", "Grobogan", "Kudus",
        ],
    },
    "DI Yogyakarta": {
        "bbox": (-8.3, -7.5, 109.9, 110.9),
        "coastal": ["Bantul", "Gunungkidul", "Kulon Progo"],
        "inland": ["Kota Yogyakarta", "Sleman"],
    },
    "Jawa Timur": {
        "bbox": (-8.8, -7.0, 111.0, 114.7),
        "coastal": [
            "Kota Surabaya", "Kota Pasuruan", "Kota Probolinggo", "Sidoarjo", "Gresik",
            "Lamongan", "Tuban", "Bangkalan", "Sampang", "Pamekasan", "Sumenep",
            "Pasuruan", "Probolinggo", "Situbondo", "Banyuwangi", "Jember", "Lumajang",
            "Malang", "Tulungagung", "Trenggalek", "Pacitan",
        ],
        "inland": [
            "Kota Malang", "Kota Kediri", "Kota Blitar", "Kota Madiun", "Kota Mojokerto",
            "Batu", "Blitar", "Kediri", "Mojokerto", "Nganjuk", "Madiun", "Magetan",
            "Ngawi", "Ponorogo", "Bojonegoro", "Bondowoso", "Jombang",
        ],
    },
    "Bali": {
        "bbox": (-9.0, -8.0, 114.0, 115.8),
        "coastal": [
            "Kota Denpasar", "Badung", "Buleleng", "Karangasem", "Jembrana",
            "Klungkung", "Tabanan",
        ],
        "inland": ["Bangli", "Gianyar"],
    },
    "Nusa Tenggara Barat": {
        "bbox": (-9.5, -8.0, 115.8, 119.2),
        "coastal": [
            "Kota Mataram", "Kota Bima", "Lombok Barat", "Lombok Utara", "Lombok Tengah",
            "Lombok Timur", "Sumbawa", "Sumbawa Barat", "Dompu", "Bima",
        ],
        "inland": [],
    },
    "Nusa Tenggara Timur": {
        "bbox": (-11.2, -8.0, 118.0, 125.2),
        "coastal": [
            "Kota Kupang", "Kupang", "Sumba Barat", "Sumba Timur", "Sumba Tengah",
            "Sumba Barat Daya", "Manggarai", "Manggarai Barat", "Manggarai Timur",
            "Ngada", "Nagekeo", "Ende", "Sikka", "Flores Timur", "Lembata", "Alor",
            "Rote Ndao", "Sabu Raijua", "Belu", "Malaka",
        ],
        "inland": ["Timor Tengah Selatan", "Timor Tengah Utara"],
    },
    "Kalimantan Barat": {
        "bbox": (-3.0, 2.0, 108.0, 114.5),
        "coastal": [
            "Kota Pontianak", "Kota Singkawang", "Pontianak", "Mempawah", "Kubu Raya",
            "Sambas", "Bengkayang", "Ketapang", "Kayong Utara",
        ],
        "inland": [
            "Landak", "Sanggau", "Sintang", "Kapuas Hulu", "Sekadau", "Melawi",
        ],
    },
    "Kalimantan Tengah": {
        "bbox": (-4.0, -0.5, 110.0, 116.0),
        "coastal": ["Kotawaringin Barat", "Kotawaringin Timur", "Seruyan", "Sukamara", "Pulang Pisau"],
        "inland": [
            "Kota Palangka Raya", "Katingan", "Kapuas", "Gunung Mas", "Barito Selatan",
            "Barito Timur", "Barito Utara", "Murung Raya", "Lamandau",
        ],
    },
    "Kalimantan Selatan": {
        "bbox": (-4.3, -1.0, 114.0, 116.5),
        "coastal": ["Kota Banjarmasin", "Tanah Laut", "Tanah Bumbu", "Kotabaru", "Barito Kuala"],
        "inland": [
            "Kota Banjarbaru", "Banjar", "Tapin", "Hulu Sungai Selatan", "Hulu Sungai Tengah",
            "Hulu Sungai Utara", "Balangan", "Tabalong",
        ],
    },
    "Kalimantan Timur": {
        "bbox": (-2.0, 3.0, 114.0, 118.5),
        "coastal": [
            "Kota Balikpapan", "Kota Bontang", "Kota Samarinda", "Penajam Paser Utara",
            "Paser", "Kutai Kartanegara", "Berau", "Kutai Timur",
        ],
        "inland": ["Kutai Barat", "Mahakam Ulu"],
    },
    "Kalimantan Utara": {
        "bbox": (1.0, 4.5, 114.5, 118.0),
        "coastal": ["Kota Tarakan", "Nunukan", "Tana Tidung", "Bulungan"],
        "inland": ["Malinau"],
    },
    "Sulawesi Utara": {
        "bbox": (0.3, 5.0, 119.0, 127.5),
        "coastal": [
            "Kota Manado", "Kota Bitung", "Minahasa", "Minahasa Utara", "Minahasa Selatan",
            "Minahasa Tenggara", "Bolaang Mongondow", "Bolaang Mongondow Utara",
            "Bolaang Mongondow Selatan", "Bolaang Mongondow Timur", "Kepulauan Sangihe",
            "Kepulauan Talaud", "Kepulauan Siau Tagulandang Biaro",
        ],
        "inland": ["Kota Tomohon", "Kota Kotamobagu"],
    },
    "Gorontalo": {
        "bbox": (0.0, 1.3, 121.5, 124.0),
        "coastal": [
            "Kota Gorontalo", "Gorontalo", "Boalemo", "Pohuwato", "Bone Bolango",
            "Gorontalo Utara",
        ],
        "inland": [],
    },
    "Sulawesi Tengah": {
        "bbox": (-3.5, 1.2, 119.0, 123.5),
        "coastal": [
            "Kota Palu", "Donggala", "Parigi Moutong", "Tojo Una-Una", "Banggai",
            "Banggai Laut", "Banggai Kepulauan", "Tolitoli", "Buol", "Morowali",
            "Morowali Utara", "Poso",
        ],
        "inland": ["Sigi"],
    },
    "Sulawesi Barat": {
        "bbox": (-4.0, -0.5, 118.0, 121.5),
        "coastal": ["Mamuju", "Majene", "Polewali Mandar", "Pasangkayu", "Mamuju Tengah"],
        "inland": ["Mamasa"],
    },
    "Sulawesi Selatan": {
        "bbox": (-7.5, 0.0, 118.0, 122.0),
        "coastal": [
            "Kota Makassar", "Kota Parepare", "Kota Palopo", "Maros", "Gowa", "Takalar",
            "Jeneponto", "Bantaeng", "Bulukumba", "Sinjai", "Bone",
            "Pangkajene dan Kepulauan", "Pinrang", "Barru", "Selayar", "Luwu", "Luwu Timur",
        ],
        "inland": [
            "Enrekang", "Tana Toraja", "Toraja Utara", "Soppeng", "Wajo",
            "Sidenreng Rappang", "Luwu Utara",
        ],
    },
    "Sulawesi Tenggara": {
        "bbox": (-5.5, -2.0, 120.0, 124.5),
        "coastal": [
            "Kota Kendari", "Kota Bau-Bau", "Wakatobi", "Buton", "Buton Utara",
            "Buton Tengah", "Buton Selatan", "Muna", "Muna Barat", "Konawe",
            "Konawe Selatan", "Konawe Utara", "Kolaka", "Kolaka Timur", "Kolaka Utara",
            "Bombana", "Konawe Kepulauan",
        ],
        "inland": [],
    },
    "Maluku": {
        "bbox": (-4.5, 0.0, 125.0, 134.0),
        "coastal": [
            "Kota Ambon", "Kota Tual", "Maluku Tengah", "Seram Bagian Barat",
            "Seram Bagian Timur", "Buru", "Buru Selatan", "Maluku Tenggara",
            "Kepulauan Aru", "Kepulauan Tanimbar", "Maluku Barat Daya",
        ],
        "inland": [],
    },
    "Maluku Utara": {
        "bbox": (-3.0, 2.5, 126.0, 129.5),
        "coastal": [
            "Kota Ternate", "Kota Tidore Kepulauan", "Halmahera Barat", "Halmahera Utara",
            "Halmahera Timur", "Halmahera Tengah", "Halmahera Selatan", "Pulau Morotai",
            "Kepulauan Sula", "Pulau Taliabu",
        ],
        "inland": [],
    },
    "Papua Barat": {
        "bbox": (-4.5, -0.5, 129.0, 136.5),
        "coastal": [
            "Manokwari", "Manokwari Selatan", "Teluk Wondama", "Teluk Bintuni",
            "Fakfak", "Kaimana",
        ],
        "inland": ["Pegunungan Arfak"],
    },
    "Papua Barat Daya": {
        "bbox": (-2.5, 0.0, 130.0, 133.5),
        "coastal": ["Kota Sorong", "Sorong", "Sorong Selatan", "Tambrauw", "Raja Ampat"],
        "inland": ["Maybrat"],
    },
    "Papua": {
        "bbox": (-9.0, -1.0, 135.0, 141.0),
        "coastal": [
            "Kota Jayapura", "Jayapura", "Sarmi", "Mamberamo Raya", "Biak Numfor",
            "Supiori", "Waropen", "Yapen",
        ],
        "inland": ["Keerom", "Mamberamo Tengah"],
    },
    "Papua Tengah": {
        "bbox": (-5.0, -2.0, 135.5, 138.5),
        "coastal": ["Nabire", "Mimika"],
        "inland": ["Paniai", "Dogiyai", "Deiyai", "Intan Jaya", "Puncak", "Puncak Jaya"],
    },
    "Papua Pegunungan": {
        "bbox": (-5.0, -3.0, 137.0, 141.0),
        "coastal": [],
        "inland": [
            "Jayawijaya", "Lanny Jaya", "Tolikara", "Yalimo", "Nduga", "Pegunungan Bintang",
        ],
    },
    "Papua Selatan": {
        "bbox": (-9.0, -5.0, 137.0, 141.0),
        "coastal": ["Merauke", "Asmat", "Mappi"],
        "inland": ["Boven Digoel"],
    },
}

# ---------------------------------------------------------------------------
# Land anchors: real coordinates inside each regency so markers land on land
# (not in the sea). Each anchor: {"regency", "lat", "lon"}.
# ---------------------------------------------------------------------------
ANCHORS = {
    "Aceh": {
        "coastal": [
            {"regency": "Kota Banda Aceh", "lat": 5.55, "lon": 95.32},
            {"regency": "Kota Lhokseumawe", "lat": 5.18, "lon": 97.14},
            {"regency": "Kota Sabang", "lat": 5.89, "lon": 95.32},
            {"regency": "Aceh Utara", "lat": 5.08, "lon": 97.20},
            {"regency": "Simeulue", "lat": 2.62, "lon": 96.08},
        ],
        "inland": [
            {"regency": "Aceh Tengah", "lat": 4.61, "lon": 96.85},
            {"regency": "Gayo Lues", "lat": 3.95, "lon": 97.34},
            {"regency": "Aceh Tenggara", "lat": 3.31, "lon": 97.68},
        ],
    },
    "Sumatera Utara": {
        "coastal": [
            {"regency": "Kota Medan", "lat": 3.59, "lon": 98.67},
            {"regency": "Kota Sibolga", "lat": 1.74, "lon": 98.78},
            {"regency": "Kota Tanjungbalai", "lat": 2.97, "lon": 99.80},
            {"regency": "Deli Serdang", "lat": 3.42, "lon": 98.67},
        ],
        "inland": [
            {"regency": "Karo", "lat": 3.19, "lon": 98.51},
            {"regency": "Toba", "lat": 2.33, "lon": 99.06},
            {"regency": "Kota Pematangsiantar", "lat": 2.96, "lon": 99.06},
            {"regency": "Kota Padangsidimpuan", "lat": 1.38, "lon": 99.27},
        ],
    },
    "Sumatera Barat": {
        "coastal": [
            {"regency": "Kota Padang", "lat": -0.95, "lon": 100.35},
            {"regency": "Kota Pariaman", "lat": -0.63, "lon": 100.12},
            {"regency": "Pesisir Selatan", "lat": -1.35, "lon": 100.55},
            {"regency": "Padang Pariaman", "lat": -0.62, "lon": 100.29},
        ],
        "inland": [
            {"regency": "Kota Bukittinggi", "lat": -0.31, "lon": 100.37},
            {"regency": "Agam", "lat": -0.33, "lon": 100.16},
            {"regency": "Tanah Datar", "lat": -0.46, "lon": 100.57},
            {"regency": "Solok", "lat": -0.79, "lon": 100.66},
        ],
    },
    "Riau": {
        "coastal": [
            {"regency": "Kota Dumai", "lat": 1.67, "lon": 101.44},
            {"regency": "Bengkalis", "lat": 1.49, "lon": 102.08},
            {"regency": "Indragiri Hilir", "lat": -0.32, "lon": 103.16},
            {"regency": "Rokan Hilir", "lat": 1.70, "lon": 100.80},
        ],
        "inland": [
            {"regency": "Kota Pekanbaru", "lat": 0.51, "lon": 101.45},
            {"regency": "Kampar", "lat": 0.31, "lon": 101.11},
            {"regency": "Indragiri Hulu", "lat": -0.57, "lon": 102.32},
        ],
    },
    "Kepulauan Riau": {
        "coastal": [
            {"regency": "Kota Batam", "lat": 1.05, "lon": 104.03},
            {"regency": "Kota Tanjungpinang", "lat": 0.92, "lon": 104.44},
            {"regency": "Bintan", "lat": 1.10, "lon": 104.55},
            {"regency": "Natuna", "lat": 3.93, "lon": 108.39},
            {"regency": "Kepulauan Anambas", "lat": 3.09, "lon": 106.15},
        ],
        "inland": [],
    },
    "Jambi": {
        "coastal": [
            {"regency": "Tanjung Jabung Barat", "lat": -0.82, "lon": 103.46},
            {"regency": "Tanjung Jabung Timur", "lat": -1.05, "lon": 103.85},
        ],
        "inland": [
            {"regency": "Kota Jambi", "lat": -1.60, "lon": 103.62},
            {"regency": "Kerinci", "lat": -2.09, "lon": 101.48},
            {"regency": "Batanghari", "lat": -1.67, "lon": 103.13},
        ],
    },
    "Sumatera Selatan": {
        "coastal": [
            {"regency": "Kota Palembang", "lat": -2.99, "lon": 104.76},
            {"regency": "Banyuasin", "lat": -2.43, "lon": 104.91},
        ],
        "inland": [
            {"regency": "Lahat", "lat": -3.79, "lon": 103.54},
            {"regency": "Kota Lubuklinggau", "lat": -3.29, "lon": 102.86},
            {"regency": "Ogan Komering Ulu", "lat": -4.13, "lon": 104.10},
            {"regency": "Musi Rawas", "lat": -3.08, "lon": 102.55},
        ],
    },
    "Bengkulu": {
        "coastal": [
            {"regency": "Kota Bengkulu", "lat": -3.80, "lon": 102.26},
            {"regency": "Mukomuko", "lat": -2.56, "lon": 101.10},
            {"regency": "Kaur", "lat": -4.78, "lon": 103.35},
        ],
        "inland": [
            {"regency": "Rejang Lebong", "lat": -3.47, "lon": 102.52},
            {"regency": "Kepahiang", "lat": -3.64, "lon": 102.58},
        ],
    },
    "Lampung": {
        "coastal": [
            {"regency": "Kota Bandar Lampung", "lat": -5.42, "lon": 105.26},
            {"regency": "Lampung Selatan", "lat": -5.67, "lon": 105.61},
            {"regency": "Pesisir Barat", "lat": -5.19, "lon": 103.93},
            {"regency": "Tanggamus", "lat": -5.40, "lon": 104.67},
        ],
        "inland": [
            {"regency": "Kota Metro", "lat": -5.11, "lon": 105.31},
            {"regency": "Pringsewu", "lat": -5.36, "lon": 104.97},
            {"regency": "Lampung Tengah", "lat": -4.80, "lon": 105.31},
        ],
    },
    "Kepulauan Bangka Belitung": {
        "coastal": [
            {"regency": "Kota Pangkalpinang", "lat": -2.13, "lon": 106.11},
            {"regency": "Belitung", "lat": -2.75, "lon": 107.65},
            {"regency": "Belitung Timur", "lat": -2.87, "lon": 108.27},
            {"regency": "Bangka", "lat": -1.89, "lon": 105.95},
        ],
        "inland": [],
    },
    "DKI Jakarta": {
        "coastal": [
            {"regency": "Jakarta Utara", "lat": -6.11, "lon": 106.79},
            {"regency": "Kepulauan Seribu", "lat": -5.60, "lon": 106.55},
        ],
        "inland": [
            {"regency": "Jakarta Selatan", "lat": -6.26, "lon": 106.82},
            {"regency": "Jakarta Pusat", "lat": -6.19, "lon": 106.85},
            {"regency": "Jakarta Timur", "lat": -6.24, "lon": 106.90},
        ],
    },
    "Banten": {
        "coastal": [
            {"regency": "Kota Cilegon", "lat": -6.00, "lon": 106.01},
            {"regency": "Kota Serang", "lat": -6.12, "lon": 106.15},
            {"regency": "Pandeglang", "lat": -6.31, "lon": 106.10},
        ],
        "inland": [
            {"regency": "Kota Tangerang Selatan", "lat": -6.29, "lon": 106.72},
        ],
    },
    "Jawa Barat": {
        "coastal": [
            {"regency": "Kota Cirebon", "lat": -6.72, "lon": 108.55},
            {"regency": "Pangandaran", "lat": -7.70, "lon": 108.65},
            {"regency": "Karawang", "lat": -6.31, "lon": 107.31},
            {"regency": "Sukabumi", "lat": -6.99, "lon": 106.55},
        ],
        "inland": [
            {"regency": "Kota Bandung", "lat": -6.92, "lon": 107.61},
            {"regency": "Kota Bogor", "lat": -6.60, "lon": 106.81},
            {"regency": "Cianjur", "lat": -6.82, "lon": 107.14},
            {"regency": "Garut", "lat": -7.21, "lon": 107.90},
            {"regency": "Sumedang", "lat": -6.84, "lon": 107.92},
        ],
    },
    "Jawa Tengah": {
        "coastal": [
            {"regency": "Kota Semarang", "lat": -6.97, "lon": 110.42},
            {"regency": "Cilacap", "lat": -7.73, "lon": 109.01},
            {"regency": "Jepara", "lat": -6.58, "lon": 110.67},
            {"regency": "Kebumen", "lat": -7.67, "lon": 109.66},
        ],
        "inland": [
            {"regency": "Kota Surakarta", "lat": -7.57, "lon": 110.82},
            {"regency": "Kota Magelang", "lat": -7.47, "lon": 110.22},
            {"regency": "Wonosobo", "lat": -7.35, "lon": 109.90},
            {"regency": "Boyolali", "lat": -7.53, "lon": 110.60},
            {"regency": "Banjarnegara", "lat": -7.39, "lon": 109.69},
        ],
    },
    "DI Yogyakarta": {
        "coastal": [
            {"regency": "Bantul", "lat": -7.98, "lon": 110.28},
            {"regency": "Gunungkidul", "lat": -8.04, "lon": 110.62},
            {"regency": "Kulon Progo", "lat": -7.86, "lon": 110.15},
        ],
        "inland": [
            {"regency": "Kota Yogyakarta", "lat": -7.80, "lon": 110.36},
            {"regency": "Sleman", "lat": -7.72, "lon": 110.35},
        ],
    },
    "Jawa Timur": {
        "coastal": [
            {"regency": "Kota Surabaya", "lat": -7.25, "lon": 112.75},
            {"regency": "Banyuwangi", "lat": -8.22, "lon": 114.37},
            {"regency": "Pacitan", "lat": -8.19, "lon": 111.10},
            {"regency": "Kota Probolinggo", "lat": -7.75, "lon": 113.22},
            {"regency": "Situbondo", "lat": -7.71, "lon": 114.01},
            {"regency": "Sumenep", "lat": -7.02, "lon": 113.86},
        ],
        "inland": [
            {"regency": "Kota Malang", "lat": -7.98, "lon": 112.63},
            {"regency": "Kota Kediri", "lat": -7.82, "lon": 112.02},
            {"regency": "Kota Madiun", "lat": -7.63, "lon": 111.52},
            {"regency": "Ponorogo", "lat": -7.87, "lon": 111.46},
            {"regency": "Batu", "lat": -7.87, "lon": 112.52},
        ],
    },
    "Bali": {
        "coastal": [
            {"regency": "Kota Denpasar", "lat": -8.65, "lon": 115.22},
            {"regency": "Badung", "lat": -8.72, "lon": 115.17},
            {"regency": "Buleleng", "lat": -8.13, "lon": 115.05},
            {"regency": "Karangasem", "lat": -8.44, "lon": 115.62},
            {"regency": "Klungkung", "lat": -8.73, "lon": 115.55},
        ],
        "inland": [
            {"regency": "Gianyar", "lat": -8.51, "lon": 115.26},
            {"regency": "Bangli", "lat": -8.45, "lon": 115.36},
        ],
    },
    "Nusa Tenggara Barat": {
        "coastal": [
            {"regency": "Kota Mataram", "lat": -8.58, "lon": 116.12},
            {"regency": "Lombok Barat", "lat": -8.49, "lon": 116.04},
            {"regency": "Lombok Utara", "lat": -8.37, "lon": 116.15},
            {"regency": "Lombok Timur", "lat": -8.58, "lon": 116.57},
            {"regency": "Sumbawa", "lat": -8.49, "lon": 117.42},
            {"regency": "Kota Bima", "lat": -8.46, "lon": 118.72},
        ],
        "inland": [],
    },
    "Nusa Tenggara Timur": {
        "coastal": [
            {"regency": "Kota Kupang", "lat": -10.17, "lon": 123.61},
            {"regency": "Manggarai Barat", "lat": -8.49, "lon": 119.89},
            {"regency": "Ende", "lat": -8.84, "lon": 121.66},
            {"regency": "Sikka", "lat": -8.62, "lon": 122.21},
            {"regency": "Sumba Timur", "lat": -9.66, "lon": 120.26},
            {"regency": "Manggarai", "lat": -8.61, "lon": 120.46},
            {"regency": "Rote Ndao", "lat": -10.74, "lon": 123.12},
        ],
        "inland": [
            {"regency": "Timor Tengah Utara", "lat": -9.45, "lon": 124.48},
            {"regency": "Timor Tengah Selatan", "lat": -9.86, "lon": 124.28},
        ],
    },
    "Kalimantan Barat": {
        "coastal": [
            {"regency": "Kota Pontianak", "lat": -0.03, "lon": 109.34},
            {"regency": "Kota Singkawang", "lat": 0.91, "lon": 108.98},
            {"regency": "Sambas", "lat": 1.36, "lon": 109.27},
            {"regency": "Ketapang", "lat": -1.86, "lon": 109.97},
        ],
        "inland": [
            {"regency": "Sintang", "lat": 0.07, "lon": 111.50},
            {"regency": "Kapuas Hulu", "lat": 0.83, "lon": 112.94},
        ],
    },
    "Kalimantan Tengah": {
        "coastal": [
            {"regency": "Kotawaringin Barat", "lat": -2.68, "lon": 111.62},
            {"regency": "Kotawaringin Timur", "lat": -2.53, "lon": 112.95},
            {"regency": "Seruyan", "lat": -3.40, "lon": 112.55},
        ],
        "inland": [
            {"regency": "Kota Palangka Raya", "lat": -2.21, "lon": 113.91},
            {"regency": "Katingan", "lat": -2.49, "lon": 113.40},
        ],
    },
    "Kalimantan Selatan": {
        "coastal": [
            {"regency": "Kota Banjarmasin", "lat": -3.32, "lon": 114.59},
            {"regency": "Kotabaru", "lat": -3.00, "lon": 115.98},
            {"regency": "Tanah Laut", "lat": -3.80, "lon": 114.74},
        ],
        "inland": [
            {"regency": "Kota Banjarbaru", "lat": -3.46, "lon": 114.83},
            {"regency": "Banjar", "lat": -3.41, "lon": 114.85},
            {"regency": "Tapin", "lat": -2.91, "lon": 115.12},
        ],
    },
    "Kalimantan Timur": {
        "coastal": [
            {"regency": "Kota Balikpapan", "lat": -1.26, "lon": 116.83},
            {"regency": "Kota Samarinda", "lat": -0.50, "lon": 117.15},
            {"regency": "Kota Bontang", "lat": 0.13, "lon": 117.48},
            {"regency": "Berau", "lat": 2.15, "lon": 117.50},
            {"regency": "Penajam Paser Utara", "lat": -1.29, "lon": 116.55},
        ],
        "inland": [
            {"regency": "Kutai Barat", "lat": -0.22, "lon": 115.63},
            {"regency": "Mahakam Ulu", "lat": -0.48, "lon": 114.80},
        ],
    },
    "Kalimantan Utara": {
        "coastal": [
            {"regency": "Kota Tarakan", "lat": 3.31, "lon": 117.60},
            {"regency": "Bulungan", "lat": 2.84, "lon": 117.36},
            {"regency": "Nunukan", "lat": 4.13, "lon": 116.71},
            {"regency": "Tana Tidung", "lat": 3.68, "lon": 116.80},
        ],
        "inland": [
            {"regency": "Malinau", "lat": 3.58, "lon": 116.63},
        ],
    },
    "Sulawesi Utara": {
        "coastal": [
            {"regency": "Kota Manado", "lat": 1.47, "lon": 124.84},
            {"regency": "Kota Bitung", "lat": 1.44, "lon": 125.19},
            {"regency": "Minahasa", "lat": 1.30, "lon": 124.91},
            {"regency": "Kepulauan Sangihe", "lat": 3.61, "lon": 125.48},
            {"regency": "Kepulauan Talaud", "lat": 4.00, "lon": 126.68},
        ],
        "inland": [
            {"regency": "Kota Tomohon", "lat": 1.32, "lon": 124.83},
            {"regency": "Kota Kotamobagu", "lat": 0.73, "lon": 124.31},
        ],
    },
    "Gorontalo": {
        "coastal": [
            {"regency": "Kota Gorontalo", "lat": 0.54, "lon": 123.06},
            {"regency": "Boalemo", "lat": 0.49, "lon": 122.29},
            {"regency": "Pohuwato", "lat": 0.48, "lon": 121.75},
            {"regency": "Gorontalo Utara", "lat": 0.83, "lon": 122.92},
        ],
        "inland": [],
    },
    "Sulawesi Tengah": {
        "coastal": [
            {"regency": "Kota Palu", "lat": -0.90, "lon": 119.87},
            {"regency": "Donggala", "lat": -0.66, "lon": 119.74},
            {"regency": "Banggai", "lat": -0.94, "lon": 122.79},
            {"regency": "Parigi Moutong", "lat": -0.84, "lon": 120.18},
            {"regency": "Poso", "lat": -1.40, "lon": 120.75},
            {"regency": "Tolitoli", "lat": 1.04, "lon": 120.82},
        ],
        "inland": [
            {"regency": "Sigi", "lat": -0.93, "lon": 120.03},
        ],
    },
    "Sulawesi Barat": {
        "coastal": [
            {"regency": "Mamuju", "lat": -2.68, "lon": 118.89},
            {"regency": "Majene", "lat": -3.54, "lon": 118.97},
            {"regency": "Polewali Mandar", "lat": -3.40, "lon": 119.35},
            {"regency": "Pasangkayu", "lat": -0.62, "lon": 119.37},
        ],
        "inland": [
            {"regency": "Mamasa", "lat": -2.92, "lon": 119.39},
        ],
    },
    "Sulawesi Selatan": {
        "coastal": [
            {"regency": "Kota Makassar", "lat": -5.14, "lon": 119.42},
            {"regency": "Kota Parepare", "lat": -4.01, "lon": 119.63},
            {"regency": "Kota Palopo", "lat": -2.99, "lon": 120.20},
            {"regency": "Bulukumba", "lat": -5.55, "lon": 120.21},
            {"regency": "Selayar", "lat": -6.11, "lon": 120.48},
            {"regency": "Bantaeng", "lat": -5.55, "lon": 119.95},
            {"regency": "Pinrang", "lat": -3.78, "lon": 119.65},
        ],
        "inland": [
            {"regency": "Toraja Utara", "lat": -2.97, "lon": 119.90},
            {"regency": "Enrekang", "lat": -3.56, "lon": 119.76},
            {"regency": "Soppeng", "lat": -4.35, "lon": 119.89},
            {"regency": "Luwu Utara", "lat": -2.68, "lon": 120.10},
        ],
    },
    "Sulawesi Tenggara": {
        "coastal": [
            {"regency": "Kota Kendari", "lat": -3.99, "lon": 122.51},
            {"regency": "Kota Bau-Bau", "lat": -5.46, "lon": 122.60},
            {"regency": "Wakatobi", "lat": -5.32, "lon": 123.59},
            {"regency": "Kolaka", "lat": -4.05, "lon": 121.63},
            {"regency": "Muna", "lat": -4.84, "lon": 122.72},
        ],
        "inland": [],
    },
    "Maluku": {
        "coastal": [
            {"regency": "Kota Ambon", "lat": -3.69, "lon": 128.17},
            {"regency": "Kota Tual", "lat": -5.64, "lon": 132.75},
            {"regency": "Maluku Tenggara", "lat": -7.98, "lon": 131.30},
            {"regency": "Maluku Tengah", "lat": -3.30, "lon": 128.96},
            {"regency": "Buru", "lat": -3.26, "lon": 127.10},
            {"regency": "Kepulauan Aru", "lat": -5.76, "lon": 134.21},
        ],
        "inland": [],
    },
    "Maluku Utara": {
        "coastal": [
            {"regency": "Kota Ternate", "lat": 0.79, "lon": 127.38},
            {"regency": "Halmahera Utara", "lat": 1.73, "lon": 128.01},
            {"regency": "Halmahera Barat", "lat": 1.09, "lon": 127.48},
            {"regency": "Halmahera Selatan", "lat": -0.63, "lon": 127.49},
            {"regency": "Pulau Morotai", "lat": 2.20, "lon": 128.43},
            {"regency": "Kepulauan Sula", "lat": -2.06, "lon": 125.97},
        ],
        "inland": [],
    },
    "Papua Barat": {
        "coastal": [
            {"regency": "Manokwari", "lat": -0.86, "lon": 134.08},
            {"regency": "Fakfak", "lat": -2.93, "lon": 132.29},
            {"regency": "Kaimana", "lat": -3.66, "lon": 133.76},
            {"regency": "Teluk Bintuni", "lat": -2.10, "lon": 133.52},
        ],
        "inland": [
            {"regency": "Pegunungan Arfak", "lat": -1.30, "lon": 133.80},
        ],
    },
    "Papua Barat Daya": {
        "coastal": [
            {"regency": "Kota Sorong", "lat": -0.87, "lon": 131.28},
            {"regency": "Raja Ampat", "lat": -0.42, "lon": 130.86},
            {"regency": "Sorong Selatan", "lat": -1.44, "lon": 132.03},
        ],
        "inland": [
            {"regency": "Maybrat", "lat": -1.35, "lon": 132.20},
            {"regency": "Tambrauw", "lat": -0.82, "lon": 132.45},
        ],
    },
    "Papua": {
        "coastal": [
            {"regency": "Kota Jayapura", "lat": -2.54, "lon": 140.72},
            {"regency": "Biak Numfor", "lat": -1.17, "lon": 136.08},
            {"regency": "Yapen", "lat": -1.88, "lon": 136.24},
            {"regency": "Sarmi", "lat": -1.87, "lon": 138.75},
        ],
        "inland": [
            {"regency": "Keerom", "lat": -3.04, "lon": 140.79},
        ],
    },
    "Papua Tengah": {
        "coastal": [
            {"regency": "Nabire", "lat": -3.37, "lon": 135.49},
            {"regency": "Mimika", "lat": -4.55, "lon": 136.89},
        ],
        "inland": [
            {"regency": "Paniai", "lat": -3.92, "lon": 136.29},
            {"regency": "Puncak Jaya", "lat": -3.98, "lon": 137.25},
            {"regency": "Dogiyai", "lat": -4.02, "lon": 135.95},
        ],
    },
    "Papua Pegunungan": {
        "coastal": [],
        "inland": [
            {"regency": "Jayawijaya", "lat": -4.09, "lon": 138.95},
            {"regency": "Lanny Jaya", "lat": -3.97, "lon": 138.45},
            {"regency": "Pegunungan Bintang", "lat": -4.91, "lon": 140.62},
        ],
    },
    "Papua Selatan": {
        "coastal": [
            {"regency": "Merauke", "lat": -8.49, "lon": 140.40},
            {"regency": "Asmat", "lat": -5.54, "lon": 138.13},
            {"regency": "Mappi", "lat": -6.52, "lon": 139.35},
        ],
        "inland": [
            {"regency": "Boven Digoel", "lat": -5.81, "lon": 140.35},
        ],
    },
}

INLAND_JITTER = 0.15   # degrees (~17 km) around an inland anchor
COASTAL_JITTER = 0.06  # degrees (~7 km) around a coastal anchor

for _prov, _data in PROVINCES.items():
    _data["regencies"] = _data["coastal"] + _data["inland"]
    _data["anchors"] = ANCHORS[_prov]

# ---------------------------------------------------------------------------
# Categories & behaviour
# ---------------------------------------------------------------------------
CATEGORIES = {
    "gunung": {
        "facilities": ["parkir", "pos_pendakian", "papan_informasi", "warung_makan", "wc"],
        "price_range": (0, 30000), "beauty": (4.0, 5.0), "road": (1.5, 3.5),
        "crowd": (1.0, 3.5), "free_rate": 0.10, "popularity_scale": 0.9,
    },
    "bukit": {
        "facilities": ["parkir", "spot_foto", "gazebo", "warung_makan"],
        "price_range": (0, 20000), "beauty": (3.8, 5.0), "road": (2.0, 4.0),
        "crowd": (1.5, 4.0), "free_rate": 0.25, "popularity_scale": 0.8,
    },
    "pantai": {
        "facilities": ["parkir", "wc", "warung_makan", "spot_foto", "sewa_pelampung", "gazebo"],
        "price_range": (0, 25000), "beauty": (3.8, 5.0), "road": (2.5, 4.5),
        "crowd": (2.0, 5.0), "free_rate": 0.30, "popularity_scale": 1.2,
    },
    "pulau": {
        "facilities": ["dermaga", "penginapan", "sewa_pelampung", "warung_makan", "homestay"],
        "price_range": (25000, 300000), "beauty": (4.2, 5.0), "road": (1.0, 3.0),
        "crowd": (1.0, 3.0), "free_rate": 0.0, "popularity_scale": 1.0,
    },
    "air-terjun": {
        "facilities": ["parkir", "spot_foto", "warung_makan", "gazebo", "papan_informasi"],
        "price_range": (0, 20000), "beauty": (3.8, 5.0), "road": (1.5, 4.0),
        "crowd": (1.5, 4.0), "free_rate": 0.35, "popularity_scale": 0.9,
    },
    "curug": {
        "facilities": ["parkir", "spot_foto", "warung_makan"],
        "price_range": (0, 15000), "beauty": (3.5, 4.8), "road": (2.0, 4.0),
        "crowd": (2.0, 4.5), "free_rate": 0.35, "popularity_scale": 0.8,
    },
    "danau": {
        "facilities": ["parkir", "spot_foto", "sewa_perahu", "warung_makan", "gazebo"],
        "price_range": (0, 30000), "beauty": (3.5, 5.0), "road": (2.0, 4.0),
        "crowd": (1.5, 4.0), "free_rate": 0.25, "popularity_scale": 0.9,
    },
    "camping": {
        "facilities": ["parkir", "camping_area", "wc", "pos_pendakian", "papan_informasi"],
        "price_range": (10000, 75000), "beauty": (3.8, 5.0), "road": (1.5, 3.5),
        "crowd": (1.0, 3.5), "free_rate": 0.05, "popularity_scale": 0.8,
    },
    "tracking": {
        "facilities": ["parkir", "pos_pendakian", "papan_informasi", "guide"],
        "price_range": (0, 30000), "beauty": (3.8, 5.0), "road": (1.0, 3.0),
        "crowd": (1.0, 3.0), "free_rate": 0.15, "popularity_scale": 0.7,
    },
    "sunrise": {
        "facilities": ["parkir", "spot_foto", "gazebo", "papan_informasi"],
        "price_range": (0, 20000), "beauty": (4.0, 5.0), "road": (2.0, 3.5),
        "crowd": (2.0, 4.5), "free_rate": 0.30, "popularity_scale": 1.1,
    },
    "sunset": {
        "facilities": ["parkir", "spot_foto", "warung_makan", "gazebo"],
        "price_range": (0, 20000), "beauty": (4.0, 5.0), "road": (2.0, 4.0),
        "crowd": (2.0, 4.5), "free_rate": 0.30, "popularity_scale": 1.0,
    },
    "gua": {
        "facilities": ["parkir", "papan_informasi", "guide", "spot_foto"],
        "price_range": (0, 30000), "beauty": (3.2, 4.8), "road": (2.0, 4.0),
        "crowd": (1.0, 3.0), "free_rate": 0.20, "popularity_scale": 0.6,
    },
    "taman": {
        "facilities": ["parkir", "spot_foto", "gazebo", "wc", "warung_makan", "papan_informasi"],
        "price_range": (0, 15000), "beauty": (3.0, 4.5), "road": (3.0, 5.0),
        "crowd": (2.5, 5.0), "free_rate": 0.40, "popularity_scale": 0.9,
    },
    "desa-wisata": {
        "facilities": ["homestay", "warung_makan", "guide", "papan_informasi", "wc"],
        "price_range": (0, 50000), "beauty": (3.2, 4.5), "road": (2.5, 4.5),
        "crowd": (1.0, 3.0), "free_rate": 0.30, "popularity_scale": 0.6,
    },
    "pemandian": {
        "facilities": ["parkir", "wc", "gazebo", "warung_makan", "spot_foto"],
        "price_range": (0, 25000), "beauty": (3.0, 4.5), "road": (3.0, 5.0),
        "crowd": (2.5, 5.0), "free_rate": 0.25, "popularity_scale": 0.8,
    },
    "budaya": {
        "facilities": ["parkir", "tiket", "papan_informasi", "mushola", "souvenir", "wc"],
        "price_range": (0, 50000), "beauty": (3.5, 4.8), "road": (2.5, 4.5),
        "crowd": (2.5, 5.0), "free_rate": 0.20, "popularity_scale": 1.0,
    },
    "religi": {
        "facilities": ["parkir", "tempat_wudhu", "papan_informasi", "wc"],
        "price_range": (0, 10000), "beauty": (3.0, 4.5), "road": (3.0, 5.0),
        "crowd": (2.0, 4.5), "free_rate": 0.70, "popularity_scale": 0.8,
    },
}

FEATURE_POOL = {
    "gunung": ["Gunung", "Puncak", "Bukit", "Lereng"],
    "bukit": ["Bukit", "Puncak", "Perbukitan", "Punggung"],
    "pantai": ["Pantai", "Pasir", "Tanjung", "Teluk"],
    "pulau": ["Pulau", "Atol", "Kepulauan"],
    "air-terjun": ["Air Terjun", "Curug", "Tirta"],
    "curug": ["Curug", "Air Terjun"],
    "danau": ["Danau", "Telaga", "Rawa"],
    "camping": ["Lahan Camping", "Bumi Perkemahan", "Camping Ground", "Glamping"],
    "tracking": ["Jalur Tracking", "Trail", "Hutan Lindung", "Trekking"],
    "sunrise": ["Puncak", "Sunrise Point", "Spot Sunrise", "Bukit"],
    "sunset": ["Bukit", "Sunset Point", "Spot Sunset", "Tanjung"],
    "gua": ["Gua", "Goa"],
    "taman": ["Taman", "Kebun", "Taman Wisata", "Kebun Raya"],
    "desa-wisata": ["Desa Wisata", "Kampung Adat", "Perkampungan"],
    "pemandian": ["Pemandian", "Sungai", "Kolam Alami", "Sumber Air"],
    "budaya": ["Candi", "Pura", "Kraton", "Museum", "Situs", "Benteng"],
    "religi": ["Masjid", "Pura", "Klenteng", "Gereja", "Makam"],
}

# Keywords used by loremflickr so each destination gets photos that match its
# category. The ?lock= parameter keeps a given URL returning the same photo, so
# images stay stable across regenerations and always resolve to a real image.
IMAGE_KEYWORDS = {
    "gunung": "mountain,indonesia",
    "bukit": "hill,landscape",
    "danau": "lake,landscape",
    "air-terjun": "waterfall,indonesia",
    "pantai": "beach,indonesia",
    "pulau": "island,indonesia",
    "taman": "garden,indonesia",
    "desa-wisata": "village,indonesia",
    "tracking": "hiking,indonesia",
    "sunrise": "sunrise,mountain",
    "sunset": "sunset,beach",
    "gua": "cave,indonesia",
    "pemandian": "river,swimming",
    "camping": "camping,forest",
    "budaya": "temple,indonesia",
    "religi": "mosque,indonesia",
}

IMAGE_COUNT = 4


def build_images(category: str, slug: str) -> list[str]:
    """Deterministic set of photo URLs for a destination (one primary + rest)."""
    keywords = IMAGE_KEYWORDS.get(category, "landscape,nature")
    base = zlib.crc32(slug.encode("utf-8"))
    return [
        f"https://loremflickr.com/800/600/{keywords}?lock={base + offset}"
        for offset in (0, 7, 13, 29)
    ]

# Generic scenic tails. No wayang character or specific real-place names here so
# the generated name can never contradict the province/regency it is placed in.
NAME_TAIL = [
    "Bidadari", "Sari", "Putri", "Hijau", "Biru", "Cinta", "Pelangi", "Sejuk",
    "Indah", "Permai", "Nirmala", "Tirta", "Senja", "Cahaya", "Embun", "Kristal",
    "Jernih", "Wangi", "Harum", "Sakura", "Mawar", "Melati", "Anggrek", "Kencana",
    "Asri", "Elok", "Biru Langit", "Emas", "Perak", "Surya", "Rimbun", "Bening",
    "Memukau", "Tersembunyi", "Sunyi", "Damai", "Segar", "Manis", "Mutiara",
    "Zamrud", "Mekar", "Rindu", "Seribu", "Hijau Asri", "Bintang", "Suling",
    "Nusa", "Kuta", "Beringin", "Cemara", "Kenanga",
]

# Generic geographic descriptors safe to combine anywhere in Indonesia.
GENERIC_WORD = [
    "Barat", "Wetan", "Kulon", "Lor", "Kidul", "Atas", "Bawah", "Raya", "Kecil",
    "Besar", "Madia", "Alas", "Lengkong", "Kedung", "Sawah", "Ladang", "Sambung",
    "Tapak", "Gajah", "Kuda", "Kelinci", "Rajawali", "Elang", "Garuda", "Naga",
    "Srigala", "Banteng", "Pandan", "Tiga", "Dua", "Candi", "Jembatan", "Bendungan",
    "Rawa", "Karang", "Pasar", "Pelabuhan", "Gunung Kecil",
]

DISTRICT_WORD = [
    "Pondok", "Sukamaju", "Margasari", "Karanganyar", "Tanjungsari", "Mulyasari",
    "Cibiru", "Pangalengan", "Sumberjaya", "Beringin", "Tamansari", "Babakan",
    "Lebak", "Wonosari", "Sumberrejo", "Kencana", "Medang", "Tegal", "Gamping",
    "Kedawung", "Sindang", "Cikole",
]

VILLAGE_WORD = [
    "Mekar Sari", "Cihideung", "Sukamulya", "Karang Sari", "Cikalong", "Babakan",
    "Lebak", "Sumber Rejo", "Tegal Rejo", "Wonokerto", "Pasar Baru", "Margasari",
    "Cibodas", "Rancabango", "Sumber Mukti", "Cijeruk", "Mulya Sari", "Cipedes",
    "Sukamaju", "Batu Hitam",
]

FACILITY_NAMES = [
    "Parkir", "Toilet", "Mushola", "Warung Makan", "Penginapan", "Area Camping", "Wifi",
    "Papan Informasi", "Pos Pendakian", "Pemandu Lokal", "Spot Foto", "Gazebo", "Dermaga",
    "Sewa Perahu", "Sewa Pelampung", "Toko Souvenir", "ATM", "Pos Kesehatan", "Homestay",
]

# audience mapping
AUDIENCE_TAGS = ["anak", "keluarga", "pasangan", "solo"]

# ---------------------------------------------------------------------------
# Name generation
# ---------------------------------------------------------------------------
def generate_name(rng: random.Random, category: str) -> str:
    feature = rng.choice(FEATURE_POOL[category])
    tail = rng.choice(NAME_TAIL)
    if rng.random() < 0.55:
        return f"{feature} {tail}"
    word = rng.choice(GENERIC_WORD)
    while word.lower() in (feature.lower(), tail.lower()):
        word = rng.choice(GENERIC_WORD)
    return f"{feature} {tail} {word}"


def build_address(name: str, regency: str, province: str) -> str:
    """Kabupaten / Kota / Kota Administrasi prefix correct per region."""
    if province == "DKI Jakarta":
        label = "Kabupaten Administrasi" if regency == "Kepulauan Seribu" else "Kota Administrasi"
        loc = f"{label} {regency}"
    elif regency.startswith("Kota "):
        loc = regency
    else:
        loc = f"Kabupaten {regency}"
    return f"{name}, {loc}, Provinsi {province}, Indonesia"


# ---------------------------------------------------------------------------
# Score ground truth
# ---------------------------------------------------------------------------
def compute_score(rng: random.Random, beauty: float, crowd: float, popularity: float,
                  safety: float, cleanliness: float, road: float) -> float:
    norm_pop = min(popularity / 100.0, 1.0)
    raw = 100.0 * (
        0.35 * (beauty / 5.0)
        + 0.25 * ((6.0 - crowd) / 5.0)
        + 0.20 * (1.0 - norm_pop)
        + 0.10 * (safety / 5.0)
        + 0.10 * (cleanliness / 5.0)
    )
    noise = rng.gauss(0, 3.0)
    return round(max(0.0, min(100.0, raw + noise)), 2)


# ---------------------------------------------------------------------------
# Main generator
# ---------------------------------------------------------------------------
def build_fields(rng, category, name, province, regency, lat, lon,
                 real: bool = False, real_images: list[str] | None = None) -> dict:
    cfg = CATEGORIES[category]

    beauty = round(rng.uniform(*cfg["beauty"]), 2)
    road = round(rng.uniform(*cfg["road"]), 2)
    crowd = round(rng.uniform(*cfg["crowd"]), 2)
    safety = round(rng.uniform(3.0, 5.0), 2)
    cleanliness = round(rng.uniform(3.0, 5.0), 2)

    pop_scale = cfg["popularity_scale"]
    popularity = int(rng.expovariate(1.0 / (25 * pop_scale)))
    popularity = max(1, min(120, popularity))

    review_count = int(popularity * rng.uniform(2, 6))
    rating = round(min(5.0, max(3.0, beauty * 0.6 + rng.gauss(4.0, 0.35))), 2)
    visitor_count = int(review_count * rng.uniform(180, 900))

    price_min = round(rng.uniform(*cfg["price_range"]), 2)
    is_free = rng.random() < cfg["free_rate"] or price_min == 0
    if is_free:
        price_min = 0
    price_max = round(price_min * rng.uniform(1.0, 1.8), 2) if not is_free and rng.random() < 0.6 else None

    open_24h = category in ("pantai", "sunrise", "sunset") and rng.random() < 0.5
    opening = "00:00" if open_24h else rng.choice(["06:00", "07:00", "08:00"])
    closing = "23:59" if open_24h else rng.choice(["17:00", "18:00", "19:00", "22:00"])

    days = rng.sample(["mon", "tue", "wed", "thu", "fri", "sat", "sun"], k=rng.randint(6, 7))
    days = sorted(days) if rng.random() < 0.9 else ["sat", "sun"]

    facilities = rng.sample(cfg["facilities"], k=rng.randint(3, len(cfg["facilities"])))
    if rng.random() < 0.3:
        facilities.append(rng.choice(AUDIENCE_TAGS))
    facilities = sorted(set(facilities))

    slug = "-".join(name.lower().split())
    score = compute_score(rng, beauty, crowd, popularity, safety, cleanliness, road)

    if real_images:
        placeholders = build_images(category, slug)
        images = (real_images + placeholders)[:IMAGE_COUNT]
    else:
        images = build_images(category, slug)

    is_trending = rng.random() < 0.08 and popularity > 30
    is_featured = rng.random() < 0.12 and score > 65

    phone = f"0{rng.randint(811, 899)}{rng.randint(1000000, 9999999)}"

    return {
        "name": name,
        "slug": slug,
        "category": category,
        "province": province,
        "regency": regency,
        "district": "Kecamatan " + rng.choice(DISTRICT_WORD),
        "village": rng.choice(["Desa", "Kelurahan", "Kampung"]) + " " + rng.choice(VILLAGE_WORD),
        "address": build_address(name, regency, province),
        "latitude": round(lat, 6),
        "longitude": round(lon, 6),
        "price_min": price_min,
        "price_max": price_max,
        "is_free": is_free,
        "opening_time": opening,
        "closing_time": closing,
        "is_open_24h": open_24h,
        "days_open": days,
        "facilities": facilities,
        "images": images,
        "rating": rating,
        "review_count": review_count,
        "popularity": popularity,
        "visitor_count": visitor_count,
        "safety": safety,
        "cleanliness": cleanliness,
        "beauty": beauty,
        "road_access": road,
        "crowd_level": crowd,
        "hidden_gem_score": score,
        "phone": phone,
        "is_trending": is_trending,
        "is_featured": is_featured,
        "_real": real,
    }


def load_real_pool(path) -> list[dict]:
    """Read the scraped real-destination pool (name, category, province, regency, lat/lon, images)."""
    pool: list[dict] = []
    if not path or not path.exists():
        return pool
    with path.open(newline="", encoding="utf-8") as f:
        for raw in csv.DictReader(f):
            if not raw.get("name") or not raw.get("latitude") or not raw.get("longitude"):
                continue
            images = [u for u in (raw.get("images") or "").split("|") if u]
            pool.append({
                "name": raw["name"],
                "category": raw["category"],
                "province": raw["province"],
                "regency": raw["regency"],
                "latitude": float(raw["latitude"]),
                "longitude": float(raw["longitude"]),
                "images": images,
            })
    return pool


def generate_rows(total: int, seed: int, real_pool: list[dict] | None = None) -> list[dict]:
    rng = random.Random(seed)
    rows: list[dict] = []
    used_names: set[str] = set()

    if real_pool:
        for real in real_pool:
            rows.append(build_fields(
                rng,
                real["category"],
                real["name"],
                real["province"],
                real["regency"],
                real["latitude"],
                real["longitude"],
                real=True,
                real_images=real.get("images"),
            ))
            used_names.add(real["name"].lower())

    province_names = list(PROVINCES.keys())
    weights = [
        (1.0 if p in ("Jawa Barat", "Jawa Timur", "Jawa Tengah") else
         0.9 if p in ("Sumatera Utara", "Sumatera Barat", "Aceh", "Sulawesi Selatan", "Bali", "Banten", "Lampung", "Nusa Tenggara Barat", "Kalimantan Selatan") else
         0.7) for p in province_names
    ]
    categories = list(CATEGORIES.keys())
    category_weights = [1.0, 1.0, 1.2, 0.5, 0.9, 0.6, 0.9, 0.5, 0.8, 0.7, 0.8, 0.5, 0.7, 0.5, 0.6, 0.7, 0.7]

    while len(rows) < total:
        province = rng.choices(province_names, weights=weights, k=1)[0]
        prov_cfg = PROVINCES[province]
        lat_min, lat_max, lon_min, lon_max = prov_cfg["bbox"]

        category = rng.choices(categories, weights=category_weights, k=1)[0]
        # Coastal categories must live in a coastal regency. Provinces without
        # any coastline (e.g. Papua Pegunungan) fall back to an inland category.
        if category in COASTAL_CATEGORIES and not prov_cfg["coastal"]:
            inland_cats = [c for c in categories if c not in COASTAL_CATEGORIES]
            inland_weights = [category_weights[categories.index(c)] for c in inland_cats]
            category = rng.choices(inland_cats, weights=inland_weights, k=1)[0]

        # Place the destination on a real land point of its regency (anchored to
        # a real town/coast), then jitter slightly. This keeps every marker on
        # land and inside the regency instead of random points in the sea.
        if category in COASTAL_CATEGORIES:
            anchors = prov_cfg["anchors"]["coastal"] or prov_cfg["anchors"]["inland"]
            jitter = COASTAL_JITTER
        else:
            anchors = prov_cfg["anchors"]["inland"] or prov_cfg["anchors"]["coastal"]
            jitter = INLAND_JITTER
        anchor = rng.choice(anchors)
        regency = anchor["regency"]

        lat = min(lat_max, max(lat_min, anchor["lat"] + rng.uniform(-jitter, jitter)))
        lon = min(lon_max, max(lon_min, anchor["lon"] + rng.uniform(-jitter, jitter)))

        name = generate_name(rng, category)
        while name.lower() in used_names:
            name = generate_name(rng, category)
        used_names.add(name.lower())

        rows.append(build_fields(rng, category, name, province, regency, lat, lon))

    return rows


def write_csv(rows: list[dict], output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    fields = list(rows[0].keys())
    with output.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for r in rows:
            row = dict(r)
            row.pop("_real", None)
            row["days_open"] = "|".join(r["days_open"])
            row["facilities"] = "|".join(r["facilities"])
            row["images"] = "|".join(r["images"])
            writer.writerow(row)


def validate(rows: list[dict]) -> list[str]:
    """Sanity checks: regency belongs to province, anchors consistent,
    coordinates inside the province bbox, addresses well-formed, slugs unique."""
    problems: list[str] = []
    slugs: set[str] = set()
    regency_owner = {}
    for prov, cfg in PROVINCES.items():
        for r in cfg["regencies"]:
            regency_owner.setdefault(r, prov)

    for prov, cfg in PROVINCES.items():
        anchors = cfg.get("anchors", {})
        if not (anchors.get("coastal") or anchors.get("inland")):
            problems.append(f"{prov}: tidak punya anchor sama sekali")
        for kind in ("coastal", "inland"):
            for a in anchors.get(kind, []):
                if a["regency"] not in cfg["regencies"]:
                    problems.append(f"{prov}: anchor {a['regency']} tidak ada di daftar kabupaten")
                if kind == "coastal" and a["regency"] not in cfg["coastal"]:
                    problems.append(f"{prov}: anchor pesisir {a['regency']} tidak di daftar coastal")
        # Coastal provinces must offer a coastal anchor, otherwise pantai/pulau
        # categories can never be placed there.
        if cfg["coastal"] and not anchors.get("coastal"):
            problems.append(f"{prov}: punya kabupaten pesisir tapi tanpa anchor coastal")

    for row in rows:
        owner = regency_owner.get(row["regency"])
        if owner != row["province"]:
            problems.append(f"{row['name']}: {row['regency']} tidak ada di {row['province']}")
        if row["address"].endswith("Indonesia") is False:
            problems.append(f"{row['name']}: alamat tidak lengkap")
        if row["slug"] in slugs:
            problems.append(f"duplicate slug: {row['slug']}")
        slugs.add(row["slug"])
        if row.get("_real"):
            # Real-world rows come from Wikidata and are trusted as-is: they can
            # legitimately sit outside our coarse bboxes or in a regency that our
            # manual coastal list does not flag.
            continue
        if row["category"] in COASTAL_CATEGORIES and row["regency"] not in PROVINCES[row["province"]]["coastal"]:
            problems.append(f"{row['name']}: kategori pesisir di {row['regency']} (bukan pesisir)")
        lat_min, lat_max, lon_min, lon_max = PROVINCES[row["province"]]["bbox"]
        lat, lon = float(row["latitude"]), float(row["longitude"])
        if not (lat_min - 0.05 <= lat <= lat_max + 0.05 and lon_min - 0.05 <= lon <= lon_max + 0.05):
            problems.append(f"{row['name']}: koordinat di luar bbox {row['province']}")
        images = row.get("images") or []
        if len(images) < 2:
            problems.append(f"{row['name']}: hanya {len(images)} gambar (minimal 2)")
        if any(not u.startswith("https://") for u in images):
            problems.append(f"{row['name']}: URL gambar tidak valid")
    return problems


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate BerWisata destinations dataset")
    parser.add_argument("--output", default="app/ml/data/destinations.csv")
    parser.add_argument("--rows", type=int, default=None)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--real-data", default="app/ml/data/real_destinations.csv")
    args = parser.parse_args()

    real_pool = load_real_pool(Path(args.real_data)) if args.real_data else []
    if args.rows is None:
        args.rows = len(real_pool) if real_pool else 6000

    rows = generate_rows(args.rows, args.seed, real_pool=real_pool or None)
    out = Path(args.output)
    write_csv(rows, out)

    problems = validate(rows)
    print(f"Generated {len(rows)} destinations -> {out} "
          f"({len(real_pool)} real, {max(0, len(rows) - len(real_pool))} synthetic)")
    print(f"Provinces: {len(set(r['province'] for r in rows))}")
    print("Top categories:", Counter(r["category"] for r in rows).most_common(5))
    print("Score range:", min(r["hidden_gem_score"] for r in rows), "-", max(r["hidden_gem_score"] for r in rows))
    if problems:
        print(f"VALIDATION: {len(problems)} masalah")
        for p in problems[:10]:
            print("  -", p)
    else:
        print("VALIDATION: OK — semua regency sesuai provinsi, alamat benar, slug unik")


if __name__ == "__main__":
    main()
