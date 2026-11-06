import { render, screen, waitFor } from "@testing-library/react";
import { toast } from "sonner";
import { afterEach, describe, expect, it, vi } from "vitest";
import type { ShadletNode } from "@/protocol/schema";
import { TreeRenderer } from "@/runtime/tree";

function renderTree(tree: ShadletNode) {
  return render(
    <TreeRenderer
      tree={tree}
      onEvent={() => {}}
      navigate={() => {}}
      route="/"
    />,
  );
}

afterEach(() => {
  vi.restoreAllMocks();
});

describe("direction and toast adapters", () => {
  it("applies the requested text direction to its children", () => {
    const tree = {
      id: "direction",
      type: "Direction",
      props: { dir: "rtl" },
      children: [
        {
          id: "text",
          type: "#text",
          props: {},
          children: [],
          events: {},
          slots: {},
          text: "مرحبا",
        },
      ],
      events: {},
      slots: {},
      text: null,
    } as unknown as ShadletNode;

    const { container } = renderTree(tree);
    const wrapper = container.querySelector('[data-slot="direction"]');
    expect(wrapper).not.toBeNull();
    expect(wrapper?.getAttribute("dir")).toBe("rtl");
    expect(screen.getByText("مرحبا")).toBeInTheDocument();
  });

  it("shows a declarative toast through sonner", async () => {
    const success = vi.spyOn(toast, "success");
    const tree = {
      id: "toast",
      type: "Toast",
      props: {
        title: "Saved",
        description: "changes stored",
        level: "success",
        duration: 2000,
      },
      children: [],
      events: {},
      slots: {},
      text: null,
    } as unknown as ShadletNode;

    renderTree(tree);
    await waitFor(() => {
      expect(success).toHaveBeenCalledWith(
        "Saved",
        expect.objectContaining({
          description: "changes stored",
          duration: 2000,
        }),
      );
    });
  });
});
