import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { getCompetitorWarRoom, type WarRoomDossier, type WarRoomReport } from "@/shared/api";

function ThemeChip({ theme, open }: { theme: string; open?: boolean }) {
  return (
    <span
      className={`rounded-md border px-2 py-0.5 text-[11px] font-semibold ${
        open
          ? "border-radj-navy/30 bg-radj-lime/40 text-radj-navy"
          : "border-slate-200 bg-white text-slate-700"
      }`}
    >
      {theme}
    </span>
  );
}

function DossierCard({ d }: { d: WarRoomDossier }) {
  return (
    <article className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-card">
      <div className="border-b border-slate-100 bg-gradient-to-r from-[#12142b] to-[#1c1c68] px-5 py-4 text-white">
        <div className="flex flex-wrap items-start justify-between gap-2">
          <h3 className="font-display text-xl font-semibold">{d.name}</h3>
          <span className="rounded-full border border-white/20 px-2.5 py-0.5 text-[11px] font-semibold">
            {d.signal_count} signals
          </span>
        </div>
        <p className="mt-2 text-sm text-white/75">{d.audience_attracted}</p>
      </div>

      <div className="grid gap-0 md:grid-cols-2">
        <section className="space-y-3 border-b border-slate-100 p-5 md:border-b-0 md:border-r">
          <div>
            <h4 className="text-[11px] font-semibold uppercase tracking-wide text-slate-500">
              What are they talking about?
            </h4>
            <ul className="mt-2 space-y-1.5 text-sm text-slate-800">
              {(d.talking_about.length ? d.talking_about : ["—"]).map((t) => (
                <li key={t} className="rounded-lg bg-slate-50 px-3 py-2">
                  {t}
                </li>
              ))}
            </ul>
          </div>
          <div>
            <h4 className="text-[11px] font-semibold uppercase tracking-wide text-slate-500">
              Campaigns gaining traction
            </h4>
            <ul className="mt-2 space-y-1.5 text-sm">
              {(d.campaigns_gaining_traction.length ? d.campaigns_gaining_traction : []).map((c) => (
                <li key={String(c.title)} className="rounded-lg border border-slate-100 px-3 py-2">
                  <p className="font-medium text-slate-900">{c.title}</p>
                  <p className="text-[11px] text-slate-500">
                    {c.platform}
                    {c.engagement ? ` · eng ${c.engagement}` : ""}
                  </p>
                </li>
              ))}
              {!d.campaigns_gaining_traction.length ? (
                <li className="text-sm text-slate-400">—</li>
              ) : null}
            </ul>
          </div>
          <div>
            <h4 className="text-[11px] font-semibold uppercase tracking-wide text-slate-500">
              Themes they own
            </h4>
            <div className="mt-2 flex flex-wrap gap-1.5">
              {(d.themes_owned.length ? d.themes_owned : ["none yet"]).map((t) => (
                <ThemeChip key={t} theme={t} />
              ))}
            </div>
          </div>
        </section>

        <section className="space-y-3 p-5">
          <div>
            <h4 className="text-[11px] font-semibold uppercase tracking-wide text-slate-500">
              Audience attracted
            </h4>
            <p className="mt-1 text-sm text-slate-800">{d.audience_attracted}</p>
          </div>
          <div>
            <h4 className="text-[11px] font-semibold uppercase tracking-wide text-slate-500">
              Content format performance
            </h4>
            <ul className="mt-2 space-y-1 text-sm text-slate-800">
              {(d.content_formats.length ? d.content_formats : [{ format: "n/a", share: 0 }]).map((f) => (
                <li key={f.format} className="flex justify-between gap-2 rounded-lg bg-slate-50 px-3 py-1.5">
                  <span>{f.format}</span>
                  <span className="font-semibold tabular-nums">{Math.round(f.share)}%</span>
                </li>
              ))}
            </ul>
          </div>
          <div>
            <h4 className="text-[11px] font-semibold uppercase tracking-wide text-slate-500">
              Where are they silent?
            </h4>
            <div className="mt-2 flex flex-wrap gap-1.5">
              {(d.where_silent.length ? d.where_silent : ["—"]).map((t) => (
                <ThemeChip key={t} theme={t} open />
              ))}
            </div>
          </div>
          <div>
            <h4 className="text-[11px] font-semibold uppercase tracking-wide text-slate-500">
              Trends they adopted before us
            </h4>
            <ul className="mt-2 space-y-1.5 text-sm text-slate-800">
              {(d.trends_adopted_before_us.length ? d.trends_adopted_before_us : []).map((t) => (
                <li key={String(t.label)} className="rounded-lg border border-slate-100 px-3 py-2">
                  <p className="font-medium">{t.label}</p>
                  <p className="text-[11px] text-slate-500">{t.note}</p>
                </li>
              ))}
              {!d.trends_adopted_before_us.length ? (
                <li className="text-sm text-slate-400">Pas encore de cluster lié.</li>
              ) : null}
            </ul>
          </div>
        </section>
      </div>
      {d.notes ? <p className="border-t border-slate-100 px-5 py-3 text-xs text-slate-500">{d.notes}</p> : null}
    </article>
  );
}

