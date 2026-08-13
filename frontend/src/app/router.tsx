import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import BrandBrainPage from "@/features/brand/pages/BrandBrainPage";
import BriefPage from "@/features/brief/pages/BriefPage";
import CompetitorsPage from "@/features/competitors/pages/CompetitorsPage";
import ContactPage from "@/features/contact/pages/ContactPage";
import PricingPage from "@/features/pricing/pages/PricingPage";
import RadarPage from "@/features/radar/pages/RadarPage";
import SourcesPage from "@/features/sources/pages/SourcesPage";
import AppShell from "@/shared/ui/AppShell";

export default function AppRouter() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<AppShell />}>
          <Route index element={<Navigate to="/dashboard" replace />} />
          <Route path="dashboard" element={<RadarPage />} />
          <Route path="marque" element={<BrandBrainPage />} />
          <Route path="brief" element={<BriefPage />} />
          <Route path="concurrents" element={<CompetitorsPage />} />
          <Route path="sources" element={<SourcesPage />} />
          <Route path="tarifs" element={<PricingPage />} />
          <Route path="contact" element={<ContactPage />} />
          <Route path="*" element={<Navigate to="/dashboard" replace />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}
