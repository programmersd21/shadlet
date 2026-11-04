"""Display, data and feedback components."""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from typing import Any, Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    ValidationError,
    field_validator,
    model_validator,
)
from pydantic import (
    Field as PydanticField,
)

from shadlet.components.base import Child, Component, ComponentError, validate_choice
from shadlet.components.enums import (
    AlertVariant,
    BadgeVariant,
    ChartKind,
    Orientation,
    ToggleSize,
    ToggleVariant,
)
from shadlet.components.options import (
    AccordionItem,
    ChartSeries,
    TableColumn,
)
from shadlet.events.types import Event
from shadlet.layout.values import Length, css_length


class DataTableSort(BaseModel):
    """One validated server-side table sort key."""

    model_config = ConfigDict(extra="forbid", strict=True)

    key: str = PydanticField(min_length=1, max_length=128)
    direction: Literal["asc", "desc"]


class DataTableQuery(BaseModel):
    """Validated server-side table query delivered to a query handler."""

    model_config = ConfigDict(extra="forbid", strict=True)

    page_index: int = PydanticField(ge=0)
    page_size: int = PydanticField(ge=1, le=500)
    sorting: list[DataTableSort] = PydanticField(default_factory=list, max_length=8)
    search: str = PydanticField(default="", max_length=256)
    filters: dict[str, str] = PydanticField(default_factory=dict, max_length=32)

    @field_validator("filters")
    @classmethod
    def validate_filter_lengths(cls, filters: dict[str, str]) -> dict[str, str]:
        if any(len(key) > 128 or len(value) > 256 for key, value in filters.items()):
            raise ValueError("filter keys and values exceed the maximum length")
        return filters

    @model_validator(mode="after")
    def validate_unique_sort_keys(self) -> DataTableQuery:
        keys = [item.key for item in self.sorting]
        if len(keys) != len(set(keys)):
            raise ValueError("sorting keys must be unique")
        return self


DataTableQueryHandler = Callable[[DataTableQuery], Any]


def normalize_table_columns(
    columns: Sequence[TableColumn | Mapping[str, Any]],
) -> list[dict[str, Any]]:
    if not isinstance(columns, Sequence) or isinstance(columns, (str, bytes)):
        raise ComponentError("columns must be a sequence")
    result: list[dict[str, Any]] = []
    seen: set[str] = set()
    for index, column in enumerate(columns):
        key: str
        header: str
        align: str = "left"
        width: int | str | None = None
        sortable: bool = False
        filterable: bool = False
        if isinstance(column, TableColumn):
            key = column.key
            header = column.header
            align = column.align
            width = column.width
            sortable = column.sortable
            filterable = column.filterable
        elif isinstance(column, Mapping):
            try:
                key = str(column["key"])
                header = str(column["header"])
            except KeyError as error:
                raise ComponentError(
                    f"column {index} requires key and header"
                ) from error
            align = str(column.get("align", "left"))
            width = column.get("width")
            sortable = bool(column.get("sortable", False))
            filterable = bool(column.get("filterable", False))
        else:
            raise ComponentError(f"column {index} must be TableColumn or mapping")
        if not key or not header:
            raise ComponentError(f"column {index} requires non-empty key and header")
        validate_choice(
            align,
            ("left", "center", "right"),
            argument=f"columns[{index}].align",
        )
        if key in seen:
            raise ComponentError(f"duplicate column key {key!r}")
        seen.add(key)
        result.append(
            {
                "key": key,
                "header": header,
                "align": align,
                "width": width,
                "sortable": sortable,
                "filterable": filterable,
            }
        )
    return result


def normalize_series(
    series: Sequence[ChartSeries | Mapping[str, Any]],
) -> list[dict[str, Any]]:
    if (
        not isinstance(series, Sequence)
        or isinstance(series, (str, bytes))
        or not series
    ):
        raise ComponentError("series must be a non-empty sequence")
    result: list[dict[str, Any]] = []
    seen: set[str] = set()
    for index, item in enumerate(series):
        if isinstance(item, ChartSeries):
            key, label, color = item.key, item.label, item.color
        elif isinstance(item, Mapping):
            key = str(item.get("key", ""))
            label = str(item.get("label", key))
            color = item.get("color")
        else:
            raise ComponentError(f"series {index} must be ChartSeries or mapping")
        if not key:
            raise ComponentError(f"series {index} requires a key")
        if key in seen:
            raise ComponentError(f"duplicate series key {key!r}")
        seen.add(key)
        result.append({"key": key, "label": label, "color": color})
    return result


