import { useEffect, useState } from "react";

export function useGeolocation() {
  const [coords, setCoords] = useState(() => {
    const lat = localStorage.getItem("user_lat");
    const lon = localStorage.getItem("user_lon");
    return lat && lon ? { latitude: Number(lat), longitude: Number(lon) } : null;
  });
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);

  const enable = () => {
    if (!navigator.geolocation) {
      setError("Geolocation tidak didukung browser ini");
      return;
    }
    setLoading(true);
    setError(null);
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        const c = {
          latitude: pos.coords.latitude,
          longitude: pos.coords.longitude,
        };
        setCoords(c);
        localStorage.setItem("user_lat", String(c.latitude));
        localStorage.setItem("user_lon", String(c.longitude));
        setLoading(false);
      },
      (err) => {
        setError(err.message || "Gagal mengambil lokasi");
        setLoading(false);
      },
      { enableHighAccuracy: true, timeout: 10_000 }
    );
  };

  return { coords, error, loading, enable };
}
