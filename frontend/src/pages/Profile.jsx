import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Camera, Save, KeyRound, User as UserIcon } from "lucide-react";
import api from "../lib/api";
import { useAuth } from "../context/AuthContext";
import Alert from "../components/ui/Alert";
import Button from "../components/ui/Button";
import { getErrorMessage } from "../lib/format";

export default function Profile() {
  const { user, refreshUser } = useAuth();
  const queryClient = useQueryClient();

  const [form, setForm] = useState({
    full_name: user?.full_name || "",
    bio: user?.bio || "",
    phone: user?.phone || "",
  });

  const [pw, setPw] = useState({ current_password: "", new_password: "" });
  const [pwOk, setPwOk] = useState(false);

  const updateMutation = useMutation({
    mutationFn: async (payload) => {
      const res = await api.patch("/users/me", payload);
      return res.data.data;
    },
    onSuccess: () => {
      refreshUser();
      queryClient.invalidateQueries({ queryKey: ["profile"] });
    },
  });

  const avatarMutation = useMutation({
    mutationFn: async (file) => {
      const fd = new FormData();
      fd.append("file", file);
      const res = await api.post("/users/me/avatar", fd, { headers: { "Content-Type": "multipart/form-data" } });
      return res.data.data;
    },
    onSuccess: () => refreshUser(),
  });

  const passwordMutation = useMutation({
    mutationFn: async (payload) => {
      const res = await api.post("/users/me/password", payload);
      return res.data;
    },
    onSuccess: () => {
      setPwOk(true);
      setPw({ current_password: "", new_password: "" });
      setTimeout(() => setPwOk(false), 3000);
    },
  });

  const onAvatar = (e) => {
    const file = e.target.files?.[0];
    if (file) avatarMutation.mutate(file);
  };

  return (
    <div className="container-app py-8">
      <h1 className="text-3xl font-extrabold text-ink-900">Profil Saya</h1>
      <p className="mt-1 text-sm text-ink-500">Kelola informasi akun kamu</p>

      <div className="mt-6 grid grid-cols-1 gap-6 lg:grid-cols-3">
        <div className="card p-6 text-center">
          <div className="relative mx-auto h-24 w-24">
            {user?.avatar_url ? (
              <img src={user.avatar_url} alt="avatar" className="h-24 w-24 rounded-full object-cover" />
            ) : (
              <div className="flex h-24 w-24 items-center justify-center rounded-full bg-ink-100 text-ink-400">
                <UserIcon className="h-10 w-10" />
              </div>
            )}
            <label className="absolute -bottom-1 -right-1 flex h-9 w-9 cursor-pointer items-center justify-center rounded-full bg-brand-600 text-white shadow hover:bg-brand-700">
              <Camera className="h-4 w-4" />
              <input type="file" accept="image/*" className="hidden" onChange={onAvatar} />
            </label>
          </div>
          <h2 className="mt-4 text-lg font-bold text-ink-900">{user?.full_name || user?.username}</h2>
          <p className="text-sm text-ink-500">@{user?.username}</p>
          <span className={`badge mt-2 ${user?.role === "admin" ? "bg-amber-100 text-amber-700" : "bg-sky-100 text-sky-700"}`}>
            {user?.role === "admin" ? "Administrator" : "Member"}
          </span>
          {avatarMutation.isError && <Alert type="error" className="mt-3">{getErrorMessage(avatarMutation.error)}</Alert>}
        </div>

        <div className="card space-y-5 p-6 lg:col-span-2">
          <div>
            <h3 className="mb-3 flex items-center gap-2 font-bold text-ink-900">
              <Save className="h-4 w-4" /> Informasi Profil
            </h3>
            <div className="space-y-4">
              <div>
                <label className="label">Nama lengkap</label>
                <input
                  className="input"
                  value={form.full_name}
                  onChange={(e) => setForm({ ...form, full_name: e.target.value })}
                />
              </div>
              <div>
                <label className="label">Bio</label>
                <textarea
                  className="input"
                  rows={3}
                  placeholder="Ceritakan tentang dirimu..."
                  value={form.bio || ""}
                  onChange={(e) => setForm({ ...form, bio: e.target.value })}
                />
              </div>
              <div>
                <label className="label">No. HP</label>
                <input
                  className="input"
                  placeholder="08xxxxxxxxxx"
                  value={form.phone || ""}
                  onChange={(e) => setForm({ ...form, phone: e.target.value })}
                />
              </div>
              <Button
                onClick={() => updateMutation.mutate(form)}
                loading={updateMutation.isPending}
                disabled={!form.full_name.trim()}
              >
                Simpan perubahan
              </Button>
              {updateMutation.isSuccess && <Alert type="success">Profil diperbarui</Alert>}
              {updateMutation.isError && <Alert type="error">{getErrorMessage(updateMutation.error)}</Alert>}
            </div>
          </div>

          <div className="border-t border-ink-100 pt-5">
            <h3 className="mb-3 flex items-center gap-2 font-bold text-ink-900">
              <KeyRound className="h-4 w-4" /> Ganti Kata Sandi
            </h3>
            <div className="space-y-4">
              <div>
                <label className="label">Kata sandi saat ini</label>
                <input
                  className="input"
                  type="password"
                  value={pw.current_password}
                  onChange={(e) => setPw({ ...pw, current_password: e.target.value })}
                />
              </div>
              <div>
                <label className="label">Kata sandi baru</label>
                <input
                  className="input"
                  type="password"
                  value={pw.new_password}
                  onChange={(e) => setPw({ ...pw, new_password: e.target.value })}
                />
              </div>
              <Button
                variant="secondary"
                onClick={() => passwordMutation.mutate(pw)}
                loading={passwordMutation.isPending}
                disabled={!pw.current_password || !pw.new_password}
              >
                Ganti kata sandi
              </Button>
              {pwOk && <Alert type="success">Kata sandi berhasil diubah</Alert>}
              {passwordMutation.isError && <Alert type="error">{getErrorMessage(passwordMutation.error)}</Alert>}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
