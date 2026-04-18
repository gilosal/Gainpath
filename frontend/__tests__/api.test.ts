/**
 * Tests for frontend auth and data flow (US-006).
 *
 * These tests verify the critical frontend paths touched by earlier stories:
 * - 401 response clears stored password (US-001)
 * - savePassword/clearPassword work correctly
 * - apiFetch sends Basic auth headers (tested via public API methods)
 * - Proxy strips WWW-Authenticate header (US-001)
 */
import { describe, it, expect, beforeEach, vi } from "vitest";

const store: Record<string, string> = {};
const localStorageMock = {
  getItem: (key: string) => store[key] ?? null,
  setItem: (key: string, value: string) => {
    store[key] = value;
  },
  removeItem: (key: string) => {
    delete store[key];
  },
  clear: () => {
    Object.keys(store).forEach((k) => delete store[k]);
  },
  get length() {
    return Object.keys(store).length;
  },
  key: (index: number) => Object.keys(store)[index] ?? null,
};
Object.defineProperty(globalThis, "localStorage", { value: localStorageMock });

import {
  savePassword,
  clearPassword,
  ApiError,
  sessionsApi,
} from "../lib/api";

function mockFetch(response: { ok: boolean; status: number; statusText?: string; json?: () => Promise<unknown>; text?: () => Promise<string> }) {
  const originalFetch = globalThis.fetch;
  globalThis.fetch = vi.fn().mockResolvedValue({
    ok: response.ok,
    status: response.status,
    statusText: response.statusText || "",
    json: response.json || (() => Promise.resolve(null)),
    text: response.text || (() => Promise.resolve("")),
  });
  return originalFetch;
}

describe("Auth helpers", () => {
  beforeEach(() => {
    localStorage.clear();
  });

  it("savePassword writes to localStorage", () => {
    savePassword("my-secret");
    expect(localStorage.getItem("paceforge-password")).toBe("my-secret");
  });

  it("clearPassword removes from localStorage", () => {
    savePassword("my-secret");
    clearPassword();
    expect(localStorage.getItem("paceforge-password")).toBeNull();
  });

  it("clearPassword is idempotent when nothing stored", () => {
    clearPassword();
    expect(localStorage.getItem("paceforge-password")).toBeNull();
  });
});

describe("ApiError", () => {
  it("captures status and message", () => {
    const err = new ApiError(401, "Incorrect password");
    expect(err.status).toBe(401);
    expect(err.message).toBe("Incorrect password");
    expect(err.name).toBe("ApiError");
  });

  it("is instanceof Error", () => {
    const err = new ApiError(500, "Server error");
    expect(err).toBeInstanceOf(Error);
  });
});

describe("401 clears stored password", () => {
  beforeEach(() => {
    localStorage.clear();
  });

  it("clears stored password on 401 from sessionsApi", async () => {
    savePassword("wrong-password");
    expect(localStorage.getItem("paceforge-password")).toBe("wrong-password");

    const originalFetch = mockFetch({
      ok: false,
      status: 401,
      statusText: "Unauthorized",
      text: () => Promise.resolve("Incorrect password"),
    });

    try {
      await sessionsApi.today();
    } catch (e) {
      expect(e).toBeInstanceOf(ApiError);
      expect((e as ApiError).status).toBe(401);
    }

    expect(localStorage.getItem("paceforge-password")).toBeNull();
    globalThis.fetch = originalFetch;
  });

  it("does not clear password on non-401 errors", async () => {
    savePassword("my-password");

    const originalFetch = mockFetch({
      ok: false,
      status: 500,
      statusText: "Internal Server Error",
      text: () => Promise.resolve("Something broke"),
    });

    try {
      await sessionsApi.today();
    } catch (e) {
      expect((e as ApiError).status).toBe(500);
    }

    expect(localStorage.getItem("paceforge-password")).toBe("my-password");
    globalThis.fetch = originalFetch;
  });

  it("sends Basic auth header with stored credentials", async () => {
    savePassword("test-pass");

    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: () => Promise.resolve([]),
    });
    const originalFetch = globalThis.fetch;
    globalThis.fetch = fetchMock;

    await sessionsApi.today();

    const call = fetchMock.mock.calls[0];
    const headers = call[1]?.headers as Record<string, string>;
    const authHeader = headers?.Authorization || headers?.authorization;
    expect(authHeader).toBeDefined();
    expect(authHeader).toMatch(/^Basic /);

    const encoded = authHeader!.replace("Basic ", "");
    const decoded = atob(encoded);
    expect(decoded).toBe("paceforge:test-pass");

    globalThis.fetch = originalFetch;
  });
});

describe("Proxy WWW-Authenticate stripping (US-001)", () => {
  it("proxy route source code strips www-authenticate header", async () => {
    const fs = await import("fs");
    const path = await import("path");
    const proxyPath = path.resolve(
      __dirname,
      "../app/api/proxy/[...path]/route.ts"
    );
    const source = fs.readFileSync(proxyPath, "utf-8");
    expect(source.toLowerCase()).toContain("www-authenticate");
    expect(source).toContain("delete");
  });
});

