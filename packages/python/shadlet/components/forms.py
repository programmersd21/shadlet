"""Form controls and field composition."""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from typing import Any, TypeVar

from pydantic import BaseModel, ValidationError

from shadlet.components.base import Child, Component, ComponentError, validate_choice
from shadlet.components.enums import (
    ButtonSize,
    ButtonVariant,
    CalendarMode,
    Orientation,
)
from shadlet.components.options import SelectOption
from shadlet.events.types import Event
from shadlet.state.state import State

OptionLike = SelectOption | str | Mapping[str, Any]
ModelT = TypeVar("ModelT", bound=BaseModel)


def normalize_options(
    options: Sequence[OptionLike], *, argument: str = "options"
) -> list[dict[str, Any]]:
    if not isinstance(options, Sequence) or isinstance(options, (str, bytes)):
        raise ComponentError(f"{argument} must be a sequence")
    result: list[dict[str, Any]] = []
    seen: set[str] = set()
    for index, option in enumerate(options):
        if isinstance(option, str):
            value, label, disabled = option, option, False
        elif isinstance(option, SelectOption):
            value, label, disabled = option.value, option.label, option.disabled
        elif isinstance(option, Mapping):
            try:
                value = option["value"]
                label = option["label"]
            except KeyError as error:
                raise ComponentError(
                    f"{argument}[{index}] requires 'value' and 'label'"
                ) from error
            disabled = bool(option.get("disabled", False))
        else:
            raise ComponentError(
                f"{argument}[{index}] must be a string, SelectOption or mapping"
            )
        if not isinstance(value, str) or not value:
            raise ComponentError(
                f"{argument}[{index}].value must be a non-empty string"
            )
        if not isinstance(label, str):
            raise ComponentError(f"{argument}[{index}].label must be a string")
        if value in seen:
            raise ComponentError(f"{argument} contains duplicate value {value!r}")
        seen.add(value)
        result.append({"value": value, "label": label, "disabled": disabled})
    return result


class Button(Component):
    type = "Button"

    def __init__(
        self,
        *children: Child | Sequence[Child],
        variant: ButtonVariant | str = ButtonVariant.DEFAULT,
        size: ButtonSize | str = ButtonSize.DEFAULT,
        type: str = "button",
        disabled: bool = False,
        loading: bool = False,
        name: str | None = None,
        value: str | None = None,
        icon: str | None = None,
        icon_position: str = "start",
        aria_label: str | None = None,
        class_name: str | None = None,
        on_click: Any = None,
    ) -> None:
        validate_choice(variant, tuple(ButtonVariant), argument="variant")
        validate_choice(size, tuple(ButtonSize), argument="size")
        validate_choice(type, ("button", "submit", "reset"), argument="type")
        validate_choice(icon_position, ("start", "end"), argument="icon_position")
        if not isinstance(disabled, bool) or not isinstance(loading, bool):
            raise ComponentError("disabled and loading must be booleans")
        super().__init__(
            *children,
            variant=str(variant),
            size=str(size),
            type=type,
            disabled=disabled or loading,
            loading=loading,
            name=name,
            value=value,
            icon=icon,
            iconPosition=icon_position,
            ariaLabel=aria_label,
            class_name=class_name,
        )
        self.bind("click", on_click)


class Input(Component):
    type = "Input"

    def __init__(
        self,
        *,
        value: Any = None,
        placeholder: str | None = None,
        type: str = "text",
        disabled: bool = False,
        required: bool = False,
        read_only: bool = False,
        invalid: bool = False,
        name: str | None = None,
        auto_complete: str | None = None,
        min: float | str | None = None,
        max: float | str | None = None,
        step: float | str | None = None,
        pattern: str | None = None,
        aria_label: str | None = None,
        class_name: str | None = None,
        on_change: Any = None,
    ) -> None:
        super().__init__(
            value=value,
            placeholder=placeholder,
            type=type,
            disabled=disabled,
            required=required,
            readOnly=read_only,
            ariaInvalid=invalid,
            name=name,
            autoComplete=auto_complete,
            min=min,
            max=max,
            step=step,
            pattern=pattern,
            ariaLabel=aria_label,
            class_name=class_name,
        )
        self.bind("change", on_change)


class Textarea(Component):
    type = "Textarea"

    def __init__(
        self,
        *,
        value: Any = None,
        placeholder: str | None = None,
        rows: int = 3,
        disabled: bool = False,
        required: bool = False,
        read_only: bool = False,
        invalid: bool = False,
        name: str | None = None,
        max_length: int | None = None,
        aria_label: str | None = None,
        class_name: str | None = None,
        on_change: Any = None,
    ) -> None:
        if isinstance(rows, bool) or not isinstance(rows, int) or rows < 1:
            raise ComponentError("rows must be a positive integer")
        super().__init__(
            value=value,
            placeholder=placeholder,
            rows=rows,
            disabled=disabled,
            required=required,
            readOnly=read_only,
            ariaInvalid=invalid,
            name=name,
            maxLength=max_length,
            ariaLabel=aria_label,
            class_name=class_name,
        )
        self.bind("change", on_change)


