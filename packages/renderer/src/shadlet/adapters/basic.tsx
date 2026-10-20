import * as React from "react";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { AspectRatio } from "@/components/ui/aspect-ratio";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { ButtonGroup } from "@/components/ui/button-group";
import {
  Empty,
  EmptyContent,
  EmptyDescription,
  EmptyHeader,
  EmptyMedia,
  EmptyTitle,
} from "@/components/ui/empty";
import { InputGroup, InputGroupAddon } from "@/components/ui/input-group";
import {
  Item,
  ItemActions,
  ItemContent,
  ItemDescription,
  ItemMedia,
  ItemTitle,
} from "@/components/ui/item";
import {
  Progress,
  ProgressLabel,
  ProgressValue,
} from "@/components/ui/progress";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";
import { Skeleton } from "@/components/ui/skeleton";
import { Spinner } from "@/components/ui/spinner";
import { Toggle } from "@/components/ui/toggle";
import { ToggleGroup, ToggleGroupItem } from "@/components/ui/toggle-group";
import { cn } from "@/lib/utils";
import { ShadletIcon, iconFor } from "@/shadlet/icons";
import {
  boolean,
  className,
  list,
  number,
  record,
  style,
  text,
  type AdapterProps,
} from "@/shadlet/types";
import { useTheme } from "@/themes/provider";
import { Monitor, Moon, Sun } from "lucide-react";

const TAGS = new Set([
  "div",
  "section",
  "main",
  "header",
  "footer",
  "nav",
  "aside",
  "article",
  "ul",
  "ol",
  "li",
  "span",
]);

function boxTag(props: Record<string, unknown>): string {
  const value = text(props.as);
  return value && TAGS.has(value) ? value : "div";
}

export function BoxAdapter({ props, children }: AdapterProps) {
  return React.createElement(
    boxTag(props),
    { className: className(props), style: style(props) },
    children,
  );
}

function gridVariables(value: unknown, prefix: string): Record<string, string> {
  const result: Record<string, string> = {};
  if (typeof value === "number") {
    result[`--shadlet-${prefix}-base`] = String(value);
    return result;
  }
  const values = record(value);
  for (const [key, track] of Object.entries(values)) {
    if (typeof track === "number" && Number.isInteger(track) && track > 0) {
      result[`--shadlet-${prefix}-${key}`] = String(track);
    }
  }
  return result;
}

export function GridAdapter({ props, children }: AdapterProps) {
  const variables = {
    ...gridVariables(props.columns, "grid-cols"),
    ...gridVariables(props.rows, "grid-rows"),
  };
  return React.createElement(
    boxTag(props),
    {
      className: cn("shadlet-grid", className(props)),
      style: { ...variables, ...style(props) } as React.CSSProperties,
    },
    children,
  );
}

export function ScrollAreaAdapter({ props, children }: AdapterProps) {
  if (props.orientation === "horizontal") {
    return (
      <div
        className={cn("overflow-x-auto", className(props))}
        style={style(props)}
      >
        {children}
      </div>
    );
  }
  return (
    <ScrollArea className={className(props)} style={style(props)}>
      {children}
    </ScrollArea>
  );
}

const textClasses: Record<string, string> = {
  default: "",
  muted: "text-muted-foreground",
  small: "text-sm",
  lead: "text-lg text-muted-foreground",
  large: "text-lg font-semibold",
  bold: "font-semibold",
  code: "rounded bg-muted px-1.5 py-0.5 font-mono text-sm",
};

export function TextAdapter({ props, children }: AdapterProps) {
  const variant = text(props.variant) ?? "default";
  const tag = text(props.as) ?? "p";
  return React.createElement(
    tag,
    {
      className: cn(textClasses[variant] ?? "", className(props)),
      style: style(props),
    },
    children,
  );
}

const headingClasses: Record<number, string> = {
  1: "scroll-m-20 text-4xl font-bold tracking-tight text-balance",
  2: "scroll-m-20 text-3xl font-semibold tracking-tight",
  3: "scroll-m-20 text-2xl font-semibold tracking-tight",
  4: "scroll-m-20 text-xl font-semibold tracking-tight",
  5: "scroll-m-20 text-lg font-semibold tracking-tight",
  6: "scroll-m-20 text-base font-semibold tracking-tight",
};

export function HeadingAdapter({ props, children }: AdapterProps) {
  const level = Math.min(6, Math.max(1, number(props.level) ?? 1));
  const tag = `h${level}` as "h1";
  return React.createElement(
    tag,
    {
      className: cn(headingClasses[level], className(props)),
      style: style(props),
    },
    children,
  );
}

