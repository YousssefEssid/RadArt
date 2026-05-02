import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import {
  getCompetitorsDemo,
  getCompetitorsReport,
  getLatestBrief,
  type CompetitorsReport,
  type LatestBrief,
} from "../api";

const btnOutline = "rounded-lg border border-slate-300 bg-white px-4 py-2 text-sm font-semibold text-slate-700 shadow-sm hover:border-radj-navy hover:text-radj-navy disabled:opacity-50";
const btnPrimary = "rounded-lg bg-radj-navy px-4 py-2 text-sm font-semibold text-radj-lime shadow-sm transition hover:bg-radj-navy/90 disabled:opacity-50";

function BriefPicker({
  value,
  onChange,
  disabled,
}: {
  value: number | "";
  onChange: (v: number | "") => void;
  disabled?: boolean;
}) {
  return (
    <label className="block text-[11px] font-medium text-slate-700">
      Brief (ID)
      <input
        type="number"
        min={1}
        value={value === "" ? "" : value}
        disabled={disabled}
        onChange={(e) => {
          const t = e.target.value;
          onChange(t === "" ? "" : parseInt(t, 10));
        }}
        className="mt-1 w-full max-w-[10rem] rounded-lg border border-slate-300 bg-white px-2 py-1.5 text-sm text-slate-900 shadow-sm outline-none focus:border-radj-navy focus:ring-2 focus:ring-radj-navy/20"
      />
    </label>
  );
}

