import { Link } from "react-router-dom";
import type { OpportunityCard } from "@/shared/api";
import JumpOnThisPanel from "@/features/radar/components/JumpOnThisPanel";
import RadScoreBadge from "@/features/radar/components/RadScoreBadge";

type Props = {
  card: OpportunityCard;
  signalLabel?: string;
  compact?: boolean;
};

function Meter({ label, value, hint }: { label: string; value: number; hint?: string }) {
  const v = Math.max(0, Math.min(100, Math.round(value)));
  return (
    <div>
      <div className="flex items-baseline justify-between gap-2">
        <span className="text-[11px] font-semibold uppercase tracking-wide text-slate-500">{label}</span>
        <span className="text-sm font-semibold text-slate-900">
          {v}/100{hint ? <span className="ml-1 text-xs font-medium text-emerald-700">{hint}</span> : null}
        </span>
      </div>
      <div className="mt-1 h-1.5 overflow-hidden rounded-full bg-slate-100">
        <div className="h-full rounded-full bg-radj-navy" style={{ width: `${v}%` }} />
      </div>
    </div>
  );
}

export default function OpportunityCardView({ card, signalLabel, compact }: Props) {
  const move = card.recommended_move;
  const fit = card.brand_fit;
  const rad = card.rad_score;

  return (
    <article className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-card">
      <div className="border-b border-slate-100 px-5 py-4 sm:px-6">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div className="min-w-0">
            <div className="flex flex-wrap items-center gap-2">
              <span className="text-lg" aria-hidden>
                {card.status_dot}
              </span>
              <h3 className="font-display text-xl font-semibold text-slate-900 sm:text-2xl">
                “{card.title}”
              </h3>
            </div>
            {signalLabel ? (
              <p className="mt-1 text-xs font-medium text-slate-500">{signalLabel}</p>
            ) : null}
          </div>
          <div className="rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 text-right">
            <p className="text-[10px] font-semibold uppercase tracking-wide text-slate-500">Lifecycle</p>
            <p className="text-sm font-semibold text-slate-900">
              {card.lifecycle.badge} {card.lifecycle.label}
            </p>
          </div>
        </div>

        {rad ? (
          <div className="mt-4">
            <RadScoreBadge rad={rad} />
          </div>
        ) : null}

        <div className="mt-4 grid gap-4 sm:grid-cols-2">
          <Meter label="Momentum" value={card.momentum.score} hint={card.momentum.direction} />
          <Meter label="Tunisia relevance" value={card.tunisia_relevance} />
        </div>

        <div className="mt-4 grid gap-3 sm:grid-cols-2">
          <div>
            <p className="text-[11px] font-semibold uppercase tracking-wide text-slate-500">Audience</p>
            <p className="mt-0.5 text-sm text-slate-800">{card.audience.label}</p>
          </div>
          <div>
            <p className="text-[11px] font-semibold uppercase tracking-wide text-slate-500">Sources</p>
            <div className="mt-1 flex flex-wrap gap-1.5">
              {card.sources.length ? (
                card.sources.map((s) => (
                  <span
                    key={s}
                    className="rounded-md border border-slate-200 bg-white px-2 py-0.5 text-[11px] font-medium text-slate-700"
                  >
                    {s}
                  </span>
                ))
              ) : (
                <span className="text-sm text-slate-500">Sources en cours d’agrégation</span>
              )}
            </div>
          </div>
        </div>
      </div>

      <div className="space-y-5 px-5 py-5 sm:px-6">
        <div>
          <h4 className="font-display text-sm font-semibold text-slate-900">Why it’s growing</h4>
          <p className="mt-2 text-sm leading-relaxed text-slate-700">{card.why_growing}</p>
        </div>

        {fit ? (
          <div
            className={`rounded-xl border px-4 py-4 ${
              fit.verdict === "skip"
                ? "border-red-200 bg-red-50"
                : fit.verdict === "caution"
                  ? "border-amber-200 bg-amber-50"
                  : "border-radj-navy/15 bg-[#f7ffe8]"
            }`}
          >
            <div className="flex flex-wrap items-end justify-between gap-2">
              <div>
                <h4
                  className={`font-display text-sm font-semibold ${
                    fit.verdict === "skip" ? "text-red-900" : "text-radj-navy"
                  }`}
                >
                  Brand Fit · {fit.brand}
                  {fit.from_brand_brain ? (
                    <span className="ml-2 text-[10px] font-semibold uppercase tracking-wide text-slate-500">
                      Brand Brain
                    </span>
                  ) : null}
                </h4>
                {fit.verdict_label ? (
                  <p
                    className={`mt-1 text-xs font-semibold ${
                      fit.verdict === "skip"
                        ? "text-red-800"
                        : fit.verdict === "caution"
                          ? "text-amber-900"
                          : "text-emerald-800"
                    }`}
                  >
                    {fit.verdict === "skip" ? "⛔ " : fit.verdict === "chase" ? "🟢 " : "🟡 "}
                    {fit.verdict_label}
                  </p>
                ) : null}
              </div>
              <p
                className={`font-display text-2xl font-semibold ${
                  fit.verdict === "skip" ? "text-red-800" : "text-radj-navy"
                }`}
              >
                {fit.fit_label}
              </p>
            </div>
            {fit.action ? <p className="mt-2 text-sm text-slate-800">{fit.action}</p> : null}
            <ul className="mt-3 space-y-1.5">
              {fit.reasons.map((r) => (
                <li key={r} className="flex gap-2 text-sm text-slate-800">
                  <span
                    className={`mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full ${
                      fit.verdict === "skip" ? "bg-red-600" : "bg-radj-navy"
                    }`}
                  />
                  <span>{r}</span>
                </li>
              ))}
            </ul>
          </div>
        ) : (
          <div className="rounded-xl border border-dashed border-slate-300 bg-slate-50 px-4 py-3 text-sm text-slate-600">
            Créez un{" "}
            <Link to="/marque" className="font-semibold text-radj-navy underline-offset-2 hover:underline">
              Brand Brain
            </Link>{" "}
            pour scorer chaque tendance à travers le DNA marque (y compris les « don’t chase »).
          </div>
        )}

        <div className="rounded-xl border border-slate-200 bg-slate-50/80 px-4 py-4">
          <h4 className="font-display text-sm font-semibold text-slate-900">Recommended move</h4>
          <p className="mt-2 font-display text-lg font-semibold text-slate-900">
            Campaign: “{move.campaign}”
          </p>
          <p className="mt-2 text-sm leading-relaxed text-slate-700">{move.concept}</p>
          <dl className="mt-4 grid gap-2 text-sm sm:grid-cols-2">
            <div>
              <dt className="text-[11px] font-semibold uppercase tracking-wide text-slate-500">Channels</dt>
              <dd className="font-medium text-slate-900">{move.channels}</dd>
            </div>
            <div>
              <dt className="text-[11px] font-semibold uppercase tracking-wide text-slate-500">Timing</dt>
              <dd className="font-medium text-slate-900">{move.timing}</dd>
            </div>
            <div>
              <dt className="text-[11px] font-semibold uppercase tracking-wide text-slate-500">Risk</dt>
              <dd className="font-medium capitalize text-slate-900">
                {move.risk}
                <span className="ml-1 text-xs font-normal text-slate-500">({move.risk_score})</span>
              </dd>
            </div>
            <div>
              <dt className="text-[11px] font-semibold uppercase tracking-wide text-slate-500">
                Trend saturation
              </dt>
              <dd className="font-medium text-slate-900">{move.trend_saturation_label}</dd>
            </div>
          </dl>
          {!compact ? (
            <p className="mt-4 border-t border-slate-200 pt-3 text-xs italic text-slate-500">
              {card.value_prop ||
                "RadArt just saved your strategist hours and gave creative something to work on."}
            </p>
          ) : null}
        </div>

        <JumpOnThisPanel clusterId={card.cluster_id} trendTitle={card.title} />
      </div>
    </article>
  );
}