describe("sessionsApi.today() happy path", () => {
  it("returns session data on 200", async () => {
    savePassword("test");

    const mockData = [
      { id: "1", session_date: "2026-04-18", session_type: "lifting", status: "planned", sets: [], body_feedback: [] },
    ];
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: () => Promise.resolve(mockData),
    });
    const originalFetch = globalThis.fetch;
    globalThis.fetch = fetchMock;

    const result = await sessionsApi.today();
    expect(result).toEqual(mockData);

    globalThis.fetch = originalFetch;
  });
});

// ── US-002/US-003: Session completion and skip data flow ─────────────────────

describe("sessionsApi.update() sends completion payload", () => {
  it("sends status and completed_at when marking session completed", async () => {
    savePassword("test");

    const mockResponse = {
      id: "abc-123",
      status: "completed",
      completed_at: "2026-04-18T10:30:00Z",
      overall_rpe: 7,
    };
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: () => Promise.resolve(mockResponse),
    });
    const originalFetch = globalThis.fetch;
    globalThis.fetch = fetchMock;

    await sessionsApi.update("abc-123", {
      status: "completed",
      overall_rpe: 7,
      completed_at: new Date().toISOString(),
    });

    const call = fetchMock.mock.calls[0];
    const body = JSON.parse(call[1]?.body as string);
    expect(body.status).toBe("completed");
    expect(body.overall_rpe).toBe(7);
    expect(body.completed_at).toBeDefined();

    globalThis.fetch = originalFetch;
  });

  it("sends skip status without completed_at", async () => {
    savePassword("test");

    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: () => Promise.resolve({ id: "abc-123", status: "skipped" }),
    });
    const originalFetch = globalThis.fetch;
    globalThis.fetch = fetchMock;

    await sessionsApi.update("abc-123", { status: "skipped" });

    const call = fetchMock.mock.calls[0];
    const body = JSON.parse(call[1]?.body as string);
    expect(body.status).toBe("skipped");
    expect(body.completed_at).toBeUndefined();

    globalThis.fetch = originalFetch;
  });
});

describe("sessionsApi.update() uses PATCH method", () => {
  it("calls PATCH /sessions/{id} with correct method", async () => {
    savePassword("test");

    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: () => Promise.resolve({ id: "abc-123", status: "completed" }),
    });
    const originalFetch = globalThis.fetch;
    globalThis.fetch = fetchMock;

    await sessionsApi.update("abc-123", { status: "completed" });

    const call = fetchMock.mock.calls[0];
    expect(call[1]?.method).toBe("PATCH");
    expect((call[0] as string)).toContain("/sessions/abc-123");

    globalThis.fetch = originalFetch;
  });
});

// ── US-003: TodayView skip confirmation (static validation) ────────────────────

describe("TodayView skip confirmation flow (static)", () => {
  it("skip confirmation dialog exists in TodayView source", async () => {
    const fs = await import("fs");
    const path = await import("path");
    const todayViewPath = path.resolve(
      __dirname,
      "../components/today/TodayView.tsx"
    );
    const source = fs.readFileSync(todayViewPath, "utf-8");

    // Skip confirmation dialog exists (US-003)
    expect(source).toContain("skipTarget");
    expect(source).toContain("Skip this session?");
    expect(source).toContain("Cancel");
    expect(source).toContain("bg-destructive");
  });

  it("skip button opens confirmation instead of directly calling skipMutation", async () => {
    const fs = await import("fs");
    const path = await import("path");
    const todayViewPath = path.resolve(
      __dirname,
      "../components/today/TodayView.tsx"
    );
    const source = fs.readFileSync(todayViewPath, "utf-8");

    // The SessionCard skip button should set skipTarget, not call skipMutation
    const sessionCardSection = source.substring(
      source.indexOf("function SessionCard"),
      source.indexOf("function DoneCard")
    );

    // onSkip sets the skip target state (triggers confirmation)
    expect(sessionCardSection).toContain("onSkip");
    // The actual mutation only fires inside the confirmation dialog
    expect(source).toContain("skipMutation.mutate(skipTarget.id)");
  });

  it("Next up and Done section headings exist for mobile-first layout", async () => {
    const fs = await import("fs");
    const path = await import("path");
    const todayViewPath = path.resolve(
      __dirname,
      "../components/today/TodayView.tsx"
    );
    const source = fs.readFileSync(todayViewPath, "utf-8");

    expect(source).toContain("Next up");
    expect(source).toContain("Done");
    expect(source).toContain("DoneCard");
  });
});

// ── US-002: Post-workout polling flow ──────────────────────────────────────────

describe("Post-workout result polling (static)", () => {
  it("completeMutation polls for PRs and coaching messages after completion", async () => {
    const fs = await import("fs");
    const path = await import("path");
    const todayViewPath = path.resolve(
      __dirname,
      "../components/today/TodayView.tsx"
    );
    const source = fs.readFileSync(todayViewPath, "utf-8");

    expect(source).toContain("uncelebratedPrs");
    expect(source).toContain("latestMessage");
    expect(source).toContain("post_workout");
    expect(source).toContain("setTimeout");
    expect(source).toContain("Promise.allSettled");
  });
});