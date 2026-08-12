import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useMemo, useState } from "react";
import BriefDuJourCard from "@/features/brief/components/BriefDuJourCard";
import {
  getCollectionStatus,
  getHealth,
  getMediaItems,
  getMetaFilters,
  getTrends,
  refreshAllIntel,
} from "@/shared/api";
import DashboardKpiStrip from "@/shared/ui/DashboardKpiStrip";
import FilterBar, { type DashboardFilters } from "@/shared/ui/FilterBar";
import MediaSignalsPreview from "@/shared/ui/MediaSignalsPreview";
import TrendPlatformGroups from "@/shared/ui/TrendPlatformGroups";

const HOT_TREND_MIN = 55;

const DEFAULT_FILTERS: DashboardFilters = {
  category: "",
  platform: "",
  q: "",
  minTrendScore: String(HOT_TREND_MIN),
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
  const queryClient = useQueryClient();
  const [filters, setFilters] = useState<DashboardFilters>(DEFAULT_FILTERS);

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
      limit: 80,
      per_platform: 6,
      category: filters.category || undefined,
      platform: filters.platform || undefined,
      q: filters.q || undefined,
    }),
    [filters]
  );

  const metaQuery = useQuery({
    queryKey: ["meta", "filters"],
    queryFn: getMetaFilters,
  });

  const trendsQuery = useQuery({
    queryKey: ["trends", trendApiFilters],
    queryFn: () => getTrends(trendApiFilters),
    refetchInterval: 25_000,
  });

  const mediaQuery = useQuery({
    queryKey: ["media", mediaApiFilters],
    queryFn: () => getMediaItems(mediaApiFilters),
    refetchInterval: 25_000,
  });

  const healthQuery = useQuery({
    queryKey: ["health"],
    queryFn: getHealth,
    refetchInterval: 25_000,
  });

  const collectQuery = useQuery({
    queryKey: ["collect", "status"],
    queryFn: getCollectionStatus,
    refetchInterval: 25_000,
  });

  const refreshMutation = useMutation({
    mutationFn: () => refreshAllIntel(),
    onSuccess: async () => {
      await queryClient.invalidateQueries();
    },
  });

  const allTrends = trendsQuery.data ?? [];
  const trends = useMemo(() => {
    const min = parseNum(filters.minTrendScore) ?? HOT_TREND_MIN;
    const hot = allTrends.filter((t) => t.trend_score >= min);
    if (hot.length >= 4) return hot;
    return [...allTrends].sort((a, b) => b.trend_score - a.trend_score).slice(0, 6);
  }, [allTrends, filters.minTrendScore]);
  const mediaPreview = mediaQuery.data ?? [];
  const meta = metaQuery.data ?? { categories: [], platforms: [] };
  const collectStatus = collectQuery.data ?? null;
  const health =
    healthQuery.data != null ? `${healthQuery.data.scheduler} · ${healthQuery.data.db}` : "…";
  const refreshing = refreshMutation.isPending;

  return (
    <div className="space-y-6">
      <div className="flex md:hidden items-center justify-between gap-3 rounded-xl border border-slate-200 bg-white px-3 py-2 shadow-sm">
        <span className="truncate text-[11px] text-slate-500">{health}</span>
        <button
          type="button"
          onClick={() => refreshMutation.mutate()}
          disabled={refreshing}
          className="shrink-0 rounded-lg border border-radj-navy bg-radj-navy px-3 py-1.5 text-xs font-semibold text-radj-lime shadow-sm hover:bg-radj-navy/90 disabled:opacity-50"
        >
          {refreshing ? "Sources…" : "Rafraîchir"}
        </button>
      </div>

      <div className="hidden md:flex md:flex-wrap md:items-end md:justify-between md:gap-4">
        <p className="max-w-xl text-sm text-slate-600">
          Tendances détectées sur les signaux collectés — filtrez par secteur, plateforme ou score.
        </p>
        <button
          type="button"
          onClick={() => refreshMutation.mutate()}
          disabled={refreshing}
          className={btnSecondary}
        >
          {refreshing ? "Collecte de toutes les sources…" : "Rafraîchir toutes les sources"}
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
          <h3 className="font-display text-lg font-semibold text-slate-900">Tendances qui montent fort</h3>
          <span className="text-xs font-medium text-slate-500">
            {trends.length} carte{trends.length !== 1 ? "s" : ""} · score ≥ {parseNum(filters.minTrendScore) ?? HOT_TREND_MIN}
          </span>
        </div>
        <TrendPlatformGroups trends={trends} filterPlatform={filters.platform || undefined} />
      </div>

      <div>
        <h3 className="mb-2 font-display text-sm font-semibold text-slate-900">Signaux par plateforme</h3>
        <MediaSignalsPreview items={mediaPreview} />
      </div>
    </div>
  );
}
