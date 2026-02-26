import { render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { App } from "./App";

beforeEach(() => {
  vi.spyOn(globalThis, "fetch").mockImplementation((input: RequestInfo | URL, init?: RequestInit) => {
    const url = String(input);
    if (url.endsWith("/api/v1/health")) {
      return Promise.resolve(
        new Response(JSON.stringify({ status: "ok" }), { status: 200 })
      );
    }
    if (url.endsWith("/api/v1/tasks") && init?.method === "POST") {
      return Promise.resolve(
        new Response(
          JSON.stringify({ id: "1", title: "Task", created_at: "2026-01-01T00:00:00Z" }),
          { status: 201 }
        )
      );
    }
    if (url.endsWith("/api/v1/tasks")) {
      return Promise.resolve(
        new Response(
          JSON.stringify([{ id: "1", title: "Task", created_at: "2026-01-01T00:00:00Z" }]),
          { status: 200 }
        )
      );
    }
    return Promise.resolve(new Response("Not found", { status: 404 }));
  });
});

describe("App", () => {
  it("renders header and fetched task", async () => {
    render(<App />);

    expect(screen.getByText("Bootstrap App")).toBeInTheDocument();
    expect(await screen.findByText("Task")).toBeInTheDocument();
    expect(await screen.findByText("Backend health: ok")).toBeInTheDocument();
  });
});
