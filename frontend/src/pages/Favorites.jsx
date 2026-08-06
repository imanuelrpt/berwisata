import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Heart, Trash2 } from "lucide-react";
import api from "../lib/api";
import DestinationCard from "../components/DestinationCard";
import EmptyState from "../components/ui/EmptyState";
import Alert from "../components/ui/Alert";
import { DestinationCardSkeleton } from "../components/ui/Skeleton";
import Pagination from "../components/ui/Pagination";
import { getErrorMessage } from "../lib/format";

export default function Favorites() {
  const queryClient = useQueryClient();
  const [page, setPage] = useState(1);

  const { data, isLoading, isError, error } = useQuery({
    queryKey: ["favorites", page],
    queryFn: async () => {
      const res = await api.get("/favorites", { params: { page, per_page: 12 } });
      return res.data.data;
    },
  });

  const removeMutation = useMutation({
    mutationFn: async (id) => {
      await api.delete(`/favorites/${id}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["favorites"] });
    },
  });

  const destinations = data?.data?.map((f) => ({ ...f.destination, is_favorited: true })) || [];

  return (
    <div className="container-app py-8">
      <div className="mb-6 flex items-center gap-3">
        <span className="flex h-11 w-11 items-center justify-center rounded-2xl bg-red-50 text-red-500">
          <Heart className="h-5 w-5 fill-current" />
        </span>
        <div>
          <h1 className="text-3xl font-extrabold text-ink-900">Favorit Saya</h1>
          <p className="text-sm text-ink-500">
            {data?.meta?.total != null ? `${data.meta.total} destinasi tersimpan` : "Destinasi yang kamu simpan"}
          </p>
        </div>
      </div>

      {isError && <Alert type="error">Gagal memuat: {getErrorMessage(error)}</Alert>}

      {isLoading ? (
        <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
          {Array.from({ length: 8 }).map((_, i) => (
            <DestinationCardSkeleton key={i} />
          ))}
        </div>
      ) : destinations.length === 0 ? (
        <EmptyState
          title="Belum ada favorit"
          subtitle="Simpan destinasi yang kamu suka agar mudah ditemukan kembali."
        />
      ) : (
        <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
          {destinations.map((d) => (
            <div key={d.id} className="relative">
              <DestinationCard destination={d} />
              <button
                className="absolute right-3 bottom-3 z-10 flex h-8 w-8 items-center justify-center rounded-full bg-white/90 text-red-500 shadow hover:bg-white"
                onClick={() => removeMutation.mutate(d.id)}
                title="Hapus dari favorit"
              >
                <Trash2 className="h-4 w-4" />
              </button>
            </div>
          ))}
        </div>
      )}

      <Pagination meta={data?.meta} onChange={setPage} />
    </div>
  );
}
