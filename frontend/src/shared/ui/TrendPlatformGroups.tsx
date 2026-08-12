import { useMemo, useState } from "react";
import type { Trend } from "@/shared/api";
import { platformKey, platformLabel } from "@/shared/lib/platforms";
import TrendCard from "@/shared/ui/TrendCard";

type Group = { key: string; label: string; trends: Trend[] };

function platformsOf(trend: Trend): string[] {
  const keys = new Set<string>();
  for (const it of trend.latest_items || []) {
    keys.add(platformKey(it.platform));
  }
  return keys.size ? [...keys] : ["autre"];
}

function groupTrends(trends: Trend[], onlyPlatform?: string): Group[] {
  const map = new Map<string, Trend[]>();
  for (const trend of trends) {
    let plats = platformsOf(trend);
    if (onlyPlatform) {
      const want = platformKey(onlyPlatform);
      if (!plats.includes(want)) continue;
      plats = [want];
    }
    for (const p of plats) {
      const list = map.get(p) ?? [];
      list.push(trend);
      map.set(p, list);
    }
  }
  return [...map.entries()]
    .map(([key, list]) => ({
      key,
      label: platformLabel(key),
      trends: [...list].sort((a, b) => b.trend_score - a.trend_score),
    }))
    .sort((a, b) => b.trends.length - a.trends.length || a.label.localeCompare(b.label, "fr"));
}

export default function TrendPlatformGroups({
  trends,
  filterPlatform,
}: {
  trends: Trend[];
  filterPlatform?: string;
}) {
  const groups = useMemo(() => groupTrends(trends, filterPlatform), [trends, filterPlatform]);
  const [openKeys, setOpenKeys] = useState<string[]>([]);
  const [touched, setTouched] = useState(false);

  const visibleOpen = useMemo(() => {
    const valid = new Set(groups.map((g) => g.key));
    if (!touched) return groups[0] ? [groups[0].key] : [];
    return openKeys.filter((k) => valid.has(k));
  }, [groups, openKeys, touched]);

  function toggle(key: string) {
    setTouched(true);
    setOpenKeys((prev) => {
      const base = (!touched && groups[0] ? [groups[0].key] : prev).filter((k) =>
        groups.some((g) => g.key === k)
      );
      return base.includes(key) ? base.filter((k) => k !== key) : [...base, key];
    });
  }

  if (!groups.length) {
    return (
      <p className="rounded-xl border border-dashed border-radj-mist bg-white/70 p-8 text-center text-sm text-slate-500">
        Aucune tendance chaude pour ces plateformes.
      </p>
    );
  }

  return (
    <div className="space-y-3">
      {groups.map((group) => {
        const open = visibleOpen.includes(group.key);
        const panelId = `plat-${group.key}`;
        return (
          <section key={group.key} className="overflow-hidden rounded-2xl border border-radj-mist bg-white shadow-card">
            <button
              type="button"
              className="flex w-full items-center gap-3 px-4 py-3 text-left hover:bg-slate-50/80"
              aria-expanded={open}
              aria-controls={panelId}
              onClick={() => toggle(group.key)}
            >
              <span className={`text-slate-400 transition ${open ? "rotate-90" : ""}`} aria-hidden>
                ▸
              </span>
              <span className="min-w-0 flex-1">
                <span className="font-display text-base font-semibold text-[#12142b]">{group.label}</span>
                <span className="mt-0.5 block text-xs text-slate-500">
                  {group.trends.length} tendance{group.trends.length > 1 ? "s" : ""} — cliquer pour{" "}
                  {open ? "masquer" : "voir"} la liste
                </span>
              </span>
              <span className="rounded-full border border-radj-mist bg-[#faf9f6] px-2.5 py-0.5 text-xs font-semibold tabular-nums text-radj-navy">
                {group.trends.length}
              </span>
            </button>
            {open ? (
              <div id={panelId} className="border-t border-radj-mist px-4 py-4">
                <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
                  {group.trends.map((t) => (
                    <TrendCard key={`${group.key}-${t.id}`} trend={t} />
                  ))}
                </div>
              </div>
            ) : null}
          </section>
        );
      })}
    </div>
  );
}
