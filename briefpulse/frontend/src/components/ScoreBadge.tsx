type Props = { label: string; value: number; variant?: "trend" | "risk" | "fit" };

export default function ScoreBadge({ label, value, variant = "trend" }: Props) {
  const emphasis =
    variant === "risk" && value >= 70
      ? "border-radj-navy bg-radj-navy text-radj-lime shadow-sm"
      : "border-slate-200 bg-slate-50 text-slate-800 shadow-sm";

  return (
    <div className={`inline-flex items-center gap-2 rounded-full border px-3 py-1 text-xs font-medium ${emphasis}`}>
      <span className={variant === "risk" && value >= 70 ? "text-radj-lime/90" : "text-slate-500"}>{label}</span>
      <span
        className={`font-semibold tabular-nums ${
          variant === "risk" && value >= 70 ? "text-radj-lime" : "text-radj-navy"
        }`}
      >
        {Math.round(value)}
      </span>
    </div>
  );
}
