import type { Trend } from "@/shared/api";

function fmt(n: number): string {
  return n.toLocaleString("fr-FR");
}

type Props = {
  trends: Trend[];
  mediaItemsTotal: number;
  trendClustersTotal: number;
  sourcesOkCount: number;
  sourcesTotalCount: number;
  lastItemsCollected?: number;
};

export default function DashboardKpiStrip({
  trends,
  mediaItemsTotal,
  trendClustersTotal,
  sourcesOkCount,
  sourcesTotalCount,
  lastItemsCollected,
}: Props) {
  const criticalCount = trends.filter((t) => t.risk_score >= 68).length;
  const activeTrends = trends.length;

  const card =
    "rounded-2xl border border-radj-mist bg-white px-4 py-3 shadow-card";

  return (
    <section className="grid grid-cols-2 gap-3 lg:grid-cols-4">
      <div className={card}>
        <p className="text-xs font-medium text-slate-500">Signaux captés</p>
        <p className="mt-1 font-display text-2xl font-bold tabular-nums text-slate-900">{fmt(mediaItemsTotal)}</p>
        <p className="mt-1 text-xs font-medium text-emerald-600">
          {lastItemsCollected != null && lastItemsCollected > 0
            ? `+${fmt(lastItemsCollected)} dernière collecte`
            : "Indexés en base"}
        </p>
      </div>

      <div className={card}>
        <p className="text-xs font-medium text-slate-500">Tendances actives</p>
        <p className="mt-1 font-display text-2xl font-bold tabular-nums text-slate-900">{fmt(activeTrends)}</p>
        <p className="mt-1 text-xs font-medium text-emerald-600">
          {trendClustersTotal > activeTrends
            ? `${fmt(activeTrends)} sur ${fmt(trendClustersTotal)} clusters`
            : `${fmt(trendClustersTotal)} clusters en base`}
        </p>
      </div>

      <div className={card}>
        <p className="text-xs font-medium text-slate-500">Alertes critiques</p>
        <p className="mt-1 font-display text-2xl font-bold tabular-nums text-slate-900">{fmt(criticalCount)}</p>
        <p className={`mt-1 text-xs font-medium ${criticalCount > 0 ? "text-red-600" : "text-slate-500"}`}>
          {criticalCount > 0 ? "Agir maintenant" : "RAS"}
        </p>
      </div>

      <div className={card}>
        <p className="text-xs font-medium text-slate-500">Sources actives</p>
        <p className="mt-1 font-display text-2xl font-bold tabular-nums text-slate-900">{fmt(sourcesOkCount)}</p>
        <p className="mt-1 text-xs font-medium text-slate-500">
          {sourcesTotalCount > 0 && sourcesOkCount === sourcesTotalCount
            ? "Stable"
            : `${sourcesOkCount}/${sourcesTotalCount} OK`}
        </p>
      </div>
    </section>
  );
}
