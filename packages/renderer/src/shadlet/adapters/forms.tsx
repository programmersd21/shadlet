import * as React from "react";
import { format } from "date-fns";
import { CalendarDays } from "lucide-react";
import { Button as UiButton } from "@/components/ui/button";
import { Calendar as UiCalendar } from "@/components/ui/calendar";
import { Checkbox as UiCheckbox } from "@/components/ui/checkbox";
import {
  Combobox as UiCombobox,
  ComboboxContent,
  ComboboxEmpty,
  ComboboxInput,
  ComboboxItem,
  ComboboxList,
} from "@/components/ui/combobox";
import {
  Field as UiField,
  FieldDescription,
  FieldError,
  FieldLabel,
} from "@/components/ui/field";
import { Input as UiInput } from "@/components/ui/input";
import {
  InputOTP as UiInputOTP,
  InputOTPGroup,
  InputOTPSlot,
} from "@/components/ui/input-otp";
import { Label as UiLabel } from "@/components/ui/label";
import {
  NativeSelect as UiNativeSelect,
  NativeSelectOption,
} from "@/components/ui/native-select";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import {
  RadioGroup as UiRadioGroup,
  RadioGroupItem,
} from "@/components/ui/radio-group";
import {
  Select as UiSelect,
  SelectContent,
  SelectGroup,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Slider as UiSlider } from "@/components/ui/slider";
import { Spinner } from "@/components/ui/spinner";
import { Switch as UiSwitch } from "@/components/ui/switch";
import { Textarea as UiTextarea } from "@/components/ui/textarea";
import { cn } from "@/lib/utils";
import { iconFor } from "@/shadlet/icons";
import {
  boolean,
  changePayload,
  className,
  formPayload,
  list,
  number,
  style,
  text,
  type AdapterProps,
} from "@/shadlet/types";

type Option = { value: string; label: string; disabled: boolean };

function options(value: unknown): Option[] {
  return list<Record<string, unknown>>(value).map((item) => ({
    value: text(item.value) ?? "",
    label: text(item.label) ?? "",
    disabled: boolean(item.disabled),
  }));
}

function inputValue(props: Record<string, unknown>): string | undefined {
  const value = props.value;
  return value === null || value === undefined ? undefined : String(value);
}

export function ButtonAdapter({
  props,
  children,
  events,
  dispatch,
}: AdapterProps) {
  const loading = boolean(props.loading);
  const icon = text(props.icon);
  const iconPosition = text(props.iconPosition) ?? "start";
  return (
    <UiButton
      type={
        (text(props.type) as "button" | "submit" | "reset" | undefined) ??
        "button"
      }
      variant={
        (text(props.variant) as
          | "default"
          | "outline"
          | "secondary"
          | "ghost"
          | "destructive"
          | "link"
          | undefined) ?? "default"
      }
      size={
        (text(props.size) as
          | "default"
          | "xs"
          | "sm"
          | "lg"
          | "icon"
          | "icon-xs"
          | "icon-sm"
          | "icon-lg"
          | undefined) ?? "default"
      }
      disabled={boolean(props.disabled)}
      name={text(props.name)}
      value={text(props.value)}
      aria-label={text(props.ariaLabel)}
      aria-busy={loading || undefined}
      className={className(props)}
      onClick={events.click ? () => dispatch("click") : undefined}
    >
      {loading ? <Spinner className="size-4" /> : null}
      {!loading && icon && iconPosition === "start" ? iconFor(icon) : null}
      {children}
      {!loading && icon && iconPosition === "end" ? iconFor(icon) : null}
    </UiButton>
  );
}

export function InputAdapter({ props, events, dispatch }: AdapterProps) {
  const value = inputValue(props);
  return (
    <UiInput
      id={text(props.id)}
      type={text(props.type) ?? "text"}
      {...(value === undefined ? { defaultValue: "" } : { value })}
      placeholder={text(props.placeholder)}
      disabled={boolean(props.disabled)}
      required={boolean(props.required)}
      readOnly={boolean(props.readOnly)}
      aria-invalid={boolean(props.ariaInvalid)}
      aria-label={text(props.ariaLabel)}
      aria-labelledby={text(props.ariaLabelledBy)}
      name={text(props.name)}
      autoComplete={text(props.autoComplete)}
      min={props.min as number | string | undefined}
      max={props.max as number | string | undefined}
      step={props.step as number | string | undefined}
      pattern={text(props.pattern)}
      className={className(props)}
      style={style(props)}
      onChange={
        events.change
          ? (event) => dispatch("change", changePayload(event))
          : undefined
      }
    />
  );
}

