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
  first_seen_at?: string | null;
  last_seen_at?: string | null;
  updated_at?: string | null;
  latest_items: {
    id: number;
    title: string;
    url: string | null;
    source: string;
    platform: string;
    published_at?: string | null;
    collected_at?: string | null;
  }[];
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

export type MorningSignalKind =
  | "emerging"
  | "growing"
  | "competitor_move"
  | "conversation_shift"
  | "reputation"
  | "brand_opportunity"
  | "fading";

export type OpportunityCard = {
  cluster_id: number;
  title: string;
  status: string;
  status_dot: string;
  rad_score?: RadScore;
  momentum: {
    score: number;
    direction: string;
    arrow: string;
    growth_score: number;
  };
  tunisia_relevance: number;
  audience: { ages: string; profile: string; label: string };
  lifecycle: { key: string; label: string; badge: string };
  sources: string[];
  why_growing: string;
  brand_fit: {
    brand: string;
    fit_percent: number;
    fit_label: string;
    reasons: string[];
    verdict?: "chase" | "caution" | "skip" | string;
    verdict_label?: string;
    action?: string;
    from_brand_brain?: boolean;
  } | null;
  recommended_move: {
    campaign: string;
    concept: string;
    channels: string;
    timing: string;
    risk: string;
    risk_score: number;
    trend_saturation: number;
    trend_saturation_label: string;
  };
  value_prop?: string;
};

export type RadScore = {
  score: number;
  score_int: number;
  formula: string;
  formula_note?: string;
  pillars: {
    relevance: number;
    acceleration: number;
    differentiation: number;
  };
  components: {
    momentum: number;
    freshness: number;
    tunisia_relevance: number;
    audience_overlap: number;
    brand_fit: number;
    source_diversity: number;
    competitive_saturation: number;
    brand_safety_risk: number;
  };
  tier: { key: string; label: string; label_fr?: string };
  why: string;
  label: string;
};

export type MorningRadarItem = Trend & {
  growth_score?: number;
  volume_score?: number;
  diversity_score?: number;
  recency_score?: number;
  signal_kind: MorningSignalKind;
  priority: number;
  why_it_matters: string;
  what_to_do: string;
  brand_fit_hint?: number | null;
  competitor_matched?: string | null;
  meta: { emoji: string; label_fr: string; question: string };
  opportunity?: OpportunityCard;
};

export type OpportunitiesReport = {
  brief_context: {
    brief_id?: number;
    client_name?: string | null;
    sector?: string | null;
    has_brief: boolean;
  };
  count: number;
  cards: OpportunityCard[];
};

export function getOpportunities(limit = 12, enrich = false) {
  const q = new URLSearchParams({ limit: String(limit), enrich: enrich ? "true" : "false" });
  return j<OpportunitiesReport>(fetch(`${getApiBase()}/api/opportunities?${q}`));
}

export function getOpportunity(clusterId: number, enrich = true) {
  const q = enrich ? "?enrich=true" : "?enrich=false";
  return j<OpportunityCard>(fetch(`${getApiBase()}/api/opportunities/${clusterId}${q}`));
}

export type BrandDNA = {
  id: number;
  brand_name: string;
  industry?: string;
  country?: string;
  audience?: string;
  personality?: string;
  languages: string[];
  competitors: string[];
  channels: string[];
  objectives: string[];
  forbidden_topics: string[];
  tone?: string;
  previous_campaigns?: string;
  brand_guidelines_text?: string;
  products?: string;
  budget_level?: string;
  is_active?: boolean;
};

export type BrandDNAInput = {
  brand_name: string;
  industry?: string;
  country?: string;
  audience?: string;
  personality?: string;
  languages?: string[];
  competitors?: string[];
  channels?: string[];
  objectives?: string[];
  forbidden_topics?: string[];
  tone?: string;
  previous_campaigns?: string;
  brand_guidelines_text?: string;
  products?: string;
  budget_level?: string;
};

export async function getActiveBrand(): Promise<BrandDNA | null> {
  const data = await j<BrandDNA | Record<string, never>>(fetch(`${getApiBase()}/api/brands/active`));
  if (!data || !(data as BrandDNA).id) return null;
  return data as BrandDNA;
}

