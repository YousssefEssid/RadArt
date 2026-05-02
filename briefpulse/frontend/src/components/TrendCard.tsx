import { useEffect, useId, useState } from "react";
import { createPortal } from "react-dom";
import type { Trend } from "../api";
import ScoreBadge from "./ScoreBadge";
import {
  actionCopy,
  getMomentum,
  getTrendAction,
  momentumCopy,
  type Momentum,
  type TrendAction,
} from "../lib/trendInsights";

const sectorHints: Record<string, string[]> = {
  weather: ["Food & beverage", "Retail", "Tourism"],
  youth: ["Telecom", "Education", "Food & beverage"],
  economy: ["Banking", "Retail", "Automotive"],
  sport: ["Telecom", "Beverage", "Betting (careful)"],
  culture: ["Tourism", "Telco", "Lifestyle"],
  lifestyle: ["Beauty", "Retail", "Food"],
  retail: ["CPG", "Discount retail", "Fintech"],
  politics: ["News brands", "NGO"],
  general: ["Multiple sectors"],
};

function sectorsFor(category: string) {
  return sectorHints[category] || sectorHints.general;
}

/** Évite d’afficher des fragments hex (#RRGGBB) comme faux hashtags. */
function displayableKeywords(kws: string[] | undefined): string[] {
  if (!kws?.length) return [];
  return kws.filter((kw) => {
    const t = kw.trim();
    if (!t) return false;
    if (/^#?[0-9a-f]{6}$/i.test(t)) return false;
    if (/^#?[0-9a-f]{3}$/i.test(t)) return false;
    return true;
  });
}

function sourceMeta(trend: Trend): string {
  const li = trend.latest_items;
  if (li.length >= 1) {
    const a = li[0];
    return `${a.platform} · ${a.source}`;
  }
  return trend.category || "—";
}

function heatBadge(trend: Trend): { label: string; className: string } {
  if (trend.trend_score >= 58 && trend.risk_score < 55) {
    return {
      label: "Hot 🔥",
      className: "border-radj-navy/25 bg-radj-lime/50 text-radj-navy",
    };
  }
  if (trend.risk_score >= 65) {
    return { label: "Risque", className: "border-red-200 bg-red-50 text-red-900" };
  }
  return { label: "Suivi", className: "border-slate-200 bg-slate-100 text-slate-700" };
}

function statusDotClass(trend: Trend): string {
  if (trend.risk_score >= 65) return "bg-red-500";
  if (trend.trend_score >= 52) return "bg-radj-navy";
  return "bg-emerald-500";
}

function ctaSummaryLabel(action: TrendAction): string {
  switch (action) {
    case "publish_now":
      return "Agir maintenant";
    case "wait":
      return "Patienter";
    case "avoid":
      return "Prudence";
  }
}

/** Pastilles CTA : une couleur par type de reco (carte + détail). */
function ctaChipClass(action: TrendAction): string {
  switch (action) {
    case "publish_now":
      return "border-emerald-200 bg-emerald-50 text-emerald-900";
    case "wait":
      return "border-sky-200 bg-sky-50 text-sky-900";
    case "avoid":
      return "border-amber-200 bg-amber-50 text-amber-900";
  }
}

function ctaLectureTitleClass(action: TrendAction): string {
  switch (action) {
    case "publish_now":
      return "text-emerald-900";
    case "wait":
      return "text-sky-900";
    case "avoid":
      return "text-amber-900";
  }
}

function PulseBars({ score }: { score: number }) {
  const s = Math.max(0, Math.min(100, score)) / 100;
  const ratios = [0.35, 0.48, 0.58, 0.72, 1];
  /** Alternate navy / green like the dashboard chart */
  const barTone = (i: number) =>
    i % 2 === 0 ? "bg-radj-navy" : "bg-emerald-500";
  return (
    <div className="flex h-8 items-end justify-center gap-1" role="img" aria-label={`Pulse ${Math.round(score)}`}>
      {ratios.map((r, i) => (
        <div
          key={i}
          className={`w-2 rounded-sm ${barTone(i)}`}
          style={{ height: `${Math.max(6, Math.round(10 + r * s * 22))}px` }}
        />
      ))}
    </div>
  );
}

function MomentumBar({ momentum }: { momentum: Momentum }) {
  const order: Momentum[] = ["falling", "stable", "rising"];
  return (
    <div className="flex gap-1.5" role="img" aria-label={`Momentum : ${momentumCopy[momentum].label}`}>
      {order.map((m) => (
        <div
          key={m}
          className={`h-2 flex-1 rounded-full ${m === momentum ? "bg-radj-navy" : "bg-slate-200"}`}
        />
      ))}
    </div>
  );
}

function TrendDetailBody({ trend }: { trend: Trend }) {
  const momentum = getMomentum(trend);
  const action = getTrendAction(trend);
  const mText = momentumCopy[momentum];
  const aText = actionCopy[action];

  return (
    <>
      <div className="flex flex-wrap gap-2">
        <ScoreBadge label="Pulse" value={trend.trend_score} variant="trend" />
        <ScoreBadge label="Risque" value={trend.risk_score} variant="risk" />
      </div>

      <p className="mt-4 text-sm leading-relaxed text-slate-700">{trend.summary}</p>

      <div className="mt-4 rounded-xl border border-slate-100 bg-slate-50/80 p-4">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <p className="text-[11px] font-semibold uppercase tracking-wide text-slate-500">Momentum</p>
          <span className="rounded-md border border-slate-200 bg-white px-2 py-0.5 text-xs font-semibold text-radj-navy shadow-sm">
            {mText.label}
          </span>
        </div>
        <p className="mt-2 text-[11px] text-slate-600">{mText.hint}</p>
        <div className="mt-3">
          <div className="mb-1 flex justify-between text-[10px] text-slate-500">
            <span>Redescend</span>
            <span>Stable</span>
            <span>Montée</span>
          </div>
          <MomentumBar momentum={momentum} />
        </div>
        <div className="mt-4 border-t border-slate-200 pt-3">
          <p className="text-[11px] font-semibold uppercase tracking-wide text-slate-500">Lecture</p>
          <p className={`mt-1 font-display text-sm font-semibold ${ctaLectureTitleClass(action)}`}>{aText.label}</p>
          <p className="mt-1 text-[11px] text-slate-600">{aText.sub}</p>
        </div>
      </div>

      <dl className="mt-4 grid grid-cols-2 gap-2 text-[11px] sm:grid-cols-4">
        <div className="rounded-lg border border-slate-200 bg-white px-2 py-2 shadow-sm">
          <dt className="text-slate-500">Sources</dt>
          <dd className="font-semibold tabular-nums text-slate-900">{trend.source_count}</dd>
        </div>
        <div className="rounded-lg border border-slate-200 bg-white px-2 py-2 shadow-sm">
          <dt className="text-slate-500">Signaux</dt>
          <dd className="font-semibold tabular-nums text-slate-900">{trend.item_count}</dd>
        </div>
        <div className="rounded-lg border border-slate-200 bg-white px-2 py-2 shadow-sm">
          <dt className="text-slate-500">Pulse</dt>
          <dd className="font-semibold tabular-nums text-radj-navy">{Math.round(trend.trend_score)}</dd>
        </div>
        <div className="rounded-lg border border-slate-200 bg-white px-2 py-2 shadow-sm">
          <dt className="text-slate-500">Risque</dt>
          <dd className="font-semibold tabular-nums text-slate-900">{Math.round(trend.risk_score)}</dd>
        </div>
      </dl>

      <div className="mt-4 flex flex-wrap gap-2">
        <span className="rounded-md border border-slate-200 bg-slate-50 px-2 py-0.5 text-xs text-slate-700">
          {trend.category}
        </span>
        {displayableKeywords(trend.keywords).map((kw) => (
          <span
            key={kw}
            className="rounded-md border border-dashed border-slate-300 px-2 py-0.5 text-[11px] text-slate-600"
          >
            #{kw}
          </span>
        ))}
      </div>

      <div className="mt-4">
        <p className="text-xs font-medium uppercase tracking-wide text-slate-500">Secteurs</p>
        <div className="mt-1 flex flex-wrap gap-1.5">
          {sectorsFor(trend.category).map((s) => (
            <span
              key={s}
              className="rounded-full border border-radj-navy/25 bg-radj-lime/25 px-2 py-0.5 text-[11px] text-slate-800"
            >
              {s}
            </span>
          ))}
        </div>
      </div>

      {trend.latest_items?.length ? (
        <ul className="mt-4 space-y-2 border-t border-slate-100 pt-4 text-xs text-slate-600">
          {trend.latest_items.map((it) => (
            <li key={it.id} className="min-w-0">
              <span className="font-medium text-radj-navy">{it.source}</span> · {it.title}
              {it.url ? (
                <a
                  href={it.url}
                  target="_blank"
                  rel="noreferrer"
                  className="ml-1 font-medium text-radj-navy hover:text-radj-lime hover:underline"
                >
                  →
                </a>
              ) : null}
            </li>
          ))}
        </ul>
      ) : null}
    </>
  );
}

export default function TrendCard({ trend }: { trend: Trend }) {
  const [open, setOpen] = useState(false);
  const dialogId = useId();
  const action = getTrendAction(trend);
  const badge = heatBadge(trend);
  const metaLine =
    trend.source_count <= 1
      ? `${trend.source_count} source`
      : `${trend.source_count} sources`;

  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") setOpen(false);
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open]);

  useEffect(() => {
    if (open) document.body.style.overflow = "hidden";
    return () => {
      document.body.style.overflow = "";
    };
  }, [open]);

  const modal =
    open &&
    createPortal(
      <div className="fixed inset-0 z-[100] flex items-center justify-center p-4">
        <button
          type="button"
          className="absolute inset-0 bg-slate-900/40 backdrop-blur-[2px]"
          aria-label="Fermer"
          onClick={() => setOpen(false)}
        />
        <div
          role="dialog"
          id={dialogId}
          aria-modal
          aria-labelledby={`${dialogId}-title`}
          className="relative z-10 max-h-[min(90vh,720px)] w-full max-w-lg overflow-y-auto rounded-2xl border border-slate-200 bg-white p-6 shadow-xl"
        >
          <button
            type="button"
            className="absolute right-4 top-4 flex h-9 w-9 items-center justify-center rounded-lg border border-slate-200 bg-white text-lg leading-none text-slate-600 shadow-sm hover:bg-slate-50"
            onClick={() => setOpen(false)}
            aria-label="Fermer"
          >
            ×
          </button>
          <h3 id={`${dialogId}-title`} className="pr-10 font-display text-xl font-semibold text-slate-900">
            {trend.label}
          </h3>
          <div className="mt-4">
            <TrendDetailBody trend={trend} />
          </div>
        </div>
      </div>,
      document.body
    );

  return (
    <>
      <button
        type="button"
        onClick={() => setOpen(true)}
        aria-haspopup="dialog"
        aria-expanded={open}
        aria-controls={open ? dialogId : undefined}
        className="flex h-full w-full flex-col rounded-2xl border border-slate-200 bg-white p-4 text-left shadow-sm ring-1 ring-slate-900/5 transition hover:border-slate-300 hover:shadow-md focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-radj-navy"
      >
        <div className="flex items-start justify-between gap-2">
          <div className="flex min-w-0 items-center gap-2">
            <span className={`h-2 w-2 shrink-0 rounded-full ${statusDotClass(trend)}`} aria-hidden />
            <span className="truncate text-xs text-slate-500">{sourceMeta(trend)}</span>
          </div>
          <span
            className={`shrink-0 rounded-full border px-2.5 py-0.5 text-[11px] font-semibold ${badge.className}`}
          >
            {badge.label}
          </span>
        </div>

        <h3 className="mt-3 font-display text-base font-semibold leading-snug text-slate-900">{trend.label}</h3>
        <p className="mt-2 line-clamp-2 text-sm leading-relaxed text-slate-600">{trend.summary}</p>

        <div className="mt-3">
          <PulseBars score={trend.trend_score} />
        </div>

        <div className="mt-4 flex flex-wrap items-center justify-between gap-2 border-t border-slate-100 pt-3">
          <span className="text-[11px] text-slate-400">
            {metaLine}
            {trend.item_count > 0 ? ` · ${trend.item_count} signaux` : null}
          </span>
          <span
            className={`rounded-lg border px-3 py-1.5 text-xs font-semibold shadow-sm ${ctaChipClass(action)}`}
          >
            {ctaSummaryLabel(action)}
          </span>
        </div>
      </button>

      {modal}
    </>
  );
}
