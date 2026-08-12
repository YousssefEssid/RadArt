import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { getCollectionStatus, getHealth, refreshAllIntel } from "@/shared/api";
import SourceStatus from "@/shared/ui/SourceStatus";

const btnSecondary =
  "rounded-xl border border-slate-300 bg-white px-5 py-2.5 text-sm font-semibold text-slate-700 shadow-sm transition hover:border-radj-navy hover:text-radj-navy disabled:opacity-50";

export default function SourcesPage() {
  const queryClient = useQueryClient();

  const statusQuery = useQuery({
    queryKey: ["collect", "status"],
    queryFn: getCollectionStatus,
    refetchInterval: 20_000,
  });

  const healthQuery = useQuery({
    queryKey: ["health"],
    queryFn: getHealth,
    refetchInterval: 20_000,
  });

  const collectMutation = useMutation({
    mutationFn: () => refreshAllIntel(),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["collect"] });
      await queryClient.invalidateQueries({ queryKey: ["health"] });
      await queryClient.invalidateQueries({ queryKey: ["trends"] });
      await queryClient.invalidateQueries({ queryKey: ["media"] });
    },
  });

  const status = statusQuery.data ?? null;
  const health =
    healthQuery.data != null ? `${healthQuery.data.scheduler} · ${healthQuery.data.db}` : "…";
  const refreshing = collectMutation.isPending;

  return (
    <div className="space-y-6">
      <div className="flex md:hidden items-center justify-between gap-3 rounded-xl border border-slate-200 bg-white px-3 py-2 shadow-sm">
        <span className="truncate text-[11px] text-slate-500">{health}</span>
        <button
          type="button"
          onClick={() => collectMutation.mutate()}
          disabled={refreshing}
          className="shrink-0 rounded-lg border border-radj-navy bg-radj-navy px-3 py-1.5 text-xs font-semibold text-radj-lime shadow-sm hover:bg-radj-navy/90 disabled:opacity-50"
        >
          {refreshing ? "…" : "Collecte"}
        </button>
      </div>

      <div className="flex flex-wrap items-center justify-between gap-4">
        <p className="hidden text-sm text-slate-600 md:block">
          État des collecteurs RSS, APIs et signaux mock — relancez une passe à tout moment.
        </p>
        <button
          type="button"
          onClick={() => collectMutation.mutate()}
          disabled={refreshing}
          className={btnSecondary}
        >
          {refreshing ? "Collecte de toutes les sources…" : "Lancer une collecte complète"}
        </button>
      </div>

      {status ? (
        <SourceStatus
          mediaCount={status.media_items_count}
          trendCount={status.trend_clusters_count}
          lastRuns={status.last_runs}
          sourceStatus={status.source_status}
        />
      ) : (
        <p className="text-sm text-slate-500">Chargement…</p>
      )}
    </div>
  );
}
