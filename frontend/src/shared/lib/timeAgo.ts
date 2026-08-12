/** Recency helpers — so agencies know if they can still hop on a trend. */

export type Freshness = {
  label: string;
  hint: string;
  className: string;
};

export function parseIsoDate(value?: string | null): Date | null {
  if (!value || typeof value !== "string") return null;
  const d = new Date(value);
  return Number.isNaN(d.getTime()) ? null : d;
}

export function formatRelativeFr(date: Date, now = new Date()): string {
  const diffMs = now.getTime() - date.getTime();
  const future = diffMs < 0;
  const abs = Math.abs(diffMs);
  const mins = Math.floor(abs / 60_000);
  const hours = Math.floor(abs / 3_600_000);
  const days = Math.floor(abs / 86_400_000);

  if (mins < 2) return future ? "dans un instant" : "à l’instant";
  if (mins < 60) return future ? `dans ${mins} min` : `il y a ${mins} min`;
  if (hours < 24) return future ? `dans ${hours} h` : `il y a ${hours} h`;
  if (days === 1) return future ? "demain" : "hier";
  if (days < 7) return future ? `dans ${days} j` : `il y a ${days} j`;
  return date.toLocaleDateString("fr-TN", { day: "numeric", month: "short", year: "numeric" });
}

export function formatAbsoluteFr(date: Date): string {
  return date.toLocaleString("fr-TN", {
    day: "numeric",
    month: "short",
    hour: "2-digit",
    minute: "2-digit",
  });
}

/** Window for hopping on a trend: now / still time / cooling / late. */
export function freshnessFor(date: Date, now = new Date()): Freshness {
  const hours = (now.getTime() - date.getTime()) / 3_600_000;
  if (hours < 6) {
    return {
      label: "Maintenant",
      hint: "Signal très frais — bonne fenêtre pour hop on.",
      className: "border-emerald-200 bg-emerald-50 text-emerald-900",
    };
  }
  if (hours < 24) {
    return {
      label: "Encore temps",
      hint: "Moins de 24 h — tu n’es pas en retard.",
      className: "border-lime-200 bg-radj-lime/40 text-radj-navy",
    };
  }
  if (hours < 72) {
    return {
      label: "Ça refroidit",
      hint: "2–3 jours — hop on vite ou passe.",
      className: "border-amber-200 bg-amber-50 text-amber-900",
    };
  }
  return {
    label: "En retard",
    hint: "Plus de 3 jours — le pic est probablement passé.",
    className: "border-slate-200 bg-slate-100 text-slate-600",
  };
}
