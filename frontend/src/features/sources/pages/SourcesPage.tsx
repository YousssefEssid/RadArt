import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useMemo, useState } from "react";
import {
  addWatchlistAccount,
  addWatchlistTerm,
  deleteWatchlistAccount,
  deleteWatchlistTerm,
  getCollectionStatus,
  getHealth,
  getSignalCoverage,
  getSourceHealth,
  getWatchlist,
  listWatchlists,
  refreshAllIntel,
  uploadCustomerOwnedFile,
  type SignalCoverageLayer,
  type SourceHealthMatrixRow,
  type WatchlistTerm,
} from "@/shared/api";
import SourceStatus from "@/shared/ui/SourceStatus";

const btnSecondary =
  "rounded-xl border border-slate-300 bg-white px-5 py-2.5 text-sm font-semibold text-slate-700 shadow-sm transition hover:border-radj-navy hover:text-radj-navy disabled:opacity-50";

const fieldClass =
  "rounded-lg border border-slate-300 bg-white px-2.5 py-1.5 text-sm text-slate-900 outline-none focus:border-radj-navy";

const tierTone: Record<string, string> = {
  live: "border-emerald-200 bg-emerald-50",
  optional_key: "border-sky-200 bg-sky-50",
  customer_owned: "border-radj-navy/20 bg-[#f7ffe8]",
  planned: "border-amber-200 bg-amber-50",
  forbidden: "border-red-200 bg-red-50",
};

const TERM_TYPES = ["brand", "competitor", "topic", "keyword", "hashtag", "creator"] as const;

function lightEmoji(light: string) {
  if (light === "green") return "🟢";
  if (light === "yellow") return "🟡";
  if (light === "red") return "🔴";
  return "⚪";
}

function statusDot(status: string) {
  if (status === "live") return "bg-emerald-500";
  if (status === "needs_key") return "bg-sky-500";
  if (status === "planned") return "bg-amber-500";
  if (status === "forbidden") return "bg-red-500";
  return "bg-slate-400";
}

function CoverageLayer({ layer }: { layer: SignalCoverageLayer }) {
  return (
    <article className={`rounded-2xl border p-4 shadow-sm ${tierTone[layer.tier] || "border-slate-200 bg-white"}`}>
      <h3 className="font-display text-base font-semibold text-slate-900">{layer.title}</h3>
      <p className="mt-1 text-xs text-slate-600">{layer.compliance}</p>
      <ul className="mt-3 space-y-2">
        {layer.sources.map((s) => (
          <li key={s.name} className="flex items-start gap-2 rounded-xl border border-white/70 bg-white/80 px-3 py-2 text-sm">
            <span className={`mt-1.5 h-2 w-2 shrink-0 rounded-full ${statusDot(s.status)}`} />
            <div className="min-w-0">
              <p className="font-medium text-slate-900">{s.name}</p>
              <p className="text-[11px] text-slate-500">
                {s.status}
                {s.env ? ` · ${s.env}` : ""}
                {s.path ? ` · ${s.path}` : ""}
                {s.detail ? ` · ${s.detail}` : ""}
              </p>
            </div>
          </li>
        ))}
      </ul>
    </article>
  );
}

