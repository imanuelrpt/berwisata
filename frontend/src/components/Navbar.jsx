import { useState } from "react";
import { Link, NavLink, useNavigate } from "react-router-dom";
import { MapPin, Menu, X, User as UserIcon, Compass, LogOut } from "lucide-react";
import { useAuth } from "../context/AuthContext";

const navLinkClass = ({ isActive }) =>
  `rounded-lg px-3 py-2 text-sm font-semibold transition ${
    isActive ? "bg-brand-50 text-brand-700" : "text-ink-600 hover:bg-ink-100 hover:text-ink-900"
  }`;

export default function Navbar() {
  const { user, isAuthenticated, isAdmin, logout } = useAuth();
  const [open, setOpen] = useState(false);
  const [userMenu, setUserMenu] = useState(false);
  const navigate = useNavigate();

  return (
    <header className="sticky top-0 z-40 border-b border-ink-100 bg-white/90 backdrop-blur">
      <div className="container-app flex h-16 items-center justify-between gap-4">
        <Link to="/" className="flex items-center gap-2">
          <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-brand-600 text-white">
            <Compass className="h-5 w-5" />
          </span>
          <span className="text-lg font-extrabold tracking-tight text-ink-900">
            Ber<span className="text-brand-600">Wisata</span>
          </span>
        </Link>

        <nav className="hidden items-center gap-1 md:flex">
          <NavLink to="/" className={navLinkClass} end>
            Beranda
          </NavLink>
          <NavLink to="/search" className={navLinkClass}>
            Jelajahi
          </NavLink>
          {isAuthenticated && (
            <NavLink to="/favorites" className={navLinkClass}>
              Favorit
            </NavLink>
          )}
          {isAdmin && (
            <NavLink to="/admin" className={navLinkClass}>
              Admin
            </NavLink>
          )}
        </nav>

        <div className="hidden items-center gap-3 md:flex">
          {isAuthenticated ? (
            <div className="relative">
              <button
                onClick={() => setUserMenu((v) => !v)}
                className="flex h-9 w-9 items-center justify-center rounded-full bg-ink-100 text-ink-700 hover:bg-ink-200"
                aria-label="Menu pengguna"
              >
                {user?.avatar_url ? (
                  <img src={user.avatar_url} alt={user.full_name || ""} className="h-9 w-9 rounded-full object-cover" />
                ) : (
                  <UserIcon className="h-5 w-5" />
                )}
              </button>
              {userMenu && (
                <div className="absolute right-0 mt-2 w-48 overflow-hidden rounded-xl border border-ink-100 bg-white py-1 shadow-lift">
                  <div className="border-b border-ink-100 px-4 py-2.5">
                    <p className="truncate text-sm font-bold text-ink-800">{user.full_name || user.username}</p>
                    <p className="truncate text-xs text-ink-500">{user.email}</p>
                  </div>
                  <button
                    className="flex w-full items-center gap-2 px-4 py-2.5 text-left text-sm font-medium text-ink-700 hover:bg-ink-50"
                    onClick={() => {
                      setUserMenu(false);
                      navigate("/profile");
                    }}
                  >
                    <UserIcon className="h-4 w-4" /> Profil
                  </button>
                  {isAdmin && (
                    <button
                      className="flex w-full items-center gap-2 px-4 py-2.5 text-left text-sm font-medium text-ink-700 hover:bg-ink-50"
                      onClick={() => {
                        setUserMenu(false);
                        navigate("/admin");
                      }}
                    >
                      <Compass className="h-4 w-4" /> Admin Panel
                    </button>
                  )}
                  <button
                    className="flex w-full items-center gap-2 px-4 py-2.5 text-left text-sm font-medium text-red-600 hover:bg-red-50"
                    onClick={() => {
                      setUserMenu(false);
                      logout();
                      navigate("/");
                    }}
                  >
                    <LogOut className="h-4 w-4" /> Keluar
                  </button>
                </div>
              )}
            </div>
          ) : (
            <>
              <Link to="/login" className="btn-ghost px-4 py-2 text-sm">
                Masuk
              </Link>
              <Link to="/register" className="btn-primary px-4 py-2 text-sm">
                Daftar
              </Link>
            </>
          )}
        </div>

        <button className="md:hidden" onClick={() => setOpen((v) => !v)} aria-label="Menu">
          {open ? <X className="h-6 w-6" /> : <Menu className="h-6 w-6" />}
        </button>
      </div>

      {open && (
        <div className="border-t border-ink-100 bg-white px-4 py-3 md:hidden">
          <div className="flex flex-col gap-1">
            <NavLink to="/" className={navLinkClass} end onClick={() => setOpen(false)}>
              Beranda
            </NavLink>
            <NavLink to="/search" className={navLinkClass} onClick={() => setOpen(false)}>
              Jelajahi
            </NavLink>
            {isAuthenticated && (
              <>
                <NavLink to="/favorites" className={navLinkClass} onClick={() => setOpen(false)}>
                  Favorit
                </NavLink>
                <NavLink to="/profile" className={navLinkClass} onClick={() => setOpen(false)}>
                  Profil
                </NavLink>
              </>
            )}
            {isAdmin && (
              <NavLink to="/admin" className={navLinkClass} onClick={() => setOpen(false)}>
                Admin
              </NavLink>
            )}
            {isAuthenticated ? (
              <button
                className="flex items-center gap-2 rounded-lg px-3 py-2 text-left text-sm font-semibold text-red-600 hover:bg-red-50"
                onClick={() => {
                  setOpen(false);
                  logout();
                }}
              >
                <LogOut className="h-4 w-4" /> Keluar
              </button>
            ) : (
              <div className="mt-2 flex gap-2">
                <Link to="/login" className="btn-secondary flex-1 px-4 py-2 text-sm" onClick={() => setOpen(false)}>
                  Masuk
                </Link>
                <Link to="/register" className="btn-primary flex-1 px-4 py-2 text-sm" onClick={() => setOpen(false)}>
                  Daftar
                </Link>
              </div>
            )}
          </div>
        </div>
      )}

      <span className="sr-only">
        <MapPin />
      </span>
    </header>
  );
}
