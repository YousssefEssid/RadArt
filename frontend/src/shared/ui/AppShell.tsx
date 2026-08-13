import { useEffect, useState } from "react";
import { NavLink, Outlet, useLocation } from "react-router-dom";
import { NAV_GROUPS, navIdFromPath, navMetaFromPath, type NavId } from "@/shared/config/nav";

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

function IconBrand({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75">
      <circle cx="12" cy="8" r="3.5" />
      <path d="M5 20c1.5-3.5 4-5 7-5s5.5 1.5 7 5" strokeLinecap="round" />
      <path d="M16.5 6.5l1.2-2.2M18.8 9.2l2.2-.2M7.5 6.5L6.3 4.3M5.2 9.2l-2.2-.2" strokeLinecap="round" />
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

function IconMenu({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75">
      <path d="M4 7h16M4 12h16M4 17h16" strokeLinecap="round" />
    </svg>
  );
}

function IconClose({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75">
      <path d="M6 6l12 12M18 6L6 18" strokeLinecap="round" />
    </svg>
  );
}

const ICONS: Record<NavId, typeof IconRadar> = {
  radar: IconRadar,
  brand: IconBrand,
  brief: IconBrief,
  competitors: IconCompetitors,
  sources: IconSources,
  pricing: IconPricing,
};

function SidebarNav({ onNavigate }: { onNavigate?: () => void }) {
  const { pathname } = useLocation();
  const active = navIdFromPath(pathname);

  return (
    <div className="flex h-full min-h-full flex-col">
      <div className="border-b border-white/15 px-5 py-5">
        <img
          src={NAV_LOGO}
          alt="RAD'ART"
          className="pointer-events-none block h-9 w-auto max-w-[11rem] object-contain object-left"
          decoding="async"
        />
        <p className="mt-3 text-[11px] font-semibold uppercase tracking-[0.18em] text-[#d7ff7b]">
          Intelligence culturelle
        </p>
      </div>

      <nav className="flex-1 space-y-6 overflow-y-auto px-3 py-5" aria-label="Navigation principale">
        {NAV_GROUPS.map((group) => (
          <div key={group.label}>
            <p className="mb-2 px-3 text-[11px] font-semibold uppercase tracking-[0.16em] text-white/55">
              {group.label}
            </p>
            <ul className="space-y-1">
              {group.items.map((item) => {
                const Icon = ICONS[item.id];
                const isActive = active === item.id;
                return (
                  <li key={item.id}>
                    <NavLink
                      to={item.path}
                      title={item.label}
                      onClick={onNavigate}
                      className={`ra-sidebar-link flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm transition ${
                        isActive ? "is-active" : ""
                      }`}
                    >
                      <Icon className={`h-4 w-4 shrink-0 ${isActive ? "text-[#12142b]" : "text-[#d7ff7b]"}`} />
                      <span className="min-w-0">
                        <span className="block font-semibold leading-tight">{item.short}</span>
                        <span className={`block text-[11px] leading-tight ${isActive ? "text-[#12142b]/70" : "text-white/60"}`}>
                          {item.hint}
                        </span>
                      </span>
                    </NavLink>
                  </li>
                );
              })}
            </ul>
          </div>
        ))}
      </nav>

      <div className="border-t border-white/15 px-5 py-4">
        <p className="text-[11px] leading-relaxed text-white/60">
          Ce qui monte · ce qui compte · quoi faire
        </p>
      </div>
    </div>
  );
}

export default function AppShell() {
  const { pathname } = useLocation();
  const meta = navMetaFromPath(pathname);
  const [mobileOpen, setMobileOpen] = useState(false);

  useEffect(() => {
    setMobileOpen(false);
  }, [pathname]);

  useEffect(() => {
    document.body.style.overflow = mobileOpen ? "hidden" : "";
    return () => {
      document.body.style.overflow = "";
    };
  }, [mobileOpen]);

  return (
    <div className="flex min-h-screen bg-[#f3f1ec] text-slate-700">
      <aside className="ra-sidebar hidden w-[17.5rem] shrink-0 lg:sticky lg:top-0 lg:flex lg:h-screen lg:flex-col lg:overflow-hidden">
        <SidebarNav />
      </aside>

      {mobileOpen ? (
        <div className="fixed inset-0 z-50 lg:hidden">
          <button
            type="button"
            className="absolute inset-0 bg-black/40 backdrop-blur-[2px]"
            aria-label="Fermer le menu"
            onClick={() => setMobileOpen(false)}
          />
          <aside className="ra-sidebar relative h-full w-[min(18rem,86vw)] shadow-2xl">
            <button
              type="button"
              className="absolute right-3 top-4 rounded-lg p-2 text-radj-lime hover:bg-white/10"
              onClick={() => setMobileOpen(false)}
              aria-label="Fermer"
            >
              <IconClose className="h-5 w-5" />
            </button>
            <SidebarNav onNavigate={() => setMobileOpen(false)} />
          </aside>
        </div>
      ) : null}

      <div className="flex min-h-screen min-w-0 flex-1 flex-col">
        <header className="sticky top-0 z-40 border-b border-[#e8e6e0] bg-[#faf9f6]/90 backdrop-blur-md">
          <div className="flex items-center gap-3 px-4 py-3 sm:px-6 lg:px-8">
            <button
              type="button"
              className="rounded-xl border border-[#e8e6e0] bg-white p-2 text-[#1c1c68] shadow-sm lg:hidden"
              onClick={() => setMobileOpen(true)}
              aria-label="Ouvrir le menu"
            >
              <IconMenu className="h-5 w-5" />
            </button>
            <div className="min-w-0 flex-1">
              <p className="text-[10px] font-semibold uppercase tracking-[0.16em] text-[#1c1c68]/60">RadArt</p>
              <h1 className="truncate font-display text-lg font-semibold text-[#12142b] sm:text-xl">{meta.label}</h1>
            </div>
            <img
              src={NAV_LOGO}
              alt=""
              className="h-8 w-auto object-contain lg:hidden"
              decoding="async"
            />
          </div>
        </header>

        <main className="w-full flex-1 px-4 py-6 sm:px-6 lg:px-8 xl:px-10">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