function HealthMatrix({ rows }: { rows: SourceHealthMatrixRow[] }) {
  return (
    <div className="overflow-x-auto rounded-2xl border border-slate-200 bg-white shadow-sm">
      <table className="min-w-full text-left text-sm">
        <thead className="border-b border-slate-100 bg-slate-50 text-[11px] uppercase tracking-wide text-slate-500">
          <tr>
            <th className="px-4 py-3 font-semibold">Source</th>
            <th className="px-4 py-3 font-semibold">Status</th>
            <th className="px-4 py-3 font-semibold">Collection</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((r) => (
            <tr key={r.source} className="border-b border-slate-50 last:border-0">
              <td className="px-4 py-3 font-medium text-slate-900">{r.source}</td>
              <td className="px-4 py-3">
                {lightEmoji(r.light)} {r.status}
              </td>
              <td className="px-4 py-3 text-slate-600">
                {r.collection}
                {r.detail ? <span className="mt-0.5 block text-[11px] text-slate-400">{r.detail}</span> : null}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function WatchlistPanel() {
  const qc = useQueryClient();
  const listsQ = useQuery({ queryKey: ["watchlists"], queryFn: listWatchlists });
  const defaultId = listsQ.data?.watchlists?.[0]?.id;
  const [activeId, setActiveId] = useState<number | null>(null);
  const wid = activeId ?? defaultId ?? null;

  const bundleQ = useQuery({
    queryKey: ["watchlists", wid],
    queryFn: () => getWatchlist(wid!),
    enabled: wid != null,
  });

  const [termType, setTermType] = useState<(typeof TERM_TYPES)[number]>("topic");
  const [termValue, setTermValue] = useState("");
  const [handle, setHandle] = useState("");
  const [platform, setPlatform] = useState("tiktok");

  const addTermM = useMutation({
    mutationFn: () => addWatchlistTerm(wid!, termType, termValue),
    onSuccess: async () => {
      setTermValue("");
      await qc.invalidateQueries({ queryKey: ["watchlists"] });
    },
  });

  const addAccM = useMutation({
    mutationFn: () => addWatchlistAccount(wid!, platform, handle),
    onSuccess: async () => {
      setHandle("");
      await qc.invalidateQueries({ queryKey: ["watchlists"] });
    },
  });

  const termsByType = useMemo(() => {
    const map: Record<string, WatchlistTerm[]> = {};
    for (const t of bundleQ.data?.terms || []) {
      (map[t.term_type] ||= []).push(t);
    }
    return map;
  }, [bundleQ.data]);

  return (
    <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
      <h3 className="font-display text-base font-semibold text-slate-900">Watchlists</h3>
      <p className="mt-1 text-sm text-slate-600">
        Brands, competitors, topics, hashtags, creators, keywords — collectors query these instead of “the whole
        internet”.
      </p>

      {listsQ.data?.watchlists?.length ? (
        <div className="mt-3 flex flex-wrap gap-2">
          {listsQ.data.watchlists.map((w) => (
            <button
              key={w.id}
              type="button"
              onClick={() => setActiveId(w.id)}
              className={`rounded-lg px-3 py-1.5 text-xs font-semibold ${
                wid === w.id ? "bg-radj-navy text-radj-lime" : "border border-slate-300 bg-white text-slate-700"
              }`}
            >
              {w.name}
              {w.is_default ? " · default" : ""}
            </button>
          ))}
        </div>
      ) : null}

      {wid ? (
        <>
          <div className="mt-4 grid gap-2 sm:grid-cols-[140px_1fr_auto]">
            <select className={fieldClass} value={termType} onChange={(e) => setTermType(e.target.value as typeof termType)}>
              {TERM_TYPES.map((t) => (
                <option key={t} value={t}>
                  {t}
                </option>
              ))}
            </select>
            <input
              className={fieldClass}
              placeholder="valeur (ex. Ramadan, Boga, tunisia)"
              value={termValue}
              onChange={(e) => setTermValue(e.target.value)}
            />
            <button
              type="button"
              disabled={!termValue.trim() || addTermM.isPending}
              onClick={() => addTermM.mutate()}
              className="rounded-lg bg-radj-navy px-3 py-1.5 text-sm font-semibold text-radj-lime disabled:opacity-50"
            >
              Ajouter
            </button>
          </div>

          <div className="mt-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {TERM_TYPES.map((tt) => (
              <div key={tt} className="rounded-xl border border-slate-100 bg-slate-50/80 p-3">
                <p className="text-[11px] font-semibold uppercase tracking-wide text-slate-500">{tt}</p>
                <ul className="mt-2 space-y-1">
                  {(termsByType[tt] || []).map((t) => (
                    <li key={t.id} className="flex items-center justify-between gap-2 text-sm text-slate-800">
                      <span className="truncate">{tt === "hashtag" ? `#${t.value}` : t.value}</span>
                      <button
                        type="button"
                        className="text-[11px] text-red-600 hover:underline"
                        onClick={() =>
                          deleteWatchlistTerm(wid, t.id).then(() => qc.invalidateQueries({ queryKey: ["watchlists"] }))
                        }
                      >
                        ×
                      </button>
                    </li>
                  ))}
                  {!(termsByType[tt] || []).length ? <li className="text-xs text-slate-400">—</li> : null}
                </ul>
              </div>
            ))}
          </div>

          <div className="mt-4 grid gap-2 sm:grid-cols-[140px_1fr_auto]">
            <select className={fieldClass} value={platform} onChange={(e) => setPlatform(e.target.value)}>
              <option value="tiktok">tiktok</option>
              <option value="instagram">instagram</option>
              <option value="facebook">facebook</option>
              <option value="youtube">youtube</option>
            </select>
            <input
              className={fieldClass}
              placeholder="@creator"
              value={handle}
              onChange={(e) => setHandle(e.target.value)}
            />
            <button
              type="button"
              disabled={!handle.trim() || addAccM.isPending}
              onClick={() => addAccM.mutate()}
              className="rounded-lg border border-slate-300 bg-white px-3 py-1.5 text-sm font-semibold text-slate-700 disabled:opacity-50"
            >
              Compte
            </button>
          </div>
          <ul className="mt-2 flex flex-wrap gap-2">
            {(bundleQ.data?.accounts || []).map((a) => (
              <li
                key={a.id}
                className="inline-flex items-center gap-2 rounded-full border border-slate-200 bg-white px-2.5 py-1 text-xs"
              >
                {a.platform}/@{a.handle}
                <button
                  type="button"
                  className="text-red-600"
                  onClick={() =>
                    deleteWatchlistAccount(wid, a.id).then(() => qc.invalidateQueries({ queryKey: ["watchlists"] }))
                  }
                >
                  ×
                </button>
              </li>
            ))}
          </ul>
        </>
      ) : null}
    </section>
  );
}

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

  const coverageQuery = useQuery({
    queryKey: ["sources", "coverage"],
    queryFn: getSignalCoverage,
  });

  const sourceHealthQ = useQuery({
    queryKey: ["sources", "health"],
    queryFn: getSourceHealth,
  });

  const collectMutation = useMutation({
    mutationFn: () => refreshAllIntel(),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["collect"] });
      await queryClient.invalidateQueries({ queryKey: ["health"] });
      await queryClient.invalidateQueries({ queryKey: ["trends"] });
      await queryClient.invalidateQueries({ queryKey: ["media"] });
      await queryClient.invalidateQueries({ queryKey: ["sources"] });
    },
  });

  const uploadMutation = useMutation({
    mutationFn: (file: File) => uploadCustomerOwnedFile(file),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["sources"] });
    },
  });

  const status = statusQuery.data ?? null;
  const coverage = coverageQuery.data;
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
        <p className="hidden max-w-2xl text-sm text-slate-600 md:block">
          Real coverage vs missing access. Watchlists drive discovery. No unofficial Meta/TikTok scrapes.
        </p>
        <button type="button" onClick={() => collectMutation.mutate()} disabled={refreshing} className={btnSecondary}>
          {refreshing ? "Collecte…" : "Lancer une collecte complète"}
        </button>
      </div>

      {sourceHealthQ.data ? (
        <section className="space-y-2">
          <h2 className="font-display text-lg font-semibold text-slate-900">Source status</h2>
          <p className="text-sm text-slate-500">{sourceHealthQ.data.principle}</p>
          <HealthMatrix rows={sourceHealthQ.data.matrix} />
        </section>
      ) : null}

      <WatchlistPanel />

      {coverage ? (
        <section className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-card">
          <div className="bg-gradient-to-br from-[#12142b] via-[#1c1c68] to-[#2a2d4a] px-5 py-5 text-white sm:px-6">
            <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-[#d7ff7b]">
              Signal coverage · Tunisia
            </p>
            <h2 className="mt-2 font-display text-xl font-semibold">Where RadArt gets cultural signal</h2>
            <p className="mt-2 max-w-3xl text-sm text-white/80">{coverage.principle}</p>
          </div>
          <div className="grid gap-3 p-4 lg:grid-cols-2">
            {coverage.layers.map((layer) => (
              <CoverageLayer key={layer.id} layer={layer} />
            ))}
          </div>
        </section>
      ) : null}

      <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
        <h3 className="font-display text-base font-semibold text-slate-900">Upload customer-owned export</h3>
        <p className="mt-1 text-sm text-slate-600">JSON you have rights to use. Ingested on next collection.</p>
        <label className="mt-3 inline-flex cursor-pointer rounded-xl border border-radj-navy bg-radj-navy px-4 py-2 text-sm font-semibold text-radj-lime">
          {uploadMutation.isPending ? "Upload…" : "Choisir un fichier JSON"}
          <input
            type="file"
            accept=".json,application/json"
            className="hidden"
            onChange={(e) => {
              const f = e.target.files?.[0];
              if (f) uploadMutation.mutate(f);
              e.target.value = "";
            }}
          />
        </label>
        {uploadMutation.isSuccess ? (
          <p className="mt-2 text-sm text-emerald-800">{uploadMutation.data.saved} items saved</p>
        ) : null}
        {uploadMutation.isError ? (
          <p className="mt-2 text-sm text-red-700">{(uploadMutation.error as Error).message}</p>
        ) : null}
      </section>

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