class Badge(Component):
    type = "Badge"

    def __init__(
        self,
        *children: Child | Sequence[Child],
        variant: BadgeVariant | str = BadgeVariant.DEFAULT,
        class_name: str | None = None,
    ) -> None:
        validate_choice(variant, tuple(BadgeVariant), argument="variant")
        super().__init__(*children, variant=str(variant), class_name=class_name)


class Card(Component):
    type = "Card"

    def __init__(
        self,
        *children: Child | Sequence[Child],
        title: str | None = None,
        description: str | None = None,
        action: Child | Sequence[Child] | None = None,
        footer: Child | Sequence[Child] | None = None,
        class_name: str | None = None,
        **kwargs: Any,
    ) -> None:
        all_children = list(children)
        if "children" in kwargs:
            extra = kwargs.pop("children")
            if extra is not None:
                if isinstance(extra, (list, tuple)):
                    all_children.extend(extra)
                else:
                    all_children.append(extra)
        super().__init__(
            *all_children,
            title=title,
            description=description,
            class_name=class_name,
            **kwargs,
        )
        self.add_slot("action", action)
        self.add_slot("footer", footer)


class Avatar(Component):
    type = "Avatar"

    def __init__(
        self,
        *,
        src: str | None = None,
        alt: str = "",
        fallback: str | None = None,
        size: str = "default",
        class_name: str | None = None,
    ) -> None:
        validate_choice(size, ("sm", "default", "lg"), argument="size")
        if src is not None and not isinstance(src, str):
            raise ComponentError("src must be a string")
        super().__init__(
            src=src,
            alt=alt,
            fallback=fallback,
            size=size,
            class_name=class_name,
        )


class AspectRatio(Component):
    type = "AspectRatio"

    def __init__(
        self,
        *children: Child | Sequence[Child],
        ratio: float = 16 / 9,
        class_name: str | None = None,
    ) -> None:
        if isinstance(ratio, bool) or not isinstance(ratio, (int, float)) or ratio <= 0:
            raise ComponentError("ratio must be a positive number")
        super().__init__(*children, ratio=float(ratio), class_name=class_name)


class Alert(Component):
    type = "Alert"

    def __init__(
        self,
        *children: Child | Sequence[Child],
        title: str | None = None,
        description: str | None = None,
        variant: AlertVariant | str = AlertVariant.DEFAULT,
        icon: str | None = None,
        class_name: str | None = None,
    ) -> None:
        validate_choice(variant, tuple(AlertVariant), argument="variant")
        super().__init__(
            *children,
            title=title,
            description=description,
            variant=str(variant),
            icon=icon,
            class_name=class_name,
        )


class Empty(Component):
    type = "Empty"

    def __init__(
        self,
        *children: Child | Sequence[Child],
        title: str | None = None,
        description: str | None = None,
        icon: str | None = None,
        action: Child | Sequence[Child] | None = None,
        class_name: str | None = None,
    ) -> None:
        super().__init__(
            *children,
            title=title,
            description=description,
            icon=icon,
            class_name=class_name,
        )
        self.add_slot("action", action)


class Item(Component):
    type = "Item"

    def __init__(
        self,
        *children: Child | Sequence[Child],
        title: str | None = None,
        description: str | None = None,
        media: Child | Sequence[Child] | None = None,
        actions: Child | Sequence[Child] | None = None,
        class_name: str | None = None,
    ) -> None:
        super().__init__(
            *children,
            title=title,
            description=description,
            class_name=class_name,
        )
        self.add_slot("media", media)
        self.add_slot("actions", actions)


class Separator(Component):
    type = "Separator"

    def __init__(
        self,
        *,
        orientation: Orientation | str = Orientation.HORIZONTAL,
        decorative: bool = True,
        class_name: str | None = None,
    ) -> None:
        validate_choice(orientation, tuple(Orientation), argument="orientation")
        super().__init__(
            orientation=str(orientation),
            decorative=decorative,
            class_name=class_name,
        )


