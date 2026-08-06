import { Link } from "react-router-dom";
import { MapPin, Heart, Gem } from "lucide-react";
import { formatDistance, formatRupiah } from "../lib/format";
import RatingStars from "./ui/RatingStars";

export default function DestinationCard({ destination, showDistance = true }) {
  const img = destination.images?.find((i) => i.is_primary) || destination.images?.[0];
  const gemTier =
    destination.hidden_gem_score >= 75
      ? "bg-brand-600 text-white"
      : destination.hidden_gem_score >= 55
      ? "bg-brand-100 text-brand-700"
      : "bg-amber-100 text-amber-700";

  return (
    <Link
      to={`/destinations/${destination.id}`}
      className="card group overflow-hidden transition-transform duration-200 hover:-translate-y-1 hover:shadow-lift"
    >
      <div className="relative h-48 overflow-hidden">
        {img ? (
          <img
            src={img.url}
            alt={destination.name}
            loading="lazy"
            className="h-full w-full object-cover transition-transform duration-300 group-hover:scale-105"
          />
        ) : (
          <div className="flex h-full w-full items-center justify-center bg-gradient-to-br from-brand-100 to-sky-100">
            <MapPin className="h-10 w-10 text-brand-400" />
          </div>
        )}
        <div className="absolute left-3 top-3 flex gap-2">
          <span className={`badge shadow ${gemTier}`}>
            <Gem className="h-3 w-3" />
            {Math.round(destination.hidden_gem_score)}
          </span>
          {destination.category && (
            <span className="badge bg-white/90 text-ink-700 shadow backdrop-blur">
              {destination.category.name}
            </span>
          )}
        </div>
        {destination.is_favorited && (
          <span className="absolute right-3 top-3 flex h-8 w-8 items-center justify-center rounded-full bg-white/90 shadow backdrop-blur">
            <Heart className="h-4 w-4 fill-red-500 text-red-500" />
          </span>
        )}
      </div>
      <div className="space-y-2 p-4">
        <h3 className="line-clamp-1 font-bold text-ink-900 group-hover:text-brand-700">
          {destination.name}
        </h3>
        <p className="line-clamp-1 flex items-center gap-1 text-xs text-ink-500">
          <MapPin className="h-3.5 w-3.5 shrink-0" />
          {destination.regency}, {destination.province}
        </p>
        <div className="flex items-center justify-between pt-1">
          <div className="flex items-center gap-2">
            <RatingStars rating={destination.rating} size="sm" />
            <span className="text-xs font-semibold text-ink-700">{destination.rating}</span>
          </div>
          {destination.is_free ? (
            <span className="text-sm font-bold text-brand-600">Gratis</span>
          ) : (
            <span className="text-sm font-bold text-ink-900">
              {formatRupiah(destination.price_min)}
            </span>
          )}
        </div>
        {showDistance && destination.distance_km != null && (
          <p className="text-xs font-medium text-sky-600">{formatDistance(destination.distance_km)} dari Anda</p>
        )}
      </div>
    </Link>
  );
}
