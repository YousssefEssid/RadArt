import type { RadScore } from "@/shared/api";

const TIER_STYLES: Record<string, string> = {
  high: "from-[#12142b] to-[#1c1c68] text-[#d7ff7b]",
  solid: "from-[#1c1c68] to-[#2a3a7a] text-white",
  watch: "from-slate-700 to-slate-600 text-white",
  weak: "from-amber-800 to-amber-700 text-amber-50",
  skip: "from-slate-500 to-slate-400 text-white",
};

type Props = {
  rad: RadScore;
};

export default function RadScoreBadge({ rad }: Props) {
  const style = TIER_STYLES[rad.tier.key] || TIER_STYLES.watch;
  const comps = rad.components;
  const pillars = rad.pillars;

  return (
    <div className="overflow-hidden rounded-2xl border border-slate-200 shadow-sm">
      <div className={`bg-gradient-to-br px-4 py-4 sm:px-5 ${style}`}>
        <p className="text-[10px] font-semibold uppercase tracking-[0.2em] opacity-80">
          Trend × Brand
        </p>
        <div className="mt-1 flex flex-wrap items-end justify-between gap-3">
          <div>
            <p className="font-display text-xs font-semibold uppercase tracking-[0.14em]">
              RAD SCORE
            </p>
            <p className="font-display text-4xl font-semibold leading-none sm:text-5xl">
              {rad.score_int}
            </p>
          </div>
          <p className="max-w-[14rem] text-right text-sm font-semibold leading-snug">
            {rad.tier.label_fr || rad.tier.label}
          </p>
        </div>
        <p className="mt-3 text-[11px] opacity-80">{rad.formula}</p>
      </div>

      <div className="space-y-3 bg-white px-4 py-4 sm:px-5">
        <div className="grid grid-cols-3 gap-2 text-center">
          {(
            [
              ["R", "Relevance", pillars.relevance],
              ["A", "Acceleration", pillars.acceleration],
              ["D", "Differentiation", pillars.differentiation],
            ] as const
          ).map(([letter, name, val]) => (
            <div key={letter} className="rounded-xl border border-slate-100 bg-slate-50 px-2 py-2">
              <p className="font-display text-lg font-semibold text-radj-navy">{Math.round(val)}</p>
              <p className="text-[10px] font-semibold uppercase tracking-wide text-slate-500">
                {letter} · {name}
              </p>
            </div>
          ))}
        </div>

        <div>
          <p className="text-[11px] font-semibold uppercase tracking-wide text-slate-500">Why</p>
          <p className="mt-1 text-sm leading-relaxed text-slate-700">{rad.why}</p>
        </div>

        <details className="rounded-xl border border-slate-100 bg-slate-50/80 px-3 py-2">
          <summary className="cursor-pointer text-xs font-semibold text-slate-600">
            Under the hood
          </summary>
          <ul className="mt-2 grid gap-1 text-[11px] text-slate-600 sm:grid-cols-2">
            <li>Momentum {Math.round(comps.momentum)}</li>
            <li>Freshness {Math.round(comps.freshness)}</li>
            <li>Tunisia relevance {Math.round(comps.tunisia_relevance)}</li>
            <li>Audience overlap {Math.round(comps.audience_overlap)}</li>
            <li>Brand fit {Math.round(comps.brand_fit)}</li>
            <li>Source diversity {Math.round(comps.source_diversity)}</li>
            <li>Competitive saturation {Math.round(comps.competitive_saturation)}</li>
            <li>− Brand safety risk {Math.round(comps.brand_safety_risk)}</li>
          </ul>
        </details>
      </div>
    </div>
  );
}
