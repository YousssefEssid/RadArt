export const PLATFORM_LABEL: Record<string, string> = {
  itunes: "Apple Music",
  reddit: "Reddit",
  rss: "Presse / RSS",
  google_news_rss: "Google News",
  youtube: "YouTube",
  tiktok: "TikTok",
  instagram: "Instagram",
  facebook: "Facebook",
  social: "Social",
  curated: "Veille RadArt",
  gdelt: "GDELT",
  serpapi: "Google Trends",
  google_trends: "Google Trends",
  public_page: "Pages publiques",
};

export function platformLabel(raw: string | null | undefined): string {
  const key = (raw || "autre").trim().toLowerCase();
  if (!key) return "Autre";
  return PLATFORM_LABEL[key] || raw || "Autre";
}

export function platformKey(raw: string | null | undefined): string {
  const key = (raw || "autre").trim().toLowerCase();
  return key || "autre";
}
