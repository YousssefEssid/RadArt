import { useState } from "react";

type Billing = "monthly" | "yearly";

const START_MONTHLY = 99;
const PRO_MONTHLY = 249;
const YEARLY_FACTOR = 0.8;

function yearlyTotal(monthly: number): number {
  return Math.round(monthly * 12 * YEARLY_FACTOR);
}

function formatPrice(n: number): string {
  return n.toLocaleString("fr-TN");
}

type Props = {
  /** Équivalent tableau de bord — correspond à la vue Radar */
  onDashboard: () => void;
  onContact: () => void;
};

export default function PricingPage({ onDashboard, onContact }: Props) {
  const [billing, setBilling] = useState<Billing>("monthly");

  const startPrice =
    billing === "monthly" ? `${formatPrice(START_MONTHLY)} TND / mois` : `${formatPrice(yearlyTotal(START_MONTHLY))} TND / an`;
  const proPrice =
    billing === "monthly" ? `${formatPrice(PRO_MONTHLY)} TND / mois` : `${formatPrice(yearlyTotal(PRO_MONTHLY))} TND / an`;

  const cardBase =
    "relative flex flex-col rounded-2xl border bg-white p-6 shadow-sm ring-1 ring-slate-900/5 transition";

  return (
    <div className="relative overflow-hidden">
      <div className="pointer-events-none absolute inset-0 -z-10 overflow-hidden">
        <div className="absolute -left-16 top-20 h-72 w-72 rounded-full border border-radj-navy/10 bg-radj-lime/5 blur-3xl" />
        <div className="absolute -right-20 top-40 h-56 w-56 rounded-full border border-cyan-400/15 bg-cyan-400/5 blur-2xl" />
        <div className="absolute bottom-10 left-1/3 h-40 w-40 rounded-full border border-radj-navy/10 opacity-60 blur-2xl" />
        <svg className="absolute right-[12%] top-16 h-24 w-24 text-radj-navy/[0.07]" viewBox="0 0 100 100" aria-hidden>
          <circle cx="50" cy="50" r="45" fill="none" stroke="currentColor" strokeWidth="1" />
          <circle cx="50" cy="50" r="28" fill="none" stroke="currentColor" strokeWidth="1" />
          <circle cx="50" cy="50" r="12" fill="none" stroke="currentColor" strokeWidth="1" />
        </svg>
        <svg className="absolute bottom-24 left-[8%] h-16 w-16 text-radj-navy/[0.06]" viewBox="0 0 100 100" aria-hidden>
          <circle cx="50" cy="50" r="48" fill="none" stroke="currentColor" strokeWidth="1.5" />
        </svg>
      </div>

      <div className="relative mx-auto max-w-5xl space-y-10">
        <div className="text-center">
          <h2 className="font-display text-2xl font-semibold text-slate-900 sm:text-3xl">Tarifs</h2>
          <p className="mt-2 text-sm text-slate-600">Choisissez la formule adaptée à votre agence.</p>

          <div className="mt-6 inline-flex rounded-full border border-slate-200 bg-slate-50 p-1 shadow-inner">
            <button
              type="button"
              onClick={() => setBilling("monthly")}
              className={`rounded-full px-5 py-2 text-sm font-semibold transition ${
                billing === "monthly" ? "bg-white text-radj-navy shadow-sm" : "text-slate-600 hover:text-slate-900"
              }`}
            >
              Mensuel
            </button>
            <button
              type="button"
              onClick={() => setBilling("yearly")}
              className={`rounded-full px-5 py-2 text-sm font-semibold transition ${
                billing === "yearly" ? "bg-white text-radj-navy shadow-sm" : "text-slate-600 hover:text-slate-900"
              }`}
            >
              Annuel
              <span className="ml-2 rounded-md bg-emerald-100 px-2 py-0.5 text-xs font-bold text-emerald-800">
                Économisez 20 %
              </span>
            </button>
          </div>
        </div>

        <div className="grid gap-6 lg:grid-cols-3 lg:items-stretch lg:gap-5">
          {/* Radar Start */}
          <article className={`${cardBase} border-slate-200`}>
            <div>
              <h3 className="font-display text-lg font-semibold text-slate-900">Radar Start</h3>
              <p className="mt-1 text-sm text-slate-600">Pour capter les premiers signaux.</p>
              <p className="mt-4 font-display text-2xl font-bold tabular-nums text-slate-900">{startPrice}</p>
            </div>
            <ul className="mt-6 flex flex-1 flex-col gap-3 text-sm text-slate-700">
              <li className="flex gap-2">
                <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-radj-navy" />
                Veille tendances générale
              </li>
              <li className="flex gap-2">
                <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-radj-navy" />
                Synthèses IA quotidiennes
              </li>
              <li className="flex gap-2">
                <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-radj-navy" />
                Jusqu’à 3 clients
              </li>
              <li className="flex gap-2">
                <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-radj-navy" />
                10 idées créatives par semaine
              </li>
              <li className="flex gap-2">
                <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-radj-navy" />
                Export PDF simple
              </li>
            </ul>
            <button
              type="button"
              onClick={() => onDashboard()}
              className="mt-8 w-full rounded-xl border border-radj-navy bg-white px-4 py-3 text-sm font-semibold text-radj-navy shadow-sm transition hover:bg-radj-navy hover:text-radj-lime"
            >
              Commencer
            </button>
          </article>

          {/* Radar Pro — highlighted */}
          <article
            className={`${cardBase} z-[1] border-2 border-cyan-400 bg-white shadow-[0_0_28px_-4px_rgba(34,211,238,0.45)] ring-cyan-400/30 md:scale-[1.04] md:shadow-[0_0_36px_-2px_rgba(34,211,238,0.5)]`}
          >
            <span className="absolute -top-3 left-1/2 -translate-x-1/2 rounded-full bg-cyan-500 px-4 py-1 text-xs font-bold uppercase tracking-wide text-white shadow-md">
              Recommandé
            </span>
            <div className="pt-2">
              <h3 className="font-display text-lg font-semibold text-slate-900">Radar Pro</h3>
              <p className="mt-1 text-sm text-slate-600">Pour transformer les signaux en opportunités.</p>
              <p className="mt-4 font-display text-2xl font-bold tabular-nums text-slate-900">{proPrice}</p>
            </div>
            <ul className="mt-6 flex flex-1 flex-col gap-3 text-sm text-slate-700">
              <li className="flex gap-2">
                <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-cyan-500" />
                Veille personnalisée par client
              </li>
              <li className="flex gap-2">
                <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-cyan-500" />
                Analyse du brief client
              </li>
              <li className="flex gap-2">
                <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-cyan-500" />
                Score opportunité
              </li>
              <li className="flex gap-2">
                <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-cyan-500" />
                Score risque
              </li>
              <li className="flex gap-2">
                <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-cyan-500" />
                Cartes campagne actionnables
              </li>
              <li className="flex gap-2">
                <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-cyan-500" />
                Jusqu’à 15 clients
              </li>
            </ul>
            <button
              type="button"
              onClick={() => onDashboard()}
              className="mt-8 w-full rounded-xl bg-cyan-500 px-4 py-3 text-sm font-semibold text-white shadow-md transition hover:bg-cyan-600"
            >
              Activer Pro
            </button>
          </article>

          {/* Radar Agency */}
          <article className={`${cardBase} border-slate-200`}>
            <div>
              <h3 className="font-display text-lg font-semibold text-slate-900">Radar Agency</h3>
              <p className="mt-1 text-sm text-slate-600">Pour piloter plusieurs marques en temps réel.</p>
              <p className="mt-4 font-display text-2xl font-bold text-slate-900">Tarif sur mesure</p>
            </div>
            <ul className="mt-6 flex flex-1 flex-col gap-3 text-sm text-slate-700">
              <li className="flex gap-2">
                <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-radj-navy" />
                Clients illimités
              </li>
              <li className="flex gap-2">
                <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-radj-navy" />
                Tableau de bord multi-comptes
              </li>
              <li className="flex gap-2">
                <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-radj-navy" />
                Collaboration équipe
              </li>
              <li className="flex gap-2">
                <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-radj-navy" />
                Alertes stratégiques
              </li>
              <li className="flex gap-2">
                <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-radj-navy" />
                Analyse concurrentielle
              </li>
              <li className="flex gap-2">
                <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-radj-navy" />
                Export decks clients
              </li>
            </ul>
            <button
              type="button"
              onClick={() => onContact()}
              className="mt-8 w-full rounded-xl border border-slate-300 bg-white px-4 py-3 text-sm font-semibold text-slate-800 shadow-sm transition hover:border-radj-navy hover:text-radj-navy"
            >
              Contacter l’équipe
            </button>
          </article>
        </div>

        <section className="rounded-2xl border border-slate-200 bg-slate-50/80 px-6 py-6 text-center shadow-sm">
          <h3 className="font-display text-sm font-semibold uppercase tracking-wide text-slate-500">
            Tous les forfaits incluent :
          </h3>
          <ul className="mx-auto mt-4 flex max-w-2xl flex-wrap justify-center gap-x-6 gap-y-2 text-sm text-slate-700">
            <li className="flex items-center gap-2">
              <span className="h-1 w-1 rounded-full bg-radj-navy" />
              Radar tendances
            </li>
            <li className="flex items-center gap-2">
              <span className="h-1 w-1 rounded-full bg-radj-navy" />
              Synthèses IA
            </li>
            <li className="flex items-center gap-2">
              <span className="h-1 w-1 rounded-full bg-radj-navy" />
              Interface tableau de bord
            </li>
            <li className="flex items-center gap-2">
              <span className="h-1 w-1 rounded-full bg-radj-navy" />
              Support standard
            </li>
          </ul>
          <p className="mt-6 text-sm italic text-slate-600">
            Changez de formule à tout moment selon le rythme de vos clients.
          </p>
        </section>
      </div>
    </div>
  );
}