class Label(Component):
    type = "Label"

    def __init__(
        self,
        *children: Child | Sequence[Child],
        html_for: str | None = None,
        class_name: str | None = None,
    ) -> None:
        super().__init__(*children, htmlFor=html_for, class_name=class_name)


class Checkbox(Component):
    type = "Checkbox"

    def __init__(
        self,
        *,
        checked: Any = False,
        disabled: bool = False,
        required: bool = False,
        name: str | None = None,
        value: str | None = None,
        label: str | None = None,
        description: str | None = None,
        class_name: str | None = None,
        on_change: Any = None,
    ) -> None:
        super().__init__(
            checked=checked,
            disabled=disabled,
            required=required,
            name=name,
            value=value,
            label=label,
            description=description,
            class_name=class_name,
        )
        self.bind("change", on_change)


class Switch(Component):
    type = "Switch"

    def __init__(
        self,
        *,
        checked: Any = False,
        disabled: bool = False,
        name: str | None = None,
        label: str | None = None,
        description: str | None = None,
        class_name: str | None = None,
        on_change: Any = None,
    ) -> None:
        super().__init__(
            checked=checked,
            disabled=disabled,
            name=name,
            label=label,
            description=description,
            class_name=class_name,
        )
        self.bind("change", on_change)


class Slider(Component):
    type = "Slider"

    def __init__(
        self,
        *,
        value: float | Sequence[int | float] = 0,
        min: float = 0,
        max: float = 100,
        step: float = 1,
        disabled: bool = False,
        orientation: Orientation | str = Orientation.HORIZONTAL,
        aria_label: str | None = None,
        class_name: str | None = None,
        on_change: Any = None,
    ) -> None:
        if max <= min:
            raise ComponentError("max must be greater than min")
        if step <= 0:
            raise ComponentError("step must be greater than zero")
        validate_choice(orientation, tuple(Orientation), argument="orientation")
        values = list(value) if isinstance(value, (list, tuple)) else [value]
        if not values:
            raise ComponentError("value must contain at least one number")
        for item in values:
            if isinstance(item, bool) or not isinstance(item, (int, float)):
                raise ComponentError("slider values must be numbers")
            if not min <= item <= max:
                raise ComponentError(f"slider value {item} is outside {min}..{max}")
        super().__init__(
            value=values,
            min=min,
            max=max,
            step=step,
            disabled=disabled,
            orientation=str(orientation),
            ariaLabel=aria_label,
            class_name=class_name,
        )
        self.bind("value_change", on_change)


class Select(Component):
    type = "Select"

    def __init__(
        self,
        options: Sequence[OptionLike],
        *,
        value: Any = None,
        placeholder: str = "select an option",
        disabled: bool = False,
        required: bool = False,
        name: str | None = None,
        class_name: str | None = None,
        on_change: Any = None,
    ) -> None:
        super().__init__(
            options=normalize_options(options),
            value=value,
            placeholder=placeholder,
            disabled=disabled,
            required=required,
            name=name,
            class_name=class_name,
        )
        self.bind("value_change", on_change)


class NativeSelect(Component):
    type = "NativeSelect"

    def __init__(
        self,
        options: Sequence[OptionLike],
        *,
        value: Any = None,
        disabled: bool = False,
        required: bool = False,
        name: str | None = None,
        class_name: str | None = None,
        on_change: Any = None,
    ) -> None:
        super().__init__(
            options=normalize_options(options),
            value=value,
            disabled=disabled,
            required=required,
            name=name,
            class_name=class_name,
        )
        self.bind("change", on_change)


class RadioGroup(Component):
    type = "RadioGroup"

    def __init__(
        self,
        options: Sequence[OptionLike],
        *,
        value: Any = None,
        orientation: Orientation | str = Orientation.VERTICAL,
        disabled: bool = False,
        name: str | None = None,
        class_name: str | None = None,
        on_change: Any = None,
    ) -> None:
        validate_choice(orientation, tuple(Orientation), argument="orientation")
        super().__init__(
            options=normalize_options(options),
            value=value,
            orientation=str(orientation),
            disabled=disabled,
            name=name,
            class_name=class_name,
        )
        self.bind("value_change", on_change)


