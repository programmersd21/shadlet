import type { ShadletNode, ShadletPatch } from "@/protocol/schema";

function splitPath(path: string): string[] {
  return path === "" ? [] : path.split(".");
}

function updateAtPath(
  node: ShadletNode,
  segments: string[],
  updater: (node: ShadletNode) => ShadletNode,
): ShadletNode {
  if (segments.length === 0) return updater(node);
  const [head, ...rest] = segments;

  if (head.startsWith("@")) {
    const slot = head.slice(1);
    const items = node.slots[slot] ?? [];
    const index = Number(rest[0]);
    if (!Number.isInteger(index) || index < 0 || index >= items.length) {
      throw new Error(`invalid patch path in slot ${slot}: ${rest[0]}`);
    }
    const nextItems = [...items];
    nextItems[index] = updateAtPath(items[index], rest.slice(1), updater);
    return { ...node, slots: { ...node.slots, [slot]: nextItems } };
  }

  const index = Number(head);
  if (!Number.isInteger(index) || index < 0 || index >= node.children.length) {
    throw new Error(`invalid patch path: ${segments.join(".")}`);
  }
  const nextChildren = [...node.children];
  nextChildren[index] = updateAtPath(node.children[index], rest, updater);
  return { ...node, children: nextChildren };
}

function nodeAtPath(node: ShadletNode, segments: string[]): ShadletNode {
  let current = node;
  for (const segment of segments) {
    if (segment.startsWith("@")) {
      const slot = segment.slice(1);
      throw new Error(`cannot address slot container directly: ${slot}`);
    }
    const index = Number(segment);
    if (
      !Number.isInteger(index) ||
      index < 0 ||
      index >= current.children.length
    ) {
      throw new Error(`invalid patch path segment: ${segment}`);
    }
    current = current.children[index];
  }
  return current;
}

export function applyPatch(
  tree: ShadletNode,
  patch: ShadletPatch,
): ShadletNode {
  const segments = splitPath(patch.path);

  if (patch.op === "replace") {
    if (!patch.node) throw new Error("replace patch requires a node");
    return updateAtPath(tree, segments, () => patch.node!);
  }

  if (patch.op === "set_props") {
    return updateAtPath(tree, segments, (node) => ({
      ...node,
      props: patch.props ?? {},
      events: patch.events ?? {},
    }));
  }

  if (patch.op === "set_children") {
    return updateAtPath(tree, segments, (node) => ({
      ...node,
      children: patch.children ?? [],
    }));
  }

  if (patch.op === "set_slots") {
    return updateAtPath(tree, segments, (node) => ({
      ...node,
      slots: patch.slots ?? {},
    }));
  }

  if (patch.op === "insert") {
    if (!patch.node || patch.index == null) {
      throw new Error("insert patch requires node and index");
    }
    return updateAtPath(tree, segments, (node) => {
      const children = [...node.children];
      children.splice(patch.index!, 0, patch.node!);
      return { ...node, children };
    });
  }

  if (patch.op === "remove") {
    if (patch.index == null) throw new Error("remove patch requires index");
    return updateAtPath(tree, segments, (node) => {
      const children = [...node.children];
      children.splice(patch.index!, 1);
      return { ...node, children };
    });
  }

  return tree;
}

export function applyPatches(
  tree: ShadletNode,
  patches: ShadletPatch[],
): ShadletNode {
  return patches.reduce(applyPatch, tree);
}

export function nodeAt(tree: ShadletNode, path: string): ShadletNode {
  return nodeAtPath(tree, splitPath(path));
}
