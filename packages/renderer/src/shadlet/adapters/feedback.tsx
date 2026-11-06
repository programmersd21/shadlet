import * as React from "react";
import { toast } from "sonner";
import { DirectionProvider } from "@/components/ui/direction";
import {
  boolean,
  className,
  number,
  text,
  type AdapterProps,
} from "@/shadlet/types";

type ToastLevel = "default" | "success" | "error" | "warning" | "info";
type ToastPosition =
  | "top-left"
  | "top-right"
  | "bottom-left"
  | "bottom-right"
  | "top-center"
  | "bottom-center";

const toastPositions = new Set<string>([
  "top-left",
  "top-right",
  "bottom-left",
  "bottom-right",
  "top-center",
  "bottom-center",
]);

export function DirectionAdapter({ props, children }: AdapterProps) {
  const dir = props.dir === "rtl" ? "rtl" : "ltr";
  return (
    <DirectionProvider direction={dir}>
      <div dir={dir} data-slot="direction" className={className(props)}>
        {children}
      </div>
    </DirectionProvider>
  );
}

export function ToastAdapter({ props, events, dispatch }: AdapterProps) {
  const title = text(props.title) ?? "";
  const description = text(props.description);
  const level = (text(props.level) ?? "default") as ToastLevel;
  const duration = number(props.duration);
  const rawPosition = text(props.position);
  const position =
    rawPosition && toastPositions.has(rawPosition)
      ? (rawPosition as ToastPosition)
      : undefined;
  const closeButton = boolean(props.closeButton);
  const dismiss = events.dismiss;
  const toastClassName = className(props);

  React.useEffect(() => {
    if (!title) return;
    const options = {
      description: description ?? undefined,
      duration: duration ?? undefined,
      position: position ?? undefined,
      closeButton,
      className: toastClassName || undefined,
      onDismiss: dismiss ? () => dispatch("dismiss", {}) : undefined,
    };
    switch (level) {
      case "success":
        toast.success(title, options);
        break;
      case "error":
        toast.error(title, options);
        break;
      case "warning":
        toast.warning(title, options);
        break;
      case "info":
        toast.info(title, options);
        break;
      default:
        toast(title, options);
    }
  }, [
    title,
    description,
    level,
    duration,
    position,
    closeButton,
    toastClassName,
    dismiss,
    dispatch,
  ]);

  return null;
}