export default function CompetitorsPage() {
  const [report, setReport] = useState<CompetitorsReport | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [isDemo, setIsDemo] = useState(true);
  const [briefIdInput, setBriefIdInput] = useState<number | "">("");
  const briefIdInputRef = useRef(briefIdInput);
  briefIdInputRef.current = briefIdInput;

  const loadDemo = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const r = await getCompetitorsDemo();
      setReport(r);
      setIsDemo(true);
    } catch (e) {
      setReport(null);
      setError(e instanceof Error ? e.message : "Démo indisponible");
    } finally {
      setLoading(false);
    }
  }, []);

  const loadLive = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      let bid: number | undefined;
      const typed = briefIdInputRef.current;
      if (typed !== "" && Number.isFinite(typed)) {
        bid = typed;
      } else {
        try {
          const raw =
            localStorage.getItem("radj_last_brief_id") ?? localStorage.getItem("briefpulse_last_brief_id");
          if (raw) {
            const n = parseInt(raw, 10);
            if (Number.isFinite(n)) bid = n;
          }
        } catch {
          /* ignore */
        }
        if (bid == null) {
          const latest = await getLatestBrief();
          if (latest && "id" in latest && typeof (latest as LatestBrief).id === "number") {
            bid = (latest as LatestBrief).id;
          }
        }
      }
      const r = await getCompetitorsReport(bid);
      setReport(r);
      setIsDemo(false);
      if (bid != null) setBriefIdInput(bid);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Chargement impossible");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadDemo().catch(console.error);
  }, [loadDemo]);

  const totals = useMemo(() => {
    if (!report) return { competitors: 0, signals: 0 };
    return {
      competitors: report.cards.length,
      signals: report.cards.reduce((a, c) => a + c.signal_count, 0),
    };
  }, [report]);

  return (
    <div className="mx-auto max-w-5xl space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3 md:hidden">
        <h2 className="font-display text-xl font-semibold text-slate-900">Concurrents</h2>
        {isDemo && !loading ? (
          <span className="rounded-full border border-amber-300 bg-amber-50 px-2 py-0.5 text-[10px] font-semibold text-amber-900">
            Démo TT
          </span>
        ) : null}
      </div>
      <div className="hidden md:flex md:flex-wrap md:items-end md:justify-between md:gap-4">
        <h2 className="font-display text-2xl font-semibold text-slate-900">Concurrents</h2>
        {isDemo && !loading ? (
          <span className="rounded-full border border-amber-300 bg-amber-50 px-3 py-1 text-xs font-semibold text-amber-900">
            Démo — Tunisie Telecom
          </span>
        ) : null}
        {!loading && report ? (
          <div className="flex flex-wrap gap-2">
            <span className="rounded-full border border-slate-200 bg-slate-50 px-3 py-1 text-xs font-semibold tabular-nums text-slate-800">
              {totals.competitors} marque{totals.competitors !== 1 ? "s" : ""}
            </span>
            <span className="rounded-full border border-radj-navy/20 bg-radj-lime/15 px-3 py-1 text-xs font-semibold tabular-nums text-radj-navy">
              {totals.signals} signal{totals.signals !== 1 ? "x" : ""}
            </span>
          </div>
        ) : null}
      </div>

      {isDemo ? (
        <div className="rounded-2xl border border-cyan-200 bg-cyan-50/80 px-4 py-3 text-sm text-slate-800">
          <p className="font-semibold text-slate-900">Visualisation d’exemple</p>
          <p className="mt-1 text-xs text-slate-600">
            Données statiques : <strong>Tunisie Telecom</strong> et ses principaux concurrents (Orange Tunisie, Ooredoo
            Tunisie), signaux et tendances factices pour tester l’interface. Utilisez le bouton ci-dessous pour
            afficher le rapport lié à un vrai brief analysé.
          </p>
        </div>
      ) : null}

      <div className="flex flex-col gap-3 rounded-2xl border border-slate-200 bg-white p-4 shadow-sm ring-1 ring-slate-900/5 sm:flex-row sm:flex-wrap sm:items-end sm:justify-between">
        <BriefPicker value={briefIdInput} onChange={setBriefIdInput} disabled={loading} />
        <div className="flex flex-wrap gap-2">
          <button
            type="button"
            disabled={loading}
            onClick={() => loadLive().catch(console.error)}
            className={btnPrimary}
          >
            {loading && !isDemo ? "Chargement…" : "Charger le brief (données réelles)"}
          </button>
          <button
            type="button"
            disabled={loading}
            onClick={() => loadDemo().catch(console.error)}
            className={btnOutline}
          >
            {loading && isDemo ? "Chargement…" : "Revenir à la démo TT"}
          </button>
        </div>
      </div>

      {error ? (
        <div className="rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-900">{error}</div>
      ) : null}

      {!loading && report ? (
        <>
          <div className="flex flex-col gap-3 rounded-2xl border border-slate-200 bg-gradient-to-br from-slate-50 to-white px-4 py-4 shadow-sm ring-1 ring-slate-900/5 sm:flex-row sm:flex-wrap sm:items-center sm:justify-between">
            <div className="flex min-w-0 flex-wrap items-center gap-x-3 gap-y-1 text-sm text-slate-800">
              <span className="font-display font-semibold text-radj-navy">#{report.brief_id}</span>
              {report.client_name ? (
                <span className="truncate">
                  <span className="text-slate-400">·</span> {report.client_name}
                </span>
              ) : null}
              {report.sector ? (
                <span className="truncate">
                  <span className="text-slate-400">·</span> {report.sector}
                </span>
              ) : null}
              {report.target ? (
                <span className="truncate text-slate-600">
                  <span className="text-slate-400">·</span> {report.target}
                </span>
              ) : null}
            </div>
            {report.competitor_source === "demo_static" ? (
              <span className="shrink-0 rounded-full border border-cyan-300 bg-cyan-50 px-3 py-1 text-[11px] font-semibold text-cyan-900">
                Démo statique
              </span>
            ) : report.competitor_source === "sector_benchmark" ? (
              <span className="shrink-0 rounded-full border border-amber-200 bg-amber-50 px-3 py-1 text-[11px] font-medium text-amber-900">
                Repères sectoriels
              </span>
            ) : (
              <span className="shrink-0 rounded-full bg-radj-navy px-3 py-1 text-[11px] font-semibold text-radj-lime">
                Brief
              </span>
            )}
          </div>

          <div className="space-y-5">
            {report.cards.map((card) => (
              <article
                key={card.name}
                className="relative overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-md ring-1 ring-slate-900/5"
              >
                <div className="h-1 bg-gradient-to-r from-radj-lime via-radj-lime/70 to-transparent" aria-hidden />
                <div className="border-b border-slate-100 bg-white px-5 py-4">
                  <div className="flex flex-wrap items-start justify-between gap-3">
                    <div className="min-w-0">
                      <h3 className="font-display text-xl font-semibold tracking-tight text-slate-900">{card.name}</h3>
                      {card.notes ? (
                        <p className="mt-2 line-clamp-2 text-xs text-slate-500">{card.notes}</p>
                      ) : null}
                    </div>
                    <div className="flex shrink-0 flex-col items-end gap-1">
                      <span className="rounded-full bg-slate-100 px-2.5 py-1 text-xs font-semibold tabular-nums text-slate-800">
                        {card.signal_count} signal{card.signal_count !== 1 ? "x" : ""}
                      </span>
                      <span className="text-[10px] font-medium uppercase tracking-wide text-slate-400">
                        {card.source_tag === "brief" ? "Brief" : "Secteur"}
                      </span>
                    </div>
                  </div>
                </div>

                <div className="grid gap-0 bg-slate-50/50 md:grid-cols-2">
                  <div className="border-b border-slate-100 p-5 md:border-b-0 md:border-r md:border-slate-100">
                    <h4 className="text-[11px] font-semibold uppercase tracking-wide text-slate-500">Signaux</h4>
                    {card.recent_signals.length === 0 ? (
                      <p className="mt-3 text-sm text-slate-400">—</p>
                    ) : (
                      <ul className="mt-2 space-y-2 text-sm">
                        {card.recent_signals.map((s) => (
                          <li key={s.id} className="rounded-lg border border-white bg-white px-3 py-2 shadow-sm">
                            <p className="font-medium text-slate-900">{s.title}</p>
                            <p className="mt-1 text-[11px] text-slate-500">
                              {s.source} · {s.platform}
                              {s.category ? ` · ${s.category}` : ""}
                            </p>
                            {s.url ? (
                              <a
                                href={s.url}
                                target="_blank"
                                rel="noreferrer"
                                className="mt-1 inline-block text-xs font-medium text-radj-navy hover:text-radj-lime hover:underline"
                              >
                                Ouvrir le lien
                              </a>
                            ) : null}
                          </li>
                        ))}
                      </ul>
                    )}
                  </div>
                  <div className="p-5">
                    <h4 className="text-[11px] font-semibold uppercase tracking-wide text-slate-500">Clusters</h4>
                    {card.related_clusters.length === 0 ? (
                      <p className="mt-3 text-sm text-slate-400">—</p>
                    ) : (
                      <ul className="mt-2 space-y-2 text-sm">
                        {card.related_clusters.map((c) => (
                          <li key={c.id} className="rounded-lg border border-white bg-white px-3 py-2 shadow-sm">
                            <p className="font-medium text-slate-900">{c.label}</p>
                            {c.summary ? <p className="mt-1 line-clamp-3 text-xs text-slate-600">{c.summary}</p> : null}
                            <p className="mt-1 text-[11px] text-slate-500">
                              Pulse {c.trend_score != null ? Math.round(c.trend_score) : "—"} · Risque{" "}
                              {c.risk_score != null ? Math.round(c.risk_score) : "—"}
                              {c.category ? ` · ${c.category}` : ""}
                            </p>
                          </li>
                        ))}
                      </ul>
                    )}
                  </div>
                </div>
              </article>
            ))}
          </div>
        </>
      ) : null}

      {!loading && !error && !report ? (
        <p className="text-sm text-slate-400">—</p>
      ) : null}
    </div>
  );
}
