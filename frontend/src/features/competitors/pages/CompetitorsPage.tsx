import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { getTelecomCompetitiveStudy, type CompetitorsReport } from "@/shared/api";

const fieldClass =
  "mt-1 w-full max-w-md rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 shadow-sm outline-none placeholder:text-slate-400 focus:border-radj-navy focus:ring-2 focus:ring-radj-navy/20";

const btnPrimary =
  "inline-flex items-center justify-center rounded-xl bg-radj-navy px-5 py-2.5 text-sm font-semibold text-radj-lime shadow-sm transition hover:bg-radj-navy/90 disabled:opacity-50";

/** Délai minimum pour une phase de chargement lisible (UX). */
const MIN_LOAD_MS = 1100;

function isTelecomUnlock(value: string): boolean {
  return value.trim().toLowerCase() === "telecom";
}

export default function CompetitorsPage() {
  const [unlockInput, setUnlockInput] = useState("");
  const [report, setReport] = useState<CompetitorsReport | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const inputRef = useRef(unlockInput);
  inputRef.current = unlockInput;

  const unlocked = isTelecomUnlock(unlockInput);

  useEffect(() => {
    if (!isTelecomUnlock(unlockInput)) {
      setReport(null);
      setError(null);
    }
  }, [unlockInput]);

  const loadStudy = useCallback(async () => {
    if (!isTelecomUnlock(inputRef.current)) {
      setError("Saisissez exactement le mot-clé telecom, puis cliquez sur le bouton.");
      return;
    }
    setError(null);
    setLoading(true);
    const t0 = Date.now();
    try {
      const r = await getTelecomCompetitiveStudy();
      const elapsed = Date.now() - t0;
      const rest = Math.max(0, MIN_LOAD_MS - elapsed);
      if (rest > 0) {
        await new Promise((res) => setTimeout(res, rest));
      }
      if (!isTelecomUnlock(inputRef.current)) {
        setReport(null);
        return;
      }
      setReport(r);
    } catch (e) {
      setReport(null);
      setError(e instanceof Error ? e.message : "Chargement impossible");
    } finally {
      setLoading(false);
    }
  }, []);

  const totals = useMemo(() => {
    if (!report) return { competitors: 0, signals: 0 };
    return {
      competitors: report.cards.length,
      signals: report.cards.reduce((a, c) => a + c.signal_count, 0),
    };
  }, [report]);

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3 md:hidden">
        <h2 className="font-display text-xl font-semibold text-slate-900">Concurrents</h2>
        {report && !loading ? (
          <div className="flex flex-wrap gap-2">
            <span className="rounded-full border border-slate-200 bg-slate-50 px-2 py-0.5 text-[10px] font-semibold tabular-nums text-slate-800">
              {totals.competitors} marque{totals.competitors !== 1 ? "s" : ""}
            </span>
            <span className="rounded-full border border-radj-navy/20 bg-radj-lime/15 px-2 py-0.5 text-[10px] font-semibold tabular-nums text-radj-navy">
              {totals.signals} signal{totals.signals !== 1 ? "x" : ""}
            </span>
          </div>
        ) : null}
      </div>
      <div className="hidden md:flex md:flex-wrap md:items-end md:justify-between md:gap-4">
        <p className="max-w-xl text-sm text-slate-600">
          Étude concurrentielle et signaux associés aux marques du brief.
        </p>
        {report && !loading ? (
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

      <div className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm ring-1 ring-slate-900/5">
        <label className="block text-xs font-medium text-slate-700">
          Accès à l’étude concurrentielle
          <input
            type="text"
            value={unlockInput}
            disabled={loading}
            onChange={(e) => setUnlockInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter") {
                e.preventDefault();
                loadStudy().catch(console.error);
              }
            }}
            placeholder="telecom"
            autoComplete="off"
            className={fieldClass}
          />
        </label>
        <p className="mt-2 text-xs text-slate-500">
          Saisissez <code className="rounded bg-slate-100 px-1 py-0.5 text-[11px]">telecom</code> (insensible à la
          casse), puis cliquez sur <strong className="font-medium text-slate-700">Charger l’étude</strong>.
        </p>
        <div className="mt-4">
          <button
            type="button"
            disabled={loading}
            onClick={() => loadStudy().catch(console.error)}
            className={btnPrimary}
          >
            {loading ? "Chargement en cours…" : "Charger l’étude concurrentielle"}
          </button>
        </div>
      </div>

      {!report && !loading ? (
        <div className="rounded-xl border border-dashed border-slate-200 bg-slate-50/80 px-4 py-8 text-center text-sm text-slate-600">
          {unlocked
            ? "Cliquez sur « Charger l’étude concurrentielle » pour lancer l’analyse et afficher le rapport."
            : "Saisissez le mot-clé telecom, puis validez avec le bouton ci-dessus."}
        </div>
      ) : null}

      {loading ? (
        <div className="rounded-2xl border border-slate-200 bg-white px-6 py-10 shadow-sm ring-1 ring-slate-900/5">
          <div className="mx-auto max-w-sm text-center">
            <div
              className="mx-auto h-10 w-10 animate-spin rounded-full border-2 border-radj-navy border-t-transparent"
              aria-hidden
            />
            <p className="mt-4 font-display text-sm font-semibold text-slate-900">Analyse concurrentielle en cours</p>
            <p className="mt-2 text-xs text-slate-500">
              Agrégation des signaux, veille marques et tendances secteur télécom…
            </p>
          </div>
        </div>
      ) : null}

      {error ? (
        <div className="rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-900">{error}</div>
      ) : null}

      {!loading && report ? (
        <>
          <h3 className="font-display text-lg font-semibold text-slate-900">Étude concurrentielle</h3>

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
                      <h4 className="font-display text-xl font-semibold tracking-tight text-slate-900">{card.name}</h4>
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
                    <h5 className="text-[11px] font-semibold uppercase tracking-wide text-slate-500">Signaux</h5>
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
                    <h5 className="text-[11px] font-semibold uppercase tracking-wide text-slate-500">Clusters</h5>
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
    </div>
  );
}
