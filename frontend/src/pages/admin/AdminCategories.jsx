import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Plus, Pencil, Trash2, X } from "lucide-react";
import api from "../../lib/api";
import Alert from "../../components/ui/Alert";
import Button from "../../components/ui/Button";
import Spinner from "../../components/ui/Spinner";
import { getErrorMessage } from "../../lib/format";

function CategoryForm({ editing, initial, onClose }) {
  const [form, setForm] = useState(
    editing
      ? { name: initial.name, slug: initial.slug, description: initial.description || "", icon: initial.icon || "" }
      : { name: "", slug: "", description: "", icon: "" }
  );
  const [error, setError] = useState("");
  const queryClient = useQueryClient();

  const mutation = useMutation({
    mutationFn: async (payload) => {
      if (editing) {
        const res = await api.patch(`/categories/${initial.id}`, payload);
        return res.data;
      }
      const res = await api.post("/categories", payload);
      return res.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["categories"] });
      onClose();
    },
    onError: (err) => setError(getErrorMessage(err)),
  });

  const submit = (e) => {
    e.preventDefault();
    mutation.mutate(form);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4 backdrop-blur-sm">
      <div className="card w-full max-w-md p-6">
        <div className="mb-4 flex items-center justify-between">
          <h2 className="text-xl font-extrabold text-ink-900">{editing ? "Edit Kategori" : "Tambah Kategori"}</h2>
          <button onClick={onClose} className="rounded-lg p-2 hover:bg-ink-100" aria-label="Tutup">
            <X className="h-5 w-5" />
          </button>
        </div>
        {error && <Alert type="error" className="mb-4">{error}</Alert>}
        <form onSubmit={submit} className="space-y-4">
          <div>
            <label className="label">Nama *</label>
            <input className="input" required value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} />
          </div>
          <div>
            <label className="label">Slug</label>
            <input className="input" value={form.slug} onChange={(e) => setForm({ ...form, slug: e.target.value })} />
          </div>
          <div>
            <label className="label">Deskripsi</label>
            <textarea className="input" rows={2} value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} />
          </div>
          <div>
            <label className="label">Icon</label>
            <input className="input" value={form.icon} onChange={(e) => setForm({ ...form, icon: e.target.value })} />
          </div>
          <div className="flex justify-end gap-2">
            <Button type="button" variant="secondary" onClick={onClose}>Batal</Button>
            <Button type="submit" loading={mutation.isPending}>{editing ? "Simpan" : "Tambah"}</Button>
          </div>
        </form>
      </div>
    </div>
  );
}

export default function AdminCategories() {
  const queryClient = useQueryClient();
  const [showForm, setShowForm] = useState(false);
  const [editing, setEditing] = useState(null);

  const { data, isLoading, isError, error } = useQuery({
    queryKey: ["categories"],
    queryFn: async () => {
      const res = await api.get("/categories");
      return res.data.data.data;
    },
  });

  const deleteMutation = useMutation({
    mutationFn: async (id) => {
      await api.delete(`/categories/${id}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["categories"] });
    },
  });

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-extrabold text-ink-900">Kategori</h2>
        <Button
          onClick={() => {
            setEditing(null);
            setShowForm(true);
          }}
        >
          <Plus className="h-4 w-4" /> Tambah
        </Button>
      </div>

      {isError && <Alert type="error">{getErrorMessage(error)}</Alert>}
      {isLoading ? (
        <Spinner size="lg" className="mx-auto block py-16" />
      ) : (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {data?.map((c) => (
            <div key={c.id} className="card flex items-center justify-between p-5">
              <div className="min-w-0">
                <div className="flex items-center gap-2">
                  {c.icon && <span className="text-xl">{c.icon}</span>}
                  <h3 className="truncate font-bold text-ink-900">{c.name}</h3>
                </div>
                <p className="mt-1 truncate text-xs text-ink-500">slug: {c.slug}</p>
                {c.destination_count != null && (
                  <p className="text-xs font-semibold text-brand-600">{c.destination_count} destinasi</p>
                )}
              </div>
              <div className="flex gap-1">
                <button
                  className="rounded-lg p-2 hover:bg-sky-50"
                  onClick={() => {
                    setEditing(c);
                    setShowForm(true);
                  }}
                  aria-label="Edit"
                >
                  <Pencil className="h-4 w-4 text-sky-600" />
                </button>
                <button
                  className="rounded-lg p-2 hover:bg-red-50"
                  onClick={() => {
                    if (window.confirm(`Hapus kategori "${c.name}"?`)) deleteMutation.mutate(c.id);
                  }}
                  aria-label="Hapus"
                >
                  <Trash2 className="h-4 w-4 text-red-500" />
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {showForm && (
        <CategoryForm editing={Boolean(editing)} initial={editing} onClose={() => setShowForm(false)} />
      )}
    </div>
  );
}