class Skeleton(Component):
    type = "Skeleton"

    def __init__(
        self,
        *,
        width: Length | None = None,
        height: Length | None = None,
        class_name: str | None = None,
    ) -> None:
        style: dict[str, str] = {}
        width_value = css_length(width, argument="width")
        height_value = css_length(height, argument="height")
        if width_value:
            style["width"] = width_value
        if height_value:
            style["height"] = height_value
        super().__init__(class_name=class_name, style=style or None)


class Spinner(Component):
    type = "Spinner"

    def __init__(
        self,
        *,
        size: int | str = 16,
        label: str = "loading",
        class_name: str | None = None,
    ) -> None:
        super().__init__(size=size, label=label, class_name=class_name)


class Progress(Component):
    type = "Progress"

    def __init__(
        self,
        *,
        value: float = 0,
        max: float = 100,
        label: str | None = None,
        class_name: str | None = None,
    ) -> None:
        if max <= 0:
            raise ComponentError("max must be greater than zero")
        if not 0 <= value <= max:
            raise ComponentError("value must be between 0 and max")
        super().__init__(value=value, max=max, label=label, class_name=class_name)


class Toggle(Component):
    type = "Toggle"

    def __init__(
        self,
        *children: Child | Sequence[Child],
        pressed: Any = False,
        variant: ToggleVariant | str = ToggleVariant.DEFAULT,
        size: ToggleSize | str = ToggleSize.DEFAULT,
        disabled: bool = False,
        class_name: str | None = None,
        on_change: Any = None,
    ) -> None:
        validate_choice(variant, tuple(ToggleVariant), argument="variant")
        validate_choice(size, tuple(ToggleSize), argument="size")
        super().__init__(
            *children,
            pressed=pressed,
            variant=str(variant),
            size=str(size),
            disabled=disabled,
            class_name=class_name,
        )
        self.bind("value_change", on_change)


class ToggleGroup(Component):
    type = "ToggleGroup"

    def __init__(
        self,
        items: Sequence[Mapping[str, Any] | str],
        *,
        type: str = "single",
        value: Any = None,
        variant: ToggleVariant | str = ToggleVariant.DEFAULT,
        size: ToggleSize | str = ToggleSize.DEFAULT,
        orientation: Orientation | str = Orientation.HORIZONTAL,
        disabled: bool = False,
        class_name: str | None = None,
        on_change: Any = None,
    ) -> None:
        validate_choice(type, ("single", "multiple"), argument="type")
        validate_choice(variant, tuple(ToggleVariant), argument="variant")
        validate_choice(size, tuple(ToggleSize), argument="size")
        validate_choice(orientation, tuple(Orientation), argument="orientation")
        normalized: list[dict[str, Any]] = []
        for index, item in enumerate(items):
            if isinstance(item, str):
                normalized.append(
                    {"value": item, "label": item, "icon": None, "disabled": False}
                )
            elif isinstance(item, Mapping):
                value_text = str(item.get("value", ""))
                if not value_text:
                    raise ComponentError(f"toggle item {index} requires a value")
                normalized.append(
                    {
                        "value": value_text,
                        "label": str(item.get("label", value_text)),
                        "icon": item.get("icon"),
                        "disabled": bool(item.get("disabled", False)),
                    }
                )
            else:
                raise ComponentError(f"toggle item {index} must be a string or mapping")
        super().__init__(
            items=normalized,
            type=type,
            value=value,
            variant=str(variant),
            size=str(size),
            orientation=str(orientation),
            disabled=disabled,
            class_name=class_name,
        )
        self.bind("value_change", on_change)


class ButtonGroup(Component):
    type = "ButtonGroup"

    def __init__(
        self,
        *children: Child | Sequence[Child],
        orientation: Orientation | str = Orientation.HORIZONTAL,
        class_name: str | None = None,
    ) -> None:
        validate_choice(orientation, tuple(Orientation), argument="orientation")
        super().__init__(*children, orientation=str(orientation), class_name=class_name)


