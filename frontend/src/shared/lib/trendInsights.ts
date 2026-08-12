import type { Trend } from "@/shared/api";

/** Momentum dérivé du pulse (pas d’historique API → heuristique MVP). */
export type Momentum = "rising" | "stable" | "falling";

export type TrendAction = "publish_now" | "wait" | "avoid";

export function getMomentum(t: Trend): Momentum {
  const p = t.trend_score;
  if (p >= 62) return "rising";
  if (p >= 38) return "stable";
  return "falling";
}

/** Reco action : croise pulse + risque. */
export function getTrendAction(t: Trend): TrendAction {
  const { trend_score: pulse, risk_score: risk } = t;
  if (risk >= 72 || pulse < 28) return "avoid";
  if (pulse >= 52 && risk <= 48) return "publish_now";
  return "wait";
}

export const momentumCopy: Record<Momentum, { label: string; hint: string }> = {
  rising: { label: "Montée", hint: "Le sujet prend de l’ampleur dans les signaux agrégés." },
  stable: { label: "Stable", hint: "Le momentum est stationnaire — surveiller la prochaine fenêtre." },
  falling: { label: "Redescend", hint: "Le pic médiatique faiblit ; prioriser d’autres sujets." },
};

export const actionCopy: Record<TrendAction, { label: string; sub: string }> = {
  publish_now: {
    label: "Publier maintenant",
    sub: "Pulse solide et risque modéré : bonne fenêtre de réaction créative.",
  },
  wait: {
    label: "Attendre",
    sub: "Signal mitigé ou risque à clarifier avant d’engager du budget.",
  },
  avoid: {
    label: "Éviter",
    sub: "Risque élevé ou signal trop faible — ne pas forcer une présence.",
  },
};