export function TextareaAdapter({ props, events, dispatch }: AdapterProps) {
  const value = inputValue(props);
  return (
    <UiTextarea
      id={text(props.id)}
      {...(value === undefined ? { defaultValue: "" } : { value })}
      placeholder={text(props.placeholder)}
      rows={number(props.rows) ?? 3}
      disabled={boolean(props.disabled)}
      required={boolean(props.required)}
      readOnly={boolean(props.readOnly)}
      aria-invalid={boolean(props.ariaInvalid)}
      aria-label={text(props.ariaLabel)}
      aria-labelledby={text(props.ariaLabelledBy)}
      name={text(props.name)}
      maxLength={number(props.maxLength)}
      className={className(props)}
      style={style(props)}
      onChange={
        events.change
          ? (event) => dispatch("change", changePayload(event))
          : undefined
      }
    />
  );
}

export function LabelAdapter({ props, children }: AdapterProps) {
  return (
    <UiLabel htmlFor={text(props.htmlFor)} className={className(props)}>
      {children}
    </UiLabel>
  );
}

function useFieldId(nodeId: string): string {
  const reactId = React.useId();
  return `${nodeId.replace(/[^a-zA-Z0-9_-]/g, "-")}-${reactId.replace(/:/g, "")}`;
}

export function CheckboxAdapter({
  props,
  events,
  dispatch,
  nodeId,
}: AdapterProps) {
  const generatedId = useFieldId(nodeId);
  const id = text(props.id) ?? generatedId;
  const checked = props.checked;
  const controlled = checked !== null && checked !== undefined;
  const label = text(props.label);
  const description = text(props.description);
  const box = (
    <UiCheckbox
      id={id}
      aria-labelledby={text(props.ariaLabelledBy)}
      checked={controlled ? boolean(checked) : undefined}
      defaultChecked={controlled ? undefined : false}
      disabled={boolean(props.disabled)}
      required={boolean(props.required)}
      name={text(props.name)}
      value={text(props.value)}
      onCheckedChange={
        events.change
          ? (value) => dispatch("change", { value, checked: value === true })
          : undefined
      }
    />
  );
  if (!label && !description) return box;
  return (
    <div className={cn("flex flex-col gap-1.5", className(props))}>
      <div className="flex items-center gap-2">
        {box}
        {label ? <UiLabel htmlFor={id}>{label}</UiLabel> : null}
      </div>
      {description ? (
        <p className="text-sm text-muted-foreground">{description}</p>
      ) : null}
    </div>
  );
}

export function SwitchAdapter({
  props,
  events,
  dispatch,
  nodeId,
}: AdapterProps) {
  const generatedId = useFieldId(nodeId);
  const id = text(props.id) ?? generatedId;
  const checked = props.checked;
  const controlled = checked !== null && checked !== undefined;
  const label = text(props.label);
  const description = text(props.description);
  const control = (
    <UiSwitch
      id={id}
      aria-labelledby={text(props.ariaLabelledBy)}
      checked={controlled ? boolean(checked) : undefined}
      defaultChecked={controlled ? undefined : false}
      disabled={boolean(props.disabled)}
      name={text(props.name)}
      onCheckedChange={
        events.change
          ? (value) => dispatch("change", { value, checked: value })
          : undefined
      }
    />
  );
  if (!label && !description) return control;
  return (
    <div
      className={cn(
        "flex items-center justify-between gap-4",
        className(props),
      )}
    >
      <div className="flex flex-col gap-1">
        {label ? <UiLabel htmlFor={id}>{label}</UiLabel> : null}
        {description ? (
          <p className="text-sm text-muted-foreground">{description}</p>
        ) : null}
      </div>
      {control}
    </div>
  );
}

export function SliderAdapter({ props, events, dispatch }: AdapterProps) {
  const raw = props.value;
  const values = Array.isArray(raw)
    ? raw.map(Number)
    : raw === null || raw === undefined
      ? undefined
      : [Number(raw)];
  const min = number(props.min) ?? 0;
  const max = number(props.max) ?? 100;
  return (
    <UiSlider
      value={values}
      defaultValue={values === undefined ? [min] : undefined}
      min={min}
      max={max}
      step={number(props.step) ?? 1}
      disabled={boolean(props.disabled)}
      orientation={props.orientation === "vertical" ? "vertical" : "horizontal"}
      aria-label={text(props.ariaLabel)}
      aria-labelledby={text(props.ariaLabelledBy)}
      className={className(props)}
      onValueChange={
        events.value_change
          ? (next: number | readonly number[]) =>
              dispatch("value_change", {
                value:
                  Array.isArray(next) && next.length === 1 ? next[0] : next,
              })
          : undefined
      }
    />
  );
}

