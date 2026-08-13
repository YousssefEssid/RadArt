from __future__ import annotations

from typing import Any


def _clamp(v: float, lo: float = 0.0, hi: float = 100.0) -> float:
    return max(lo, min(hi, v))


def _tier(score: float) -> dict[str, str]:
    if score >= 80:
        return {
            "key": "high",
            "label": "High-potential opportunity",
            "label_fr": "Opportunité à fort potentiel",
        }
    if score >= 65:
        return {
            "key": "solid",
            "label": "Solid opportunity",
            "label_fr": "Opportunité solide",
        }
    if score >= 45:
        return {
            "key": "watch",
            "label": "Watchlist — selective play",
            "label_fr": "À surveiller — jeu sélectif",
        }
    if score >= 30:
        return {
            "key": "weak",
            "label": "Weak fit — don’t force it",
            "label_fr": "Fit faible — ne pas forcer",
        }
    return {
        "key": "skip",
        "label": "Low RAD — skip or monitor only",
        "label_fr": "RAD bas — passer ou monitorer",
    }


def compute_rad_score(
    *,
    momentum: float,
    freshness: float,
    tunisia_relevance: float,
    audience_overlap: float,
    brand_fit: float,
    source_diversity: float,
    competitive_saturation: float,
    brand_safety_risk: float,
    brand_name: str | None = None,
    verdict: str | None = None,
) -> dict[str, Any]:
    """
    Proprietary Trend × Brand score.

    RAD = Relevance × Acceleration × Differentiation  (geometric mean of pillars)
    Pillars are built from the component metrics below, then mapped 0–100.
    Always returns an explanation (why).
    """
    m = _clamp(momentum)
    f = _clamp(freshness)
    tn = _clamp(tunisia_relevance)
    aud = _clamp(audience_overlap)
    bf = _clamp(brand_fit if brand_fit > 0 else 45.0)  # neutral if no brand yet
    div = _clamp(source_diversity)
    sat = _clamp(competitive_saturation)
    risk = _clamp(brand_safety_risk)

    # Pillars 0–100
    relevance = _clamp(0.40 * bf + 0.35 * aud + 0.25 * tn)
    acceleration = _clamp(0.55 * m + 0.45 * f)
    # Differentiation rises when diversity is high and competitive saturation is low
    differentiation = _clamp(0.55 * div + 0.45 * (100.0 - sat))

    # Geometric mean keeps one weak pillar from being hidden by two strong ones
    rad_raw = (max(relevance, 1) * max(acceleration, 1) * max(differentiation, 1)) ** (1 / 3)

    # Brand safety soft penalty (stronger only when risk is material)
    if risk >= 55:
        safety_factor = 1.0 - (risk / 100.0) * 0.35
    else:
        safety_factor = 1.0 - (risk / 100.0) * 0.12
    rad = _clamp(rad_raw * safety_factor)

    if verdict == "skip":
        rad = min(rad, 32.0)

    tier = _tier(rad)
    components = {
        "momentum": round(m, 1),
        "freshness": round(f, 1),
        "tunisia_relevance": round(tn, 1),
        "audience_overlap": round(aud, 1),
        "brand_fit": round(bf, 1),
        "source_diversity": round(div, 1),
        "competitive_saturation": round(sat, 1),
        "brand_safety_risk": round(risk, 1),
    }
    pillars = {
        "relevance": round(relevance, 1),
        "acceleration": round(acceleration, 1),
        "differentiation": round(differentiation, 1),
    }

    why_parts: list[str] = []
    brand_bit = f" for {brand_name}" if brand_name else ""
    why_parts.append(
        f"RAD{brand_bit} = Relevance ({pillars['relevance']:.0f}) × "
        f"Acceleration ({pillars['acceleration']:.0f}) × "
        f"Differentiation ({pillars['differentiation']:.0f})."
    )

    drivers: list[str] = []
    if bf >= 70:
        drivers.append(f"strong brand fit ({bf:.0f})")
    elif bf < 40:
        drivers.append(f"weak brand fit ({bf:.0f})")
    if m >= 70:
        drivers.append(f"high momentum ({m:.0f})")
    if f >= 70:
        drivers.append(f"fresh signal ({f:.0f})")
    if tn >= 70:
        drivers.append(f"Tunisia relevance ({tn:.0f})")
    if aud >= 70:
        drivers.append(f"audience overlap ({aud:.0f})")
    if div >= 65:
        drivers.append(f"diverse sources ({div:.0f})")
    if sat >= 70:
        drivers.append(f"crowded space — saturation {sat:.0f}")
    if risk >= 60:
        drivers.append(f"brand-safety risk ({risk:.0f}) pulls RAD down")

    if drivers:
        why_parts.append("Driven by: " + ", ".join(drivers[:5]) + ".")
    else:
        why_parts.append("Balanced signals without a single extreme driver.")

    if verdict == "skip":
        why_parts.append("Brand Brain verdict is don’t-chase — RAD is capped so you don’t over-invest.")
    elif rad >= 80:
        why_parts.append("High-potential: worth a creative brief this week.")
    elif rad < 45:
        why_parts.append("Keep on the radar; don’t force a campaign unless the angle is uniquely on-brand.")

    return {
        "score": round(rad, 1),
        "score_int": int(round(rad)),
        "formula": "RAD = Relevance × Acceleration × Differentiation",
        "formula_note": "Geometric mean of pillars; minus brand-safety drag",
        "pillars": pillars,
        "components": components,
        "tier": tier,
        "why": " ".join(why_parts),
        "label": f"RAD SCORE {int(round(rad))}",
    }
