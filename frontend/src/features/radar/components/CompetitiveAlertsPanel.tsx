import { Link } from "react-router-dom";
import type { CompetitiveAlert, CompetitiveAlertsReport } from "@/shared/api";

type Props = {
  report?: CompetitiveAlertsReport | null;
};

function AlertCard({ alert }: { alert: CompetitiveAlert }) {
  return (
    <article
      className={`rounded-2xl border px-4 py-4 shadow-sm sm:px-5 ${
        alert.severity === "high"
          ? "border-red-200 bg-gradient-to-br from-red-50 to-white"
          : "border-amber-200 bg-gradient-to-br from-amber-50 to-white"
      }`}
    >
      <div className="flex flex-wrap items-start justify-between gap-2">
        <div>
          <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-red-800">
            {alert.emoji} {alert.headline}
          </p>
          <h3 className="mt-1 font-display text-lg font-semibold text-slate-900">
            {alert.competitor} · {alert.theme_label}
          </h3>
        </div>
        <span
          className={`rounded-full px-2.5 py-1 text-[11px] font-semibold ${
            alert.severity === "high" ? "bg-red-100 text-red-900" : "bg-amber-100 text-amber-900"
          }`}
        >
          {alert.acceleration_pct >= 0 ? "+" : ""}
          {Math.round(alert.acceleration_pct)}% accel
        </span>
      </div>

      <p className="mt-3 text-sm leading-relaxed text-slate-800">{alert.summary}</p>
      <p className="mt-2 text-sm font-medium text-slate-800">{alert.acceleration_line}</p>

      <div className="mt-4 rounded-xl border border-radj-navy/15 bg-[#f7ffe8] px-3 py-3">
        <p className="text-[11px] font-semibold uppercase tracking-wide text-radj-navy">
          RadArt recommends
        </p>
        <p className="mt-1 text-sm leading-relaxed text-slate-900">{alert.recommendation}</p>
      </div>

      {alert.sample_titles?.length ? (
        <ul className="mt-3 space-y-1 text-xs text-slate-500">
          {alert.sample_titles.slice(0, 2).map((t) => (
            <li key={t} className="truncate">
              · {t}
            </li>
          ))}
        </ul>
      ) : null}

      <Link
        to={alert.cta_path || "/concurrents"}
        className="mt-3 inline-flex text-xs font-semibold text-radj-navy underline-offset-2 hover:underline"
      >
        {alert.cta || "Open War Room"} →
      </Link>
    </article>
  );
}

export default function CompetitiveAlertsPanel({ report }: Props) {
  if (!report?.alerts?.length) return null;

  return (
    <section className="space-y-3">
      <div className="flex flex-wrap items-end justify-between gap-2">
        <div>
          <h2 className="font-display text-lg font-semibold text-slate-900">Competitive alerts</h2>
          <p className="text-sm text-slate-500">
            {report.dependency_line || "Competitor moves, with a differentiated response — not louder copy."}
          </p>
        </div>
        {report.brand ? (
          <span className="rounded-full border border-slate-200 bg-white px-2.5 py-1 text-[11px] font-semibold text-slate-600">
            Watching for {report.brand}
          </span>
        ) : null}
      </div>
      <div className="space-y-3">
        {report.alerts.map((a) => (
          <AlertCard key={a.id} alert={a} />
        ))}
      </div>
    </section>
  );
}
