import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { TreeRenderer } from "@/runtime/tree";

describe("renderer smoke", () => {
  it("renders a component tree", () => {
    render(
      <TreeRenderer
        tree={{
          id: "r",
          type: "Card",
          props: { title: "hello", description: "world" },
          children: [],
          events: {},
          slots: {},
          text: null,
        }}
        onEvent={() => {}}
        navigate={() => {}}
        route="/"
      />,
    );
    expect(screen.getByText("hello")).toBeInTheDocument();
  });
});
