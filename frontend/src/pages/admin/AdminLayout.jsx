import { NavLink, Outlet } from "react-router-dom";
import { LayoutDashboard, MapPin, Tag, Users, Cpu, Shield } from "lucide-react";

const linkClass = ({ isActive }) =>
  `flex items-center gap-2 rounded-lg px-3 py-2 text-sm font-semibold transition ${
    isActive ? "bg-brand-600 text-white" : "text-ink-600 hover:bg-ink-100"
  }`;

export default function AdminLayout() {
  return (
    <div className="container-app py-8">
      <div className="mb-6 flex items-center gap-3">
        <span className="flex h-11 w-11 items-center justify-center rounded-2xl bg-ink-900 text-white">
          <Shield className="h-5 w-5" />
        </span>
        <div>
          <h1 className="text-3xl font-extrabold text-ink-900">Admin Panel</h1>
          <p className="text-sm text-ink-500">Kelola data wisata, user, dan model AI</p>
        </div>
      </div>
      <div className="flex flex-col gap-6 lg:flex-row">
        <aside className="lg:w-56 lg:shrink-0">
          <nav className="card flex flex-row gap-1 overflow-x-auto p-2 lg:flex-col">
            <NavLink to="/admin" className={linkClass} end>
              <LayoutDashboard className="h-4 w-4" /> Dashboard
            </NavLink>
            <NavLink to="/admin/destinations" className={linkClass}>
              <MapPin className="h-4 w-4" /> Destinasi
            </NavLink>
            <NavLink to="/admin/categories" className={linkClass}>
              <Tag className="h-4 w-4" /> Kategori
            </NavLink>
            <NavLink to="/admin/users" className={linkClass}>
              <Users className="h-4 w-4" /> Pengguna
            </NavLink>
            <NavLink to="/admin/train" className={linkClass}>
              <Cpu className="h-4 w-4" /> Model AI
            </NavLink>
          </nav>
        </aside>
        <section className="min-w-0 flex-1">
          <Outlet />
        </section>
      </div>
    </div>
  );
}