class Combobox(Component):
    type = "Combobox"

    def __init__(
        self,
        options: Sequence[OptionLike],
        *,
        value: Any = None,
        placeholder: str = "select an option",
        search_placeholder: str = "search...",
        empty_text: str = "no results found",
        disabled: bool = False,
        class_name: str | None = None,
        on_change: Any = None,
    ) -> None:
        super().__init__(
            options=normalize_options(options),
            value=value,
            placeholder=placeholder,
            searchPlaceholder=search_placeholder,
            emptyText=empty_text,
            disabled=disabled,
            class_name=class_name,
        )
        self.bind("value_change", on_change)


class InputOTP(Component):
    type = "InputOTP"

    def __init__(
        self,
        *,
        length: int = 6,
        value: Any = "",
        disabled: bool = False,
        class_name: str | None = None,
        on_change: Any = None,
    ) -> None:
        if (
            isinstance(length, bool)
            or not isinstance(length, int)
            or not 1 <= length <= 12
        ):
            raise ComponentError("length must be an integer from 1 to 12")
        super().__init__(
            length=length,
            value=value,
            disabled=disabled,
            class_name=class_name,
        )
        self.bind("change", on_change)


class Calendar(Component):
    type = "Calendar"

    def __init__(
        self,
        *,
        mode: CalendarMode | str = CalendarMode.SINGLE,
        selected: Any = None,
        min_date: str | None = None,
        max_date: str | None = None,
        disabled: bool = False,
        class_name: str | None = None,
        on_select: Any = None,
    ) -> None:
        validate_choice(mode, tuple(CalendarMode), argument="mode")
        super().__init__(
            mode=str(mode),
            selected=selected,
            minDate=min_date,
            maxDate=max_date,
            disabled=disabled,
            class_name=class_name,
        )
        self.bind("select", on_select)


class DatePicker(Component):
    type = "DatePicker"

    def __init__(
        self,
        *,
        value: Any = None,
        placeholder: str = "pick a date",
        disabled: bool = False,
        min_date: str | None = None,
        max_date: str | None = None,
        class_name: str | None = None,
        on_change: Any = None,
    ) -> None:
        super().__init__(
            value=value,
            placeholder=placeholder,
            disabled=disabled,
            minDate=min_date,
            maxDate=max_date,
            class_name=class_name,
        )
        self.bind("select", on_change)


class Form(Component):
    type = "Form"

    def __init__(
        self,
        *children: Child | Sequence[Child],
        name: str | None = None,
        class_name: str | None = None,
        on_submit: Any = None,
    ) -> None:
        super().__init__(*children, name=name, class_name=class_name)
        self.bind("submit", on_submit)


def pydantic_form(
    model: type[ModelT],
    *children: Child | Sequence[Child],
    on_submit: Callable[[ModelT], Any],
    field_errors: State[dict[str, str]] | None = None,
    form_error: State[str] | None = None,
    name: str | None = None,
    class_name: str | None = None,
) -> Form:
    """Create a server-validated form backed by a Pydantic v2 model.

    On invalid input, field errors are stored under dot-separated field paths
    and the form-level error is updated when the matching state is supplied.
    """
    if not isinstance(model, type) or not issubclass(model, BaseModel):
        raise ComponentError("model must be a Pydantic BaseModel subclass")
    if not callable(on_submit):
        raise ComponentError("on_submit must be callable")

    def validate_submission(event: Event) -> Any:
        try:
            values = model.model_validate(event.values)
        except ValidationError as validation_error:
            if field_errors is not None:
                field_errors.value = {
                    ".".join(str(part) for part in item["loc"]): item["msg"]
                    for item in validation_error.errors(
                        include_input=False, include_context=False
                    )
                    if item["loc"]
                }
            if form_error is not None:
                form_error.value = "please correct the highlighted fields"
            return None

        if field_errors is not None:
            field_errors.value = {}
        if form_error is not None:
            form_error.value = ""
        return on_submit(values)

    return Form(
        *children,
        name=name,
        class_name=class_name,
        on_submit=validate_submission,
    )


class Field(Component):
    type = "Field"

    def __init__(
        self,
        *children: Child | Sequence[Child],
        label: str | None = None,
        description: str | None = None,
        error: str | None = None,
        required: bool = False,
        invalid: bool = False,
        class_name: str | None = None,
    ) -> None:
        super().__init__(
            *children,
            label=label,
            description=description,
            error=error,
            required=required,
            invalid=invalid,
            class_name=class_name,
        )


__all__ = [
    "Button",
    "Calendar",
    "Checkbox",
    "Combobox",
    "DatePicker",
    "Field",
    "Form",
    "Input",
    "InputOTP",
    "Label",
    "NativeSelect",
    "RadioGroup",
    "Select",
    "Slider",
    "Switch",
    "Textarea",
    "normalize_options",
    "pydantic_form",
]
