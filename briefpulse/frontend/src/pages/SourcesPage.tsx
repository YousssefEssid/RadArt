import { useCallback, useEffect, useState } from "react";
import { getCollectionStatus, getHealth, runCollection } from "../api";
import SourceStatus from "../components/SourceStatus";

const btnSecondary =
  "rounded-xl border border-slate-300 bg-white px-5 py-2.5 text-sm font-semibold text-slate-700 shadow-sm transition hover:border-radj-navy hover:text-radj-navy disabled:opacity-50";

export default function SourcesPage() {
  const [status, setStatus] = useState<Awaited<ReturnType<typeof getCollectionStatus>> | null>(null);
  const [health, setHealth] = useState<string>("…");
  const [refreshing, setRefreshing] = useState(false);

  const load = useCallback(async () => {
    const [st, h] = await Promise.all([getCollectionStatus(), getHealth()]);
    setStatus(st);
    setHealth(`${h.scheduler} · ${h.db}`);
  }, []);

  useEffect(() => {
    load().catch(console.error);
    const id = setInterval(() => load().catch(console.error), 20000);
    return () => clearInterval(id);
  }, [load]);

  async function onRefresh() {
    setRefreshing(true);
    try {
      await runCollection();
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
          {refreshing ? "…" : "Collecte"}
        </button>
      </div>

      <div className="flex flex-wrap items-center justify-between gap-4">
        <div className="hidden md:block">
          <h2 className="font-display text-2xl font-semibold text-slate-900">Sources & collecte</h2>
        </div>
        <button type="button" onClick={onRefresh} disabled={refreshing} className={btnSecondary}>
          {refreshing ? "Collecte…" : "Lancer une collecte"}
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
