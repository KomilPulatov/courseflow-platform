import { render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it } from "vitest";

import { AppProviders } from "./providers";
import { AppRouter } from "./router";

describe("AppRouter", () => {
  beforeEach(() => {
    localStorage.clear();
  });

  it("renders the login app at /login", () => {
    window.history.pushState({}, "", "/login");
    render(
      <AppProviders>
        <AppRouter />
      </AppProviders>,
    );

    expect(screen.getByText(/Portal System/)).toBeInTheDocument();
    expect(screen.getByRole("tab", { name: "Login" })).toBeInTheDocument();
  });

  it("renders the demo experience at /demo", () => {
    window.history.pushState({}, "", "/demo");
    render(
      <AppProviders>
        <AppRouter />
      </AppProviders>,
    );

    expect(screen.getByText("CRSP Demo Console")).toBeInTheDocument();
  });

  it("redirects unauthenticated student requests to login", () => {
    window.history.pushState({}, "", "/student/catalog");
    render(
      <AppProviders>
        <AppRouter />
      </AppProviders>,
    );

    expect(screen.getByText(/Portal System/)).toBeInTheDocument();
  });

  it("redirects unauthenticated admin requests to login", () => {
    window.history.pushState({}, "", "/admin/courses");
    render(
      <AppProviders>
        <AppRouter />
      </AppProviders>,
    );

    expect(screen.getByText(/Portal System/)).toBeInTheDocument();
  });
});
