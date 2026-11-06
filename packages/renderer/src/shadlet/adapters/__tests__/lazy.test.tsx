import { render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import type { ShadletNode } from "@/protocol/schema";
import { TreeRenderer } from "@/runtime/tree";
import { ThemeProvider } from "@/themes/provider";

type TestNode = {
  id: string;
  type: string;
  props: Record<string, unknown>;
  children: TestNode[];
  events: Record<string, string>;
  slots: Record<string, unknown>;
  text: string | null;
};

function node(type: string, props: Record<string, unknown> = {}): TestNode {
  return {
    id: `lazy-${type.toLowerCase()}`,
    type,
    props,
    children: [],
    events: {},
    slots: {},
    text: null,
  };
}

function renderNode(tree: TestNode) {
  return render(
    <ThemeProvider>
      <TreeRenderer
        tree={tree as unknown as ShadletNode}
        onEvent={() => {}}
        navigate={() => {}}
        route="/"
      />
    </ThemeProvider>,
  );
}

describe("lazy component adapters", () => {
  it("shows a loading placeholder then renders the chart chunk", async () => {
    const { container } = renderNode(
      node("Chart", {
        data: [{ name: "a", value: 3 }],
        series: [{ key: "value", label: "Value" }],
      }),
    );

    expect(container.querySelector(".shadlet-loading")).not.toBeNull();
    await waitFor(
      () => {
        expect(container.querySelector('[data-slot="chart"]')).not.toBeNull();
      },
      { timeout: 5_000 },
    );
    expect(container.querySelector(".shadlet-loading")).toBeNull();
  });

  it("lazy-loads the calendar chunk", async () => {
    const { container } = renderNode(node("Calendar", { mode: "single" }));

    expect(container.querySelector(".shadlet-loading")).not.toBeNull();
    await waitFor(
      () => {
        expect(
          container.querySelector('[data-slot="calendar"]'),
        ).not.toBeNull();
      },
      { timeout: 5_000 },
    );
  });

  it("lazy-loads the date picker from the calendar chunk", async () => {
    renderNode(node("DatePicker", {}));

    expect(await screen.findByText("pick a date")).toBeInTheDocument();
  });

  it("lazy-loads the carousel chunk", async () => {
    const { container } = renderNode(node("Carousel", {}));

    expect(container.querySelector(".shadlet-loading")).not.toBeNull();
    await waitFor(() => {
      expect(container.querySelector('[data-slot="carousel"]')).not.toBeNull();
    });
  });
});
