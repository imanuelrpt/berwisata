import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Link, useNavigate, useParams } from "react-router-dom";
import {
  MapPin,
  Clock,
  Phone,
  Globe,
  Instagram,
  Heart,
  Share2,
  Navigation,
  ArrowLeft,
  Users,
  Eye,
  Calendar,
  DollarSign,
  Gem,
} from "lucide-react";
import api from "../lib/api";
import {
  formatRupiah,
  formatCompact,
  formatDistance,
  formatDuration,
  getErrorMessage,
} from "../lib/format";
import RatingStars from "../components/ui/RatingStars";
import WeatherWidget from "../components/WeatherWidget";
import DestinationMap from "../components/map/DestinationMap";
import Alert from "../components/ui/Alert";
import Button from "../components/ui/Button";
import Spinner from "../components/ui/Spinner";
import { useAuth } from "../context/AuthContext";
import { useGeolocation } from "../hooks/useGeolocation";

const FACILITY_LABELS = {
  parkir: "Parkir",
  spot_foto: "Spot foto",
  toilet: "Toilet",
  mushola: "Mushola",
  warung_makan: "Warung makan",
  penginapan: "Penginapan",
  camping_ground: "Camping ground",
  restoran: "Restoran",
  wahana_anak: "Wahana anak",
  area_piknik: "Area piknik",
  toko_souvenir: "Toko souvenir",
  penyewaan_alat: "Penyewaan alat",
  area_kemah: "Area kemah",
  area_memancing: "Area memancing",
  jembatan_gantung: "Jembatan gantung",
  wifi: "Wi-Fi",
};

function RatingForm({ destinationId }) {
  const { isAuthenticated } = useAuth();
  const queryClient = useQueryClient();
  const [score, setScore] = useState(0);
  const [hover, setHover] = useState(0);
  const [comment, setComment] = useState("");
  const navigate = useNavigate();

  const mutation = useMutation({
    mutationFn: async (payload) => {
      const res = await api.post(`/destinations/${destinationId}/ratings`, payload);
      return res.data.data;
    },
    onSuccess: () => {
      setScore(0);
      setComment("");
      queryClient.invalidateQueries({ queryKey: ["ratings", destinationId] });
    },
  });

  if (!isAuthenticated) {
    return (
      <Alert type="info" className="mt-4">
        <Link to="/login" className="font-bold underline">
          Masuk
        </Link>{" "}
        untuk memberi rating dan ulasan.
      </Alert>
    );
  }

  return (
    <form
      className="mt-4 space-y-3"
      onSubmit={(e) => {
        e.preventDefault();
        if (score > 0) mutation.mutate({ score, comment: comment.trim() || null });
      }}
    >
      <div className="flex items-center gap-1">
        {[1, 2, 3, 4, 5].map((i) => (
          <button
            key={i}
            type="button"
            onMouseEnter={() => setHover(i)}
            onMouseLeave={() => setHover(0)}
            onClick={() => setScore(i)}
            className="p-0.5"
            aria-label={`${i} bintang`}
          >
            <RatingStars rating={hover || score} size="lg" />
          </button>
        ))}
        <span className="ml-2 text-sm font-semibold text-ink-700">
          {score > 0 ? `${score}/5` : "Pilih rating"}
        </span>
      </div>
      <textarea
        value={comment}
        onChange={(e) => setComment(e.target.value)}
        rows={3}
        placeholder="Bagikan pengalamanmu di sini..."
        className="input"
      />
      <Button type="submit" loading={mutation.isPending} disabled={score === 0}>
        Kirim Rating
      </Button>
      {mutation.isError && <Alert type="error">{getErrorMessage(mutation.error)}</Alert>}
    </form>
  );
}

