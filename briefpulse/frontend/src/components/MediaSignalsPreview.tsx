import type { MediaItem } from "../api";

export default function MediaSignalsPreview({ items }: { items: MediaItem[] }) {
  if (!items.length) {
    return (
      <p className="rounded-xl border border-dashed border-slate-300 bg-slate-50 px-4 py-6 text-center text-xs text-slate-500">
        —
      </p>
    );
  }

  return (
    <div className="overflow-x-auto rounded-xl border border-slate-200 bg-white shadow-sm ring-1 ring-slate-900/5">
      <table className="w-full text-left text-xs text-slate-700">
        <thead className="border-b border-slate-200 bg-slate-100 text-[10px] uppercase tracking-wide text-slate-600">
          <tr>
            <th className="px-3 py-2.5 font-semibold">Plateforme</th>
            <th className="px-3 py-2.5 font-semibold">Catégorie</th>
            <th className="px-3 py-2.5 font-semibold">Titre</th>
            <th className="px-3 py-2.5 text-right font-semibold">Eng.</th>
          </tr>
        </thead>
        <tbody>
          {items.map((m) => (
            <tr key={m.id} className="border-b border-slate-100 last:border-0 hover:bg-slate-50/80">
              <td className="whitespace-nowrap px-3 py-2 font-medium text-radj-navy">{m.platform}</td>
              <td className="whitespace-nowrap px-3 py-2 text-slate-600">{m.category}</td>
              <td className="max-w-md truncate px-3 py-2 text-slate-800">
                {m.url ? (
                  <a href={m.url} target="_blank" rel="noreferrer" className="text-radj-navy hover:text-radj-lime hover:underline">
                    {m.title}
                  </a>
                ) : (
                  m.title
                )}
              </td>
              <td className="px-3 py-2 text-right tabular-nums text-slate-500">{m.engagement}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
