import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { act } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { TreeRenderer } from "@/runtime/tree";

describe("Component Coverage and Accessibility Suite", () => {
  const dummyProps = {
    onEvent: () => {},
    navigate: () => {},
    route: "/",
  };

  it("renders Box fragment ids for native in-page navigation", () => {
    render(
      <TreeRenderer
        tree={{
          id: "pricing-section",
          type: "Box",
          props: { as: "section", id: "pricing" },
          children: [],
          events: {},
          slots: {},
          text: null,
        }}
        {...dummyProps}
      />,
    );
    expect(document.getElementById("pricing")?.tagName).toBe("SECTION");
  });

  it("renders Marker as semantic highlighted text", () => {
    render(
      <TreeRenderer
        tree={{
          id: "marker-1",
          type: "Marker",
          props: {},
          children: [
            {
              id: "marker-text",
              type: "#text",
              props: {},
              children: [],
              events: {},
              slots: {},
              text: "match",
            },
          ],
          events: {},
          slots: {},
          text: null,
        }}
        {...dummyProps}
      />,
    );
    expect(screen.getByText("match").tagName).toBe("MARK");
  });

  it("renders CodeBlock lines and line numbers accessibly", () => {
    render(
      <TreeRenderer
        tree={{
          id: "code-1",
          type: "CodeBlock",
          props: {
            code: "first\nsecond",
            title: "sample.py",
            lineNumbers: true,
            copyButton: false,
          },
          children: [],
          events: {},
          slots: {},
          text: null,
        }}
        {...dummyProps}
      />,
    );
    expect(screen.getByText("sample.py")).toBeInTheDocument();
    expect(screen.getByText("first")).toBeInTheDocument();
    expect(screen.getByText("second")).toBeInTheDocument();
    expect(screen.getByRole("code").closest("pre")).toHaveAttribute(
      "tabindex",
      "0",
    );
  });

  it("copies code and announces completion", async () => {
    Object.defineProperty(navigator, "clipboard", {
      configurable: true,
      value: { writeText: vi.fn().mockResolvedValue(undefined) },
    });
    render(
      <TreeRenderer
        tree={{
          id: "copy-code",
          type: "CodeBlock",
          props: { code: "copy me", title: "snippet" },
          children: [],
          events: {},
          slots: {},
          text: null,
        }}
        {...dummyProps}
      />,
    );
    fireEvent.click(screen.getByRole("button", { name: "Copy code" }));
    await waitFor(() =>
      expect(navigator.clipboard.writeText).toHaveBeenCalledWith("copy me"),
    );
    expect(
      await screen.findByText("Code copied to clipboard"),
    ).toBeInTheDocument();
  });

  it("returns the copy control to its ready state", async () => {
    vi.useFakeTimers();
    Object.defineProperty(navigator, "clipboard", {
      configurable: true,
      value: { writeText: vi.fn().mockResolvedValue(undefined) },
    });
    try {
      render(
        <TreeRenderer
          tree={{
            id: "copy-reset",
            type: "CodeBlock",
            props: { code: "copy me" },
            children: [],
            events: {},
            slots: {},
            text: null,
          }}
          {...dummyProps}
        />,
      );
      fireEvent.click(screen.getByRole("button", { name: "Copy code" }));
      await act(async () => {
        await Promise.resolve();
      });
      expect(
        screen.getByRole("button", { name: "Copied code" }),
      ).toBeInTheDocument();
      act(() => vi.advanceTimersByTime(1500));
      expect(
        screen.getByRole("button", { name: "Copy code" }),
      ).toBeInTheDocument();
    } finally {
      vi.useRealTimers();
    }
  });

  it("renders typography components with correct semantics", () => {
    const { unmount } = render(
      <TreeRenderer
        tree={{
          id: "t1",
          type: "Heading",
          props: { level: 2 },
          children: [
            {
              id: "t1-text",
              type: "#text",
              props: {},
              children: [],
              events: {},
              slots: {},
              text: "Section Header",
            },
          ],
          events: {},
          slots: {},
          text: null,
        }}
        {...dummyProps}
      />,
    );
    const heading = screen.getByRole("heading", { level: 2 });
    expect(heading).toBeInTheDocument();
    expect(heading).toHaveTextContent("Section Header");
    unmount();

    render(
      <TreeRenderer
        tree={{
          id: "t2",
          type: "Text",
          props: {},
          children: [
            {
              id: "t2-text",
              type: "#text",
              props: {},
              children: [],
              events: {},
              slots: {},
              text: "Regular Paragraph",
            },
          ],
          events: {},
          slots: {},
          text: null,
        }}
        {...dummyProps}
      />,
    );
    expect(screen.getByText("Regular Paragraph")).toBeInTheDocument();
  });

  it("renders interactive Form components with accessible roles", () => {
    const { unmount } = render(
      <TreeRenderer
        tree={{
          id: "btn-1",
          type: "Button",
          props: { variant: "outline", disabled: false },
          children: [
            {
              id: "btn-text",
              type: "#text",
              props: {},
              children: [],
              events: {},
              slots: {},
              text: "Submit Action",
            },
          ],
          events: { click: "e1" },
          slots: {},
          text: null,
        }}
        {...dummyProps}
      />,
    );
    const button = screen.getByRole("button", { name: "Submit Action" });
    expect(button).toBeInTheDocument();
    expect(button).not.toBeDisabled();
    unmount();

    render(
      <TreeRenderer
        tree={{
          id: "in-1",
          type: "Input",
          props: { placeholder: "Enter email address", type: "email" },
          children: [],
          events: {},
          slots: {},
          text: null,
        }}
        {...dummyProps}
      />,
    );
    const input = screen.getByPlaceholderText("Enter email address");
    expect(input).toBeInTheDocument();
  });

  it("renders display components (Badge, Alert, Card) properly", () => {
    const { unmount } = render(
      <TreeRenderer
        tree={{
          id: "alert-1",
          type: "Alert",
          props: {
            title: "System Notification",
            description: "All systems nominal",
          },
          children: [],
          events: {},
          slots: {},
          text: null,
        }}
        {...dummyProps}
      />,
    );
    expect(screen.getByText("System Notification")).toBeInTheDocument();
    expect(screen.getByText("All systems nominal")).toBeInTheDocument();
    unmount();

    render(
      <TreeRenderer
        tree={{
          id: "badge-1",
          type: "Badge",
          props: { variant: "secondary" },
          children: [
            {
              id: "badge-text",
              type: "#text",
              props: {},
              children: [],
              events: {},
              slots: {},
              text: "Verified",
            },
          ],
          events: {},
          slots: {},
          text: null,
        }}
        {...dummyProps}
      />,
    );
    expect(screen.getByText("Verified")).toBeInTheDocument();
  });

  it("renders layout and feedback primitives (Progress, Spinner, Separator)", () => {
    const { unmount } = render(
      <TreeRenderer
        tree={{
          id: "p1",
          type: "Progress",
          props: { value: 65, max: 100 },
          children: [],
          events: {},
          slots: {},
          text: null,
        }}
        {...dummyProps}
      />,
    );
    expect(screen.getByRole("progressbar")).toBeInTheDocument();
    unmount();

    render(
      <TreeRenderer
        tree={{
          id: "sp1",
          type: "Spinner",
          props: { label: "Loading content" },
          children: [],
          events: {},
          slots: {},
          text: null,
        }}
        {...dummyProps}
      />,
    );
    expect(
      screen.getByRole("status", { name: "Loading content" }),
    ).toBeInTheDocument();
  });
});
