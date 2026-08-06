import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useForm } from "react-hook-form";
import { Compass, Eye, EyeOff } from "lucide-react";
import { useAuth } from "../context/AuthContext";
import { getErrorMessage } from "../lib/format";
import Alert from "../components/ui/Alert";
import Button from "../components/ui/Button";

const PASSWORD_HINTS = [
  { re: /.{8,}/, label: "Minimal 8 karakter" },
  { re: /[A-Z]/, label: "Huruf kapital" },
  { re: /[a-z]/, label: "Huruf kecil" },
  { re: /\d/, label: "Angka" },
  { re: /[^A-Za-z0-9]/, label: "Simbol" },
];

export default function Register() {
  const { register: signUp } = useAuth();
  const navigate = useNavigate();
  const [error, setError] = useState("");
  const [showPw, setShowPw] = useState(false);
  const [password, setPassword] = useState("");
  const { register, handleSubmit, watch, formState: { errors, isSubmitting } } = useForm();

  const onSubmit = async (values) => {
    setError("");
    try {
      await signUp({
        email: values.email,
        username: values.username,
        full_name: values.full_name,
        password: values.password,
      });
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
          <h1 className="text-2xl font-extrabold text-ink-900">Buat Akun Baru</h1>
          <p className="mt-1 text-sm text-ink-500">Mulai simpan favorit dan dapatkan rekomendasi AI</p>
        </div>
        <div className="card p-6">
          <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
            {error && <Alert type="error">{error}</Alert>}
            <div>
              <label className="label">Nama lengkap</label>
              <input
                className="input"
                placeholder="Nama kamu"
                {...register("full_name", { required: "Wajib diisi", minLength: { value: 2, message: "Minimal 2 karakter" } })}
              />
              {errors.full_name && <p className="mt-1 text-xs text-red-600">{errors.full_name.message}</p>}
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="label">Username</label>
                <input
                  className="input"
                  placeholder="username"
                  {...register("username", {
                    required: "Wajib diisi",
                    minLength: { value: 3, message: "Minimal 3 karakter" },
                    pattern: { value: /^[a-zA-Z0-9_.]+$/, message: "Hanya huruf, angka, titik dan underscore" },
                  })}
                />
                {errors.username && <p className="mt-1 text-xs text-red-600">{errors.username.message}</p>}
              </div>
              <div>
                <label className="label">Email</label>
                <input
                  className="input"
                  type="email"
                  placeholder="email@example.com"
                  {...register("email", { required: "Wajib diisi", pattern: { value: /^\S+@\S+\.\S+$/, message: "Format email tidak valid" } })}
                />
                {errors.email && <p className="mt-1 text-xs text-red-600">{errors.email.message}</p>}
              </div>
            </div>
            <div>
              <label className="label">Kata sandi</label>
              <div className="relative">
                <input
                  className="input pr-12"
                  type={showPw ? "text" : "password"}
                  placeholder="••••••••"
                  {...register("password", {
                    required: "Wajib diisi",
                    minLength: { value: 8, message: "Minimal 8 karakter" },
                    validate: (v) => {
                      const rules = [
                        [/[A-Z]/, "Harus mengandung huruf kapital"],
                        [/[a-z]/, "Harus mengandung huruf kecil"],
                        [/\d/, "Harus mengandung angka"],
                        [/[^A-Za-z0-9]/, "Harus mengandung karakter khusus"],
                      ];
                      for (const [re, msg] of rules) {
                        if (!re.test(v)) return msg;
                      }
                      return true;
                    },
                  })}
                  onChange={(e) => setPassword(e.target.value)}
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
              <div className="mt-2 flex flex-wrap gap-1.5">
                {PASSWORD_HINTS.map((h) => (
                  <span
                    key={h.label}
                    className={`badge ${
                      h.re.test(password) ? "bg-brand-100 text-brand-700" : "bg-ink-100 text-ink-400"
                    }`}
                  >
                    {h.label}
                  </span>
                ))}
              </div>
            </div>
            <Button type="submit" className="w-full" size="lg" loading={isSubmitting}>
              Daftar
            </Button>
          </form>
          <p className="mt-4 text-center text-sm text-ink-500">
            Sudah punya akun?{" "}
            <Link to="/login" className="font-bold text-brand-600 hover:underline">
              Masuk
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}
