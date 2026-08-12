export type DashboardFilters = {
  category: string;
  platform: string;
  q: string;
  minTrendScore: string;
  maxRisk: string;
};

type Props = {
  categories: string[];
  platforms: string[];
  value: DashboardFilters;
  onChange: (next: DashboardFilters) => void;
};

const PRESETS = ["viral", "culture", "sport", "economy", "youth", "weather", "retail", "lifestyle", "politics"];

const inputClass =
  "mt-1 w-full rounded-lg border border-slate-300 bg-white px-2 py-1.5 text-sm text-slate-900 shadow-sm outline-none transition placeholder:text-slate-400 focus:border-radj-navy focus:ring-2 focus:ring-radj-navy/20";

export default function FilterBar({ categories, platforms, value, onChange }: Props) {
  function patch(p: Partial<DashboardFilters>) {
    onChange({ ...value, ...p });
  }

  return (
    <section className="rounded-2xl border border-radj-mist bg-white p-4 shadow-card">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <h3 className="font-display text-sm font-semibold text-slate-900">Filtres</h3>
        <button
          type="button"
          onClick={() => onChange({ category: "", platform: "", q: "", minTrendScore: "55", maxRisk: "" })}
          className="text-xs font-medium text-radj-navy hover:underline"
        >
          Reset
        </button>
      </div>

      <div className="mt-3 flex flex-wrap gap-1.5">
        <span className="text-[10px] uppercase tracking-wide text-slate-500">Raccourcis</span>
        {PRESETS.map((p) => (
          <button
            key={p}
            type="button"
            onClick={() => patch({ category: p })}
            className={`rounded-full border px-2.5 py-0.5 text-xs capitalize transition ${
              value.category.toLowerCase() === p
                ? "border-radj-navy bg-radj-navy text-radj-lime shadow-sm"
                : "border-slate-300 bg-white text-slate-700 hover:border-radj-navy/40 hover:bg-slate-50"
            }`}
          >
            {p}
          </button>
        ))}
      </div>

      <div className="mt-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6">
        <label className="block text-[11px] font-medium text-slate-700">
          Catégorie
          <select className={inputClass} value={value.category} onChange={(e) => patch({ category: e.target.value })}>
            <option value="">Toutes</option>
            {categories.map((c) => (
              <option key={c} value={c}>
                {c}
              </option>
            ))}
          </select>
        </label>
        <label className="block text-[11px] font-medium text-slate-700">
          Plateforme (signaux)
          <select className={inputClass} value={value.platform} onChange={(e) => patch({ platform: e.target.value })}>
            <option value="">Toutes</option>
            {platforms.map((p) => (
              <option key={p} value={p}>
                {p}
              </option>
            ))}
          </select>
        </label>
        <label className="block text-[11px] font-medium text-slate-700 sm:col-span-2">
          Recherche (titres &amp; mots-clés)
          <input
            type="search"
            placeholder="ex. étudiants, Ramadan, derby…"
            className={inputClass}
            value={value.q}
            onChange={(e) => patch({ q: e.target.value })}
          />
        </label>
        <label className="block text-[11px] font-medium text-slate-700">
          Score min (tendance chaude)
          <input
            type="number"
            min={0}
            max={100}
            placeholder="0–100"
            className={inputClass}
            value={value.minTrendScore}
            onChange={(e) => patch({ minTrendScore: e.target.value })}
          />
        </label>
        <label className="block text-[11px] font-medium text-slate-700">
          Risque max
          <input
            type="number"
            min={0}
            max={100}
            placeholder="0–100"
            className={inputClass}
            value={value.maxRisk}
            onChange={(e) => patch({ maxRisk: e.target.value })}
          />
        </label>
      </div>
    </section>
  );
}
