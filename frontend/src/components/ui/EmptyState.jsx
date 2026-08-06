import { SearchX } from "lucide-react";

export default function EmptyState({ title = "Tidak ada hasil", subtitle, action }) {
  return (
    <div className="flex flex-col items-center justify-center py-16 text-center">
      <div className="mb-4 flex h-16 w-16 items-center justify-center rounded-2xl bg-ink-100">
        <SearchX className="h-8 w-8 text-ink-400" />
      </div>
      <h3 className="text-lg font-bold text-ink-800">{title}</h3>
      {subtitle && <p className="mt-1 max-w-sm text-sm text-ink-500">{subtitle}</p>}
      {action && <div className="mt-5">{action}</div>}
    </div>
  );
}
