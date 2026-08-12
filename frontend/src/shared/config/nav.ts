export type NavId = "radar" | "brief" | "competitors" | "sources" | "pricing";

export type NavItem = {
  id: NavId;
  label: string;
  path: string;
};

export const NAV_ITEMS: NavItem[] = [
  { id: "radar", label: "Radar & signaux", path: "/dashboard" },
  { id: "brief", label: "Brief client", path: "/brief" },
  { id: "competitors", label: "Concurrents", path: "/concurrents" },
  { id: "sources", label: "Sources & collecte", path: "/sources" },
  { id: "pricing", label: "Tarifs", path: "/tarifs" },
];

export function navIdFromPath(pathname: string): NavId {
  if (pathname.startsWith("/brief")) return "brief";
  if (pathname.startsWith("/concurrents")) return "competitors";
  if (pathname.startsWith("/sources")) return "sources";
  if (pathname.startsWith("/tarifs") || pathname.startsWith("/contact")) return "pricing";
  return "radar";
}
