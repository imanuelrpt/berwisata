import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Plus, Pencil, Trash2, Download, Upload, X, MapPin, Gem } from "lucide-react";
import api from "../../lib/api";
import Alert from "../../components/ui/Alert";
import Button from "../../components/ui/Button";
import Spinner from "../../components/ui/Spinner";
import Pagination from "../../components/ui/Pagination";
import { getErrorMessage, formatNumber } from "../../lib/format";

const PROVINCES = [
  "Aceh", "Sumatera Utara", "Sumatera Barat", "Riau", "Jambi", "Sumatera Selatan", "Bengkulu",
  "Lampung", "Kepulauan Riau", "Kepulauan Bangka Belitung", "DKI Jakarta", "Jawa Barat",
  "Jawa Tengah", "DI Yogyakarta", "Jawa Timur", "Banten", "Bali", "Nusa Tenggara Barat",
  "Nusa Tenggara Timur", "Kalimantan Barat", "Kalimantan Tengah", "Kalimantan Selatan",
  "Kalimantan Timur", "Kalimantan Utara", "Sulawesi Utara", "Sulawesi Tengah", "Sulawesi Selatan",
  "Sulawesi Tenggara", "Gorontalo", "Sulawesi Barat", "Maluku", "Maluku Utara", "Papua",
  "Papua Barat", "Papua Tengah", "Papua Pegunungan", "Papua Selatan", "Papua Barat Daya",
];

const DAYS = [
  { value: "mon", label: "Sen" },
  { value: "tue", label: "Sel" },
  { value: "wed", label: "Rab" },
  { value: "thu", label: "Kam" },
  { value: "fri", label: "Jum" },
  { value: "sat", label: "Sab" },
  { value: "sun", label: "Min" },
];

const FACILITY_OPTIONS = [
  "parkir", "spot_foto", "toilet", "mushola", "warung_makan", "penginapan",
  "camping_ground", "restoran", "wahana_anak", "area_piknik", "toko_souvenir",
  "penyewaan_alat", "area_kemah", "area_memancing", "jembatan_gantung", "wifi",
];

const emptyForm = {
  name: "",
  category_id: "",
  address: "",
  province: "",
  regency: "",
  district: "",
  latitude: "",
  longitude: "",
  price_min: 0,
  price_max: "",
  is_free: false,
  opening_time: "08:00",
  closing_time: "17:00",
  is_open_24h: false,
  days_open: DAYS.map((d) => d.value),
  facilities: [],
  rating: 4.0,
  review_count: 0,
  visitor_count: 1000,
  safety: 4.0,
  cleanliness: 4.0,
  beauty: 4.0,
  road_access: 3.5,
  crowd_level: 3.0,
  phone: "",
  is_featured: false,
  is_trending: false,
};