class InputGroup(Component):
    type = "InputGroup"

    def __init__(
        self,
        input: Component,
        *,
        start: Child | Sequence[Child] | None = None,
        end: Child | Sequence[Child] | None = None,
        class_name: str | None = None,
    ) -> None:
        if not isinstance(input, Component):
            raise ComponentError("InputGroup input must be a Component")
        super().__init__(class_name=class_name)
        self.add_slot("input", input)
        self.add_slot("start", start)
        self.add_slot("end", end)


class Resizable(Component):
    type = "Resizable"

    def __init__(
        self,
        *panels: Child | Sequence[Child],
        direction: Orientation | str = Orientation.HORIZONTAL,
        sizes: Sequence[int | float] | None = None,
        min_sizes: Sequence[int | float] | None = None,
        class_name: str | None = None,
    ) -> None:
        validate_choice(direction, tuple(Orientation), argument="direction")
        if not panels:
            raise ComponentError("Resizable requires at least one panel")
        if sizes is not None and len(sizes) != len(panels):
            raise ComponentError("sizes must contain one value per panel")
        if min_sizes is not None and len(min_sizes) != len(panels):
            raise ComponentError("min_sizes must contain one value per panel")
        super().__init__(
            *panels,
            direction=str(direction),
            sizes=list(sizes) if sizes is not None else None,
            minSizes=list(min_sizes) if min_sizes is not None else None,
            class_name=class_name,
        )


class Table(Component):
    type = "Table"

    def __init__(
        self,
        columns: Sequence[TableColumn | Mapping[str, Any]],
        rows: Sequence[Mapping[str, Any]],
        *,
        caption: str | None = None,
        footer: str | None = None,
        class_name: str | None = None,
    ) -> None:
        super().__init__(
            columns=normalize_table_columns(columns),
            rows=[dict(row) for row in rows],
            caption=caption,
            footer=footer,
            class_name=class_name,
        )


