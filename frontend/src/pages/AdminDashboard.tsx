import { FormEvent, useState } from "react";

import { authStore, request } from "../lib/api";

type AdminTokenResponse = { access_token: string };

type AdminCard = {
  title: string;
  description: string;
};

const cards: AdminCard[] = [
  {
    title: "Catalog management",
    description: "Create and update departments, majors, courses, and offerings.",
  },
  {
    title: "Scheduling",
    description: "Run scheduling simulations and approve suggested sections.",
  },
  {
    title: "Operations",
    description: "Review audits, registration periods, and observability signals.",
  },
];

export default function AdminDashboard() {
  const [token, setToken] = useState(authStore.admin.get());
  const [status, setStatus] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function handleLogin(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setLoading(true);
    setStatus(null);

    const form = new FormData(event.currentTarget);
    const email = String(form.get("email") ?? "").trim();
    const password = String(form.get("password") ?? "");

    try {
      const result = await request<AdminTokenResponse>("/api/v1/auth/admin/login", {
        method: "POST",
        body: { email, password },
      });
      authStore.admin.set(result.access_token);
      setToken(result.access_token);
      setStatus("Signed in successfully.");
      event.currentTarget.reset();
    } catch (error) {
      setStatus(error instanceof Error ? error.message : "Sign-in failed.");
    } finally {
      setLoading(false);
    }
  }

  function handleLogout() {
    authStore.admin.clear();
    setToken(null);
    setStatus("Signed out.");
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white border-b border-gray-200 px-6 py-3 flex items-center justify-between">
        <span className="font-semibold text-gray-900">CourseFlow Admin</span>
        {token ? (
          <button
            type="button"
            onClick={handleLogout}
            className="text-sm text-gray-500 hover:text-gray-700"
          >
            Sign out
          </button>
        ) : null}
      </header>

      <main className="max-w-5xl mx-auto px-4 py-8 space-y-6">
        <section className="bg-white border border-gray-200 rounded-2xl p-6">
          <div className="flex items-start justify-between gap-6 flex-col md:flex-row">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">Admin dashboard</h1>
              <p className="text-sm text-gray-500 mt-1">
                Manage core academic data and monitor system activity.
              </p>
            </div>
            <div className="text-sm text-gray-500">
              Status: {token ? "Authenticated" : "Not signed in"}
            </div>
          </div>

          {status ? (
            <p className="mt-4 text-sm text-gray-600">{status}</p>
          ) : null}

          {!token ? (
            <form className="mt-6 grid gap-4 md:grid-cols-3" onSubmit={handleLogin}>
              <input
                name="email"
                type="text"
                required
                defaultValue="admin@crsp.local"
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-400"
              />
              <input
                name="password"
                type="password"
                required
                defaultValue="admin12345"
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-400"
              />
              <button
                type="submit"
                disabled={loading}
                className="w-full bg-blue-600 text-white rounded-lg py-2.5 font-semibold text-sm hover:bg-blue-700 disabled:opacity-50 transition-colors"
              >
                {loading ? "Signing in..." : "Sign in"}
              </button>
            </form>
          ) : null}
        </section>

        <section className="grid gap-4 md:grid-cols-3">
          {cards.map((card) => (
            <div
              key={card.title}
              className="bg-white border border-gray-200 rounded-2xl p-5"
            >
              <h2 className="text-lg font-semibold text-gray-900">{card.title}</h2>
              <p className="text-sm text-gray-500 mt-2">{card.description}</p>
            </div>
          ))}
        </section>
      </main>
    </div>
  );
}
