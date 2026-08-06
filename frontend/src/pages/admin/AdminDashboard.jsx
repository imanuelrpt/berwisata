import { useQuery } from "@tanstack/react-query";
import {
  MapPin,
  Tag,
  Users,
  Heart,
  Star,
  Search,
  Cpu,
} from "lucide-react";
import api from "../../lib/api";
import Alert from "../../components/ui/Alert";
import Spinner from "../../components/ui/Spinner";
import { getErrorMessage, formatNumber, formatDate } from "../../lib/format";

function StatCard({ icon: Icon, label, value, color }) {
  return (
    <div className="card flex items-center gap-4 p-5">
      <span className={`flex h-12 w-12 items-center justify-center rounded-2xl ${color}`}>
        <Icon className="h-6 w-6" />
      </span>
      <div>
        <p className="text-2xl font-extrabold text-ink-900">{formatNumber(value)}</p>
        <p className="text-sm text-ink-500">{label}</p>
      </div>
    </div>
  );
}

export default function AdminDashboard() {
  const { data, isLoading, isError, error } = useQuery({
    queryKey: ["admin", "dashboard"],
    queryFn: async () => {
      const res = await api.get("/admin/dashboard");
      return res.data.data;
    },
  });

  if (isLoading) return <Spinner size="lg" className="mx-auto block py-16" />;
  if (isError) return <Alert type="error">{getErrorMessage(error)}</Alert>;

  const stats = [
    { icon: MapPin, label: "Destinasi", value: data.total_destinations, color: "bg-brand-100 text-brand-700" },
    { icon: Tag, label: "Kategori", value: data.total_categories, color: "bg-sky-100 text-sky-700" },
    { icon: Users, label: "Pengguna", value: data.total_users, color: "bg-violet-100 text-violet-700" },
    { icon: Heart, label: "Favorit", value: data.total_favorites, color: "bg-red-100 text-red-600" },
    { icon: Star, label: "Rating", value: data.total_reviews, color: "bg-amber-100 text-amber-700" },
    { icon: Search, label: "Pencarian", value: data.total_searches, color: "bg-teal-100 text-teal-700" },
  ];

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-2 gap-4 lg:grid-cols-3">
        {stats.map((s) => (
          <StatCard key={s.label} {...s} />
        ))}
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <div className="card p-6">
          <h3 className="mb-4 font-bold text-ink-900">Skor Model AI</h3>
          {data.model ? (
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="flex items-center gap-2 text-sm text-ink-500">
                  <Cpu className="h-4 w-4" /> Model
                </span>
                <span className="font-bold text-ink-800">{data.model.algorithm || "RandomForest"}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-ink-500">Akurasi (R²)</span>
                <span className="font-bold text-brand-600">{data.model.r2 ?? "-"}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-ink-500">MAE</span>
                <span className="font-bold text-ink-800">{data.model.mae ?? "-"}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-ink-500">Sampel latih</span>
                <span className="font-bold text-ink-800">{formatNumber(data.model.samples)}</span>
              </div>
              {data.model.trained_at && (
                <div className="flex items-center justify-between">
                  <span className="text-sm text-ink-500">Dilatih pada</span>
                  <span className="font-bold text-ink-800">{formatDate(data.model.trained_at)}</span>
                </div>
              )}
            </div>
          ) : (
            <Alert type="warning">Model belum dilatih.</Alert>
          )}
        </div>

        <div className="card p-6">
          <h3 className="mb-4 font-bold text-ink-900">Top 5 Destinasi Hidden Gem</h3>
          <div className="space-y-3">
            {data.top_destinations?.map((d, i) => (
              <div key={d.id} className="flex items-center justify-between rounded-xl bg-ink-50 px-4 py-3">
                <div className="min-w-0">
                  <p className="truncate text-sm font-bold text-ink-800">
                    <span className="mr-2 text-ink-400">#{i + 1}</span>
                    {d.name}
                  </p>
                  <p className="text-xs text-ink-500">{d.regency}, {d.province}</p>
                </div>
                <span className="badge bg-brand-100 text-brand-700">{Math.round(d.hidden_gem_score)}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <div className="card p-6">
          <h3 className="mb-4 font-bold text-ink-900">Distribusi Kategori</h3>
          {data.category_distribution?.length ? (
            <div className="space-y-2">
              {data.category_distribution.map((c) => (
                <div key={c.name} className="flex items-center justify-between text-sm">
                  <span className="text-ink-600 capitalize">{c.name}</span>
                  <span className="font-bold text-ink-800">{formatNumber(c.count)}</span>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-sm text-ink-500">Belum ada data.</p>
          )}
        </div>
        <div className="card p-6">
          <h3 className="mb-4 font-bold text-ink-900">Top Provinsi</h3>
          {data.province_distribution?.length ? (
            <div className="space-y-2">
              {data.province_distribution.map((p) => (
                <div key={p.name} className="flex items-center gap-3 text-sm">
                  <span className="w-40 truncate text-ink-600">{p.name}</span>
                  <div className="h-2 flex-1 overflow-hidden rounded-full bg-ink-100">
                    <div
                      className="h-full rounded-full bg-brand-500"
                      style={{
                        width: `${Math.min(100, (p.count / (data.province_distribution[0]?.count || 1)) * 100)}%`,
                      }}
                    />
                  </div>
                  <span className="font-bold text-ink-800">{formatNumber(p.count)}</span>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-sm text-ink-500">Belum ada data.</p>
          )}
        </div>
      </div>
    </div>
  );
}