export function SelectAdapter({ props, events, dispatch }: AdapterProps) {
  const items = options(props.options);
  const value = props.value;
  const hasValue = value !== null && value !== undefined;
  return (
    <UiSelect
      items={items}
      value={hasValue ? String(value) : undefined}
      defaultValue={hasValue ? undefined : undefined}
      disabled={boolean(props.disabled)}
      required={boolean(props.required)}
      name={text(props.name)}
      onValueChange={
        events.value_change
          ? (next) => dispatch("value_change", { value: next })
          : undefined
      }
    >
      <SelectTrigger
        className={className(props)}
        id={text(props.id)}
        aria-label={text(props.ariaLabel)}
        aria-labelledby={text(props.ariaLabelledBy)}
      >
        <SelectValue
          placeholder={text(props.placeholder) ?? "select an option"}
        />
      </SelectTrigger>
      <SelectContent>
        <SelectGroup>
          {items.map((item) => (
            <SelectItem
              key={item.value}
              value={item.value}
              disabled={item.disabled}
            >
              {item.label}
            </SelectItem>
          ))}
        </SelectGroup>
      </SelectContent>
    </UiSelect>
  );
}

export function NativeSelectAdapter({ props, events, dispatch }: AdapterProps) {
  const items = options(props.options);
  const value = props.value;
  return (
    <UiNativeSelect
      id={text(props.id)}
      value={value !== null && value !== undefined ? String(value) : undefined}
      disabled={boolean(props.disabled)}
      required={boolean(props.required)}
      name={text(props.name)}
      aria-label={text(props.ariaLabel)}
      aria-labelledby={text(props.ariaLabelledBy)}
      className={className(props)}
      onChange={
        events.change
          ? (event) => dispatch("change", changePayload(event))
          : undefined
      }
    >
      {items.map((item) => (
        <NativeSelectOption
          key={item.value}
          value={item.value}
          disabled={item.disabled}
        >
          {item.label}
        </NativeSelectOption>
      ))}
    </UiNativeSelect>
  );
}

export function RadioGroupAdapter({
  props,
  events,
  dispatch,
  nodeId,
}: AdapterProps) {
  const items = options(props.options);
  const value = props.value;
  const hasValue = value !== null && value !== undefined;
  const id = useFieldId(nodeId);
  return (
    <UiRadioGroup
      value={hasValue ? String(value) : undefined}
      defaultValue={hasValue ? undefined : undefined}
      disabled={boolean(props.disabled)}
      name={text(props.name)}
      aria-label={text(props.ariaLabel)}
      aria-labelledby={text(props.ariaLabelledBy)}
      className={className(props)}
      onValueChange={
        events.value_change
          ? (next) => dispatch("value_change", { value: next })
          : undefined
      }
    >
      {items.map((item, index) => {
        const itemId = `${id}-${index}`;
        return (
          <div key={item.value} className="flex items-center gap-2">
            <RadioGroupItem
              id={itemId}
              value={item.value}
              disabled={item.disabled}
            />
            <UiLabel htmlFor={itemId}>{item.label}</UiLabel>
          </div>
        );
      })}
    </UiRadioGroup>
  );
}

export function ComboboxAdapter({ props, events, dispatch }: AdapterProps) {
  const items = options(props.options);
  const value = props.value;
  const hasValue = value !== null && value !== undefined;
  return (
    <UiCombobox
      items={items.map((item) => item.value)}
      value={hasValue ? String(value) : undefined}
      onValueChange={
        events.value_change
          ? (next) => dispatch("value_change", { value: next })
          : undefined
      }
      disabled={boolean(props.disabled)}
    >
      <ComboboxInput
        placeholder={text(props.placeholder) ?? "select an option"}
        id={text(props.id)}
        aria-label={text(props.ariaLabel)}
        aria-labelledby={text(props.ariaLabelledBy)}
        disabled={boolean(props.disabled)}
        className={className(props)}
      />
      <ComboboxContent>
        <ComboboxEmpty>
          {text(props.emptyText) ?? "no results found"}
        </ComboboxEmpty>
        <ComboboxList>
          {(item: string) => (
            <ComboboxItem key={item} value={item}>
              {items.find((option) => option.value === item)?.label ?? item}
            </ComboboxItem>
          )}
        </ComboboxList>
      </ComboboxContent>
    </UiCombobox>
  );
}