export function LinkAdapter({
  props,
  children,
  events,
  dispatch,
  navigate,
}: AdapterProps) {
  const href = text(props.href) ?? "#";
  const external = boolean(props.external);
  const internal = !external && href.startsWith("/");
  return (
    <a
      href={href}
      className={cn(
        "font-medium underline-offset-4 hover:underline",
        className(props),
      )}
      target={text(props.target)}
      rel={text(props.rel)}
      onClick={(event) => {
        if (events.click) dispatch("click");
        if (internal) {
          event.preventDefault();
          navigate(href);
        }
      }}
    >
      {children}
    </a>
  );
}

export function IconAdapter({ props }: AdapterProps) {
  return (
    <ShadletIcon
      name={text(props.name) ?? "circle-alert"}
      size={(props.size as number | string | undefined) ?? 16}
      strokeWidth={number(props.strokeWidth) ?? 2}
      color={text(props.color)}
      label={text(props.label)}
      className={className(props)}
    />
  );
}

export function KbdAdapter({ props, children }: AdapterProps) {
  return (
    <kbd
      className={cn(
        "pointer-events-none inline-flex h-5 w-fit min-w-5 items-center justify-center gap-1 rounded-sm bg-muted px-1 font-sans text-xs font-medium text-muted-foreground select-none",
        className(props),
      )}
    >
      {children}
    </kbd>
  );
}

export function SeparatorAdapter({ props }: AdapterProps) {
  return (
    <Separator
      orientation={props.orientation === "vertical" ? "vertical" : "horizontal"}
      className={className(props)}
    />
  );
}

export function SkeletonAdapter({ props }: AdapterProps) {
  return <Skeleton className={className(props)} style={style(props)} />;
}

export function SpinnerAdapter({ props }: AdapterProps) {
  const size = props.size ?? 16;
  return (
    <span
      role="status"
      aria-label={text(props.label) ?? "loading"}
      className={cn(
        "inline-flex shrink-0 [&>svg]:size-full [&>svg]:animate-spin",
        className(props),
      )}
      style={{
        width: size as number | string,
        height: size as number | string,
      }}
    >
      <Spinner />
    </span>
  );
}

export function BadgeAdapter({ props, children }: AdapterProps) {
  return (
    <Badge
      variant={
        (text(props.variant) as
          "default" | "secondary" | "destructive" | "outline" | undefined) ??
        "default"
      }
      className={className(props)}
    >
      {children}
    </Badge>
  );
}

export function AvatarAdapter({ props }: AdapterProps) {
  const alt = text(props.alt) ?? "";
  const fallback = text(props.fallback) ?? alt.slice(0, 2).toUpperCase();
  return (
    <Avatar
      size={
        (text(props.size) as "sm" | "default" | "lg" | undefined) ?? "default"
      }
      className={className(props)}
    >
      {text(props.src) ? <AvatarImage src={text(props.src)} alt={alt} /> : null}
      <AvatarFallback>{fallback}</AvatarFallback>
    </Avatar>
  );
}

export function AspectRatioAdapter({ props, children }: AdapterProps) {
  return (
    <AspectRatio
      ratio={number(props.ratio) ?? 16 / 9}
      className={className(props)}
    >
      {children}
    </AspectRatio>
  );
}

export function AlertAdapter({ props, children }: AdapterProps) {
  return (
    <Alert
      variant={
        (text(props.variant) as "default" | "destructive" | undefined) ??
        "default"
      }
      className={className(props)}
    >
      {iconFor(props.icon)}
      {text(props.title) ? <AlertTitle>{text(props.title)}</AlertTitle> : null}
      {text(props.description) ? (
        <AlertDescription>{text(props.description)}</AlertDescription>
      ) : null}
      {children}
    </Alert>
  );
}

export function EmptyAdapter({ props, children, slots }: AdapterProps) {
  return (
    <Empty className={className(props)}>
      <EmptyHeader>
        {props.icon ? (
          <EmptyMedia variant="icon">{iconFor(props.icon)}</EmptyMedia>
        ) : null}
        {text(props.title) ? (
          <EmptyTitle>{text(props.title)}</EmptyTitle>
        ) : null}
        {text(props.description) ? (
          <EmptyDescription>{text(props.description)}</EmptyDescription>
        ) : null}
      </EmptyHeader>
      {children ? <EmptyContent>{children}</EmptyContent> : null}
      {slots.action ? <EmptyContent>{slots.action}</EmptyContent> : null}
    </Empty>
  );
}

