import { describe, expect, it } from "vitest";
import {
  getComponentAdapter,
  registerExtensionComponents,
} from "@/runtime/registry";
import { isExtensionLoaded, loadExtension } from "@/extensions";
import type { AdapterProps } from "@/shadlet/types";
import type * as React from "react";

const DemoAdapter: React.ComponentType<AdapterProps> = () => null;

describe("extension component registration", () => {
  it("uses a namespace and supports deterministic cleanup", () => {
    const cleanup = registerExtensionComponents("sample", {
      Demo: DemoAdapter,
    });

    expect(getComponentAdapter("sample:Demo")).toBe(DemoAdapter);
    const cleanupOther = registerExtensionComponents("sample", {
      Other: DemoAdapter,
    });

    cleanup();
    cleanupOther();
    expect(getComponentAdapter("sample:Demo")).toBeUndefined();
  });

  it("preserves built-ins and rejects duplicate or invalid component names", () => {
    const builtin = getComponentAdapter("Button");
    const buttonCleanup = registerExtensionComponents("sample", {
      Button: DemoAdapter,
    });
    expect(getComponentAdapter("Button")).toBe(builtin);
    expect(getComponentAdapter("sample:Button")).toBe(DemoAdapter);
    buttonCleanup();
    const cleanup = registerExtensionComponents("sample", {
      Demo: DemoAdapter,
    });
    expect(() =>
      registerExtensionComponents("sample", { Demo: DemoAdapter }),
    ).toThrow(/already registered/);
    cleanup();
    expect(() =>
      registerExtensionComponents("sample", { "bad-name": DemoAdapter }),
    ).toThrow(/invalid extension component name/);
  });

  it("validates extension metadata and cleans up registered styles", () => {
    expect(() =>
      loadExtension({
        name: "sample",
        version: "latest",
        components: { Demo: DemoAdapter },
      }),
    ).toThrow(/invalid extension version/);

    const dispose = loadExtension({
      name: "sample",
      version: "1.0.0",
      components: { Demo: DemoAdapter },
      styles: ".sample { color: red; }",
    });
    expect(isExtensionLoaded("sample")).toBe(true);
    expect(
      document.querySelectorAll("style[data-shadlet-extension='sample']"),
    ).toHaveLength(1);
    expect(() =>
      loadExtension({
        name: "sample",
        version: "1.0.0",
        components: { Other: DemoAdapter },
      }),
    ).toThrow(/already loaded/);

    dispose();
    expect(isExtensionLoaded("sample")).toBe(false);
    expect(getComponentAdapter("sample:Demo")).toBeUndefined();
    expect(
      document.querySelector("style[data-shadlet-extension='sample']"),
    ).toBeNull();
  });
});
