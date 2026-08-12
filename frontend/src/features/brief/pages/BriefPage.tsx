import BriefForm from "@/features/brief/components/BriefForm";

export default function BriefPage() {
  return (
    <div className="mx-auto max-w-4xl space-y-4">
      <p className="hidden text-sm text-slate-600 md:block">
        Collez un brief ou importez un fichier — RadArt extrait le contexte et propose des angles de campagne.
      </p>
      <BriefForm
        onAnalyzed={(briefId) => {
          try {
            localStorage.setItem("radart_last_brief_id", String(briefId));
          } catch {
            /* ignore */
          }
        }}
      />
    </div>
  );
}
