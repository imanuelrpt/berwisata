import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Cpu, RefreshCw, Database } from "lucide-react";
import api from "../../lib/api";
import Alert from "../../components/ui/Alert";
import Button from "../../components/ui/Button";
import Spinner from "../../components/ui/Spinner";
import { getErrorMessage, formatNumber, formatDate } from "../../lib/format";

export default function AdminTrain() {
  const queryClient = useQueryClient();
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");

  const { data, isLoading } = useQuery({
    queryKey: ["admin", "dashboard"],
    queryFn: async () => {
      const res = await api.get("/admin/dashboard");
      return res.data.data;
    },
  });

  const trainMutation = useMutation({
    mutationFn: async () => {
      const res = await api.post("/admin/ml/retrain");
      return res.data.data;
    },
    onSuccess: (r) => {
      setResult(r);
      queryClient.invalidateQueries({ queryKey: ["admin", "dashboard"] });
    },
    onError: (err) => setError(getErrorMessage(err)),
  });

  const model = data?.model;

  return (
    <div className="max-w-3xl space-y-6">
      <div className="card p-6">
        <h2 className="flex items-center gap-2 text-xl font-extrabold text-ink-900">
          <Cpu className="h-5 w-5 text-brand-600" /> Model AI Rekomendasi
        </h2>
        <p className="mt-2 text-sm text-ink-500">
          Model Random Forest memprediksi skor hidden gem untuk setiap destinasi. Latih ulang untuk
          memperbarui model dan skor menggunakan data terbaru dari CSV.
        </p>
        <div className="mt-5 space-y-3 rounded-2xl bg-ink-50 p-5">
          {isLoading ? (
            <Spinner />
          ) : model ? (
            <>
              <div className="flex items-center justify-between">
                <span className="text-sm text-ink-500">Algoritma</span>
                <span className="font-bold text-ink-800">{model.algorithm || "Random Forest"}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-ink-500">Sampel latih</span>
                <span className="font-bold text-ink-800">{formatNumber(model.samples)}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-ink-500">Jumlah fitur</span>
                <span className="font-bold text-ink-800">{formatNumber(model.features)}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-ink-500">R² (akurasi)</span>
                <span className="font-bold text-brand-600">{model.r2 ?? "-"}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-ink-500">MAE</span>
                <span className="font-bold text-ink-800">{model.mae ?? "-"}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-ink-500">RMSE</span>
                <span className="font-bold text-ink-800">{model.rmse ?? "-"}</span>
              </div>
              {model.trained_at && (
                <div className="flex items-center justify-between">
                  <span className="text-sm text-ink-500">Terakhir dilatih</span>
                  <span className="font-bold text-ink-800">{formatDate(model.trained_at)}</span>
                </div>
              )}
            </>
          ) : (
            <Alert type="warning">Belum ada model yang dilatih.</Alert>
          )}
        </div>
        <div className="mt-5">
          {error && <Alert type="error" className="mb-3">{error}</Alert>}
          <Button onClick={() => trainMutation.mutate()} loading={trainMutation.isPending} size="lg">
            <RefreshCw className="h-4 w-4" /> Latih Ulang Model
          </Button>
        </div>
      </div>

      {result && (
        <div className="card p-6">
          <h3 className="mb-4 flex items-center gap-2 font-bold text-ink-900">
            <Database className="h-4 w-4 text-brand-600" /> Hasil Pelatihan
          </h3>
          <div className="grid grid-cols-2 gap-4 sm:grid-cols-3">
            <div className="rounded-2xl bg-ink-50 p-4">
              <p className="text-xs text-ink-500">Status</p>
              <p className="mt-1 font-bold text-brand-600">{result.status}</p>
            </div>
            <div className="rounded-2xl bg-ink-50 p-4">
              <p className="text-xs text-ink-500">Sampel</p>
              <p className="mt-1 font-bold text-ink-900">{formatNumber(result.samples)}</p>
            </div>
            <div className="rounded-2xl bg-ink-50 p-4">
              <p className="text-xs text-ink-500">Fitur</p>
              <p className="mt-1 font-bold text-ink-900">{formatNumber(result.features)}</p>
            </div>
            <div className="rounded-2xl bg-ink-50 p-4">
              <p className="text-xs text-ink-500">R²</p>
              <p className="mt-1 font-bold text-brand-600">{result.r2}</p>
            </div>
            <div className="rounded-2xl bg-ink-50 p-4">
              <p className="text-xs text-ink-500">MAE</p>
              <p className="mt-1 font-bold text-ink-900">{result.mae}</p>
            </div>
            <div className="rounded-2xl bg-ink-50 p-4">
              <p className="text-xs text-ink-500">RMSE</p>
              <p className="mt-1 font-bold text-ink-900">{result.rmse}</p>
            </div>
          </div>
          {result.accuracy_buckets && (
            <div className="mt-4">
              <p className="label">Akurasi per selisih skor</p>
              <pre className="rounded-xl bg-ink-900 p-4 text-xs text-brand-300">
                {JSON.stringify(result.accuracy_buckets, null, 2)}
              </pre>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
