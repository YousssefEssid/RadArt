export type NavId = "radar" | "brand" | "brief" | "competitors" | "sources" | "pricing";

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
      { id: "radar", label: "Morning Radar", short: "Radar", path: "/dashboard", hint: "Ce qui a changé" },
      { id: "brand", label: "Brand Brain", short: "Marque", path: "/marque", hint: "Brand DNA" },
      { id: "brief", label: "Brief client", short: "Brief", path: "/brief", hint: "Matcher un brief" },
      { id: "competitors", label: "Competitor War Room", short: "War Room", path: "/concurrents", hint: "Gaps & thèmes" },
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
  if (pathname.startsWith("/marque") || pathname.startsWith("/brand")) return "brand";
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
