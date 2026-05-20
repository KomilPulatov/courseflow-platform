import { render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it } from "vitest";

import { AppProviders } from "./providers";
import { AppRouter } from "./router";

describe("AppRouter", () => {
  beforeEach(() => {
    localStorage.clear();
  });

  it("renders the unified login experience at /login", () => {
    window.history.pushState({}, "", "/login");
    render(
      <AppProviders>
        <AppRouter />
      </AppProviders>,
    );

    expect(screen.getByText("Student and professor access")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Admin login" })).toHaveAttribute(
      "href",
      "/admin/login",
    );
    expect(screen.getByRole("button", { name: "Sign in" })).toBeInTheDocument();
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

    expect(screen.getByText("Student and professor access")).toBeInTheDocument();
  });

  it("redirects unauthenticated admin requests to login", () => {
    window.history.pushState({}, "", "/admin/courses");
    render(
      <AppProviders>
        <AppRouter />
      </AppProviders>,
    );

    expect(screen.getByText("CRSP Administration")).toBeInTheDocument();
  });
});
