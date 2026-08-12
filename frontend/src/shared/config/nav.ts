export type NavId = "radar" | "brief" | "competitors" | "sources" | "pricing";

export type NavItem = {
  id: NavId;
  label: string;
  short: string;
  path: string;
  hint: string;
};

export const NAV_GROUPS: { label: string; items: NavItem[] }[] = [
  {
    label: "Veille",
    items: [
      { id: "radar", label: "Radar & signaux", short: "Radar", path: "/dashboard", hint: "Tendances en cours" },
      { id: "brief", label: "Brief client", short: "Brief", path: "/brief", hint: "Matcher un brief" },
      { id: "competitors", label: "Concurrents", short: "Concurrents", path: "/concurrents", hint: "Veille concurrentielle" },
      { id: "sources", label: "Sources & collecte", short: "Sources", path: "/sources", hint: "Flux & statut" },
    ],
  },
  {
    label: "Agence",
    items: [{ id: "pricing", label: "Tarifs", short: "Tarifs", path: "/tarifs", hint: "Offres RadArt" }],
  },
];

export const NAV_ITEMS: NavItem[] = NAV_GROUPS.flatMap((g) => g.items);

export function navIdFromPath(pathname: string): NavId {
  if (pathname.startsWith("/brief")) return "brief";
  if (pathname.startsWith("/concurrents")) return "competitors";
  if (pathname.startsWith("/sources")) return "sources";
  if (pathname.startsWith("/tarifs") || pathname.startsWith("/contact")) return "pricing";
  return "radar";
}

export function navMetaFromPath(pathname: string): NavItem {
  const id = navIdFromPath(pathname);
  return NAV_ITEMS.find((i) => i.id === id) ?? NAV_ITEMS[0];
}
