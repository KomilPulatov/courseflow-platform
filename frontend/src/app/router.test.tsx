import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { AppProviders } from "./providers";
import { AppRouter } from "./router";

describe("AppRouter", () => {
  it("renders the demo experience at /demo", () => {
    window.history.pushState({}, "", "/demo");
    render(
      <AppProviders>
        <AppRouter />
      </AppProviders>,
    );

    expect(screen.getByText("CRSP Demo Console")).toBeInTheDocument();
  });

  it("redirects unauthenticated admin requests to login", () => {
    localStorage.clear();
    window.history.pushState({}, "", "/admin/courses");
    render(
      <AppProviders>
        <AppRouter />
      </AppProviders>,
    );

    expect(screen.getByText("CRSP Administration")).toBeInTheDocument();
  });
});
