"""Incremental component tree patches."""

from __future__ import annotations

from shadlet.protocol.models import Node, Patch


def patch_path(node_id: str) -> str:
    if node_id == "r":
        return ""
    if node_id.startswith("r."):
        return node_id[2:]
    if node_id.startswith("r@"):
        return node_id[1:]
    return node_id


def _diff_children(old: Node, new: Node) -> list[Patch]:
    path = patch_path(new.id)
    if len(old.children) != len(new.children):
        return [Patch(op="set_children", path=path, children=new.children)]
    patches: list[Patch] = []
    for old_child, new_child in zip(old.children, new.children, strict=True):
        patches.extend(diff_nodes(old_child, new_child))
    return patches


def diff_nodes(old: Node, new: Node) -> list[Patch]:
    path = patch_path(new.id)
    if old.type != new.type or old.text != new.text:
        return [Patch(op="replace", path=path, node=new)]
    if old.type == "#text":
        return []
    patches: list[Patch] = []
    if old.props != new.props or old.events != new.events:
        patches.append(
            Patch(op="set_props", path=path, props=new.props, events=new.events)
        )
    if old.slots != new.slots:
        patches.append(Patch(op="set_slots", path=path, slots=new.slots))
    patches.extend(_diff_children(old, new))
    return patches


def diff_trees(old: Node | None, new: Node) -> list[Patch]:
    if old is None:
        return [Patch(op="replace", path="", node=new)]
    return diff_nodes(old, new)


__all__ = ["diff_nodes", "diff_trees", "patch_path"]
