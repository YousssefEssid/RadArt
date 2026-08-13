import { Link } from "react-router-dom";
import type { MorningRadarItem, MorningRadarReport, MorningSignalKind } from "@/shared/api";
import CompetitiveAlertsPanel from "@/features/radar/components/CompetitiveAlertsPanel";
import OpportunityCardView from "@/features/radar/components/OpportunityCardView";

const KIND_STYLES: Record<MorningSignalKind, { chip: string }> = {
  emerging: { chip: "bg-orange-50 text-orange-900 border-orange-200" },
  growing: { chip: "bg-emerald-50 text-emerald-900 border-emerald-200" },
  competitor_move: { chip: "bg-violet-50 text-violet-900 border-violet-200" },
  conversation_shift: { chip: "bg-sky-50 text-sky-900 border-sky-200" },
  reputation: { chip: "bg-red-50 text-red-900 border-red-200" },
  brand_opportunity: { chip: "bg-radj-lime/40 text-radj-navy border-radj-navy/20" },
  fading: { chip: "bg-slate-100 text-slate-700 border-slate-200" },
};

function SignalFallback({ item }: { item: MorningRadarItem }) {
  return (
    <article className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
      <h4 className="font-display text-base font-semibold text-slate-900">{item.label}</h4>
      <p className="mt-2 text-sm text-slate-700">{item.why_it_matters}</p>
      <p className="mt-2 text-sm text-slate-700">{item.what_to_do}</p>
    </article>
  );
}

type Props = {
  report: MorningRadarReport;
  loading?: boolean;
};

export default function MorningRadarBoard({ report, loading }: Props) {
  const ctx = report.brief_context;
  const activeSections = report.sections.filter((s) => s.count > 0);
  const emptySections = report.sections.filter((s) => s.count === 0);

  return (
    <section className="space-y-5">
      <div className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-card">
        <div className="border-b border-slate-100 bg-gradient-to-br from-[#12142b] via-[#1c1c68] to-[#2a2d4a] px-5 py-6 text-white sm:px-6">
          <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-[#d7ff7b]">
            Morning Radar · Opportunity Cards
          </p>
          <h2 className="mt-2 font-display text-xl font-semibold sm:text-2xl">
            Qu’est-ce qui a changé — et quoi exécuter ?
          </h2>
          <p className="mt-2 max-w-2xl text-sm text-white/80">{report.question}</p>
          <p className="mt-4 text-sm font-medium text-[#d7ff7b]">{report.headline}</p>
          <div className="mt-4 flex flex-wrap gap-2 text-[11px] text-white/70">
            <span className="rounded-full border border-white/20 px-2.5 py-1">
              {report.summary.trends_scanned} tendances → opportunity cards
            </span>
            <span className="rounded-full border border-white/20 px-2.5 py-1">
              {report.summary.total_signals} classées
            </span>
            {ctx.has_brand_brain || ctx.has_brief ? (
              <span className="rounded-full border border-[#d7ff7b]/40 bg-[#d7ff7b]/10 px-2.5 py-1 text-[#d7ff7b]">
                {ctx.brand_name || ctx.client_name || `Brief #${ctx.brief_id}`}
                {ctx.sector ? ` · ${ctx.sector}` : ""}
              </span>
            ) : (
              <Link
                to="/marque"
                className="rounded-full border border-white/25 px-2.5 py-1 text-white/90 hover:bg-white/10"
              >
                Activer Brand Brain → DNA marque
              </Link>
            )}
          </div>
        </div>

        {loading ? (
          <p className="px-5 py-8 text-sm text-slate-500">Chargement du radar…</p>
        ) : (
          <div className="grid gap-3 p-4 sm:grid-cols-2 lg:grid-cols-4 xl:grid-cols-7">
            {report.sections.map((s) => {
              const style = KIND_STYLES[s.kind];
              return (
                <a
                  key={s.kind}
                  href={`#radar-${s.kind}`}
                  className={`rounded-xl border px-3 py-3 transition hover:shadow-sm ${style.chip}`}
                >
                  <div className="flex items-center justify-between gap-2">
                    <span className="text-lg" aria-hidden>
                      {s.emoji}
                    </span>
                    <span className="font-display text-lg font-semibold">{s.count}</span>
                  </div>
                  <p className="mt-1 text-xs font-semibold leading-tight">{s.label_fr}</p>
                </a>
              );
            })}
          </div>
        )}
      </div>

      <CompetitiveAlertsPanel report={report.competitive_alerts} />

      {activeSections.map((section) => (
        <div key={section.kind} id={`radar-${section.kind}`} className="scroll-mt-24 space-y-4">
          <div className="flex flex-wrap items-end justify-between gap-2">
            <div>
              <h3 className="font-display text-lg font-semibold text-slate-900">
                {section.emoji} {section.label_fr}
              </h3>
              <p className="text-sm text-slate-500">{section.question}</p>
            </div>
            <span className="text-xs font-medium text-slate-500">
              {section.count} opportunity card{section.count !== 1 ? "s" : ""}
            </span>
          </div>
          <div className="space-y-4">
            {section.items.map((item) =>
              item.opportunity ? (
                <OpportunityCardView
                  key={`${section.kind}-${item.id}`}
                  card={item.opportunity}
                  signalLabel={`${section.emoji} ${section.label_fr}`}
                />
              ) : (
                <SignalFallback key={`${section.kind}-${item.id}`} item={item} />
              )
            )}
          </div>
        </div>
      ))}

      {!loading && activeSections.length === 0 ? (
        <p className="rounded-xl border border-dashed border-slate-300 bg-white/60 px-4 py-8 text-center text-sm text-slate-500">
          Pas encore assez de signaux. Lancez une collecte puis revenez — chaque tendance devient une
          Opportunity Card.
        </p>
      ) : null}

      {emptySections.length > 0 && activeSections.length > 0 ? (
        <p className="text-xs text-slate-500">
          Buckets vides : {emptySections.map((s) => `${s.emoji} ${s.label_fr}`).join(" · ")}
        </p>
      ) : null}
    </section>
  );
}
