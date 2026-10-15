import type { CSSProperties, ReactNode } from "react";

export type AdapterProps = {
  props: Record<string, unknown>;
  children: ReactNode;
  slots: Record<string, ReactNode>;
  events: Record<string, string>;
  dispatch: (event: string, payload?: Record<string, unknown>) => void;
  navigate: (path: string) => void;
  route: string;
  nodeId: string;
};

export function text(value: unknown): string | undefined {
  return typeof value === "string" ? value : undefined;
}

export function number(value: unknown): number | undefined {
  return typeof value === "number" && Number.isFinite(value)
    ? value
    : undefined;
}

export function boolean(value: unknown): boolean {
  return value === true;
}

export function record(value: unknown): Record<string, unknown> {
  return value !== null && typeof value === "object" && !Array.isArray(value)
    ? (value as Record<string, unknown>)
    : {};
}

export function list<T = Record<string, unknown>>(value: unknown): T[] {
  return Array.isArray(value) ? (value as T[]) : [];
}

export function className(props: Record<string, unknown>): string | undefined {
  return text(props.className);
}

export function style(
  props: Record<string, unknown>,
): CSSProperties | undefined {
  const value = props.style;
  return value !== null && typeof value === "object" && !Array.isArray(value)
    ? (value as CSSProperties)
    : undefined;
}

export function isBound(events: Record<string, string>, name: string): boolean {
  return events[name] !== undefined;
}

export function controlled(
  events: Record<string, string>,
  eventName: string,
  value: unknown,
): boolean {
  return isBound(events, eventName) || (value !== undefined && value !== null);
}

export function changePayload(
  event: React.ChangeEvent<
    HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement
  >,
): Record<string, unknown> {
  const target = event.target;
  if (target instanceof HTMLInputElement && target.type === "checkbox") {
    return { value: target.checked, checked: target.checked };
  }
  return { value: target.value };
}

export function formPayload(form: HTMLFormElement): Record<string, unknown> {
  const result: Record<string, unknown> = {};
  for (const [key, value] of new FormData(form).entries()) {
    if (key in result) {
      const previous = result[key];
      result[key] = Array.isArray(previous)
        ? [...previous, value]
        : [previous, value];
    } else {
      result[key] = value;
    }
  }
  return result;
}

export function errorMessage(error: unknown): string {
  return error instanceof Error ? error.message : String(error);
}
