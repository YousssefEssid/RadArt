/**
 * Base URL du backend. Priorité : `VITE_API_BASE`, puis même hôte que la page (127.0.0.1 ≠ localhost),
 * pour éviter les appels vers le mauvais port/hôte en dev.
 */
export function getApiBase(): string {
  const fromEnv = import.meta.env.VITE_API_BASE;
  if (typeof fromEnv === "string" && fromEnv.trim() !== "") {
    return fromEnv.replace(/\/$/, "");
  }
  if (typeof window !== "undefined") {
    const h = window.location.hostname;
    if (h === "127.0.0.1" || h === "localhost") {
      return `${window.location.protocol}//${h}:8000`;
    }
  }
  return "http://localhost:8000";
}

async function j<T>(res: Response | Promise<Response>): Promise<T> {
  const r = await res;
  if (!r.ok) {
    const t = await r.text();
    if (t.trim().startsWith("{")) {
      try {
        const o = JSON.parse(t) as { detail?: string };
        if (typeof o.detail === "string") {
          throw new Error(o.detail);
        }
      } catch (e) {
        if (e instanceof SyntaxError) {
          /* ignore parse failure */
        } else if (e instanceof Error && e.message !== t) {
          throw e;
        }
      }
    }
    throw new Error(t || r.statusText);
  }
  return r.json() as Promise<T>;
}

export function getHealth() {
  return j<{ status: string; db: string; scheduler: string }>(fetch(`${getApiBase()}/health`));
}

export type Trend = {
  id: number;
  label: string;
  summary: string;
  keywords: string[];
  category: string;
  trend_score: number;
  risk_score: number;
  source_count: number;
  item_count: number;
  latest_items: { id: number; title: string; url: string | null; source: string; platform: string }[];
};

export type TrendFilters = {
  category?: string;
  q?: string;
  min_trend_score?: number;
  max_risk?: number;
};

function qsTrend(f?: TrendFilters): string {
  if (!f) return "";
  const p = new URLSearchParams();
  if (f.category) p.set("category", f.category);
  if (f.q) p.set("q", f.q);
  if (f.min_trend_score != null) p.set("min_trend_score", String(f.min_trend_score));
  if (f.max_risk != null) p.set("max_risk", String(f.max_risk));
  const s = p.toString();
  return s ? `?${s}` : "";
}

export function getTrends(filters?: TrendFilters) {
  return j<Trend[]>(fetch(`${getApiBase()}/api/trends${qsTrend(filters)}`));
}

export type MediaItem = {
  id: number;
  source: string;
  platform: string;
  title: string;
  text?: string | null;
  url?: string | null;
  category?: string | null;
  engagement?: number;
  cluster_id?: number | null;
};

export type MediaFilters = {
  limit?: number;
  category?: string;
  platform?: string;
  q?: string;
};

function qsMedia(f?: MediaFilters): string {
  const p = new URLSearchParams();
  if (f?.limit != null) p.set("limit", String(f.limit));
  if (f?.category) p.set("category", f.category);
  if (f?.platform) p.set("platform", f.platform);
  if (f?.q) p.set("q", f.q);
  const s = p.toString();
  return s ? `?${s}` : "";
}

export function getMediaItems(filters?: MediaFilters) {
  const merged: MediaFilters = { limit: 50, ...filters };
  return j<MediaItem[]>(fetch(`${getApiBase()}/api/media-items${qsMedia(merged)}`));
}

export function getMetaFilters() {
  return j<{ categories: string[]; platforms: string[] }>(fetch(`${getApiBase()}/api/meta/filters`));
}

export function getCollectionStatus() {
  return j<{
    last_runs: Record<string, unknown>[];
    media_items_count: number;
    trend_clusters_count: number;
    source_status: { source: string; status: string; detail: string }[];
    last_summary: Record<string, unknown>;
  }>(fetch(`${getApiBase()}/api/collect/status`));
}

export function runCollection() {
  return j<{ message: string }>(
    fetch(`${getApiBase()}/api/collect/run`, { method: "POST" })
  );
}

