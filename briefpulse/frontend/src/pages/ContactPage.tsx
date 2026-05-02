type Props = {
  onBackToPricing: () => void;
};

export default function ContactPage({ onBackToPricing }: Props) {
  return (
    <div className="mx-auto max-w-lg space-y-6">
      <div className="hidden md:block">
        <h2 className="font-display text-2xl font-semibold text-slate-900">Contact</h2>
        <p className="mt-2 text-sm text-slate-600">Parlez-nous de vos besoins pour Radar Agency ou d’un accompagnement sur mesure.</p>
      </div>
      <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm ring-1 ring-slate-900/5">
        <p className="text-sm text-slate-700">
          Écrivez-nous à{" "}
          <a href="mailto:contact@radj.tn" className="font-semibold text-radj-navy hover:text-radj-lime hover:underline">
            contact@radj.tn
          </a>{" "}
          ou laissez un message depuis votre messagerie habituelle.
        </p>
        <button
          type="button"
          onClick={onBackToPricing}
          className="mt-6 text-sm font-semibold text-radj-navy hover:text-radj-lime hover:underline"
        >
          ← Retour aux tarifs
        </button>
      </div>
    </div>
  );
}