export function InputOTPAdapter({ props, events, dispatch }: AdapterProps) {
  const length = number(props.length) ?? 6;
  return (
    <UiInputOTP
      maxLength={length}
      id={text(props.id)}
      aria-label={text(props.ariaLabel)}
      aria-labelledby={text(props.ariaLabelledBy)}
      value={events.change ? (text(props.value) ?? "") : undefined}
      defaultValue={events.change ? undefined : (text(props.value) ?? "")}
      disabled={boolean(props.disabled)}
      className={className(props)}
      onChange={
        events.change
          ? (next) => dispatch("change", { value: next })
          : undefined
      }
    >
      <InputOTPGroup>
        {Array.from({ length }, (_, index) => (
          <InputOTPSlot key={index} index={index} />
        ))}
      </InputOTPGroup>
    </UiInputOTP>
  );
}

function isoDate(value: unknown): Date | undefined {
  if (typeof value !== "string" || !value) return undefined;
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? undefined : date;
}

export function CalendarAdapter({ props, events, dispatch }: AdapterProps) {
  const mode = props.mode === "range" ? "range" : "single";
  const selectedRaw = props.selected;
  const selected =
    mode === "range"
      ? {
          from: isoDate(recordFrom(selectedRaw, "from")),
          to: isoDate(recordFrom(selectedRaw, "to")),
        }
      : isoDate(selectedRaw);
  return (
    <UiCalendar
      mode={mode}
      selected={selected as never}
      disabled={boolean(props.disabled)}
      required={false}
      className={className(props)}
      onSelect={
        events.select
          ? (next: unknown) => {
              if (next && typeof next === "object" && "from" in next) {
                const range = next as { from?: Date; to?: Date };
                dispatch("select", {
                  value: {
                    from: range.from?.toISOString(),
                    to: range.to?.toISOString(),
                  },
                });
              } else {
                dispatch("select", {
                  value: next instanceof Date ? next.toISOString() : null,
                });
              }
            }
          : undefined
      }
    />
  );
}

function recordFrom(value: unknown, key: string): unknown {
  return value && typeof value === "object"
    ? (value as Record<string, unknown>)[key]
    : undefined;
}

export function DatePickerAdapter({ props, events, dispatch }: AdapterProps) {
  const value = isoDate(props.value);
  return (
    <Popover>
      <PopoverTrigger
        render={
          <UiButton
            id={text(props.id)}
            aria-label={text(props.ariaLabel)}
            aria-labelledby={text(props.ariaLabelledBy)}
            variant="outline"
            className={cn(
              "w-56 justify-start text-left font-normal",
              className(props),
            )}
            disabled={boolean(props.disabled)}
          />
        }
      >
        <CalendarDays className="size-4" />
        {value
          ? format(value, "PPP")
          : (text(props.placeholder) ?? "pick a date")}
      </PopoverTrigger>
      <PopoverContent className="w-auto p-0" align="start">
        <UiCalendar
          mode="single"
          selected={value}
          onSelect={
            events.select
              ? (next) =>
                  dispatch("select", {
                    value: next ? next.toISOString() : null,
                  })
              : undefined
          }
        />
      </PopoverContent>
    </Popover>
  );
}

export function FormAdapter({
  props,
  children,
  events,
  dispatch,
}: AdapterProps) {
  return (
    <form
      name={text(props.name)}
      className={className(props)}
      onSubmit={(event) => {
        if (!events.submit) return;
        event.preventDefault();
        dispatch("submit", { values: formPayload(event.currentTarget) });
      }}
    >
      {children}
    </form>
  );
}

export function FieldAdapter({ props, children, nodeId }: AdapterProps) {
  const controlId = `${nodeId}-control`;
  const labelId = `${nodeId}-label`;
  return (
    <UiField
      className={className(props)}
      data-invalid={boolean(props.invalid) || undefined}
    >
      {text(props.label) ? (
        <FieldLabel id={labelId} htmlFor={controlId}>
          {text(props.label)}
          {boolean(props.required) ? <span aria-hidden="true"> *</span> : null}
        </FieldLabel>
      ) : null}
      {children}
      {text(props.description) ? (
        <FieldDescription>{text(props.description)}</FieldDescription>
      ) : null}
      {text(props.error) ? <FieldError>{text(props.error)}</FieldError> : null}
    </UiField>
  );
}
