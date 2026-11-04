import { fireEvent, render, screen } from "@testing-library/react";
import axe from "axe-core";
import { describe, expect, it, vi } from "vitest";
import { DataTableAdapter } from "@/shadlet/adapters/display";

describe("DataTableAdapter", () => {
  const props = {
    columns: [
      { key: "name", header: "name" },
      { key: "email", header: "email" },
    ],
    rows: [{ name: "Ruby", email: "ruby@example.com" }],
    serverSide: true,
    pageSize: 10,
    totalRows: 100,
    searchable: true,
    search: "",
    sorting: [],
    filters: {},
  };

  it("dispatches server-side searches as validated query events", () => {
    const dispatch = vi.fn();
    render(
      <DataTableAdapter
        props={{
          ...props,
        }}
        children={null}
        slots={{}}
        events={{ query_change: "query-event" }}
        dispatch={dispatch}
        navigate={() => {}}
        route="/"
        nodeId="table"
      />,
    );

    fireEvent.change(screen.getByRole("textbox", { name: "filter rows" }), {
      target: { value: "ruby" },
    });

    expect(dispatch).toHaveBeenCalledWith("query_change", {
      values: {
        page_index: 0,
        page_size: 10,
        sorting: [],
        search: "ruby",
        filters: {},
      },
    });
  });

  it("hides stale rows while loading and exposes an accessible status", () => {
    render(
      <DataTableAdapter
        props={{ ...props, loading: true }}
        children={null}
        slots={{}}
        events={{}}
        dispatch={() => {}}
        navigate={() => {}}
        route="/"
        nodeId="table"
      />,
    );

    expect(screen.getByRole("status")).toHaveTextContent("loading...");
    expect(
      screen.queryByRole("cell", { name: "Ruby" }),
    ).not.toBeInTheDocument();
  });

  it("shows a retry action for errors without rendering stale rows", () => {
    const dispatch = vi.fn();
    render(
      <DataTableAdapter
        props={{ ...props, error: "request failed" }}
        children={null}
        slots={{}}
        events={{ retry: "retry-event" }}
        dispatch={dispatch}
        navigate={() => {}}
        route="/"
        nodeId="table"
      />,
    );

    expect(screen.getByRole("alert")).toHaveTextContent("request failed");
    expect(
      screen.queryByRole("cell", { name: "Ruby" }),
    ).not.toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "retry" }));
    expect(dispatch).toHaveBeenCalledWith("retry", {});
  });

  it("allows column visibility to be changed with an accessible menu", () => {
    render(
      <DataTableAdapter
        props={props}
        children={null}
        slots={{}}
        events={{}}
        dispatch={() => {}}
        navigate={() => {}}
        route="/"
        nodeId="table"
      />,
    );

    fireEvent.click(
      screen.getByRole("button", { name: "choose visible columns" }),
    );
    fireEvent.click(screen.getByRole("menuitemcheckbox", { name: "email" }));

    expect(
      screen.queryByRole("columnheader", { name: "email" }),
    ).not.toBeInTheDocument();
  });

  it("supports row selection and dispatches stable keys", () => {
    const dispatch = vi.fn();
    render(
      <DataTableAdapter
        props={{
          ...props,
          rowKey: "id",
          selectedKeys: [],
          rows: [{ id: 8, name: "Ruby", email: "ruby@example.com" }],
        }}
        children={null}
        slots={{}}
        events={{ selection_change: "selection-event" }}
        dispatch={dispatch}
        navigate={() => {}}
        route="/"
        nodeId="table"
      />,
    );

    fireEvent.click(screen.getByRole("checkbox", { name: "select row 8" }));
    expect(dispatch).toHaveBeenCalledWith("selection_change", {
      values: { keys: ["8"] },
    });
  });

  it("makes clickable rows keyboard operable", () => {
    const dispatch = vi.fn();
    render(
      <DataTableAdapter
        props={{ ...props, rowKey: "id", rows: [{ id: 8, name: "Ruby" }] }}
        children={null}
        slots={{}}
        events={{ row_click: "row-event" }}
        dispatch={dispatch}
        navigate={() => {}}
        route="/"
        nodeId="table"
      />,
    );

    fireEvent.keyDown(screen.getByRole("row", { name: "row 8" }), {
      key: "Enter",
    });
    expect(dispatch).toHaveBeenCalledWith("row_click", {
      value: { id: 8, name: "Ruby" },
    });
  });

  it("has no automated wcag 2.1 a/aa violations in the table", async () => {
    render(
      <DataTableAdapter
        props={props}
        children={null}
        slots={{}}
        events={{}}
        dispatch={() => {}}
        navigate={() => {}}
        route="/"
        nodeId="table"
      />,
    );

    const results = await axe.run(screen.getByRole("table"), {
      runOnly: {
        type: "tag",
        values: ["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"],
      },
    });
    expect(results.violations).toEqual([]);
  });
});
