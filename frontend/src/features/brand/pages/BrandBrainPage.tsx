import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import {
  extractBrandGuidelines,
  getActiveBrand,
  saveBrandDNA,
  updateBrandDNA,
  type BrandDNA,
  type BrandDNAInput,
} from "@/shared/api";

function splitList(s: string): string[] {
  return s
    .split(/[,;\n]/)
    .map((x) => x.trim())
    .filter(Boolean);
}

const emptyForm = {
  brand_name: "",
  industry: "",
  country: "Tunisia",
  audience: "",
  personality: "",
  languages: "",
  competitors: "",
  channels: "",
  objectives: "",
  forbidden_topics: "",
  tone: "",
  previous_campaigns: "",
  brand_guidelines_text: "",
  products: "",
  budget_level: "€€",
};

function toForm(b: BrandDNA) {
  return {
    brand_name: b.brand_name || "",
    industry: b.industry || "",
    country: b.country || "Tunisia",
    audience: b.audience || "",
    personality: b.personality || "",
    languages: (b.languages || []).join(", "),
    competitors: (b.competitors || []).join(", "),
    channels: (b.channels || []).join(", "),
    objectives: (b.objectives || []).join(", "),
    forbidden_topics: (b.forbidden_topics || []).join(", "),
    tone: b.tone || "",
    previous_campaigns: b.previous_campaigns || "",
    brand_guidelines_text: b.brand_guidelines_text || "",
    products: b.products || "",
    budget_level: b.budget_level || "€€",
  };
}

function toPayload(form: typeof emptyForm): BrandDNAInput {
  return {
    brand_name: form.brand_name.trim(),
    industry: form.industry.trim() || undefined,
    country: form.country.trim() || "Tunisia",
    audience: form.audience.trim() || undefined,
    personality: form.personality.trim() || undefined,
    languages: splitList(form.languages),
    competitors: splitList(form.competitors),
    channels: splitList(form.channels),
    objectives: splitList(form.objectives),
    forbidden_topics: splitList(form.forbidden_topics),
    tone: form.tone.trim() || undefined,
    previous_campaigns: form.previous_campaigns.trim() || undefined,
    brand_guidelines_text: form.brand_guidelines_text.trim() || undefined,
    products: form.products.trim() || undefined,
    budget_level: form.budget_level || undefined,
  };
}

const fieldClass =
  "mt-1 w-full rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm text-slate-900 shadow-sm outline-none focus:border-radj-navy";
const labelClass = "text-[11px] font-semibold uppercase tracking-wide text-slate-500";

