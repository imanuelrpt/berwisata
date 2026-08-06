export function formatRupiah(value) {
  if (value == null || Number.isNaN(Number(value))) return "-";
  return new Intl.NumberFormat("id-ID", {
    style: "currency",
    currency: "IDR",
    maximumFractionDigits: 0,
  }).format(Number(value));
}

export function formatNumber(value) {
  if (value == null || Number.isNaN(Number(value))) return "-";
  return new Intl.NumberFormat("id-ID").format(Number(value));
}

export function formatCompact(value) {
  if (value == null || Number.isNaN(Number(value))) return "-";
  return new Intl.NumberFormat("id-ID", {
    notation: "compact",
    maximumFractionDigits: 1,
  }).format(Number(value));
}

export function formatDistance(km) {
  if (km == null || Number.isNaN(Number(km))) return "-";
  const n = Number(km);
  if (n < 1) return `${Math.round(n * 1000)} m`;
  return `${n.toFixed(1)} km`;
}

export function formatDuration(minutes) {
  if (minutes == null || Number.isNaN(Number(minutes))) return "-";
  const n = Number(minutes);
  if (n < 60) return `${Math.round(n)} mnt`;
  const h = Math.floor(n / 60);
  const m = Math.round(n % 60);
  return m > 0 ? `${h} jam ${m} mnt` : `${h} jam`;
}

export function formatDate(iso) {
  if (!iso) return "-";
  return new Intl.DateTimeFormat("id-ID", {
    day: "numeric",
    month: "long",
    year: "numeric",
  }).format(new Date(iso));
}

export function getErrorMessage(error) {
  const details = error?.response?.data?.error?.details;
  if (Array.isArray(details) && details.length > 0) {
    const msg = details[0].message || "";
    return msg.replace(/^Value error,\s*/, "") || "Terjadi kesalahan";
  }
  return (
    error?.response?.data?.error?.message ||
    error?.response?.data?.message ||
    error?.message ||
    "Terjadi kesalahan"
  );
}