export function saveBrandDNA(payload: BrandDNAInput) {
  return j<BrandDNA>(
    fetch(`${getApiBase()}/api/brands/`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    })
  );
}

export function updateBrandDNA(brandId: number, payload: BrandDNAInput) {
  return j<BrandDNA>(
    fetch(`${getApiBase()}/api/brands/${brandId}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    })
  );
}

export async function extractBrandGuidelines(file: File): Promise<{ text: string; filename: string }> {
  const fd = new FormData();
  fd.append("file", file);
  const r = await fetch(`${getApiBase()}/api/brands/guidelines/extract-text`, { method: "POST", body: fd });
  if (!r.ok) throw new Error((await r.text()) || r.statusText);
  return r.json();
}

export type JumpAnalysis = {
  cluster_id: number;
  trend_label: string;
  brand?: string | null;
  has_brand_brain: boolean;
  recommendation: "YES" | "CAUTION" | "NO";
  recommendation_label: string;
  recommendation_why: string;
  scores: {
    brand_fit: number;
    audience_fit: number;
    trend_maturity: string;
    trend_maturity_badge?: string;
    competitor_saturation: string;
    competitor_saturation_score: number;
    reputational_risk: string;
    reputational_risk_score: number;
    rad_score: number;
  };
  rad_why?: string;
  can_generate_campaign: boolean;
  cta: string;
};

export type CampaignBrief = {
  big_idea: string;
  consumer_insight: string;
  campaign_concept: string;
  key_message: string;
  tiktok_reel_concepts: string[];
  caption_ideas: string[];
  visual_direction: string;
  influencer_profile: string;
  hashtags: string[];
  timing: string;
  kpis: string[];
  channels: string;
  campaign_name: string;
};

export type CampaignPack = {
  cluster_id: number;
  recommendation: string;
  recommendation_label: string;
  scores: JumpAnalysis["scores"];
  brand?: string | null;
  trend_label?: string;
  campaign: CampaignBrief | null;
  blocked?: boolean;
  blocked_reason?: string;
  pipeline?: string;
};

export function analyzeJump(clusterId: number) {
  return j<JumpAnalysis>(
    fetch(`${getApiBase()}/api/opportunities/${clusterId}/jump`, { method: "POST" })
  );
}

export function generateCampaign(clusterId: number) {
  return j<CampaignPack>(
    fetch(`${getApiBase()}/api/opportunities/${clusterId}/campaign`, { method: "POST" })
  );
}

export type MorningRadarSection = {
  kind: MorningSignalKind;
  emoji: string;
  label_fr: string;
  question: string;
  count: number;
  items: MorningRadarItem[];
};

export type MorningRadarReport = {
  generated_at: string;
  headline: string;
  question: string;
  brief_context: {
    brief_id?: number;
    client_name?: string | null;
    sector?: string | null;
    competitors: string[];
    has_brief: boolean;
    has_brand_brain?: boolean;
    brand_name?: string | null;
  };
  summary: {
    trends_scanned: number;
    actionable_buckets: number;
    total_signals: number;
  };
  competitive_alerts?: CompetitiveAlertsReport;
  sections: MorningRadarSection[];
};

export type CompetitiveAlert = {
  id: string;
  type: string;
  severity: string;
  emoji: string;
  headline: string;
  competitor: string;
  theme: string;
  theme_label: string;
  content_count: number;
  window_hours: number;
  acceleration_pct: number;
  summary: string;
  acceleration_line: string;
  recommendation: string;
  sample_titles: string[];
  cta: string;
  cta_path: string;
};

export type CompetitiveAlertsReport = {
  generated_at: string;
  brand?: string | null;
  competitors_watched: string[];
  window_hours: number;
  count: number;
  source: string;
  alerts: CompetitiveAlert[];
  dependency_line?: string;
};

export function getMorningRadar() {
  return j<MorningRadarReport>(fetch(`${getApiBase()}/api/radar/morning`));
}

export function getCompetitiveAlerts() {
  return j<CompetitiveAlertsReport>(fetch(`${getApiBase()}/api/competitors/alerts`));
}

export type SignalCoverageSource = {
  name: string;
  status: string;
  needs_key?: boolean;
  env?: string;
  path?: string;
  detail?: string;
};

export type SignalCoverageLayer = {
  id: string;
  title: string;
  tier: string;
  compliance: string;
  sources: SignalCoverageSource[];
};

export type SignalCoverageReport = {
  principle: string;
  tunisia_market: {
    as_of: string;
    facebook_users_m: number;
    instagram_users_m: number;
    tiktok_adults_reachable_m: number;
    note: string;
  };
  mvp_strength: string;
  next_priority: string[];
  summary: { live: number; needs_key: number; planned: number };
  layers: SignalCoverageLayer[];
};

export function getSignalCoverage() {
  return j<SignalCoverageReport>(fetch(`${getApiBase()}/api/sources/coverage`));
}

export async function uploadCustomerOwnedFile(file: File): Promise<{ saved: number; filename?: string; message: string }> {
  const fd = new FormData();
  fd.append("file", file);
  const r = await fetch(`${getApiBase()}/api/sources/customer-owned/upload`, { method: "POST", body: fd });
  if (!r.ok) throw new Error((await r.text()) || r.statusText);
  return r.json();
}

export type SourceHealthMatrixRow = {
  source: string;
  status: string;
  light: string;
  collection: string;
  detail?: string | null;
};

export type SourceHealthReport = {
  generated_at: string;
  principle: string;
  matrix: SourceHealthMatrixRow[];
  collectors: {
    source: string;
    enabled: boolean;
    credential_status: string;
    source_method: string;
    provider: string;
    light?: string;
    collection_label?: string;
    items_collected_24h?: number;
    detail?: string | null;
    last_error?: string | null;
  }[];
};

export function getSourceHealth() {
  return j<SourceHealthReport>(fetch(`${getApiBase()}/api/sources/health`));
}

export type Watchlist = {
  id: number;
  workspace_id: number;
  name: string;
  is_default: number;
};

export type WatchlistTerm = {
  id: number;
  watchlist_id: number;
  term_type: string;
  value: string;
  lang?: string;
};

export type WatchlistAccount = {
  id: number;
  watchlist_id: number;
  platform: string;
  handle: string;
  role?: string;
};

export type WatchlistBundle = {
  watchlist: Watchlist;
  terms: WatchlistTerm[];
  accounts: WatchlistAccount[];
  by_type: Record<string, string[]>;
  creators: string[];
};

export function listWatchlists() {
  return j<{ workspace_id: number; watchlists: Watchlist[] }>(fetch(`${getApiBase()}/api/watchlists`));
}

export function getWatchlist(id: number) {
  return j<WatchlistBundle>(fetch(`${getApiBase()}/api/watchlists/${id}`));
}

export function addWatchlistTerm(watchlistId: number, term_type: string, value: string) {
  return j<WatchlistTerm>(
    fetch(`${getApiBase()}/api/watchlists/${watchlistId}/terms`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ term_type, value }),
    }),
  );
}

export function deleteWatchlistTerm(watchlistId: number, termId: number) {
  return j<{ deleted: boolean }>(
    fetch(`${getApiBase()}/api/watchlists/${watchlistId}/terms/${termId}`, { method: "DELETE" }),
  );
}

export function addWatchlistAccount(watchlistId: number, platform: string, handle: string) {
  return j<WatchlistAccount>(
    fetch(`${getApiBase()}/api/watchlists/${watchlistId}/accounts`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ platform, handle }),
    }),
  );
}

export function deleteWatchlistAccount(watchlistId: number, accountId: number) {
  return j<{ deleted: boolean }>(
    fetch(`${getApiBase()}/api/watchlists/${watchlistId}/accounts/${accountId}`, { method: "DELETE" }),
  );
}

export function confirmTrendTopic(topic: string, hours = 48) {
  const p = new URLSearchParams({ topic, hours: String(hours) });
  return j<{
    topic: string;
    tier: string;
    label: string;
    confirmation_score: number;
    narrative: string;
    categories: string[];
    independent_source_categories: number;
  }>(fetch(`${getApiBase()}/api/trends/confirm?${p}`));
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
  published_at?: string | null;
  collected_at?: string | null;
};

export type MediaFilters = {
  limit?: number;
  category?: string;
  platform?: string;
  q?: string;
  min_engagement?: number;
  per_platform?: number;
};

function qsMedia(f?: MediaFilters): string {
  const p = new URLSearchParams();
  if (f?.limit != null) p.set("limit", String(f.limit));
  if (f?.category) p.set("category", f.category);
  if (f?.platform) p.set("platform", f.platform);
  if (f?.q) p.set("q", f.q);
  if (f?.min_engagement != null) p.set("min_engagement", String(f.min_engagement));
  if (f?.per_platform != null) p.set("per_platform", String(f.per_platform));
  const s = p.toString();
  return s ? `?${s}` : "";
}

export function getMediaItems(filters?: MediaFilters) {
  const merged: MediaFilters = { limit: 80, per_platform: 6, ...filters };
  return j<MediaItem[]>(fetch(`${getApiBase()}/api/media-items${qsMedia(merged)}`));
}

export function getMetaFilters() {
  return j<{ categories: string[]; platforms: string[] }>(fetch(`${getApiBase()}/api/meta/filters`));
}

export type CollectionStatus = {
  running?: boolean;
  last_runs: Record<string, unknown>[];
  media_items_count: number;
  trend_clusters_count: number;
  source_status: { source: string; status: string; detail: string }[];
  last_summary: Record<string, unknown>;
};

export function getCollectionStatus() {
  return j<CollectionStatus>(fetch(`${getApiBase()}/api/collect/status`));
}

export function runCollection() {
  return j<{ message: string; running?: boolean }>(
    fetch(`${getApiBase()}/api/collect/run`, { method: "POST" })
  );
}

function sleep(ms: number) {
  return new Promise((r) => setTimeout(r, ms));
}

/** Start a full collection (all sources) and wait until it finishes. */
export async function refreshAllIntel(timeoutMs = 180_000): Promise<CollectionStatus> {
  const before = await getCollectionStatus();
  const prevStarted = String((before.last_runs[0] as { started_at?: string } | undefined)?.started_at || "");
  await runCollection();

  const deadline = Date.now() + timeoutMs;
  let sawRunning = Boolean(before.running);
  let last = before;

  while (Date.now() < deadline) {
    await sleep(1500);
    last = await getCollectionStatus();
    if (last.running) {
      sawRunning = true;
      continue;
    }
    const started = String((last.last_runs[0] as { started_at?: string } | undefined)?.started_at || "");
    const ended = (last.last_runs[0] as { ended_at?: string } | undefined)?.ended_at;
    if (sawRunning && !last.running) return last;
    if (ended && started && started !== prevStarted) return last;
  }
  return last;
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

export type WarRoomDossier = {
  name: string;
  source_tag: string;
  signal_count: number;
  talking_about: string[];
  campaigns_gaining_traction: {
    title?: string | null;
    platform?: string | null;
    engagement?: number;
    url?: string | null;
  }[];
  themes_owned: string[];
  theme_scores?: Record<string, number>;
  audience_attracted: string;
  content_formats: { format: string; share: number; count?: number }[];
  where_silent: string[];
  trends_adopted_before_us: { label?: string | null; trend_score?: number | null; note?: string }[];
  related_clusters?: unknown[];
  recent_signals?: unknown[];
  notes?: string;
  seeded?: boolean;
};

export type WarRoomReport = {
  title: string;
  subtitle: string;
  brand?: string | null;
  sector?: string | null;
  competitor_source: string;
  brief_id?: number | null;
  competitors: string[];
  theme_board: { theme: string; owners: string[]; status: string }[];
  opportunity_gaps: {
    theme: string;
    owned_by: string[];
    gap_type: string;
    headline: string;
    opportunity: string;
    why: string;
    priority: number;
  }[];
  dossiers: WarRoomDossier[];
  summary: {
    competitor_count: number;
    open_themes: number;
    gap_count: number;
    signals_indexed: number;
  };
  playbook: string;
};

export function getCompetitorWarRoom() {
  return j<WarRoomReport>(fetch(`${getApiBase()}/api/competitors/war-room`));
}
