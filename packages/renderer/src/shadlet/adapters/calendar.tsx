import { format } from "date-fns";
import { CalendarDays } from "lucide-react";
import { Button as UiButton } from "@/components/ui/button";
import { Calendar as UiCalendar } from "@/components/ui/calendar";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import { cn } from "@/lib/utils";
import { boolean, className, text, type AdapterProps } from "@/shadlet/types";

function isoDate(value: unknown): Date | undefined {
  if (typeof value !== "string" || !value) return undefined;
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? undefined : date;
}

function recordFrom(value: unknown, key: string): unknown {
  return value && typeof value === "object"
    ? (value as Record<string, unknown>)[key]
    : undefined;
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