export function ItemAdapter({ props, children, slots }: AdapterProps) {
  return (
    <Item className={className(props)}>
      {slots.media ? <ItemMedia>{slots.media}</ItemMedia> : null}
      <ItemContent>
        {text(props.title) ? <ItemTitle>{text(props.title)}</ItemTitle> : null}
        {text(props.description) ? (
          <ItemDescription>{text(props.description)}</ItemDescription>
        ) : null}
        {children}
      </ItemContent>
      {slots.actions ? <ItemActions>{slots.actions}</ItemActions> : null}
    </Item>
  );
}

export function ProgressAdapter({ props }: AdapterProps) {
  return (
    <Progress
      value={number(props.value) ?? 0}
      max={number(props.max) ?? 100}
      className={className(props)}
    >
      {text(props.label) ? (
        <ProgressLabel>{text(props.label)}</ProgressLabel>
      ) : null}
      <ProgressValue />
    </Progress>
  );
}

export function ToggleAdapter({
  props,
  children,
  events,
  dispatch,
}: AdapterProps) {
  const controlled = "value_change" in events || props.pressed !== null;
  return (
    <Toggle
      pressed={controlled ? boolean(props.pressed) : undefined}
      defaultPressed={!controlled ? boolean(props.pressed) : undefined}
      variant={
        (text(props.variant) as "default" | "outline" | undefined) ?? "default"
      }
      size={
        (text(props.size) as "default" | "sm" | "lg" | undefined) ?? "default"
      }
      disabled={boolean(props.disabled)}
      className={className(props)}
      onPressedChange={(pressed) =>
        dispatch("value_change", { value: pressed })
      }
    >
      {children}
    </Toggle>
  );
}

export function ToggleGroupAdapter({ props, dispatch }: AdapterProps) {
  const multiple = props.type === "multiple";
  const raw = props.value;
  const value = Array.isArray(raw)
    ? raw.map(String)
    : raw === null || raw === undefined || raw === ""
      ? []
      : [String(raw)];
  return (
    <ToggleGroup
      multiple={multiple}
      value={value}
      variant={
        (text(props.variant) as "default" | "outline" | undefined) ?? "default"
      }
      size={
        (text(props.size) as "default" | "sm" | "lg" | undefined) ?? "default"
      }
      orientation={props.orientation === "vertical" ? "vertical" : "horizontal"}
      disabled={boolean(props.disabled)}
      className={className(props)}
      onValueChange={(next) => {
        const result = multiple ? next : (next[0] ?? null);
        dispatch("value_change", { value: result });
      }}
    >
      {list(props.items).map((item) => {
        const valueText = text(item.value) ?? "";
        return (
          <ToggleGroupItem
            key={valueText}
            value={valueText}
            aria-label={text(item.label)}
            disabled={boolean(item.disabled)}
          >
            {item.icon ? iconFor(item.icon) : null}
            {text(item.label)}
          </ToggleGroupItem>
        );
      })}
    </ToggleGroup>
  );
}

export function ButtonGroupAdapter({ props, children }: AdapterProps) {
  return (
    <ButtonGroup
      orientation={props.orientation === "vertical" ? "vertical" : "horizontal"}
      className={className(props)}
    >
      {children}
    </ButtonGroup>
  );
}

export function InputGroupAdapter({ props, slots }: AdapterProps) {
  return (
    <InputGroup className={className(props)}>
      {slots.start ? (
        <InputGroupAddon align="inline-start">{slots.start}</InputGroupAddon>
      ) : null}
      {slots.input}
      {slots.end ? (
        <InputGroupAddon align="inline-end">{slots.end}</InputGroupAddon>
      ) : null}
    </InputGroup>
  );
}

export function ThemeToggleAdapter({ props }: AdapterProps) {
  const { theme, setTheme } = useTheme();
  return (
    <div
      role="group"
      aria-label="theme"
      className={cn(
        "inline-flex items-center gap-1 rounded-lg border p-1",
        className(props),
      )}
    >
      {[
        ["light", Sun],
        ["dark", Moon],
        ["system", Monitor],
      ].map(([value, Icon]) => (
        <Button
          key={value as string}
          type="button"
          size="icon-sm"
          variant={theme === value ? "secondary" : "ghost"}
          aria-label={`${value} theme`}
          aria-pressed={theme === value}
          onClick={() => setTheme(value as "light" | "dark" | "system")}
        >
          <Icon />
        </Button>
      ))}
    </div>
  );
}
