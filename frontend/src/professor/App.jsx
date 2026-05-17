import { useEffect, useState } from "react";
import { Navigate, Route, Routes } from "react-router-dom";

import { ProfessorLayout } from "./components/ProfessorLayout.jsx";
import { RequireProfessorSession } from "./components/RequireProfessorSession.jsx";
import { DashboardPage } from "./pages/DashboardPage.jsx";
import { RoomOptionsPage } from "./pages/RoomOptionsPage.jsx";
import { SectionDetailPage } from "./pages/SectionDetailPage.jsx";
import { SectionsPage } from "./pages/SectionsPage.jsx";
import { TimetablePage } from "./pages/TimetablePage.jsx";
import { restoreProfessorSession, signInProfessor } from "./session.js";
import "./styles.css";

export function App() {
  const [profile, setProfile] = useState(null);
  const [booting, setBooting] = useState(true);
  const [signingIn, setSigningIn] = useState(false);
  const [alert, setAlert] = useState({ message: "", type: "success" });

  useEffect(() => {
    let active = true;

    async function boot() {
      const restored = await restoreProfessorSession();
      if (!active) return;
      setProfile(restored);
      setBooting(false);
    }

    boot();
    return () => {
      active = false;
    };
  }, []);

  async function handleSignIn(email, password) {
    try {
      setSigningIn(true);
      setAlert({ message: "", type: "success" });
      const nextProfile = await signInProfessor(email, password);
      setProfile(nextProfile);
    } catch (error) {
      setAlert({ message: error.message, type: "error" });
    } finally {
      setSigningIn(false);
    }
  }

  if (booting) {
    return <div className="portal-loading">Loading professor portal...</div>;
  }

  return (
    <ProfessorLayout
      profile={profile}
      alert={alert}
      onDismissAlert={() => setAlert({ message: "", type: "success" })}
      onLogout={() => setProfile(null)}
    >
      <Routes>
        <Route
          index
          element={
            <RequireProfessorSession
              profile={profile}
              pageHeading="Professor Home"
              pageDescription="Sign in to load your assigned sections, room options, and teaching timetable."
              onSignIn={handleSignIn}
              loading={signingIn}
            >
              <DashboardPage />
            </RequireProfessorSession>
          }
        />
        <Route
          path="sections"
          element={
            <RequireProfessorSession
              profile={profile}
              pageHeading="My Sections"
              pageDescription="Sign in to review the sections currently assigned to your professor account."
              onSignIn={handleSignIn}
              loading={signingIn}
            >
              <SectionsPage />
            </RequireProfessorSession>
          }
        />
        <Route
          path="sections/:sectionId"
          element={
            <RequireProfessorSession
              profile={profile}
              pageHeading="Section Detail"
              pageDescription="Sign in to inspect one assigned section, its schedule, and its current room context."
              onSignIn={handleSignIn}
              loading={signingIn}
            >
              <SectionDetailPage />
            </RequireProfessorSession>
          }
        />
        <Route
          path="sections/:sectionId/room-options"
          element={
            <RequireProfessorSession
              profile={profile}
              pageHeading="Room Options"
              pageDescription="Sign in to review the room pool allocated to your section and submit a room preference."
              onSignIn={handleSignIn}
              loading={signingIn}
            >
              <RoomOptionsPage />
            </RequireProfessorSession>
          }
        />
        <Route
          path="timetable"
          element={
            <RequireProfessorSession
              profile={profile}
              pageHeading="Teaching Timetable"
              pageDescription="Sign in to load the weekly teaching schedule built from your assigned section records."
              onSignIn={handleSignIn}
              loading={signingIn}
            >
              <TimetablePage />
            </RequireProfessorSession>
          }
        />
        <Route path="*" element={<Navigate to="/professor" replace />} />
      </Routes>
    </ProfessorLayout>
  );
}
