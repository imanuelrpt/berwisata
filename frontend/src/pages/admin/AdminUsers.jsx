import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Ban, CheckCircle2, Trash2, User as UserIcon } from "lucide-react";
import api from "../../lib/api";
import Alert from "../../components/ui/Alert";
import Spinner from "../../components/ui/Spinner";
import Pagination from "../../components/ui/Pagination";
import { getErrorMessage, formatDate } from "../../lib/format";

export default function AdminUsers() {
  const queryClient = useQueryClient();
  const [page, setPage] = useState(1);
  const [query, setQuery] = useState("");

  const { data, isLoading, isError, error } = useQuery({
    queryKey: ["admin", "users", page, query],
    queryFn: async () => {
      const res = await api.get("/admin/users", { params: { page, per_page: 15, query: query || undefined } });
      return res.data.data;
    },
  });

  const statusMutation = useMutation({
    mutationFn: async ({ id, isActive }) => {
      const res = await api.patch(`/admin/users/${id}/status`, null, { params: { is_active: isActive } });
      return res.data;
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["admin", "users"] }),
  });

  const deleteMutation = useMutation({
    mutationFn: async (id) => {
      await api.delete(`/admin/users/${id}`);
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["admin", "users"] }),
  });

  return (
    <div className="space-y-5">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h2 className="text-xl font-extrabold text-ink-900">Pengguna</h2>
        <input
          className="input max-w-xs"
          placeholder="Cari pengguna..."
          value={query}
          onChange={(e) => {
            setQuery(e.target.value);
            setPage(1);
          }}
        />
      </div>

      {isError && <Alert type="error">{getErrorMessage(error)}</Alert>}
      {isLoading ? (
        <Spinner size="lg" className="mx-auto block py-16" />
      ) : (
        <div className="card overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead className="border-b border-ink-100 bg-ink-50 text-xs uppercase text-ink-500">
              <tr>
                <th className="px-4 py-3">Pengguna</th>
                <th className="px-4 py-3">Role</th>
                <th className="px-4 py-3">Status</th>
                <th className="px-4 py-3">Terdaftar</th>
                <th className="px-4 py-3 text-right">Aksi</th>
              </tr>
            </thead>
            <tbody>
              {data?.data?.map((u) => (
                <tr key={u.id} className="border-b border-ink-50 hover:bg-ink-50/50">
                  <td className="px-4 py-3">
                    <div className="flex items-center gap-3">
                      {u.avatar_url ? (
                        <img src={u.avatar_url} alt="" className="h-9 w-9 rounded-full object-cover" />
                      ) : (
                        <span className="flex h-9 w-9 items-center justify-center rounded-full bg-ink-100 text-ink-500">
                          <UserIcon className="h-4 w-4" />
                        </span>
                      )}
                      <div>
                        <p className="font-bold text-ink-800">{u.full_name || u.username}</p>
                        <p className="text-xs text-ink-500">{u.email} · @{u.username}</p>
                      </div>
                    </div>
                  </td>
                  <td className="px-4 py-3">
                    <span className={`badge ${u.role === "admin" ? "bg-amber-100 text-amber-700" : "bg-sky-100 text-sky-700"}`}>
                      {u.role}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    <span className={`badge ${u.is_active ? "bg-brand-100 text-brand-700" : "bg-red-100 text-red-600"}`}>
                      {u.is_active ? "Aktif" : "Nonaktif"}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-ink-500">{formatDate(u.created_at)}</td>
                  <td className="px-4 py-3">
                    <div className="flex justify-end gap-1">
                      <button
                        className="rounded-lg p-2 hover:bg-ink-100"
                        onClick={() => statusMutation.mutate({ id: u.id, isActive: !u.is_active })}
                        title={u.is_active ? "Nonaktifkan" : "Aktifkan"}
                      >
                        {u.is_active ? (
                          <Ban className="h-4 w-4 text-amber-600" />
                        ) : (
                          <CheckCircle2 className="h-4 w-4 text-brand-600" />
                        )}
                      </button>
                      {u.role !== "admin" && (
                        <button
                          className="rounded-lg p-2 hover:bg-red-50"
                          onClick={() => {
                            if (window.confirm(`Hapus pengguna ${u.email}?`)) deleteMutation.mutate(u.id);
                          }}
                          title="Hapus"
                        >
                          <Trash2 className="h-4 w-4 text-red-500" />
                        </button>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
      <Pagination meta={data?.meta} onChange={setPage} />
    </div>
  );
}
