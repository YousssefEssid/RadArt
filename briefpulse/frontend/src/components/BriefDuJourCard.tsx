import type { Trend } from "../api";

type Props = {
  trends: Trend[];
  sectorLabel?: string;
};

function buildLines(trends: Trend[], sectorLabel?: string): string[] {
  const sorted = [...trends].sort((a, b) => b.trend_score - a.trend_score);
  const top = sorted.slice(0, 3);
  const scope =
    sectorLabel?.trim() ||
    (sorted.length && sorted[0].category ? String(sorted[0].category) : null) ||
    "cette vue";

  if (!top.length) {
    return [`Aucune tendance pour ${scope}.`];
  }

  const items = top.map(
    (t, i) =>
      `${i + 1}. ${t.label} — pulse ${Math.round(t.trend_score)}, risque ${Math.round(t.risk_score)}, ${t.item_count} signaux.`
  );
  return items.slice(0, 5);
}

export default function BriefDuJourCard({ trends, sectorLabel }: Props) {
  const lines = buildLines(trends, sectorLabel);

  return (
    <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm ring-1 ring-slate-900/5 md:border-l-4 md:border-l-radj-lime">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <h3 className="font-display text-base font-semibold text-slate-900">Synthèse</h3>
      </div>
      <div className="mt-4 space-y-2.5 border-t border-slate-100 pt-4">
        {lines.map((line, i) => (
          <p key={i} className="text-sm leading-relaxed text-slate-600">
            {line}
          </p>
        ))}
      </div>
    </section>
  );
}
