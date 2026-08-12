import { useMemo, useState } from "react";
import type { MediaItem } from "@/shared/api";
import { platformKey, platformLabel } from "@/shared/lib/platforms";
import { formatRelativeFr, freshnessFor, parseIsoDate } from "@/shared/lib/timeAgo";

function formatPopularity(n: number | undefined): string {
  const v = Math.max(0, Number(n) || 0);
  if (v >= 1_000_000) return `${(v / 1_000_000).toFixed(1).replace(/\.0$/, "")} M`;
  if (v >= 1_000) return `${(v / 1_000).toFixed(1).replace(/\.0$/, "")} k`;
  return String(Math.round(v));
}

function groupByPlatform(items: MediaItem[]): { key: string; label: string; items: MediaItem[] }[] {
  const map = new Map<string, MediaItem[]>();
  for (const item of items) {
    const key = platformKey(item.platform);
    const list = map.get(key) ?? [];
    list.push(item);
    map.set(key, list);
  }
  return [...map.entries()]
    .map(([key, list]) => ({
      key,
      label: platformLabel(key),
      items: [...list].sort((a, b) => (b.engagement || 0) - (a.engagement || 0)),
    }))
    .sort((a, b) => (b.items[0]?.engagement || 0) - (a.items[0]?.engagement || 0));
}

export default function MediaSignalsPreview({ items }: { items: MediaItem[] }) {
  const groups = useMemo(() => groupByPlatform(items), [items]);
  const [openKeys, setOpenKeys] = useState<string[]>([]);
  const [touched, setTouched] = useState(false);
  const openSet = useMemo(() => {
    if (!touched) return new Set(groups[0] ? [groups[0].key] : []);
    return new Set(openKeys);
  }, [groups, openKeys, touched]);

  if (!items.length) {
    return (
      <p className="rounded-xl border border-dashed border-slate-300 bg-slate-50 px-4 py-6 text-center text-xs text-slate-500">
        Aucun signal fort pour le moment.
      </p>
    );
  }

  function toggle(key: string) {
    setTouched(true);
    setOpenKeys((prev) => {
      const base = !touched && groups[0] ? [groups[0].key] : prev;
      return base.includes(key) ? base.filter((k) => k !== key) : [...base, key];
    });
  }

  return (
    <div className="space-y-3">
      <p className="text-xs leading-relaxed text-slate-500">
        <span className="font-semibold text-slate-700">Popularité</span> = force du signal (likes Reddit, rang Apple
        Music, vues / partages estimés). Plus c’est haut, plus les gens en parlent — ce n’est pas un prix.
      </p>
      {groups.map((group) => {
        const open = openSet.has(group.key);
        const panelId = `signals-${group.key}`;
        return (
          <section key={group.key} className="overflow-hidden rounded-xl border border-radj-mist bg-white shadow-card">
            <button
              type="button"
              className="flex w-full items-center gap-3 px-3 py-2.5 text-left hover:bg-slate-50/80"
              aria-expanded={open}
              aria-controls={panelId}
              onClick={() => toggle(group.key)}
            >
              <span className={`text-slate-400 transition ${open ? "rotate-90" : ""}`} aria-hidden>
                ▸
              </span>
              <h4 className="min-w-0 flex-1 font-display text-sm font-semibold text-[#12142b]">{group.label}</h4>
              <span className="text-[11px] font-medium text-slate-500">
                {group.items.length} signal{group.items.length > 1 ? "s" : ""}
              </span>
            </button>
            {open ? (
              <table id={panelId} className="w-full border-t border-radj-mist text-left text-xs text-slate-700">
                <thead className="sr-only">
                  <tr>
                    <th>Titre</th>
                    <th>Popularité</th>
                  </tr>
                </thead>
                <tbody>
                  {group.items.map((m) => (
                    <tr key={m.id} className="border-b border-slate-100 last:border-0 hover:bg-slate-50/80">
                      <td className="px-3 py-2">
                        <p className="font-medium text-slate-800">
                          {m.url ? (
                            <a href={m.url} target="_blank" rel="noreferrer" className="text-radj-navy hover:underline">
                              {m.title}
                            </a>
                          ) : (
                            m.title
                          )}
                        </p>
                        <p className="mt-0.5 text-[11px] text-slate-500">
                          {m.source}
                          {m.category ? ` · ${m.category}` : ""}
                          {(() => {
                            const d = parseIsoDate(m.published_at) || parseIsoDate(m.collected_at);
                            if (!d) return null;
                            const fresh = freshnessFor(d);
                            return (
                              <>
                                {" · "}
                                <span title={fresh.hint}>
                                  {formatRelativeFr(d)} · {fresh.label}
                                </span>
                              </>
                            );
                          })()}
                        </p>
                      </td>
                      <td className="whitespace-nowrap px-3 py-2 text-right align-top">
                        <span
                          title="Popularité du signal (engagement)"
                          className="inline-flex min-w-[3rem] justify-end font-semibold tabular-nums text-radj-navy"
                        >
                          {formatPopularity(m.engagement)}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            ) : null}
          </section>
        );
      })}
    </div>
  );
}
