import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Search, MapPin } from "lucide-react";
import { useGeolocation } from "../hooks/useGeolocation";

export default function SearchBar({ initialQuery = "", large = false }) {
  const [query, setQuery] = useState(initialQuery);
  const navigate = useNavigate();
  const { coords, enable, loading } = useGeolocation();

  const submit = (e) => {
    e.preventDefault();
    const params = new URLSearchParams();
    if (query.trim()) params.set("q", query.trim());
    if (coords) {
      params.set("lat", coords.latitude.toFixed(5));
      params.set("lon", coords.longitude.toFixed(5));
    }
    navigate(`/search?${params.toString()}`);
  };

  return (
    <form onSubmit={submit} className={`flex w-full flex-col gap-2 ${large ? "sm:flex-row" : ""}`}>
      <div className="relative flex-1">
        <Search className="pointer-events-none absolute left-4 top-1/2 h-5 w-5 -translate-y-1/2 text-ink-400" />
        <input
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Cari wisata tersembunyi, mis. Pantai, Air Terjun..."
          className={`input pl-12 ${large ? "py-3.5 text-base" : ""}`}
        />
      </div>
      {!coords && !loading ? (
        <button
          type="button"
          onClick={enable}
          className="btn-secondary px-4 py-2.5 text-sm"
          title="Gunakan lokasi saya"
        >
          <MapPin className="h-4 w-4" /> Pakai Lokasi Saya
        </button>
      ) : loading ? (
        <button type="button" className="btn-secondary cursor-wait px-4 py-2.5 text-sm" disabled>
          <MapPin className="h-4 w-4 animate-pulse" /> Mencari lokasi...
        </button>
      ) : (
        <button type="button" className="btn-secondary px-4 py-2.5 text-sm" disabled title="Lokasi aktif">
          <MapPin className="h-4 w-4 text-brand-600" /> Lokasi Aktif
        </button>
      )}
      <button type="submit" className={`btn-primary ${large ? "px-8 py-3.5 text-base" : "px-6 py-2.5 text-sm"}`}>
        Cari
      </button>
    </form>
  );
}