class DataTable(Component):
    type = "DataTable"

    def __init__(
        self,
        columns: Sequence[TableColumn | Mapping[str, Any]],
        rows: Sequence[Mapping[str, Any]],
        *,
        page_size: int = 10,
        searchable: bool = True,
        search_placeholder: str = "filter rows...",
        empty_text: str = "no results",
        row_key: str | None = None,
        class_name: str | None = None,
        on_row_click: Any = None,
        on_page_change: Any = None,
        server_side: bool = False,
        total_rows: int | None = None,
        page_index: int = 0,
        sorting: Sequence[Mapping[str, str]] = (),
        search: str = "",
        filters: Mapping[str, str] | None = None,
        on_query_change: DataTableQueryHandler | None = None,
        loading: bool = False,
        error: str | None = None,
        on_retry: Any = None,
        selected_keys: Sequence[str | int] = (),
        on_selection_change: Callable[[list[str]], Any] | None = None,
    ) -> None:
        if (
            isinstance(page_size, bool)
            or not isinstance(page_size, int)
            or page_size < 1
        ):
            raise ComponentError("page_size must be a positive integer")
        if not isinstance(server_side, bool):
            raise ComponentError("server_side must be a boolean")
        if (
            isinstance(page_index, bool)
            or not isinstance(page_index, int)
            or page_index < 0
        ):
            raise ComponentError("page_index must be a non-negative integer")
        if server_side and (
            isinstance(total_rows, bool)
            or not isinstance(total_rows, int)
            or total_rows < 0
        ):
            raise ComponentError("server-side tables require non-negative total_rows")
        if server_side and on_query_change is None:
            raise ComponentError("server-side tables require on_query_change")
        if not server_side and on_query_change is not None:
            raise ComponentError("on_query_change requires server_side=True")
        if not isinstance(search, str) or len(search) > 256:
            raise ComponentError("search must be a string of at most 256 characters")
        if not isinstance(loading, bool):
            raise ComponentError("loading must be a boolean")
        if error is not None and not isinstance(error, str):
            raise ComponentError("error must be a string or None")
        if on_retry is not None and not callable(on_retry):
            raise ComponentError("on_retry must be callable")
        if row_key is not None and (not isinstance(row_key, str) or not row_key):
            raise ComponentError("row_key must be a non-empty string or None")
        if not isinstance(selected_keys, Sequence) or isinstance(
            selected_keys, (str, bytes)
        ):
            raise ComponentError(
                "selected_keys must be a sequence of strings or integers"
            )
        if on_selection_change is not None and not callable(on_selection_change):
            raise ComponentError("on_selection_change must be callable")
        if on_selection_change is not None and row_key is None:
            raise ComponentError("row_key is required for selectable rows")
        normalized_selected_keys: list[str] = []
        for key in selected_keys:
            if isinstance(key, bool) or not isinstance(key, (str, int)):
                raise ComponentError("selected_keys must contain strings or integers")
            value = str(key)
            if not value or value in normalized_selected_keys:
                raise ComponentError("selected_keys must be non-empty and unique")
            normalized_selected_keys.append(value)
        validated_columns = normalize_table_columns(columns)
        sortable = {column["key"] for column in validated_columns if column["sortable"]}
        allowed = {column["key"] for column in validated_columns}
        if row_key is not None:
            row_keys: set[str] = set()
            for index, row in enumerate(rows):
                if row_key not in row:
                    raise ComponentError(
                        f"row {index} is missing the row_key field {row_key!r}"
                    )
                value = row[row_key]
                if isinstance(value, bool) or not isinstance(value, (str, int)):
                    raise ComponentError(
                        f"row {index} has an invalid value for row_key {row_key!r}"
                    )
                stable_key = str(value)
                if not stable_key or stable_key in row_keys:
                    raise ComponentError(
                        f"row_key values must be non-empty and unique: {stable_key!r}"
                    )
                row_keys.add(stable_key)
        try:
            initial_query = DataTableQuery.model_validate(
                {
                    "page_index": page_index,
                    "page_size": page_size,
                    "sorting": list(sorting),
                    "search": search,
                    "filters": dict(filters or {}),
                }
            )
        except ValidationError as validation_error:
            raise ComponentError(
                f"invalid data table query: {validation_error}"
            ) from validation_error
        if any(item.key not in sortable for item in initial_query.sorting):
            raise ComponentError("initial sorting must use declared sortable columns")
        if not set(initial_query.filters).issubset(allowed):
            raise ComponentError("initial filters must use declared columns")
        super().__init__(
            columns=validated_columns,
            rows=[dict(row) for row in rows],
            pageSize=page_size,
            searchable=searchable,
            searchPlaceholder=search_placeholder,
            emptyText=empty_text,
            rowKey=row_key,
            serverSide=server_side,
            totalRows=total_rows if total_rows is not None else len(rows),
            pageIndex=initial_query.page_index,
            sorting=[
                {"id": item.key, "desc": item.direction == "desc"}
                for item in initial_query.sorting
            ],
            search=initial_query.search,
            filters=initial_query.filters,
            loading=loading,
            error=error,
            selectedKeys=normalized_selected_keys,
            class_name=class_name,
        )
        self.bind("row_click", on_row_click)
        self.bind("page_change", on_page_change)
        self.bind("retry", on_retry)
        if on_selection_change is not None:

            def validate_selection(event: Event) -> Any:
                keys = event.values.get("keys")
                if not isinstance(keys, list) or any(
                    not isinstance(key, str) or not key for key in keys
                ):
                    raise ComponentError("selection keys must be non-empty strings")
                if len(keys) != len(set(keys)):
                    raise ComponentError("selection keys must be unique")
                return on_selection_change(keys)

            self.bind("selection_change", validate_selection)
        if on_query_change is not None:
            if not callable(on_query_change):
                raise ComponentError("on_query_change must be callable")

            def validate_query(event: Event) -> Any:
                try:
                    query = DataTableQuery.model_validate(event.values)
                except ValidationError as validation_error:
                    raise ComponentError(
                        f"invalid data table query: {validation_error}"
                    ) from validation_error
                if any(item.key not in sortable for item in query.sorting):
                    raise ComponentError(
                        "sort keys must refer to declared sortable columns"
                    )
                if not set(query.filters).issubset(allowed):
                    raise ComponentError("filter keys must refer to declared columns")
                if (
                    query.page_index * query.page_size >= max(1, total_rows or 0)
                    and query.page_index != 0
                ):
                    raise ComponentError("requested page is outside the result set")
                return on_query_change(query)

            self.bind("query_change", validate_query)


