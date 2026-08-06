import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { Sparkles, TrendingUp, MapPin, ArrowRight, Gem } from "lucide-react";
import api from "../lib/api";
import SearchBar from "../components/SearchBar";
import DestinationCard from "../components/DestinationCard";
import { DestinationCardSkeleton } from "../components/ui/Skeleton";
import { useGeolocation } from "../hooks/useGeolocation";
import { getErrorMessage } from "../lib/format";
import Alert from "../components/ui/Alert";

const CATEGORIES = [
  { slug: "pantai", label: "Pantai", emoji: "🏖️" },
  { slug: "air-terjun", label: "Air Terjun", emoji: "💦" },
  { slug: "gunung", label: "Gunung", emoji: "🏔️" },
  { slug: "danau", label: "Danau", emoji: "🌊" },
  { slug: "gua", label: "Gua", emoji: "🕳️" },
  { slug: "budaya", label: "Budaya", emoji: "🏛️" },
  { slug: "religi", label: "Religi", emoji: "🕌" },
  { slug: "pantai", label: "Pantai", emoji: "🏖️" },
  { slug: "pulau", label: "Pulau", emoji: "🏝️" },
  { slug: "taman", label: "Taman", emoji: "🌳" },
];

function useFeatured() {
  return useQuery({
    queryKey: ["destinations", "featured"],
    queryFn: async () => {
      const res = await api.get("/destinations", { params: { page: 1, per_page: 8 } });
      return res.data.data;
    },
  });
}

function useRecommendations(coords) {
  return useQuery({
    queryKey: ["recommendations", coords?.latitude, coords?.longitude],
    queryFn: async () => {
      const res = await api.post("/recommendations", {
        limit: 6,
        latitude: coords?.latitude,
        longitude: coords?.longitude,
      });
      return res.data.data.items;
    },
    enabled: Boolean(coords),
    staleTime: 5 * 60_000,
  });
}

export default function Home() {
  const featured = useFeatured();
  const { coords, enable, loading: geoLoading } = useGeolocation();
  const recs = useRecommendations(coords);

  return (
    <div>
      <section className="relative overflow-hidden bg-gradient-to-br from-brand-600 via-brand-500 to-teal-600 py-16 text-white sm:py-24">
        <div className="pointer-events-none absolute -right-24 -top-24 h-96 w-96 rounded-full bg-white/10" />
        <div className="pointer-events-none absolute -bottom-32 -left-16 h-96 w-96 rounded-full bg-white/10" />
        <div className="container-app relative">
          <div className="mx-auto max-w-3xl text-center">
            <span className="badge mb-4 bg-white/20 text-white backdrop-blur">
              <Gem className="h-3.5 w-3.5" /> Rekomendasi AI untuk permata tersembunyi
            </span>
            <h1 className="text-4xl font-extrabold leading-tight tracking-tight sm:text-5xl lg:text-6xl">
              Temukan Wisata <span className="text-amber-300">Tersembunyi</span> di Indonesia
            </h1>
            <p className="mt-4 text-lg text-white/90">
              Telusuri destinasi tersembunyi — tinggal pilih, kami antar ke sana.
            </p>
            <div className="mt-8">
              <SearchBar large />
            </div>
            <div className="mt-6 flex flex-wrap items-center justify-center gap-x-6 gap-y-2 text-sm text-white/85">
              <span className="inline-flex items-center gap-1.5">
                <MapPin className="h-4 w-4" /> 38 provinsi
              </span>
              <span className="inline-flex items-center gap-1.5">
                <Sparkles className="h-4 w-4" /> Skor AI
              </span>
              <span className="inline-flex items-center gap-1.5">
                <TrendingUp className="h-4 w-4" /> Rekomendasi personal
              </span>
            </div>
          </div>
        </div>
      </section>

      <section className="container-app py-10">
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-5">
          {CATEGORIES.map((c) => (
            <Link
              key={c.slug}
              to={`/search?category=${c.slug}`}
              className="card flex flex-col items-center gap-2 p-4 text-center transition hover:-translate-y-0.5 hover:shadow-lift"
            >
              <span className="text-3xl">{c.emoji}</span>
              <span className="text-sm font-bold text-ink-800">{c.label}</span>
            </Link>
          ))}
        </div>
      </section>

      <section className="container-app py-10">
        <div className="mb-6 flex items-center justify-between">
          <div>
            <h2 className="text-2xl font-extrabold text-ink-900">Destinasi Unggulan</h2>
            <p className="text-sm text-ink-500">Permata tersembunyi terbaik dari seluruh Indonesia</p>
          </div>
          <Link to="/search" className="btn-ghost text-sm">
            Lihat semua <ArrowRight className="h-4 w-4" />
          </Link>
        </div>
        {featured.isError && <Alert type="error">Gagal memuat: {getErrorMessage(featured.error)}</Alert>}
        <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4">
          {featured.isLoading &&
            Array.from({ length: 8 }).map((_, i) => <DestinationCardSkeleton key={i} />)}
          {featured.data?.data?.map((d) => (
            <DestinationCard key={d.id} destination={d} />
          ))}
        </div>
      </section>

      <section className="border-t border-ink-100 bg-white py-12">
        <div className="container-app">
          <div className="mb-6 flex items-center justify-between">
            <div>
              <h2 className="text-2xl font-extrabold text-ink-900">Rekomendasi di Sekitarmu</h2>
              <p className="text-sm text-ink-500">
                {coords
                  ? "Disortir berdasarkan skor AI dan kedekatan"
                  : "Aktifkan lokasi untuk rekomendasi personal"}
              </p>
            </div>
            {!coords && (
              <button onClick={enable} className="btn-primary px-4 py-2 text-sm" disabled={geoLoading}>
                <MapPin className="h-4 w-4" />
                {geoLoading ? "Mencari..." : "Aktifkan Lokasi"}
              </button>
            )}
          </div>
          {coords ? (
            recs.isLoading ? (
              <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-3">
                {Array.from({ length: 3 }).map((_, i) => (
                  <DestinationCardSkeleton key={i} />
                ))}
              </div>
            ) : recs.data?.length ? (
              <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-3">
                {recs.data.map((r) => (
                  <DestinationCard key={r.destination.id} destination={r.destination} showDistance />
                ))}
              </div>
            ) : (
              <Alert type="info">Belum ada rekomendasi. Coba perluas jangkauan pencarian.</Alert>
            )
          ) : (
            <div className="card flex flex-col items-center gap-3 p-8 text-center">
              <MapPin className="h-10 w-10 text-brand-500" />
              <p className="max-w-md text-sm text-ink-500">
                Beri tahu kami lokasimu agar rekomendasi AI lebih relevan — berdasarkan jarak dan
                preferensi.
              </p>
            </div>
          )}
        </div>
      </section>
    </div>
  );
}