function ReviewList({ destinationId }) {
  const { data, isLoading } = useQuery({
    queryKey: ["ratings", destinationId],
    queryFn: async () => {
      const res = await api.get(`/destinations/${destinationId}/ratings`, { params: { per_page: 10 } });
      return res.data.data;
    },
  });

  if (isLoading) return <Spinner className="mt-4" />;
  if (!data?.data?.length) return null;

  return (
    <div className="mt-4 space-y-4">
      <h3 className="text-lg font-bold text-ink-900">Ulasan Pengunjung ({data.meta.total})</h3>
      {data.data.map((r) => (
        <div key={r.id} className="rounded-2xl border border-ink-100 p-4">
          <div className="flex items-center justify-between">
            <p className="text-sm font-bold text-ink-800">@{r.username}</p>
            <RatingStars rating={r.score} size="sm" />
          </div>
          {r.comment && <p className="mt-2 text-sm text-ink-600">{r.comment}</p>}
        </div>
      ))}
    </div>
  );
}

export default function Detail() {
  const { id } = useParams();
  const { isAuthenticated } = useAuth();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { coords, enable, loading: geoLoading } = useGeolocation();
  const [transport, setTransport] = useState("car");
  const [showRoute, setShowRoute] = useState(false);
  const [copied, setCopied] = useState(false);

  const { data: dest, isLoading, isError, error } = useQuery({
    queryKey: ["destination", id],
    queryFn: async () => {
      const res = await api.get(`/destinations/${id}`);
      return res.data.data;
    },
  });

  const routeQuery = useQuery({
    queryKey: ["route", id, transport, coords?.latitude, coords?.longitude],
    queryFn: async () => {
      const res = await api.get(`/destinations/${id}/route`, {
        params: {
          latitude: coords.latitude,
          longitude: coords.longitude,
          transport,
        },
      });
      return res.data.data;
    },
    enabled: showRoute && Boolean(coords) && Boolean(dest),
  });

  const favMutation = useMutation({
    mutationFn: async () => {
      if (dest.is_favorited) {
        await api.delete(`/favorites/${id}`);
        return { is_favorited: false };
      }
      await api.post("/favorites", { destination_id: Number(id) });
      return { is_favorited: true };
    },
    onSuccess: (result) => {
      queryClient.setQueryData(["destination", id], (old) => ({ ...old, is_favorited: result.is_favorited }));
      queryClient.invalidateQueries({ queryKey: ["favorites"] });
    },
  });

  if (isLoading) {
    return (
      <div className="container-app flex justify-center py-24">
        <Spinner size="lg" />
      </div>
    );
  }

  if (isError) {
    return (
      <div className="container-app py-16">
        <Alert type="error">{getErrorMessage(error)}</Alert>
        <Button variant="secondary" className="mt-4" onClick={() => navigate(-1)}>
          <ArrowLeft className="h-4 w-4" /> Kembali
        </Button>
      </div>
    );
  }

  const images = dest.images?.length ? dest.images : null;
  const primary = images?.find((i) => i.is_primary) || images?.[0];

  const share = async () => {
    const url = window.location.href;
    try {
      await navigator.clipboard.writeText(url);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      /* ignore */
    }
  };

  const toggleFav = () => {
    if (!isAuthenticated) {
      navigate("/login");
      return;
    }
    favMutation.mutate();
  };

  return (
    <div className="container-app py-8">
      <button className="btn-ghost mb-4 px-3 py-2 text-sm" onClick={() => navigate(-1)}>
        <ArrowLeft className="h-4 w-4" /> Kembali
      </button>

      <div className="grid grid-cols-1 gap-8 lg:grid-cols-3">
        <div className="space-y-6 lg:col-span-2">
          <div>
            <div className="mb-2 flex flex-wrap items-center gap-2">
              {dest.category && (
                <Link
                  to={`/search?category=${dest.category.slug}`}
                  className="badge bg-brand-50 text-brand-700"
                >
                  {dest.category.name}
                </Link>
              )}
              {dest.is_trending && <span className="badge bg-amber-100 text-amber-700">Tren</span>}
              {dest.is_free && <span className="badge bg-sky-100 text-sky-700">Gratis</span>}
            </div>
            <h1 className="text-3xl font-extrabold tracking-tight text-ink-900 sm:text-4xl">
              {dest.name}
            </h1>
            <p className="mt-2 flex items-center gap-1.5 text-sm text-ink-500">
              <MapPin className="h-4 w-4" /> {dest.address}
            </p>
            <div className="mt-3 flex flex-wrap items-center gap-4 text-sm text-ink-600">
              <span className="flex items-center gap-1.5">
                <RatingStars rating={dest.rating} size="sm" />
                <b>{dest.rating}</b> ({formatCompact(dest.review_count)} ulasan)
              </span>
              <span className="flex items-center gap-1.5">
                <Eye className="h-4 w-4" /> {formatCompact(dest.view_count)} dilihat
              </span>
              <span className="flex items-center gap-1.5">
                <Users className="h-4 w-4" /> {formatCompact(dest.visitor_count)} pengunjung
              </span>
            </div>
          </div>

          {images?.length > 1 ? (
            <div className="grid grid-cols-2 gap-2">
              <img
                src={primary.url}
                alt={dest.name}
                className="col-span-2 aspect-[16/9] w-full rounded-2xl object-cover"
              />
              {images.slice(1, 5).map((img) => (
                <img key={img.id} src={img.url} alt={img.caption || dest.name} className="aspect-[4/3] w-full rounded-xl object-cover" />
              ))}
            </div>
          ) : primary ? (
            <img src={primary.url} alt={dest.name} className="aspect-[16/9] w-full rounded-2xl object-cover" />
          ) : (
            <div className="flex aspect-[16/9] w-full items-center justify-center rounded-2xl bg-gradient-to-br from-brand-100 to-sky-100">
              <MapPin className="h-14 w-14 text-brand-400" />
            </div>
          )}

          <div className="card p-6">
            <h2 className="text-xl font-bold text-ink-900">Tentang Destinasi</h2>
            <p className="mt-3 whitespace-pre-line leading-relaxed text-ink-600">
              {dest.description || dest.summary || "Belum ada deskripsi."}
            </p>
          </div>

          <div className="card p-6">
            <h2 className="text-xl font-bold text-ink-900">Fasilitas</h2>
            {dest.facilities?.length ? (
              <div className="mt-3 flex flex-wrap gap-2">
                {dest.facilities.map((f) => (
                  <span key={f} className="badge bg-ink-100 text-ink-700">
                    {FACILITY_LABELS[f] || f}
                  </span>
                ))}
              </div>
            ) : (
              <p className="mt-2 text-sm text-ink-500">Belum ada data fasilitas.</p>
            )}
          </div>

          <div className="card overflow-hidden">
            <div className="p-6 pb-0">
              <h2 className="text-xl font-bold text-ink-900">Lokasi & Rute</h2>
            </div>
            <div className="p-3">
              <DestinationMap
                destinations={[{ ...dest, is_favorited: undefined }]}
                center={[dest.latitude, dest.longitude]}
                zoom={12}
                route={routeQuery.data}
                height="400px"
              />
            </div>
            <div className="flex flex-wrap items-center gap-3 p-5">
              {coords ? (
                <>
                  <select value={transport} onChange={(e) => setTransport(e.target.value)} className="input w-auto">
                    <option value="car">Mobil</option>
                    <option value="motorcycle">Motor</option>
                    <option value="foot-walking">Jalan kaki</option>
                  </select>
                  <Button onClick={() => setShowRoute((v) => !v)}>
                    <Navigation className="h-4 w-4" /> {showRoute ? "Sembunyikan rute" : "Tampilkan rute"}
                  </Button>
                  {routeQuery.isLoading && <Spinner />}
                  {routeQuery.data && (
                    <div className="w-full space-y-1 rounded-xl bg-ink-50 p-3 text-sm">
                      <p className="font-bold text-ink-800">Perkiraan perjalanan</p>
                      <p className="text-ink-600">
                        Jarak {formatDistance(routeQuery.data.distance_km)} ·{" "}
                        {formatDuration(routeQuery.data.duration_minutes)}
                      </p>
                    </div>
                  )}
                </>
              ) : (
                <Button onClick={enable} loading={geoLoading}>
                  <MapPin className="h-4 w-4" /> Aktifkan lokasi untuk rute
                </Button>
              )}
            </div>
          </div>

          <div className="card p-6">
            <h2 className="text-xl font-bold text-ink-900">Rating & Ulasan</h2>
            <ReviewList destinationId={id} />
            <RatingForm destinationId={id} />
          </div>
        </div>

        <aside className="space-y-5">
          <div className="card overflow-hidden">
            <div className="bg-gradient-to-br from-brand-600 to-teal-600 p-5 text-white">
              <div className="flex items-center justify-between">
                <p className="flex items-center gap-1.5 text-sm font-semibold text-white/90">
                  <Gem className="h-4 w-4" /> Skor Hidden Gem
                </p>
                <span className="text-4xl font-extrabold">{Math.round(dest.hidden_gem_score)}</span>
              </div>
              <p className="mt-1 text-xs text-white/80">
                Dihitung oleh model AI BerWisata berdasarkan kelangkaan, rating, dan keramaian.
              </p>
            </div>
            <div className="space-y-4 p-5">
              <div className="flex items-center justify-between">
                <span className="text-sm text-ink-500">Harga masuk</span>
                {dest.is_free ? (
                  <span className="font-bold text-brand-600">Gratis</span>
                ) : (
                  <span className="font-bold text-ink-900">
                    {formatRupiah(dest.price_min)}
                    {dest.price_max ? ` - ${formatRupiah(dest.price_max)}` : ""}
                  </span>
                )}
              </div>
              <div className="flex items-center justify-between">
                <span className="flex items-center gap-1.5 text-sm text-ink-500">
                  <Clock className="h-4 w-4" /> Jam buka
                </span>
                <span className="font-semibold text-ink-800">
                  {dest.is_open_24h ? "24 jam" : `${dest.opening_time} - ${dest.closing_time}`}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="flex items-center gap-1.5 text-sm text-ink-500">
                  <Calendar className="h-4 w-4" /> Hari buka
                </span>
                <span className="font-semibold text-ink-800">
                  {dest.days_open?.length ? `${dest.days_open.length} hari` : "-"}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="flex items-center gap-1.5 text-sm text-ink-500">
                  <DollarSign className="h-4 w-4" /> Rute dari Anda
                </span>
                <span className="font-semibold text-ink-800">{formatDistance(dest.distance_km)}</span>
              </div>
            </div>
            <div className="flex gap-2 border-t border-ink-100 p-4">
              <Button className="flex-1" variant={dest.is_favorited ? "danger" : "primary"} onClick={toggleFav} loading={favMutation.isPending}>
                <Heart className={`h-4 w-4 ${dest.is_favorited ? "fill-white" : ""}`} />
                {dest.is_favorited ? "Favorit" : "Simpan"}
              </Button>
              <Button variant="secondary" onClick={share}>
                <Share2 className="h-4 w-4" />
                {copied ? "Disalin!" : "Bagikan"}
              </Button>
            </div>
          </div>

          <WeatherWidget weather={dest.weather} />

          <div className="card space-y-3 p-5">
            <h3 className="font-bold text-ink-900">Kontak & Info</h3>
            {dest.phone && (
              <p className="flex items-center gap-2 text-sm text-ink-600">
                <Phone className="h-4 w-4 text-ink-400" /> {dest.phone}
              </p>
            )}
            {dest.website && (
              <a href={dest.website} target="_blank" rel="noreferrer" className="flex items-center gap-2 text-sm text-brand-600 hover:underline">
                <Globe className="h-4 w-4 text-ink-400" /> {dest.website}
              </a>
            )}
            {dest.instagram && (
              <a href={dest.instagram} target="_blank" rel="noreferrer" className="flex items-center gap-2 text-sm text-brand-600 hover:underline">
                <Instagram className="h-4 w-4 text-ink-400" /> {dest.instagram}
              </a>
            )}
          </div>
        </aside>
      </div>
    </div>
  );
}