function DestinationForm({ editing, initial, onClose }) {
  const [form, setForm] = useState(() =>
    editing
      ? {
          ...initial,
          latitude: String(initial.latitude),
          longitude: String(initial.longitude),
          price_min: Number(initial.price_min || 0),
          price_max: initial.price_max != null ? Number(initial.price_max) : "",
          category_id: String(initial.category_id),
        }
      : emptyForm
  );
  const queryClient = useQueryClient();
  const [error, setError] = useState("");

  const categoriesQuery = useQuery({
    queryKey: ["categories"],
    queryFn: async () => {
      const res = await api.get("/categories");
      return res.data.data.data;
    },
  });

  const mutation = useMutation({
    mutationFn: async (payload) => {
      if (editing) {
        const res = await api.patch(`/destinations/${initial.id}`, payload);
        return res.data.data;
      }
      const res = await api.post("/destinations", payload);
      return res.data.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["admin", "destinations"] });
      onClose();
    },
    onError: (err) => setError(getErrorMessage(err)),
  });

  const set = (k, v) => setForm((f) => ({ ...f, [k]: v }));

  const toggleDay = (d) => {
    set("days_open", form.days_open.includes(d) ? form.days_open.filter((x) => x !== d) : [...form.days_open, d]);
  };

  const toggleFacility = (f) => {
    set("facilities", form.facilities.includes(f) ? form.facilities.filter((x) => x !== f) : [...form.facilities, f]);
  };

  const submit = (e) => {
    e.preventDefault();
    const payload = {
      ...form,
      category_id: Number(form.category_id),
      latitude: Number(form.latitude),
      longitude: Number(form.longitude),
      price_min: Number(form.price_min || 0),
      price_max: form.price_max === "" ? null : Number(form.price_max),
    };
    mutation.mutate(payload);
  };

  const input = "input";
  const label = "label";

  return (
    <div className="fixed inset-0 z-50 flex items-start justify-center overflow-y-auto bg-black/40 p-4 backdrop-blur-sm">
      <div className="card w-full max-w-2xl p-6">
        <div className="mb-4 flex items-center justify-between">
          <h2 className="text-xl font-extrabold text-ink-900">{editing ? "Edit Destinasi" : "Tambah Destinasi"}</h2>
          <button onClick={onClose} className="rounded-lg p-2 hover:bg-ink-100" aria-label="Tutup">
            <X className="h-5 w-5" />
          </button>
        </div>
        {error && <Alert type="error" className="mb-4">{error}</Alert>}
        <form onSubmit={submit} className="space-y-4">
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
            <div>
              <label className={label}>Nama *</label>
              <input className={input} required value={form.name} onChange={(e) => set("name", e.target.value)} />
            </div>
            <div>
              <label className={label}>Kategori *</label>
              <select
                className={input}
                required
                value={form.category_id}
                onChange={(e) => set("category_id", e.target.value)}
              >
                <option value="">Pilih kategori</option>
                {categoriesQuery.data?.map((c) => (
                  <option key={c.id} value={c.id}>{c.name}</option>
                ))}
              </select>
            </div>
            <div className="sm:col-span-2">
              <label className={label}>Alamat *</label>
              <input className={input} required value={form.address} onChange={(e) => set("address", e.target.value)} />
            </div>
            <div>
              <label className={label}>Provinsi *</label>
              <select className={input} required value={form.province} onChange={(e) => set("province", e.target.value)}>
                <option value="">Pilih provinsi</option>
                {PROVINCES.map((p) => (
                  <option key={p} value={p}>{p}</option>
                ))}
              </select>
            </div>
            <div>
              <label className={label}>Kabupaten/Kota *</label>
              <input className={input} required value={form.regency} onChange={(e) => set("regency", e.target.value)} />
            </div>
            <div>
              <label className={label}>Latitude *</label>
              <input
                className={input}
                required
                type="number"
                step="any"
                value={form.latitude}
                onChange={(e) => set("latitude", e.target.value)}
              />
            </div>
            <div>
              <label className={label}>Longitude *</label>
              <input
                className={input}
                required
                type="number"
                step="any"
                value={form.longitude}
                onChange={(e) => set("longitude", e.target.value)}
              />
            </div>
            <div>
              <label className={label}>Harga min (Rp)</label>
              <input className={input} type="number" value={form.price_min} onChange={(e) => set("price_min", e.target.value)} />
            </div>
            <div>
              <label className={label}>Harga max (Rp)</label>
              <input className={input} type="number" value={form.price_max} onChange={(e) => set("price_max", e.target.value)} />
            </div>
            <div>
              <label className={label}>Jam buka</label>
              <input className={input} value={form.opening_time} onChange={(e) => set("opening_time", e.target.value)} />
            </div>
            <div>
              <label className={label}>Jam tutup</label>
              <input className={input} value={form.closing_time} onChange={(e) => set("closing_time", e.target.value)} />
            </div>
          </div>

          <div className="flex flex-wrap gap-4">
            <label className="flex items-center gap-2 text-sm font-semibold text-ink-700">
              <input type="checkbox" checked={form.is_free} onChange={(e) => set("is_free", e.target.checked)} />
              Gratis
            </label>
            <label className="flex items-center gap-2 text-sm font-semibold text-ink-700">
              <input type="checkbox" checked={form.is_open_24h} onChange={(e) => set("is_open_24h", e.target.checked)} />
              Buka 24 jam
            </label>
            <label className="flex items-center gap-2 text-sm font-semibold text-ink-700">
              <input type="checkbox" checked={form.is_featured} onChange={(e) => set("is_featured", e.target.checked)} />
              Unggulan
            </label>
            <label className="flex items-center gap-2 text-sm font-semibold text-ink-700">
              <input type="checkbox" checked={form.is_trending} onChange={(e) => set("is_trending", e.target.checked)} />
              Tren
            </label>
          </div>

          <div>
            <p className="label">Hari buka</p>
            <div className="flex flex-wrap gap-2">
              {DAYS.map((d) => (
                <button
                  key={d.value}
                  type="button"
                  onClick={() => toggleDay(d.value)}
                  className={`badge px-3 py-2 ${form.days_open.includes(d.value) ? "bg-brand-600 text-white" : "bg-ink-100 text-ink-500"}`}
                >
                  {d.label}
                </button>
              ))}
            </div>
          </div>

          <div>
            <p className="label">Fasilitas</p>
            <div className="flex flex-wrap gap-2">
              {FACILITY_OPTIONS.map((f) => (
                <button
                  key={f}
                  type="button"
                  onClick={() => toggleFacility(f)}
                  className={`badge px-3 py-2 ${form.facilities.includes(f) ? "bg-brand-600 text-white" : "bg-ink-100 text-ink-500"}`}
                >
                  {f.replace(/_/g, " ")}
                </button>
              ))}
            </div>
          </div>

          <div className="flex justify-end gap-2 pt-2">
            <Button type="button" variant="secondary" onClick={onClose}>Batal</Button>
            <Button type="submit" loading={mutation.isPending}>
              {editing ? "Simpan" : "Tambah"}
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
}

