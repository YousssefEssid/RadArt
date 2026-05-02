import { useCallback, useEffect, useMemo, useState } from "react";
import {
  getCollectionStatus,
  getHealth,
  getMediaItems,
  getMetaFilters,
  getTrends,
  runCollection,
  type MediaItem,
  type Trend,
} from "../api";
import BriefDuJourCard from "../components/BriefDuJourCard";
import DashboardKpiStrip from "../components/DashboardKpiStrip";
import FilterBar, { type DashboardFilters } from "../components/FilterBar";
import MediaSignalsPreview from "../components/MediaSignalsPreview";
import TrendCard from "../components/TrendCard";

const DEFAULT_FILTERS: DashboardFilters = {
  category: "",
  platform: "",
  q: "",
  minTrendScore: "",
  maxRisk: "",
};

function parseNum(s: string): number | undefined {
  const t = s.trim();
  if (!t) return undefined;
  const n = Number(t);
  return Number.isFinite(n) ? n : undefined;
}

const btnSecondary =
  "rounded-xl border border-slate-300 bg-white px-5 py-2.5 text-sm font-semibold text-slate-700 shadow-sm transition hover:border-radj-navy hover:text-radj-navy disabled:opacity-50";

export default function RadarPage() {
  const [trends, setTrends] = useState<Trend[]>([]);
  const [mediaPreview, setMediaPreview] = useState<MediaItem[]>([]);
  const [meta, setMeta] = useState<{ categories: string[]; platforms: string[] }>({
    categories: [],
    platforms: [],
  });
  const [filters, setFilters] = useState<DashboardFilters>(DEFAULT_FILTERS);
  const [health, setHealth] = useState<string>("…");
  const [refreshing, setRefreshing] = useState(false);
  const [collectStatus, setCollectStatus] = useState<Awaited<ReturnType<typeof getCollectionStatus>> | null>(null);

  const trendApiFilters = useMemo(
    () => ({
      category: filters.category || undefined,
      q: filters.q || undefined,
      min_trend_score: parseNum(filters.minTrendScore),
      max_risk: parseNum(filters.maxRisk),
    }),
    [filters]
  );

  const mediaApiFilters = useMemo(
    () => ({
      limit: 25,
      category: filters.category || undefined,
      platform: filters.platform || undefined,
      q: filters.q || undefined,
    }),
    [filters]
  );

  const load = useCallback(async () => {
    const [t, m, h, st] = await Promise.all([
      getTrends(trendApiFilters),
      getMediaItems(mediaApiFilters),
      getHealth(),
      getCollectionStatus(),
    ]);
    setTrends(t);
    setMediaPreview(m);
    setHealth(`${h.scheduler} · ${h.db}`);
    setCollectStatus(st);
  }, [trendApiFilters, mediaApiFilters]);

  useEffect(() => {
    getMetaFilters()
      .then(setMeta)
      .catch(console.error);
  }, []);

  useEffect(() => {
    load().catch(console.error);
  }, [load]);

  useEffect(() => {
    const id = setInterval(() => load().catch(console.error), 25000);
    return () => clearInterval(id);
  }, [load]);

  async function onRefresh() {
    setRefreshing(true);
    try {
      await runCollection();
      await getCollectionStatus();
      await new Promise((r) => setTimeout(r, 2500));
      await load();
    } finally {
      setRefreshing(false);
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex md:hidden items-center justify-between gap-3 rounded-xl border border-slate-200 bg-white px-3 py-2 shadow-sm">
        <span className="truncate text-[11px] text-slate-500">{health}</span>
        <button
          type="button"
          onClick={onRefresh}
          disabled={refreshing}
          className="shrink-0 rounded-lg border border-radj-navy bg-radj-navy px-3 py-1.5 text-xs font-semibold text-radj-lime shadow-sm hover:bg-radj-navy/90 disabled:opacity-50"
        >
          {refreshing ? "…" : "Rafraîchir"}
        </button>
      </div>

      <div className="hidden md:flex md:flex-wrap md:items-center md:justify-between md:gap-4">
        <div>
          <h2 className="font-display text-2xl font-semibold text-slate-900">Tableau de bord — tendances en cours</h2>
        </div>
        <button type="button" onClick={onRefresh} disabled={refreshing} className={btnSecondary}>
          {refreshing ? "Actualisation…" : "Rafraîchir les données"}
        </button>
      </div>

      <BriefDuJourCard trends={trends} sectorLabel={filters.category || undefined} />

      {collectStatus ? (
        <DashboardKpiStrip
          trends={trends}
          mediaItemsTotal={collectStatus.media_items_count}
          trendClustersTotal={collectStatus.trend_clusters_count}
          sourcesOkCount={collectStatus.source_status.filter((s) => s.status === "ok").length}
          sourcesTotalCount={collectStatus.source_status.length}
          lastItemsCollected={
            (collectStatus.last_runs[0] as { items_collected?: number } | undefined)?.items_collected
          }
        />
      ) : null}

      <FilterBar categories={meta.categories} platforms={meta.platforms} value={filters} onChange={setFilters} />

      <div className="space-y-4">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <h3 className="font-display text-lg font-semibold text-slate-900">Toutes les tendances actives</h3>
          <span className="text-xs font-medium text-slate-500">
            {trends.length} carte{trends.length !== 1 ? "s" : ""}
          </span>
        </div>
        <div className="grid gap-4 md:grid-cols-2">
          {trends.length === 0 ? (
            <p className="rounded-xl border border-dashed border-slate-300 bg-slate-50 p-8 text-center text-sm text-slate-500 md:col-span-2">
              Aucun résultat.
            </p>
          ) : (
            trends.map((t) => <TrendCard key={t.id} trend={t} />)
          )}
        </div>
      </div>

      <div>
        <h3 className="mb-2 font-display text-sm font-semibold text-slate-900">Signaux bruts</h3>
        <MediaSignalsPreview items={mediaPreview} />
      </div>
    </div>
  );
}