class Chart(Component):
    type = "Chart"

    def __init__(
        self,
        data: Sequence[Mapping[str, Any]],
        series: Sequence[ChartSeries | Mapping[str, Any]],
        *,
        kind: ChartKind | str = ChartKind.BAR,
        x_key: str = "name",
        height: Length = 300,
        stacked: bool = False,
        show_legend: bool = True,
        show_tooltip: bool = True,
        class_name: str | None = None,
    ) -> None:
        validate_choice(kind, tuple(ChartKind), argument="kind")
        if not data:
            raise ComponentError("data must contain at least one row")
        if not x_key:
            raise ComponentError("x_key must be a non-empty string")
        height_value = css_length(height, argument="height")
        super().__init__(
            data=[dict(row) for row in data],
            series=normalize_series(series),
            kind=str(kind),
            xKey=x_key,
            height=height_value,
            stacked=stacked,
            showLegend=show_legend,
            showTooltip=show_tooltip,
            class_name=class_name,
        )


class Carousel(Component):
    type = "Carousel"

    def __init__(
        self,
        *items: Child | Sequence[Child],
        orientation: Orientation | str = Orientation.HORIZONTAL,
        loop: bool = False,
        autoplay: bool = False,
        class_name: str | None = None,
    ) -> None:
        validate_choice(orientation, tuple(Orientation), argument="orientation")
        if not items:
            raise ComponentError("Carousel requires at least one item")
        super().__init__(
            *items,
            orientation=str(orientation),
            loop=loop,
            autoplay=autoplay,
            class_name=class_name,
        )


def normalize_accordion_items(
    items: Sequence[AccordionItem | Mapping[str, Any]],
) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    seen: set[str] = set()
    for index, item in enumerate(items):
        if isinstance(item, AccordionItem):
            value, title, content, disabled = (
                item.value,
                item.title,
                item.content,
                item.disabled,
            )
        elif isinstance(item, Mapping):
            value = str(item.get("value", ""))
            title = str(item.get("title", ""))
            content = item.get("content")
            disabled = bool(item.get("disabled", False))
        else:
            raise ComponentError(
                f"accordion item {index} must be AccordionItem or mapping"
            )
        if not value or not title:
            raise ComponentError(f"accordion item {index} requires value and title")
        if value in seen:
            raise ComponentError(f"duplicate accordion value {value!r}")
        seen.add(value)
        result.append(
            {
                "value": value,
                "title": title,
                "panel": f"panel_{index}",
                "disabled": disabled,
                "_content": content,
            }
        )
    return result


class Accordion(Component):
    type = "Accordion"

    def __init__(
        self,
        items: Sequence[AccordionItem | Mapping[str, Any]],
        *,
        type: str = "single",
        value: Any = None,
        default_value: Any = None,
        collapsible: bool = True,
        class_name: str | None = None,
        on_change: Any = None,
    ) -> None:
        validate_choice(type, ("single", "multiple"), argument="type")
        normalized = normalize_accordion_items(items)
        contents: list[Any] = []
        for index, item in enumerate(normalized):
            contents.append(item.pop("_content"))
        super().__init__(
            items=normalized,
            type=type,
            value=value,
            defaultValue=default_value,
            collapsible=collapsible,
            class_name=class_name,
        )
        for index, content in enumerate(contents):
            self.add_slot(f"panel_{index}", content)
        self.bind("value_change", on_change)


class Collapsible(Component):
    type = "Collapsible"

    def __init__(
        self,
        *children: Child | Sequence[Child],
        trigger: Component | None = None,
        open: Any = None,
        default_open: bool = False,
        class_name: str | None = None,
        on_open_change: Any = None,
    ) -> None:
        super().__init__(
            *children,
            open=open,
            defaultOpen=default_open,
            class_name=class_name,
        )
        self.add_slot("trigger", trigger)
        self.bind("open_change", on_open_change)


__all__ = [
    "Accordion",
    "Alert",
    "AspectRatio",
    "Avatar",
    "Badge",
    "ButtonGroup",
    "Card",
    "Carousel",
    "Chart",
    "Collapsible",
    "DataTable",
    "Empty",
    "InputGroup",
    "Item",
    "Progress",
    "Resizable",
    "Separator",
    "Skeleton",
    "Spinner",
    "Table",
    "Toggle",
    "ToggleGroup",
]
