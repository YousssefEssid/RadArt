import type { ReactNode } from "react";
import type { NavId } from "../nav";
import { NAV_ITEMS } from "../nav";

const NAV_LOGO = "/brand-logo.png";

function IconRadar({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75">
      <circle cx="12" cy="12" r="9" opacity="0.35" />
      <circle cx="12" cy="12" r="5" opacity="0.55" />
      <circle cx="12" cy="12" r="1.5" fill="currentColor" stroke="none" />
      <path d="M12 3v2M12 19v2M3 12h2M19 12h2" strokeLinecap="round" />
    </svg>
  );
}

function IconBrief({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75">
      <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
      <path d="M14 2v6h6M16 13H8M16 17H8M10 9H8" strokeLinecap="round" />
    </svg>
  );
}

function IconCompetitors({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75">
      <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2" />
      <circle cx="9" cy="7" r="4" />
      <path d="M23 21v-2a4 4 0 0 0-3-3.87M16 3.13a4 4 0 0 1 0 7.75" strokeLinecap="round" />
    </svg>
  );
}

function IconSources({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75">
      <ellipse cx="12" cy="6" rx="8" ry="3" />
      <path d="M4 6v6c0 1.66 3.58 3 8 3s8-1.34 8-3V6" />
      <path d="M4 12v6c0 1.66 3.58 3 8 3s8-1.34 8-3v-6" />
    </svg>
  );
}

function IconPricing({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75">
      <path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83" strokeLinecap="round" />
      <circle cx="12" cy="12" r="3" />
    </svg>
  );
}

const ICONS: Record<NavId, typeof IconRadar> = {
  radar: IconRadar,
  brief: IconBrief,
  competitors: IconCompetitors,
  sources: IconSources,
  pricing: IconPricing,
};

type Props = {
  active: NavId;
  onNavigate: (id: NavId) => void;
  children: ReactNode;
};

export default function AppShell({ active, onNavigate, children }: Props) {
  return (
    <div className="flex min-h-screen flex-col bg-white">
      <header className="sticky top-0 z-40 border-b border-radj-lime bg-radj-navy shadow-[0_1px_0_rgba(215,255,123,0.15)]">
        <div className="mx-auto flex min-h-[4rem] max-w-6xl flex-col items-center gap-3 px-4 py-3 sm:min-h-[4.25rem] sm:flex-row sm:items-center sm:justify-between sm:gap-5 sm:py-3.5 lg:px-8">
          <div className="flex h-10 w-auto max-w-[min(42rem,94vw)] shrink-0 items-center justify-start sm:h-11">
            <img
              src={NAV_LOGO}
              alt="RAD'ART"
              className="pointer-events-none block h-10 w-auto max-h-10 object-contain object-left sm:h-11 sm:max-h-11"
              decoding="async"
            />
          </div>

          <nav
            className="flex w-full min-w-0 items-center justify-center gap-1.5 overflow-x-auto sm:w-auto sm:flex-1 sm:justify-end md:justify-center lg:gap-2"
            aria-label="Navigation principale"
          >
            {NAV_ITEMS.map((item) => {
              const Icon = ICONS[item.id];
              const isActive = active === item.id;
              return (
                <button
                  key={item.id}
                  type="button"
                  onClick={() => onNavigate(item.id)}
                  title={item.label}
                  className={`inline-flex min-h-[2.75rem] shrink-0 items-center gap-2 rounded-xl border px-3 py-2 text-left transition sm:min-h-[3rem] sm:px-3.5 sm:py-2.5 ${
                    isActive
                      ? "border-radj-lime bg-radj-lime text-radj-navy"
                      : "border-transparent text-radj-lime hover:border-radj-lime/50 hover:bg-white/10"
                  }`}
                >
                  <Icon className={`h-4 w-4 shrink-0 sm:h-5 sm:w-5 ${isActive ? "text-radj-navy" : "text-radj-lime"}`} />
                  <span className="max-w-[9rem] truncate text-xs font-medium sm:max-w-none sm:text-sm">{item.label}</span>
                </button>
              );
            })}
          </nav>
        </div>
      </header>

      <main className="mx-auto w-full max-w-6xl flex-1 px-4 py-6 sm:px-6 lg:px-8">{children}</main>
    </div>
  );
}
