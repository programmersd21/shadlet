"""Versioned JSON wire models for the shadlet protocol.

The models in this module are the single source of truth for both peers. The
TypeScript renderer validates the same structures with zod in
``packages/renderer/src/protocol/schema.ts``.
"""

from __future__ import annotations

from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, JsonValue, model_validator

from shadlet.protocol.version import PROTOCOL_VERSION


class WireModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Node(WireModel):
    """A component node or a text node.

    Text nodes use ``type == "#text"`` and carry ``text``. Element nodes carry
    props, children, event identifiers and optional named slots. Callbacks are
    never present on the wire; ``events`` maps an event name to an opaque id.
    """

    id: str = Field(min_length=1)
    type: str = Field(min_length=1)
    props: dict[str, JsonValue] = Field(default_factory=dict)
    children: list[Node] = Field(default_factory=list)
    events: dict[str, str] = Field(default_factory=dict)
    slots: dict[str, list[Node]] = Field(default_factory=dict)
    text: str | None = None

    @model_validator(mode="after")
    def _validate_text_node(self) -> Node:
        if self.type == "#text":
            if self.text is None:
                raise ValueError("text nodes require a text value")
            if self.children or self.props or self.events or self.slots:
                raise ValueError(
                    "text nodes cannot carry props, children, events or slots"
                )
        elif self.text is not None:
            raise ValueError("element nodes cannot carry text")
        return self


class RouteInfo(WireModel):
    path: str
    title: str


class AppInfo(WireModel):
    title: str
    version: str
    theme: Literal["light", "dark", "system"] = "system"
    platform: Literal["web"] = "web"
    icon: str | None = None


class Patch(WireModel):
    op: Literal["replace", "set_props", "set_children", "set_slots", "insert", "remove"]
    path: str
    node: Node | None = None
    props: dict[str, JsonValue] | None = None
    events: dict[str, str] | None = None
    children: list[Node] | None = None
    slots: dict[str, list[Node]] | None = None
    index: int | None = None

    @model_validator(mode="after")
    def _validate_operation(self) -> Patch:
        required: dict[str, tuple[str, ...]] = {
            "replace": ("node",),
            "set_props": ("props", "events"),
            "set_children": ("children",),
            "set_slots": ("slots",),
            "insert": ("node", "index"),
            "remove": ("index",),
        }
        for field in required[self.op]:
            if getattr(self, field) is None:
                raise ValueError(f"patch op {self.op!r} requires {field!r}")
        if self.index is not None and self.index < 0:
            raise ValueError("patch index must be non-negative")
        return self


class StatePatch(WireModel):
    op: Literal["set", "delete"]
    key: str
    value: JsonValue = None


# ---------------------------------------------------------------------------
# Server -> client
# ---------------------------------------------------------------------------


class InitMessage(WireModel):
    type: Literal["init"] = "init"
    protocol: int = PROTOCOL_VERSION
    app: AppInfo
    route: RouteInfo
    routes: list[RouteInfo]
    tree: Node
    state: dict[str, JsonValue] = Field(default_factory=dict)
    features: list[str] = Field(default_factory=list)
    session_token: str | None = None


class UpdateMessage(WireModel):
    type: Literal["update"] = "update"
    seq: int
    request_id: str | None = None
    patches: list[Patch] = Field(default_factory=list)
    state_patches: list[StatePatch] = Field(default_factory=list)


class NavigationMessage(WireModel):
    type: Literal["navigation"] = "navigation"
    seq: int
    route: RouteInfo
    tree: Node
    state: dict[str, JsonValue] = Field(default_factory=dict)


class ToastMessage(WireModel):
    type: Literal["toast"] = "toast"
    level: Literal["default", "success", "error", "warning", "info"] = "default"
    message: str
    description: str | None = None
    duration: int | None = None


class ErrorMessage(WireModel):
    type: Literal["error"] = "error"
    code: str
    message: str
    request_id: str | None = None
    details: str | None = None
    fatal: bool = False


class PongMessage(WireModel):
    type: Literal["pong"] = "pong"
    seq: int


class ReloadMessage(WireModel):
    type: Literal["reload"] = "reload"
    reason: str | None = None


ServerMessage = Annotated[
    InitMessage
    | UpdateMessage
    | NavigationMessage
    | ToastMessage
    | ErrorMessage
    | PongMessage
    | ReloadMessage,
    Field(discriminator="type"),
]


# ---------------------------------------------------------------------------
# Client -> server
# ---------------------------------------------------------------------------


class HelloMessage(WireModel):
    type: Literal["hello"] = "hello"
    protocol_min: int
    protocol_max: int
    path: str = "/"
    token: str | None = None
    platform: Literal["web"] = "web"
    icon: str | None = None


class EventMessage(WireModel):
    type: Literal["event"] = "event"
    seq: int
    event_id: str = Field(min_length=1, max_length=128)
    request_id: str | None = None
    payload: dict[str, JsonValue] = Field(default_factory=dict)


class NavigateMessage(WireModel):
    type: Literal["navigate"] = "navigate"
    seq: int
    path: str = Field(min_length=1, max_length=2048)


class PingMessage(WireModel):
    type: Literal["ping"] = "ping"
    seq: int


ClientMessage = Annotated[
    HelloMessage | EventMessage | NavigateMessage | PingMessage,
    Field(discriminator="type"),
]


class ProtocolEnvelope(WireModel):
    """Validation helper used by tests and tooling."""

    protocol: int = PROTOCOL_VERSION
    message: ServerMessage | ClientMessage
