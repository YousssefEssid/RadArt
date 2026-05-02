"""Rapport concurrentiel statique pour démo UI (sans brief ni collecte réelle)."""

from __future__ import annotations

from typing import Any


def tunisia_telecom_demo_report() -> dict[str, Any]:
    """Concurrents types de Tunisie Telecom — données illustratives uniquement."""
    return {
        "brief_id": 0,
        "client_name": "Tunisie Telecom",
        "sector": "telecom",
        "target": "Particuliers, pros et PME — Tunisie",
        "competitor_source": "demo_static",
        "competitors": ["Orange Tunisie", "Ooredoo Tunisie"],
        "cards": [
            {
                "name": "Orange Tunisie",
                "source_tag": "benchmark",
                "signal_count": 4,
                "notes": "Démo statique : veille indicative sur les principaux concurrents du marché tunisien.",
                "recent_signals": [
                    {
                        "id": 91001,
                        "title": "Campagne fibre « Maison connectée » — nouvelle offre triple play",
                        "source": "demo",
                        "platform": "web",
                        "category": "retail",
                        "url": "https://www.orange.tn/",
                        "published_at": "2026-04-28T10:00:00Z",
                        "engagement": 420,
                    },
                    {
                        "id": 91002,
                        "title": "Pub réseau social : promo data illimitée week-end",
                        "source": "demo",
                        "platform": "instagram",
                        "category": "youth",
                        "url": None,
                        "published_at": "2026-04-25T14:30:00Z",
                        "engagement": 890,
                    },
                    {
                        "id": 91003,
                        "title": "Communiqué : extension couverture 5G Grand Tunis",
                        "source": "demo",
                        "platform": "rss",
                        "category": "general",
                        "url": None,
                        "published_at": "2026-04-22T09:15:00Z",
                        "engagement": 120,
                    },
                    {
                        "id": 91004,
                        "title": "Partenariat e-commerce — paiement mobile wallet",
                        "source": "demo",
                        "platform": "web",
                        "category": "economy",
                        "url": None,
                        "published_at": "2026-04-18T11:00:00Z",
                        "engagement": 210,
                    },
                ],
                "related_clusters": [
                    {
                        "id": 92001,
                        "label": "Promotions data & bundles jeunes",
                        "summary": "Les opérateurs poussent les offres volume et week-end pour capter la Gen Z.",
                        "category": "youth",
                        "trend_score": 72.0,
                        "risk_score": 28.0,
                    },
                    {
                        "id": 92002,
                        "label": "Fibre et fixe au Maghreb",
                        "summary": "Montée en puissance des offres triple play et concurrence sur le débit.",
                        "category": "general",
                        "trend_score": 65.0,
                        "risk_score": 35.0,
                    },
                ],
            },
            {
                "name": "Ooredoo Tunisie",
                "source_tag": "benchmark",
                "signal_count": 3,
                "notes": "Exemple de lecture concurrentielle sur une marque du même segment.",
                "recent_signals": [
                    {
                        "id": 91011,
                        "title": "Publicité TV — offre famille multi-lignes",
                        "source": "demo",
                        "platform": "tv",
                        "category": "culture",
                        "url": None,
                        "published_at": "2026-04-27T18:45:00Z",
                        "engagement": 0,
                    },
                    {
                        "id": 91012,
                        "title": "Story Instagram — jeu concours Ramadan",
                        "source": "demo",
                        "platform": "instagram",
                        "category": "culture",
                        "url": None,
                        "published_at": "2026-04-24T20:00:00Z",
                        "engagement": 1500,
                    },
                    {
                        "id": 91013,
                        "title": "Article presse — stratégie entreprise et IoT",
                        "source": "demo",
                        "platform": "news",
                        "category": "economy",
                        "url": None,
                        "published_at": "2026-04-15T08:00:00Z",
                        "engagement": 55,
                    },
                ],
                "related_clusters": [
                    {
                        "id": 92003,
                        "label": "Événements saisonniers & engagement social",
                        "summary": "Les campagnes autour du Ramadan et des solidarités locales amplifient la portée.",
                        "category": "culture",
                        "trend_score": 68.0,
                        "risk_score": 22.0,
                    },
                ],
            },
        ],
    }
