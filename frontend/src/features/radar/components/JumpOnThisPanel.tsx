import { Link } from "react-router-dom";
import { useMutation } from "@tanstack/react-query";
import { useState } from "react";
import {
  analyzeJump,
  generateCampaign,
  type CampaignPack,
  type JumpAnalysis,
} from "@/shared/api";

type Props = {
  clusterId: number;
  trendTitle: string;
};

const recStyles: Record<string, string> = {
  YES: "border-emerald-300 bg-emerald-50 text-emerald-950",
  CAUTION: "border-amber-300 bg-amber-50 text-amber-950",
  NO: "border-red-300 bg-red-50 text-red-950",
};

function ScoreGrid({ scores }: { scores: JumpAnalysis["scores"] }) {
  const rows: [string, string][] = [
    ["Brand fit", `${Math.round(scores.brand_fit)}%`],
    ["Audience fit", `${Math.round(scores.audience_fit)}%`],
    ["Trend maturity", scores.trend_maturity],
    ["Competitor saturation", scores.competitor_saturation],
    ["Reputational risk", scores.reputational_risk],
    ["RAD Score", String(scores.rad_score)],
  ];
  return (
    <dl className="grid gap-2 sm:grid-cols-2">
      {rows.map(([k, v]) => (
        <div key={k} className="rounded-lg border border-slate-200 bg-white px-3 py-2">
          <dt className="text-[10px] font-semibold uppercase tracking-wide text-slate-500">{k}</dt>
          <dd className="text-sm font-semibold text-slate-900">{v}</dd>
        </div>
      ))}
    </dl>
  );
}

function CampaignView({ pack }: { pack: CampaignPack }) {
  const c = pack.campaign;
  if (!c) return null;
  return (
    <div className="space-y-4 border-t border-slate-200 pt-4">
      <div>
        <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-radj-navy">
          Generate Campaign
        </p>
        <h4 className="mt-1 font-display text-lg font-semibold text-slate-900">
          “{c.campaign_name}”
        </h4>
        <p className="mt-1 text-xs text-slate-500">{pack.pipeline}</p>
      </div>
      {(
        [
          ["Big idea", c.big_idea],
          ["Consumer insight", c.consumer_insight],
          ["Campaign concept", c.campaign_concept],
          ["Key message", c.key_message],
          ["Visual direction", c.visual_direction],
          ["Influencer profile", c.influencer_profile],
          ["Timing", c.timing],
          ["Channels", c.channels],
        ] as const
      ).map(([label, body]) => (
        <div key={label}>
          <p className="text-[11px] font-semibold uppercase tracking-wide text-slate-500">{label}</p>
          <p className="mt-1 text-sm leading-relaxed text-slate-800">{body}</p>
        </div>
      ))}
      <div>
        <p className="text-[11px] font-semibold uppercase tracking-wide text-slate-500">
          TikTok / Reel concepts
        </p>
        <ul className="mt-1 list-disc space-y-1 pl-5 text-sm text-slate-800">
          {c.tiktok_reel_concepts.map((x) => (
            <li key={x}>{x}</li>
          ))}
        </ul>
      </div>
      <div>
        <p className="text-[11px] font-semibold uppercase tracking-wide text-slate-500">Caption ideas</p>
        <ul className="mt-1 list-disc space-y-1 pl-5 text-sm text-slate-800">
          {c.caption_ideas.map((x) => (
            <li key={x}>{x}</li>
          ))}
        </ul>
      </div>
      <div>
        <p className="text-[11px] font-semibold uppercase tracking-wide text-slate-500">Hashtags</p>
        <p className="mt-1 text-sm font-medium text-slate-800">{c.hashtags.join(" ")}</p>
      </div>
      <div>
        <p className="text-[11px] font-semibold uppercase tracking-wide text-slate-500">KPIs</p>
        <ul className="mt-1 list-disc space-y-1 pl-5 text-sm text-slate-800">
          {c.kpis.map((x) => (
            <li key={x}>{x}</li>
          ))}
        </ul>
      </div>
    </div>
  );
}

export default function JumpOnThisPanel({ clusterId, trendTitle }: Props) {
  const [open, setOpen] = useState(false);
  const [jump, setJump] = useState<JumpAnalysis | null>(null);
  const [campaign, setCampaign] = useState<CampaignPack | null>(null);

  const jumpMutation = useMutation({
    mutationFn: () => analyzeJump(clusterId),
    onSuccess: (data) => {
      setJump(data);
      setCampaign(null);
      setOpen(true);
    },
  });

  const campaignMutation = useMutation({
    mutationFn: () => generateCampaign(clusterId),
    onSuccess: (data) => setCampaign(data),
  });

  return (
    <div className="space-y-3">
      <button
        type="button"
        onClick={() => jumpMutation.mutate()}
        disabled={jumpMutation.isPending}
        className="w-full rounded-xl bg-radj-navy px-4 py-3 text-sm font-semibold text-radj-lime shadow-sm transition hover:bg-radj-navy/90 disabled:opacity-50 sm:w-auto"
      >
        {jumpMutation.isPending ? "Analyse…" : "Should we jump on this? · Analyse for my brand"}
      </button>
      {jumpMutation.isError ? (
        <p className="text-sm text-red-700">
          {(jumpMutation.error as Error).message || "Analyse impossible"}
        </p>
      ) : null}

      {open && jump ? (
        <div className={`rounded-2xl border p-4 sm:p-5 ${recStyles[jump.recommendation] || recStyles.CAUTION}`}>
          <div className="flex flex-wrap items-start justify-between gap-2">
            <div>
              <p className="text-[11px] font-semibold uppercase tracking-[0.16em] opacity-70">
                Should we jump on this?
              </p>
              <h4 className="mt-1 font-display text-xl font-semibold">{jump.recommendation_label}</h4>
              <p className="mt-1 text-sm opacity-90">
                {jump.brand ? `${jump.brand} · ` : ""}
                {trendTitle}
              </p>
            </div>
            <button
              type="button"
              className="text-xs font-semibold underline-offset-2 hover:underline"
              onClick={() => setOpen(false)}
            >
              Fermer
            </button>
          </div>
          <p className="mt-3 text-sm leading-relaxed">{jump.recommendation_why}</p>
          <div className="mt-4">
            <ScoreGrid scores={jump.scores} />
          </div>
          {jump.rad_why ? (
            <p className="mt-3 text-xs leading-relaxed opacity-80">{jump.rad_why}</p>
          ) : null}

          {!jump.has_brand_brain ? (
            <p className="mt-3 text-sm">
              <Link to="/marque" className="font-semibold underline-offset-2 hover:underline">
                Activez Brand Brain
              </Link>{" "}
              pour un verdict plus précis.
            </p>
          ) : null}

          {jump.can_generate_campaign ? (
            <button
              type="button"
              onClick={() => campaignMutation.mutate()}
              disabled={campaignMutation.isPending}
              className="mt-4 rounded-xl border border-current/20 bg-white/80 px-4 py-2.5 text-sm font-semibold shadow-sm disabled:opacity-50"
            >
              {campaignMutation.isPending ? "Génération…" : "Generate Campaign"}
            </button>
          ) : null}

          {campaignMutation.isError ? (
            <p className="mt-2 text-sm text-red-800">{(campaignMutation.error as Error).message}</p>
          ) : null}

          {campaign?.blocked ? (
            <p className="mt-3 text-sm font-medium">{campaign.blocked_reason}</p>
          ) : null}

          {campaign && !campaign.blocked ? <CampaignView pack={campaign} /> : null}
        </div>
      ) : null}
    </div>
  );
}
