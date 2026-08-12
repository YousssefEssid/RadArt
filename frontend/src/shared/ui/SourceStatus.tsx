type Run = Record<string, unknown>;

type Props = {
  mediaCount: number;
  trendCount: number;
  lastRuns: Run[];
  sourceStatus: { source: string; status: string; detail: string }[];
};

export default function SourceStatus({ mediaCount, trendCount, lastRuns, sourceStatus }: Props) {
  const last = lastRuns[0] as { ended_at?: string; status?: string; items_collected?: number } | undefined;

  return (
    <section className="rounded-2xl border border-radj-mist bg-white p-5 shadow-card">
      <h3 className="font-display text-sm font-semibold text-slate-900">Signal status</h3>
      <dl className="mt-4 grid grid-cols-2 gap-3 text-sm">
        <div>
          <dt className="text-slate-500">Media items</dt>
          <dd className="font-semibold text-radj-navy">{mediaCount}</dd>
        </div>
        <div>
          <dt className="text-slate-500">Trend clusters</dt>
          <dd className="font-semibold text-radj-navy">{trendCount}</dd>
        </div>
        <div className="col-span-2">
          <dt className="text-slate-500">Last collection</dt>
          <dd className="text-slate-700">{last?.ended_at || "—"} · {last?.status || "idle"} · +{last?.items_collected ?? 0} inserted</dd>
        </div>
      </dl>
      <div className="mt-4 max-h-40 overflow-y-auto rounded-lg border border-slate-200 bg-slate-50/50">
        <table className="w-full text-left text-[11px] text-slate-700">
          <thead className="sticky top-0 border-b border-slate-200 bg-slate-100 text-slate-600">
            <tr>
              <th className="px-2 py-1.5 font-semibold">Source</th>
              <th className="px-2 py-1.5 font-semibold">Status</th>
            </tr>
          </thead>
          <tbody>
            {sourceStatus.map((s) => (
              <tr key={s.source + s.detail} className="border-t border-slate-100 bg-white first:border-0">
                <td className="px-2 py-1.5 text-slate-800">{s.source}</td>
                <td className="px-2 py-1.5">
                  <span
                    className={
                      s.status === "ok"
                        ? "font-medium text-emerald-700"
                        : s.status === "skipped"
                          ? "text-slate-400"
                          : "font-semibold text-amber-700"
                    }
                  >
                    {s.status}
                  </span>
                  <span className="ml-1 text-slate-500">{s.detail}</span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}
