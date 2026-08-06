import { MapContainer, TileLayer, Marker, Popup, Polyline, CircleMarker } from "react-leaflet";
import L from "leaflet";
import { useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { decodePolyline } from "../../lib/polyline";

delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png",
  iconUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png",
  shadowUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png",
});

const userIcon = L.divIcon({
  className: "",
  html: `<div class="relative flex h-8 w-8">
    <span class="absolute inline-flex h-full w-full animate-ping rounded-full bg-brand-400 opacity-60"></span>
    <span class="relative inline-flex h-8 w-8 items-center justify-center rounded-full bg-brand-600 text-white text-xs font-bold">S</span>
  </div>`,
  iconSize: [32, 32],
  iconAnchor: [16, 16],
});

function DestinationMarker({ d, showPopup = false }) {
  const navigate = useNavigate();
  return (
    <Marker
      position={[d.latitude, d.longitude]}
      eventHandlers={{
        click: () => navigate(`/destinations/${d.id}`),
      }}
    >
      <Popup>
        <div className="min-w-[160px]">
          <p className="mb-1 font-bold text-ink-900">{d.name}</p>
          <p className="text-xs text-ink-500">
            {d.regency}, {d.province}
          </p>
          <p className="mt-1 text-xs font-semibold text-brand-600">Hidden gem: {Math.round(d.hidden_gem_score)}</p>
          <button
            className="mt-2 w-full rounded-lg bg-brand-600 px-3 py-1.5 text-xs font-bold text-white hover:bg-brand-700"
            onClick={() => navigate(`/destinations/${d.id}`)}
          >
            Lihat detail
          </button>
        </div>
      </Popup>
    </Marker>
  );
}

export default function DestinationMap({
  destinations = [],
  center = [-2.5, 118],
  zoom = 5,
  userLocation = null,
  route = null,
  activeId = null,
  height = "500px",
}) {
  useEffect(() => {
    // keep the map container crisp after async render
  }, [destinations, center]);

  const rawGeo = route?.geometry;
  const routeCoords = Array.isArray(rawGeo) ? rawGeo : typeof rawGeo === "string" ? decodePolyline(rawGeo) : null;

  return (
    <MapContainer
      center={center}
      zoom={zoom}
      style={{ height, width: "100%" }}
      scrollWheelZoom
      className="z-0 rounded-2xl"
    >
      <TileLayer
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
        url="https://tile.openstreetmap.org/{z}/{x}/{y}.png"
      />
      {userLocation && (
        <CircleMarker
          center={userLocation}
          pathOptions={{ color: "#16c462", fillColor: "#16c462", fillOpacity: 0.15, weight: 2 }}
          radius={12}
        />
      )}
      {userLocation && <Marker position={userLocation} icon={userIcon} />}
      {destinations.map((d) => (
        <DestinationMarker key={d.id} d={d} showPopup={d.id === activeId} />
      ))}
      {routeCoords && (
        <Polyline
          positions={routeCoords}
          pathOptions={{ color: "#0aa04c", weight: 5, opacity: 0.85 }}
        />
      )}
    </MapContainer>
  );
}
