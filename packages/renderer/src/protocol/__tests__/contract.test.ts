import { describe, expect, it } from "vitest";
import fixtures from "../fixtures.json";
import { parseClientMessage, parseServerMessage } from "../schema";

describe("protocol contract fixtures", () => {
  it("accepts every server fixture", () => {
    for (const fixture of fixtures.server) {
      expect(
        () => parseServerMessage(fixture.value),
        `server fixture ${fixture.name}`,
      ).not.toThrow();
    }
  });

  it("accepts every client fixture", () => {
    for (const fixture of fixtures.client) {
      expect(
        () => parseClientMessage(fixture.value),
        `client fixture ${fixture.name}`,
      ).not.toThrow();
    }
  });

  it("rejects removed desktop messages", () => {
    expect(() =>
      parseClientMessage({
        type: "desktop_result",
        id: "x",
        ok: true,
      }),
    ).toThrow();
    expect(() =>
      parseServerMessage({
        type: "desktop_request",
        id: "x",
        method: "notify",
      }),
    ).toThrow();
    expect(() => parseServerMessage({ type: "reload" })).toThrow();
  });
});
describe("node validation", () => {
  it("rejects text on an element node", () => {
    expect(() =>
      parseServerMessage({
        type: "navigation",
        seq: 1,
        route: { path: "/", title: "home" },
        tree: {
          id: "r",
          type: "Text",
          props: {},
          children: [],
          events: {},
          slots: {},
          text: "unexpected",
        },
        state: {},
      }),
    ).toThrow();
  });
});
