import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { TreeRenderer } from "@/runtime/tree";
import { getBuiltinComponentNames } from "@/runtime/registry";
import { ThemeProvider } from "@/themes/provider";

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

  it("renders every registered adapter without an unknown-component fallback", () => {
    const names = getBuiltinComponentNames();
    const propsByName: Record<string, Record<string, unknown>> = {
      Icon: { name: "check" },
      Spinner: { label: "Loading" },
      Progress: { value: 25 },
      Input: { ariaLabel: "Input" },
      Textarea: { ariaLabel: "Textarea" },
      Checkbox: { ariaLabel: "Checkbox" },
      Switch: { ariaLabel: "Switch" },
      Slider: { ariaLabel: "Slider" },
      Select: { ariaLabel: "Select", options: [] },
      NativeSelect: { ariaLabel: "Native select", options: [] },
      RadioGroup: { ariaLabel: "Radio group", options: [] },
      Combobox: { ariaLabel: "Combobox", options: [] },
      InputOTP: { ariaLabel: "One-time code", maxLength: 4 },
      DataTable: { columns: [], rows: [] },
      Chart: { data: [], series: [] },
      CodeBlock: { code: "example", copyButton: false },
      Resizable: {},
    };
    for (const [index, name] of names.entries()) {
      const { container, unmount } = render(
        <ThemeProvider>
          <TreeRenderer
            tree={{
              id: `smoke-${index}`,
              type: name,
              props: propsByName[name] ?? {},
              children:
                name === "Resizable"
                  ? [
                      {
                        id: "panel",
                        type: "#text",
                        props: {},
                        children: [],
                        events: {},
                        slots: {},
                        text: "panel",
                      },
                    ]
                  : [],
              events: {},
              slots: {},
              text: null,
            }}
            onEvent={() => {}}
            navigate={() => {}}
            route="/"
          />
        </ThemeProvider>,
      );
      const errorBoundary = container.querySelector(".shadlet-error");
      expect(
        errorBoundary,
        `${name} hit an error boundary: ${errorBoundary?.textContent}`,
      ).toBeNull();
      unmount();
    }
  });
});
