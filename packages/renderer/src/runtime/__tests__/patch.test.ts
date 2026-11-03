import { describe, expect, it } from "vitest";
import type { ShadletNode } from "@/protocol/schema";
import { applyPatches } from "@/runtime/patch";

function node(
  id: string,
  type = "Text",
  children: ShadletNode[] = [],
): ShadletNode {
  return {
    id,
    type,
    props: {},
    children,
    events: {},
    slots: {},
    text: type === "#text" ? "x" : null,
  };
}

describe("applyPatches", () => {
  it("applies nested prop updates", () => {
    const tree = node("r", "Column", [node("r.0")]);
    const next = applyPatches(tree, [
      { op: "set_props", path: "0", props: { text: "hi" }, events: {} },
    ]);
    expect(next.children[0].props).toEqual({ text: "hi" });
    expect(tree.children[0].props).toEqual({});
  });

  it("rejects out-of-range insert indices", () => {
    const tree = node("r", "Column", [node("r.0")]);
    expect(() =>
      applyPatches(tree, [
        { op: "insert", path: "", node: node("new"), index: 5 },
      ]),
    ).toThrow(/out of range/);
  });

  it("rejects out-of-range remove indices", () => {
    const tree = node("r", "Column", [node("r.0")]);
    expect(() =>
      applyPatches(tree, [{ op: "remove", path: "", index: 3 }]),
    ).toThrow(/out of range/);
  });

  it("rejects invalid child paths", () => {
    const tree = node("r", "Column", [node("r.0")]);
    expect(() =>
      applyPatches(tree, [{ op: "replace", path: "9", node: node("r.9") }]),
    ).toThrow(/invalid patch path/);
  });

  it("inserts and removes at the edges", () => {
    const tree = node("r", "Column", [node("r.0"), node("r.1")]);
    const inserted = applyPatches(tree, [
      { op: "insert", path: "", node: node("r.2"), index: 2 },
    ]);
    expect(inserted.children).toHaveLength(3);
    const removed = applyPatches(inserted, [
      { op: "remove", path: "", index: 0 },
    ]);
    expect(removed.children.map((child) => child.id)).toEqual(["r.1", "r.2"]);
  });
});