export type BriefAnalyzePayload = { client_name?: string; raw_brief: string };

export type ParsedBrief = {
  sector?: string | null;
  target?: string | null;
  objective?: string | null;
  tone?: string | null;
  constraints?: string | null;
  competitors?: string[];
};

export type Recommendation = {
  id: number;
  cluster_id: number;
  trend_label: string;
  brand_fit_score: number;
  risk_score: number;
  recommendation_text: string;
  campaign_angle_safe: string;
  campaign_angle_bold: string;
  campaign_angle_local: string;
  suggested_formats: string;
  influencer_type: string;
  urgency: string;
};

export function analyzeBrief(payload: BriefAnalyzePayload) {
  return j<{
    brief_id: number;
    parsed_brief: ParsedBrief;
    recommendations: Recommendation[];
  }>(fetch(`${getApiBase()}/api/briefs/analyze`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  }));
}

export type ExtractBriefFileResult = { text: string; filename: string };

/** Extrait le texte côté API (.pptx, .docx, .pdf, .txt). Le .ppt seul nécessite une conversion en .pptx. */
export async function extractBriefFile(file: File): Promise<ExtractBriefFileResult> {
  const fd = new FormData();
  fd.append("file", file);
  const r = await fetch(`${getApiBase()}/api/briefs/extract-text`, { method: "POST", body: fd });
  if (!r.ok) {
    let msg = await r.text();
    try {
      const err = JSON.parse(msg) as { detail?: string | string[] };
      if (err.detail) {
        msg = Array.isArray(err.detail) ? err.detail.map((d) => (typeof d === "string" ? d : d)).join(" ") : err.detail;
      }
    } catch {
      /* message brut */
    }
    throw new Error(msg || r.statusText);
  }
  return r.json() as Promise<ExtractBriefFileResult>;
}

export function getRecommendations(briefId: number) {
  return j<Recommendation[]>(fetch(`${getApiBase()}/api/briefs/${briefId}/recommendations`));
}

export type LatestBrief = {
  id: number;
  client_name: string | null;
  sector: string | null;
  target: string | null;
  competitors: string[];
  created_at: string | null;
};

export type CompetitorSignal = {
  id: number;
  title: string | null;
  source: string | null;
  platform: string | null;
  category: string | null;
  url: string | null;
  published_at: string | null;
  engagement: number | null;
};

export type CompetitorCluster = {
  id: number;
  label: string | null;
  summary: string | null;
  category: string | null;
  trend_score: number | null;
  risk_score: number | null;
};

export type CompetitorCard = {
  name: string;
  source_tag: string;
  signal_count: number;
  recent_signals: CompetitorSignal[];
  related_clusters: CompetitorCluster[];
  notes: string;
};

export type CompetitorsReport = {
  brief_id: number;
  client_name: string | null;
  sector: string | null;
  target: string | null;
  competitor_source: string;
  competitors: string[];
  cards: CompetitorCard[];
};

export function getLatestBrief() {
  return j<LatestBrief | Record<string, never>>(fetch(`${getApiBase()}/api/briefs/latest`));
}

export function getCompetitorsReport(briefId?: number) {
  const q = briefId != null && briefId > 0 ? `?brief_id=${briefId}` : "";
  return j<CompetitorsReport>(fetch(`${getApiBase()}/api/competitors/report${q}`));
}

/** Étude concurrentielle télécom (Tunisie) — API puis repli fichier local. */
export async function getTelecomCompetitiveStudy(): Promise<CompetitorsReport> {
  try {
    return await j<CompetitorsReport>(fetch(`${getApiBase()}/api/competitors/telecom-study`));
  } catch (firstError) {
    const origin = typeof window !== "undefined" ? window.location.origin : "";
    const r = await fetch(`${origin}/studies/telecom-tn.json`);
    if (!r.ok) {
      const msg = firstError instanceof Error ? firstError.message : "Chargement impossible";
      throw new Error(`${msg} Vérifiez la connexion au serveur ou rechargez la page.`);
    }
    return r.json() as Promise<CompetitorsReport>;
  }
}
