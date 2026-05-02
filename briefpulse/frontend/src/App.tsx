import { useState } from "react";
import AppShell from "./components/AppShell";
import type { NavId } from "./nav";
import BriefPage from "./pages/BriefPage";
import CompetitorsPage from "./pages/CompetitorsPage";
import ContactPage from "./pages/ContactPage";
import PricingPage from "./pages/PricingPage";
import RadarPage from "./pages/RadarPage";
import SourcesPage from "./pages/SourcesPage";

/** Vues hors navigation principale (ex. contact depuis Tarifs) */
type ViewId = NavId | "contact";

export default function App() {
  const [view, setView] = useState<ViewId>("radar");

  function setNav(id: NavId) {
    setView(id);
    const path =
      id === "radar"
        ? "/dashboard"
        : id === "pricing"
          ? "/tarifs"
          : id === "brief"
            ? "/brief"
            : id === "competitors"
              ? "/concurrents"
              : "/sources";
    window.history.replaceState(null, "", path);
  }

  function goDashboard() {
    setView("radar");
    window.history.replaceState(null, "", "/dashboard");
  }

  function goContact() {
    setView("contact");
    window.history.replaceState(null, "", "/contact");
  }

  const shellActive: NavId = view === "contact" ? "pricing" : view;

  return (
    <AppShell active={shellActive} onNavigate={setNav}>
      {view === "radar" && <RadarPage />}
      {view === "brief" && <BriefPage />}
      {view === "competitors" && <CompetitorsPage />}
      {view === "sources" && <SourcesPage />}
      {view === "pricing" && <PricingPage onDashboard={goDashboard} onContact={goContact} />}
      {view === "contact" && <ContactPage onBackToPricing={() => setNav("pricing")} />}
    </AppShell>
  );
}