export default function AdminDestinations() {
  const queryClient = useQueryClient();
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");
  const [showForm, setShowForm] = useState(false);
  const [editing, setEditing] = useState(null);
  const [importMsg, setImportMsg] = useState(null);

  const { data, isLoading, isError, error } = useQuery({
    queryKey: ["admin", "destinations", page, search],
    queryFn: async () => {
      const res = await api.get("/destinations", {
        params: { page, per_page: 10, query: search || undefined },
      });
      return res.data.data;
    },
  });

  const deleteMutation = useMutation({
    mutationFn: async (id) => {
      await api.delete(`/destinations/${id}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["admin", "destinations"] });
      queryClient.invalidateQueries({ queryKey: ["admin", "dashboard"] });
    },
  });

  const exportCsv = async () => {
    const res = await api.get("/admin/export/csv", { responseType: "blob" });
    const url = URL.createObjectURL(new Blob([res.data]));
    const a = document.createElement("a");
    a.href = url;
    a.download = "destinations.csv";
    a.click();
    URL.revokeObjectURL(url);
  };

  const onImport = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    const fd = new FormData();
    fd.append("file", file);
    try {
      const res = await api.post("/admin/import/csv", fd, { headers: { "Content-Type": "multipart/form-data" } });
      setImportMsg(`Import selesai: ${res.data.data.imported} ditambahkan, ${res.data.data.skipped} dilewati`);
      queryClient.invalidateQueries({ queryKey: ["admin", "destinations"] });
      queryClient.invalidateQueries({ queryKey: ["admin", "dashboard"] });
    } catch (err) {
      setImportMsg(getErrorMessage(err));
    }
    e.target.value = "";
  };

  return (
    <div className="space-y-5">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h2 className="text-xl font-extrabold text-ink-900">Destinasi</h2>
        <div className="flex flex-wrap gap-2">
          <label className="btn-secondary cursor-pointer px-4 py-2 text-sm">
            <Upload className="h-4 w-4" /> Import CSV
            <input type="file" accept=".csv" className="hidden" onChange={onImport} />
          </label>
          <Button variant="secondary" onClick={exportCsv}>
            <Download className="h-4 w-4" /> Export
          </Button>
          <Button
            onClick={() => {
              setEditing(null);
              setShowForm(true);
            }}
          >
            <Plus className="h-4 w-4" /> Tambah
          </Button>
        </div>
      </div>

      <input
        className="input max-w-sm"
        placeholder="Cari destinasi..."
        value={search}
        onChange={(e) => {
          setSearch(e.target.value);
          setPage(1);
        }}
      />

      {importMsg && <Alert type="success">{importMsg}</Alert>}
      {isError && <Alert type="error">{getErrorMessage(error)}</Alert>}

      {isLoading ? (
        <Spinner size="lg" className="mx-auto block py-16" />
      ) : (
        <div className="card overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead className="border-b border-ink-100 bg-ink-50 text-xs uppercase text-ink-500">
              <tr>
                <th className="px-4 py-3">Nama</th>
                <th className="px-4 py-3">Provinsi</th>
                <th className="px-4 py-3">Rating</th>
                <th className="px-4 py-3">Hidden Gem</th>
                <th className="px-4 py-3 text-right">Aksi</th>
              </tr>
            </thead>
            <tbody>
              {data?.data?.map((d) => (
                <tr key={d.id} className="border-b border-ink-50 hover:bg-ink-50/50">
                  <td className="px-4 py-3">
                    <div className="flex items-center gap-2">
                      <MapPin className="h-4 w-4 shrink-0 text-ink-400" />
                      <div>
                        <p className="font-bold text-ink-800">{d.name}</p>
                        <p className="text-xs text-ink-500">{d.regency}, {d.province}</p>
                      </div>
                    </div>
                  </td>
                  <td className="px-4 py-3 text-ink-600">{d.province}</td>
                  <td className="px-4 py-3 text-ink-600">{d.rating}</td>
                  <td className="px-4 py-3">
                    <span className="badge bg-brand-100 text-brand-700">
                      <Gem className="h-3 w-3" /> {Math.round(d.hidden_gem_score)}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex justify-end gap-1">
                      <button
                        className="rounded-lg p-2 hover:bg-sky-50"
                        onClick={() => {
                          setEditing(d);
                          setShowForm(true);
                        }}
                        aria-label="Edit"
                      >
                        <Pencil className="h-4 w-4 text-sky-600" />
                      </button>
                      <button
                        className="rounded-lg p-2 hover:bg-red-50"
                        onClick={() => {
                          if (window.confirm(`Hapus "${d.name}"?`)) deleteMutation.mutate(d.id);
                        }}
                        aria-label="Hapus"
                      >
                        <Trash2 className="h-4 w-4 text-red-500" />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {data && <Pagination meta={data.meta} onChange={setPage} />}
      <p className="text-xs text-ink-400">Total {formatNumber(data?.meta?.total)} destinasi</p>

      {showForm && (
        <DestinationForm editing={Boolean(editing)} initial={editing} onClose={() => setShowForm(false)} />
      )}
    </div>
  );
}
