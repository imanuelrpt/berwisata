import { Link } from "react-router-dom";
import { Compass } from "lucide-react";

export default function Footer() {
  return (
    <footer className="border-t border-ink-100 bg-white">
      <div className="container-app flex flex-col items-center justify-between gap-4 py-8 sm:flex-row">
        <div className="flex items-center gap-2">
          <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-brand-600 text-white">
            <Compass className="h-4 w-4" />
          </span>
          <span className="font-extrabold text-ink-900">
            Ber<span className="text-brand-600">Wisata</span>
          </span>
        </div>
        <nav className="flex items-center gap-5 text-sm text-ink-600">
          <Link to="/search" className="hover:text-brand-600">
            Jelajahi
          </Link>
          <Link to="/login" className="hover:text-brand-600">
            Masuk
          </Link>
          <Link to="/register" className="hover:text-brand-600">
            Daftar
          </Link>
        </nav>
        <p className="text-xs text-ink-400">
          &copy; {new Date().getFullYear()} BerWisata. Temukan permata tersembunyi Indonesia.
        </p>
      </div>
    </footer>
  );
}
