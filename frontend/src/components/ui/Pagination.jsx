import { ChevronLeft, ChevronRight } from "lucide-react";

export default function Pagination({ meta, onChange }) {
  if (!meta || meta.pages <= 1) return null;
  const { page, pages, has_next, has_prev } = meta;

  const nums = [];
  for (let i = Math.max(1, page - 2); i <= Math.min(pages, page + 2); i += 1) nums.push(i);

  return (
    <div className="flex items-center justify-center gap-1 pt-6">
      <button
        className="btn-secondary px-2.5 py-2"
        disabled={!has_prev}
        onClick={() => onChange(page - 1)}
        aria-label="Sebelumnya"
      >
        <ChevronLeft className="h-4 w-4" />
      </button>
      {nums[0] > 1 && <span className="px-1 text-ink-400">...</span>}
      {nums.map((n) => (
        <button
          key={n}
          onClick={() => onChange(n)}
          className={`rounded-lg px-3.5 py-2 text-sm font-semibold transition ${
            n === page ? "bg-brand-600 text-white" : "text-ink-600 hover:bg-ink-100"
          }`}
        >
          {n}
        </button>
      ))}
      {nums[nums.length - 1] < pages && <span className="px-1 text-ink-400">...</span>}
      <button
        className="btn-secondary px-2.5 py-2"
        disabled={!has_next}
        onClick={() => onChange(page + 1)}
        aria-label="Berikutnya"
      >
        <ChevronRight className="h-4 w-4" />
      </button>
    </div>
  );
}