export default function BrandBrainPage() {
  const qc = useQueryClient();
  const [form, setForm] = useState(emptyForm);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [msg, setMsg] = useState<string | null>(null);

  const brandQuery = useQuery({
    queryKey: ["brands", "active"],
    queryFn: getActiveBrand,
  });

  useEffect(() => {
    const b = brandQuery.data;
    if (b?.id) {
      setForm(toForm(b));
      setEditingId(b.id);
    }
  }, [brandQuery.data]);

  const saveMutation = useMutation({
    mutationFn: async () => {
      const payload = toPayload(form);
      if (!payload.brand_name) throw new Error("Brand name required");
      if (editingId) return updateBrandDNA(editingId, payload);
      return saveBrandDNA(payload);
    },
    onSuccess: async (b) => {
      setEditingId(b.id);
      setMsg(`Brand Brain actif : ${b.brand_name}`);
      await qc.invalidateQueries({ queryKey: ["brands"] });
      await qc.invalidateQueries({ queryKey: ["radar"] });
      await qc.invalidateQueries({ queryKey: ["opportunities"] });
    },
    onError: (e: Error) => setMsg(e.message),
  });

  const guideMutation = useMutation({
    mutationFn: (file: File) => extractBrandGuidelines(file),
    onSuccess: (r) => {
      setForm((f) => ({
        ...f,
        brand_guidelines_text: [f.brand_guidelines_text, r.text].filter(Boolean).join("\n\n").slice(0, 20000),
      }));
      setMsg(`Guidelines importées : ${r.filename}`);
    },
    onError: (e: Error) => setMsg(e.message),
  });

  function set<K extends keyof typeof emptyForm>(key: K, value: string) {
    setForm((f) => ({ ...f, [key]: value }));
  }

  return (
    <div className="mx-auto max-w-4xl space-y-6">
      <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-card sm:p-6">
        <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-radj-navy">Brand Brain</p>
        <h2 className="mt-1 font-display text-2xl font-semibold text-slate-900">Brand DNA</h2>
        <p className="mt-2 max-w-2xl text-sm text-slate-600">
          Pas juste un nom de marque. RadArt apprend le DNA — puis chaque signal est interprété à travers
          cette lentille. Savoir <strong>quand ne pas chase</strong> une tendance est le produit.
        </p>
        <div className="mt-4 flex flex-wrap gap-2">
          <Link
            to="/dashboard"
            className="rounded-xl border border-radj-navy bg-radj-navy px-4 py-2 text-sm font-semibold text-radj-lime"
          >
            Voir le Morning Radar
          </Link>
        </div>
        {msg ? <p className="mt-3 text-sm text-slate-600">{msg}</p> : null}
      </div>

      <form
        className="space-y-5 rounded-2xl border border-slate-200 bg-white p-5 shadow-card sm:p-6"
        onSubmit={(e) => {
          e.preventDefault();
          setMsg(null);
          saveMutation.mutate();
        }}
      >
        <div className="grid gap-4 sm:grid-cols-2">
          <label className="block">
            <span className={labelClass}>Brand</span>
            <input className={fieldClass} value={form.brand_name} onChange={(e) => set("brand_name", e.target.value)} required />
          </label>
          <label className="block">
            <span className={labelClass}>Industry</span>
            <input className={fieldClass} value={form.industry} onChange={(e) => set("industry", e.target.value)} placeholder="Beverage" />
          </label>
          <label className="block">
            <span className={labelClass}>Country</span>
            <input className={fieldClass} value={form.country} onChange={(e) => set("country", e.target.value)} />
          </label>
          <label className="block">
            <span className={labelClass}>Audience</span>
            <input className={fieldClass} value={form.audience} onChange={(e) => set("audience", e.target.value)} placeholder="16–35" />
          </label>
          <label className="block sm:col-span-2">
            <span className={labelClass}>Personality</span>
            <input className={fieldClass} value={form.personality} onChange={(e) => set("personality", e.target.value)} placeholder="funny / Tunisian / accessible" />
          </label>
          <label className="block">
            <span className={labelClass}>Languages</span>
            <input className={fieldClass} value={form.languages} onChange={(e) => set("languages", e.target.value)} placeholder="derja, French" />
          </label>
          <label className="block">
            <span className={labelClass}>Tone</span>
            <input className={fieldClass} value={form.tone} onChange={(e) => set("tone", e.target.value)} placeholder="playful" />
          </label>
          <label className="block sm:col-span-2">
            <span className={labelClass}>Competitors</span>
            <input className={fieldClass} value={form.competitors} onChange={(e) => set("competitors", e.target.value)} placeholder="Coca-Cola, Fanta, Apla" />
          </label>
          <label className="block">
            <span className={labelClass}>Channels</span>
            <input className={fieldClass} value={form.channels} onChange={(e) => set("channels", e.target.value)} placeholder="TikTok, IG, Facebook" />
          </label>
          <label className="block">
            <span className={labelClass}>Objectives</span>
            <input className={fieldClass} value={form.objectives} onChange={(e) => set("objectives", e.target.value)} placeholder="awareness, engagement" />
          </label>
          <label className="block sm:col-span-2">
            <span className={labelClass}>Forbidden topics</span>
            <input className={fieldClass} value={form.forbidden_topics} onChange={(e) => set("forbidden_topics", e.target.value)} placeholder="politics, religion" />
          </label>
          <label className="block">
            <span className={labelClass}>Budget level</span>
            <select className={fieldClass} value={form.budget_level} onChange={(e) => set("budget_level", e.target.value)}>
              <option value="€">€</option>
              <option value="€€">€€</option>
              <option value="€€€">€€€</option>
            </select>
          </label>
          <label className="block">
            <span className={labelClass}>Products / catalogue</span>
            <input className={fieldClass} value={form.products} onChange={(e) => set("products", e.target.value)} />
          </label>
          <label className="block sm:col-span-2">
            <span className={labelClass}>Previous campaigns</span>
            <textarea className={fieldClass} rows={3} value={form.previous_campaigns} onChange={(e) => set("previous_campaigns", e.target.value)} />
          </label>
          <div className="sm:col-span-2">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <span className={labelClass}>Brand guidelines</span>
              <label className="cursor-pointer text-xs font-semibold text-radj-navy underline-offset-2 hover:underline">
                Upload PDF / DOCX / TXT
                <input
                  type="file"
                  accept=".pdf,.docx,.txt,.pptx"
                  className="hidden"
                  onChange={(e) => {
                    const f = e.target.files?.[0];
                    if (f) guideMutation.mutate(f);
                    e.target.value = "";
                  }}
                />
              </label>
            </div>
            <textarea
              className={fieldClass}
              rows={5}
              value={form.brand_guidelines_text}
              onChange={(e) => set("brand_guidelines_text", e.target.value)}
              placeholder="Collez ou importez les guidelines…"
            />
          </div>
        </div>

        <button
          type="submit"
          disabled={saveMutation.isPending}
          className="rounded-xl bg-radj-navy px-5 py-2.5 text-sm font-semibold text-radj-lime shadow-sm disabled:opacity-50"
        >
          {saveMutation.isPending ? "Enregistrement…" : editingId ? "Mettre à jour le Brand Brain" : "Activer le Brand Brain"}
        </button>
      </form>
    </div>
  );
}
