import BriefForm from "@/features/brief/components/BriefForm";

export default function BriefPage() {
  return (
    <div className="mx-auto max-w-3xl space-y-4">
      <div className="hidden md:block">
        <h2 className="font-display text-2xl font-semibold text-slate-900">Brief client</h2>
      </div>
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
