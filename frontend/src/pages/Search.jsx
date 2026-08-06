import { useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { useSearchParams } from "react-router-dom";
import { SlidersHorizontal, Map as MapIcon, LayoutGrid, X, Search as SearchIcon } from "lucide-react";
import api from "../lib/api";
import DestinationCard from "../components/DestinationCard";
import DestinationMap from "../components/map/DestinationMap";
import Pagination from "../components/ui/Pagination";
import EmptyState from "../components/ui/EmptyState";
import Alert from "../components/ui/Alert";
import { DestinationCardSkeleton } from "../components/ui/Skeleton";
import { getErrorMessage } from "../lib/format";

const PROVINCES = [
  "Aceh", "Sumatera Utara", "Sumatera Barat", "Riau", "Jambi", "Sumatera Selatan", "Bengkulu",
  "Lampung", "Kepulauan Riau", "Kepulauan Bangka Belitung", "DKI Jakarta", "Jawa Barat",
  "Jawa Tengah", "DI Yogyakarta", "Jawa Timur", "Banten", "Bali", "Nusa Tenggara Barat",
  "Nusa Tenggara Timur", "Kalimantan Barat", "Kalimantan Tengah", "Kalimantan Selatan",
  "Kalimantan Timur", "Kalimantan Utara", "Sulawesi Utara", "Sulawesi Tengah", "Sulawesi Selatan",
  "Sulawesi Tenggara", "Gorontalo", "Sulawesi Barat", "Maluku", "Maluku Utara", "Papua",
  "Papua Barat", "Papua Tengah", "Papua Pegunungan", "Papua Selatan", "Papua Barat Daya",
];

export default function Search() {
  const [params, setParams] = useSearchParams();
  const [queryInput, setQueryInput] = useState(params.get("q") || "");
  const [view, setView] = useState("grid");

  const q = params.get("q") || "";
  const category = params.get("category") || "";
  const province = params.get("province") || "";
  const sort = params.get("sort") || "hidden_gem";
  const lat = params.get("lat") ? Number(params.get("lat")) : null;
  const lon = params.get("lon") ? Number(params.get("lon")) : null;
  const page = Number(params.get("page") || "1");

  const filters = useMemo(
    () => ({
      page,
      per_page: 12,
      query: q || null,
      category_slug: category || null,
      province: province || null,
      sort_by: sort,
      order: sort === "price_asc" || sort === "price_desc" ? "asc" : "desc",
      latitude: lat,
      longitude: lon,
    }),
    [q, category, province, sort, lat, lon, page]
  );

  const { data, isLoading, isError, error, refetch } = useQuery({
    queryKey: ["search", filters],
    queryFn: async () => {
      const res = await api.post("/destinations/search", filters);
      return res.data.data;
    },
  });

  const updateParam = (key, value) => {
    const next = new URLSearchParams(params);
    if (value) next.set(key, value);
    else next.delete(key);
    next.delete("page");
    setParams(next, { replace: true });
  };

  const submitQuery = (e) => {
    e.preventDefault();
    updateParam("q", queryInput.trim());
  };

  const center = lat && lon ? [lat, lon] : null;

  return (
    <div className="container-app py-8">
      <div className="mb-6">
        <h1 className="text-3xl font-extrabold text-ink-900">Jelajahi Destinasi</h1>
        <p className="mt-1 text-sm text-ink-500">
          {data?.meta?.total != null
            ? `${data.meta.total.toLocaleString("id-ID")} destinasi ditemukan`
            : "Cari dan filter ribuan destinasi tersembunyi"}
        </p>
      </div>

      <form onSubmit={submitQuery} className="mb-4 flex gap-2">
        <div className="relative flex-1">
          <SearchIcon className="pointer-events-none absolute left-4 top-1/2 h-5 w-5 -translate-y-1/2 text-ink-400" />
          <input
            value={queryInput}
            onChange={(e) => setQueryInput(e.target.value)}
            placeholder="Kata kunci..."
            className="input pl-12"
          />
        </div>
        <button type="submit" className="btn-primary px-6">
          Cari
        </button>
      </form>

      <div className="card mb-6 flex flex-wrap items-center gap-3 p-4">
        <SlidersHorizontal className="h-5 w-5 text-ink-400" />
        <select
          value={category}
          onChange={(e) => updateParam("category", e.target.value)}
          className="input w-auto"
        >
          <option value="">Semua kategori</option>
          <option value="pantai">Pantai</option>
          <option value="air-terjun">Air Terjun</option>
          <option value="gunung">Gunung</option>
          <option value="danau">Danau</option>
          <option value="gua">Gua</option>
          <option value="budaya">Budaya</option>
          <option value="religi">Religi</option>
          <option value="pantai">Pantai</option>
          <option value="pulau">Pulau</option>
          <option value="taman">Taman</option>
        </select>
        <select
          value={province}
          onChange={(e) => updateParam("province", e.target.value)}
          className="input w-auto"
        >
          <option value="">Semua provinsi</option>
          {PROVINCES.map((p) => (
            <option key={p} value={p}>
              {p}
            </option>
          ))}
        </select>
        <select
          value={sort}
          onChange={(e) => updateParam("sort", e.target.value)}
          className="input w-auto"
        >
          <option value="hidden_gem">Skor hidden gem tertinggi</option>
          <option value="rating">Rating tertinggi</option>
          <option value="price_asc">Harga termurah</option>
          <option value="price_desc">Harga termahal</option>
          <option value="popular">Paling populer</option>
          {lat && lon && <option value="distance">Terdekat</option>}
        </select>
        <div className="ml-auto flex gap-1 rounded-xl bg-ink-100 p-1">
          <button
            className={`rounded-lg p-2 ${view === "grid" ? "bg-white shadow" : ""}`}
            onClick={() => setView("grid")}
            aria-label="Tampilan grid"
          >
            <LayoutGrid className="h-4 w-4" />
          </button>
          <button
            className={`rounded-lg p-2 ${view === "map" ? "bg-white shadow" : ""}`}
            onClick={() => setView("map")}
            aria-label="Tampilan peta"
          >
            <MapIcon className="h-4 w-4" />
          </button>
        </div>
        {q && (
          <button
            className="btn-ghost px-3 py-2 text-sm"
            onClick={() => {
              updateParam("q", "");
              setQueryInput("");
            }}
          >
            <X className="h-4 w-4" /> Hapus
          </button>
        )}
      </div>

      {isError && (
        <Alert type="error" className="mb-6">
          Gagal memuat: {getErrorMessage(error)}{" "}
          <button onClick={refetch} className="ml-2 font-bold underline">
            Coba lagi
          </button>
        </Alert>
      )}

      {view === "map" ? (
        <div className="card overflow-hidden p-2">
          <DestinationMap
            destinations={data?.data || []}
            center={center || (data?.data?.[0] ? [data.data[0].latitude, data.data[0].longitude] : [-2.5, 118])}
            zoom={center ? 10 : 5}
            height="600px"
          />
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
          {isLoading &&
            Array.from({ length: 8 }).map((_, i) => <DestinationCardSkeleton key={i} />)}
          {data?.data?.map((d) => (
            <DestinationCard key={d.id} destination={d} showDistance />
          ))}
        </div>
      )}

      {!isLoading && !isError && data?.data?.length === 0 && (
        <EmptyState
          title="Tidak ada destinasi yang cocok"
          subtitle="Coba ubah kata kunci atau filter pencarianmu."
        />
      )}

      <Pagination meta={data?.meta} onChange={(p) => updateParam("page", String(p))} />
    </div>
  );
}
