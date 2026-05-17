import { Navigate, Route, Routes, useLocation } from "react-router-dom";

import { AppLayout } from "./components/AppLayout.jsx";
import { HealthPage } from "./pages/HealthPage.jsx";
import { NotFoundPage } from "./pages/NotFoundPage.jsx";
import { SettingsPage } from "./pages/SettingsPage.jsx";

const navItems = [
  { href: "/health", label: "Health" },
  { href: "/settings", label: "Settings" },
  { href: "/not-found", label: "Not Found" },
];

function titleFor(pathname) {
  if (pathname.startsWith("/settings")) return "Application Settings";
  if (pathname.startsWith("/not-found")) return "Route Not Found";
  return "Application Health";
}

export function App() {
  const location = useLocation();

  return (
    <AppLayout
      title={titleFor(location.pathname)}
      navItems={navItems}
      currentPath={location.pathname}
    >
      <Routes>
        <Route path="/" element={<Navigate to="/health" replace />} />
        <Route path="/health" element={<HealthPage />} />
        <Route path="/settings" element={<SettingsPage />} />
        <Route path="/not-found" element={<NotFoundPage />} />
        <Route path="*" element={<Navigate to={`/not-found?path=${encodeURIComponent(location.pathname)}`} replace />} />
      </Routes>
    </AppLayout>
  );
}
