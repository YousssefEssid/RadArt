export type NavId = "radar" | "brief" | "competitors" | "sources" | "pricing";

export const NAV_ITEMS: { id: NavId; label: string }[] = [
  { id: "radar", label: "Radar & signaux" },
  { id: "brief", label: "Brief client" },
  { id: "competitors", label: "Concurrents" },
  { id: "sources", label: "Sources & collecte" },
  { id: "pricing", label: "Tarifs" },
];