function WarRoomView({ report }: { report: WarRoomReport }) {
  return (
    <div className="space-y-6">
      <div className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-card">
        <div className="bg-gradient-to-br from-[#12142b] via-[#1c1c68] to-[#2a2d4a] px-5 py-6 text-white sm:px-6">
          <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-[#d7ff7b]">
            Competitor War Room
          </p>
          <h2 className="mt-2 font-display text-2xl font-semibold">{report.title}</h2>
          <p className="mt-1 text-sm text-white/75">{report.subtitle}</p>
          <p className="mt-4 text-sm font-medium text-[#d7ff7b]">{report.playbook}</p>
          <div className="mt-4 flex flex-wrap gap-2 text-[11px] text-white/70">
            <span className="rounded-full border border-white/20 px-2.5 py-1">
              {report.summary.competitor_count} concurrents
            </span>
            <span className="rounded-full border border-white/20 px-2.5 py-1">
              {report.summary.open_themes} thèmes ouverts
            </span>
            <span className="rounded-full border border-white/20 px-2.5 py-1">
              {report.summary.gap_count} opportunity gaps
            </span>
            {report.brand ? (
              <span className="rounded-full border border-[#d7ff7b]/40 bg-[#d7ff7b]/10 px-2.5 py-1 text-[#d7ff7b]">
                Brand lens · {report.brand}
                {report.sector ? ` · ${report.sector}` : ""}
              </span>
            ) : null}
          </div>
        </div>

        <div className="p-5">
          <h3 className="font-display text-sm font-semibold text-slate-900">Theme board</h3>
          <p className="mt-1 text-xs text-slate-500">Who owns what — green chips are still open.</p>
          <div className="mt-3 flex flex-wrap gap-2">
            {report.theme_board.map((t) => (
              <div
                key={t.theme}
                className={`rounded-xl border px-3 py-2 text-xs ${
                  t.status === "open"
                    ? "border-radj-navy/25 bg-radj-lime/30"
                    : "border-slate-200 bg-slate-50"
                }`}
              >
                <p className="font-semibold text-slate-900">{t.theme}</p>
                <p className="mt-0.5 text-slate-600">
                  {t.status === "open" ? "OPEN" : t.owners.join(", ")}
                </p>
              </div>
            ))}
          </div>
        </div>
      </div>

      <section className="space-y-3">
        <h3 className="font-display text-lg font-semibold text-slate-900">Opportunity gaps</h3>
        <p className="text-sm text-slate-600">
          Strategic white space — where competitors are silent and you can position.
        </p>
        <div className="space-y-3">
          {report.opportunity_gaps.map((g) => (
            <div
              key={`${g.theme}-${g.gap_type}`}
              className="rounded-2xl border border-radj-navy/20 bg-[#f7ffe8] px-5 py-4 shadow-sm"
            >
              <p className="text-[11px] font-semibold uppercase tracking-wide text-radj-navy">
                {g.gap_type.replace("_", " ")} · {g.theme}
              </p>
              <h4 className="mt-1 font-display text-lg font-semibold text-slate-900">{g.headline}</h4>
              <p className="mt-2 text-sm font-semibold text-radj-navy">{g.opportunity}</p>
              <p className="mt-1 text-sm text-slate-700">{g.why}</p>
              {g.owned_by.length ? (
                <p className="mt-2 text-xs text-slate-500">Owned by: {g.owned_by.join(", ")}</p>
              ) : null}
            </div>
          ))}
          {!report.opportunity_gaps.length ? (
            <p className="text-sm text-slate-500">Pas encore de gap clair — enrichissez Brand Brain / collecte.</p>
          ) : null}
        </div>
      </section>

      <section className="space-y-4">
        <h3 className="font-display text-lg font-semibold text-slate-900">Competitor dossiers</h3>
        {report.dossiers.map((d) => (
          <DossierCard key={d.name} d={d} />
        ))}
      </section>
    </div>
  );
}

export default function CompetitorsPage() {
  const q = useQuery({
    queryKey: ["competitors", "war-room"],
    queryFn: getCompetitorWarRoom,
  });

  return (
    <div className="space-y-6">
      <p className="max-w-xl text-sm text-slate-600">
        Pas seulement de la veille — une War Room : thèmes possédés, silences, et opportunity gaps.
      </p>

      {!q.data?.competitors?.length && !q.isFetching ? (
        <div className="rounded-xl border border-dashed border-slate-300 bg-white px-4 py-6 text-sm text-slate-600">
          Configurez vos concurrents dans{" "}
          <Link to="/marque" className="font-semibold text-radj-navy underline-offset-2 hover:underline">
            Brand Brain
          </Link>{" "}
          pour ouvrir la War Room.
        </div>
      ) : null}

      {q.isFetching ? (
        <p className="rounded-xl border border-slate-200 bg-white px-4 py-8 text-center text-sm text-slate-500">
          Ouverture de la War Room…
        </p>
      ) : null}

      {q.isError ? (
        <p className="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800">
          {(q.error as Error).message}
        </p>
      ) : null}

      {q.data && q.data.competitors.length ? <WarRoomView report={q.data} /> : null}
    </div>
  );
}
