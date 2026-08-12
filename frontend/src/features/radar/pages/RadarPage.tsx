import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useMemo, useState } from "react";
import BriefDuJourCard from "@/features/brief/components/BriefDuJourCard";
import {
  getCollectionStatus,
  getHealth,
  getMediaItems,
  getMetaFilters,
  getTrends,
  runCollection,
} from "@/shared/api";
import DashboardKpiStrip from "@/shared/ui/DashboardKpiStrip";
import FilterBar, { type DashboardFilters } from "@/shared/ui/FilterBar";
import MediaSignalsPreview from "@/shared/ui/MediaSignalsPreview";
import TrendCard from "@/shared/ui/TrendCard";

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
      limit: 25,
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
    mutationFn: async () => {
      await runCollection();
      await new Promise((r) => setTimeout(r, 2500));
    },
    onSuccess: async () => {
      await queryClient.invalidateQueries();
    },
  });

  const trends = trendsQuery.data ?? [];
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
          {refreshing ? "…" : "Rafraîchir"}
        </button>
      </div>

      <div className="hidden md:flex md:flex-wrap md:items-center md:justify-between md:gap-4">
        <div>
          <h2 className="font-display text-2xl font-semibold text-slate-900">Tableau de bord — tendances en cours</h2>
        </div>
        <button
          type="button"
          onClick={() => refreshMutation.mutate()}
          disabled={refreshing}
          className={btnSecondary}
        >
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
