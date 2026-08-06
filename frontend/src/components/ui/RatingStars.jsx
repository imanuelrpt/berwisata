import { Star } from "lucide-react";

export default function RatingStars({ rating, size = "md" }) {
  const num = Number(rating) || 0;
  const px = { sm: "h-3 w-3", md: "h-4 w-4", lg: "h-5 w-5" }[size];
  const full = Math.round(num);
  return (
    <span className="inline-flex items-center gap-0.5">
      {[1, 2, 3, 4, 5].map((i) => (
        <Star
          key={i}
          className={`${px} ${i <= full ? "fill-amber-400 text-amber-400" : "text-ink-300"}`}
        />
      ))}
    </span>
  );
}
