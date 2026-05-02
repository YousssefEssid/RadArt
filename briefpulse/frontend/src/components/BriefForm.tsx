import { useRef, useState, type ChangeEvent } from "react";
import type { ParsedBrief, Recommendation } from "../api";
import { analyzeBrief, extractBriefFile } from "../api";
import ScoreBadge from "./ScoreBadge";

const BRIEF_TEMPLATE_PPTX = "/templates/brief-modele-a-remplir.pptx";
const BRIEF_TEMPLATE_HTML = "/templates/brief-modele.html";

const DEFAULT_SAMPLE_BRIEF = `Client: Freshy Drink.
We are a beverage brand targeting Tunisian students and young adults.
We want a humorous summer campaign to increase engagement on TikTok and Instagram.
Avoid politics and avoid direct health claims.`;

const fieldClass =
  "mt-1 w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 shadow-sm outline-none placeholder:text-slate-400 focus:border-radj-navy focus:ring-2 focus:ring-radj-navy/20";

type Props = {
  onAnalyzed?: (briefId: number) => void;
};

export default function BriefForm({ onAnalyzed }: Props) {
  const [clientName, setClientName] = useState("Freshy Drink");
  const [rawBrief, setRawBrief] = useState(DEFAULT_SAMPLE_BRIEF);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [parsed, setParsed] = useState<ParsedBrief | null>(null);
  const [recs, setRecs] = useState<Recommendation[]>([]);
  const [importing, setImporting] = useState(false);
  const [importedName, setImportedName] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  async function onFileSelected(e: ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    e.target.value = "";
    if (!file) return;
    setError(null);
    setImporting(true);
    setImportedName(null);
    const ext = file.name.toLowerCase();
    try {
      if (ext.endsWith(".txt") || ext.endsWith(".md")) {
        const text = await file.text();
        setRawBrief(text);
        setImportedName(file.name);
        return;
      }
      const { text, filename } = await extractBriefFile(file);
      setRawBrief(text);
      setImportedName(filename);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Import impossible");
    } finally {
      setImporting(false);
    }
  }

  async function submit() {
    setLoading(true);
    setError(null);
    try {
      const res = await analyzeBrief({ client_name: clientName || undefined, raw_brief: rawBrief });
      setParsed(res.parsed_brief);
      setRecs(res.recommendations);
      onAnalyzed?.(res.brief_id);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Request failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm ring-1 ring-slate-900/5">
      <h3 className="font-display text-lg font-semibold text-slate-900">Brief analyzer</h3>

      <div className="mt-4 flex flex-col gap-3 rounded-xl border border-slate-100 bg-slate-50/60 p-4 sm:flex-row sm:flex-wrap sm:items-center sm:justify-between">
        <div className="flex flex-wrap gap-2">
          <a
            href={BRIEF_TEMPLATE_PPTX}
            download
            className="inline-flex items-center justify-center rounded-lg bg-radj-navy px-4 py-2 text-sm font-semibold text-radj-lime shadow-sm transition hover:bg-radj-navy/90"
          >
            Télécharger le modèle (.pptx)
          </a>
          <a
            href={BRIEF_TEMPLATE_HTML}
            target="_blank"
            rel="noreferrer"
            className="inline-flex items-center justify-center rounded-lg border border-slate-300 bg-white px-4 py-2 text-sm font-semibold text-slate-700 shadow-sm transition hover:border-radj-navy/40 hover:bg-white"
          >
            Modèle web (remplir ici)
          </a>
          <input
            ref={fileInputRef}
            type="file"
            className="hidden"
            accept=".ppt,.pptx,.docx,.pdf,.txt,.md"
            onChange={onFileSelected}
          />
          <button
            type="button"
            disabled={importing}
            onClick={() => fileInputRef.current?.click()}
            className="inline-flex items-center justify-center rounded-lg border border-radj-navy bg-white px-4 py-2 text-sm font-semibold text-radj-navy shadow-sm transition hover:bg-radj-navy hover:text-radj-lime disabled:opacity-50"
          >
            {importing ? "Import…" : "Importer le brief rempli"}
          </button>
        </div>
        {importedName ? (
          <p className="text-xs text-slate-600">
            <span className="font-medium text-radj-navy">{importedName}</span>
          </p>
        ) : null}
      </div>

      <div className="mt-4 space-y-3">
        <label className="block text-xs font-medium text-slate-700">
          Nom du client
          <input className={fieldClass} value={clientName} onChange={(e) => setClientName(e.target.value)} />
        </label>
        <label className="block text-xs font-medium text-slate-700">
          Texte du brief
          <textarea
            className={`${fieldClass} min-h-[160px] resize-y`}
            value={rawBrief}
            onChange={(e) => setRawBrief(e.target.value)}
          />
        </label>
        <button
          type="button"
          onClick={submit}
          disabled={loading}
          className="w-full rounded-xl bg-radj-navy px-4 py-3 text-sm font-semibold text-radj-lime shadow-sm transition hover:bg-radj-navy/90 disabled:opacity-50"
        >
          {loading ? "Generating…" : "Generate recommendations"}
        </button>
        {error ? (
          <p className="rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-800">{error}</p>
        ) : null}
      </div>

      {parsed ? (
        <div className="mt-6 border-t border-slate-100 pt-6">
          <div className="flex flex-wrap gap-2">
            {(["sector", "target", "objective", "tone", "constraints"] as const).map((k) => {
              const v = parsed[k];
              if (!v || typeof v !== "string") return null;
              return (
                <span
                  key={k}
                  className="rounded-full border border-slate-200 bg-slate-50 px-3 py-1 text-xs text-slate-800"
                >
                  <span className="text-slate-500">{k}:</span> {v}
                </span>
              );
            })}
          </div>
          {parsed.competitors && parsed.competitors.length > 0 ? (
            <p className="mt-3 text-xs text-slate-700">
              <span className="font-semibold text-radj-navy">Concurrents (pour la veille) :</span>{" "}
              {parsed.competitors.join(" · ")}
            </p>
          ) : null}
        </div>
      ) : null}

      {recs.length ? (
        <div className="mt-6 space-y-4 border-t border-slate-100 pt-6">
          {recs.map((r) => (
            <article
              key={r.id}
              className="rounded-xl border border-slate-200 bg-slate-50/40 p-4 text-sm text-slate-700 shadow-sm"
            >
              <div className="flex flex-wrap items-center justify-between gap-2">
                <h4 className="font-display font-semibold text-slate-900">{r.trend_label}</h4>
                <div className="flex gap-2">
                  <ScoreBadge label="Fit" value={r.brand_fit_score} variant="fit" />
                  <ScoreBadge label="Risk" value={r.risk_score} variant="risk" />
                </div>
              </div>
              <p className="mt-2 text-slate-600">{r.recommendation_text}</p>
              <div className="mt-3 grid gap-2 md:grid-cols-3">
                <div className="rounded-lg border border-white bg-white p-2 shadow-sm">
                  <p className="text-[10px] font-semibold uppercase text-slate-500">Safe</p>
                  <p className="text-xs text-slate-800">{r.campaign_angle_safe}</p>
                </div>
                <div className="rounded-lg border border-white bg-white p-2 shadow-sm">
                  <p className="text-[10px] font-semibold uppercase text-slate-500">Bold</p>
                  <p className="text-xs text-slate-800">{r.campaign_angle_bold}</p>
                </div>
                <div className="rounded-lg border border-white bg-white p-2 shadow-sm">
                  <p className="text-[10px] font-semibold uppercase text-slate-500">Local</p>
                  <p className="text-xs text-slate-800">{r.campaign_angle_local}</p>
                </div>
              </div>
              <p className="mt-2 text-xs text-slate-600">
                <span className="font-medium text-radj-navy">Formats:</span> {r.suggested_formats}
              </p>
              <p className="text-xs text-slate-600">
                <span className="font-medium text-radj-navy">Influencers:</span> {r.influencer_type}
              </p>
              <p className="mt-2 text-xs font-semibold text-radj-navy">{r.urgency}</p>
            </article>
          ))}
        </div>
      ) : null}
    </section>
  );
}
