import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useForm } from "react-hook-form";
import { Compass, Eye, EyeOff } from "lucide-react";
import { useAuth } from "../context/AuthContext";
import { getErrorMessage } from "../lib/format";
import Alert from "../components/ui/Alert";
import Button from "../components/ui/Button";

export default function Login() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [error, setError] = useState("");
  const [showPw, setShowPw] = useState(false);
  const { register, handleSubmit, formState: { errors, isSubmitting } } = useForm();

  const onSubmit = async (values) => {
    setError("");
    try {
      await login(values.identifier, values.password);
      navigate("/");
    } catch (err) {
      setError(getErrorMessage(err));
    }
  };

  return (
    <div className="flex min-h-[70vh] items-center justify-center py-12">
      <div className="w-full max-w-md">
        <div className="mb-6 text-center">
          <span className="mx-auto mb-3 flex h-12 w-12 items-center justify-center rounded-2xl bg-brand-600 text-white">
            <Compass className="h-6 w-6" />
          </span>
          <h1 className="text-2xl font-extrabold text-ink-900">Masuk ke BerWisata</h1>
          <p className="mt-1 text-sm text-ink-500">Lanjutkan menjelajahi wisata tersembunyi</p>
        </div>
        <div className="card p-6">
          <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
            {error && <Alert type="error">{error}</Alert>}
            <div>
              <label className="label">Email atau username</label>
              <input
                className="input"
                placeholder="email@example.com"
                {...register("identifier", { required: "Wajib diisi" })}
              />
              {errors.identifier && <p className="mt-1 text-xs text-red-600">{errors.identifier.message}</p>}
            </div>
            <div>
              <label className="label">Kata sandi</label>
              <div className="relative">
                <input
                  className="input pr-12"
                  type={showPw ? "text" : "password"}
                  placeholder="••••••••"
                  {...register("password", { required: "Wajib diisi" })}
                />
                <button
                  type="button"
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-ink-400 hover:text-ink-600"
                  onClick={() => setShowPw((v) => !v)}
                  aria-label="Tampilkan kata sandi"
                >
                  {showPw ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                </button>
              </div>
              {errors.password && <p className="mt-1 text-xs text-red-600">{errors.password.message}</p>}
            </div>
            <Button type="submit" className="w-full" size="lg" loading={isSubmitting}>
              Masuk
            </Button>
          </form>
          <p className="mt-4 text-center text-sm text-ink-500">
            Belum punya akun?{" "}
            <Link to="/register" className="font-bold text-brand-600 hover:underline">
              Daftar sekarang
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}
