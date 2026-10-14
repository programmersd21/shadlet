import * as React from "react";
import { toast } from "sonner";
import { Toaster } from "@/components/ui/sonner";
import { Spinner } from "@/components/ui/spinner";
import type {
  ErrorMessage,
  InitMessage,
  ServerMessage,
  ShadletNode,
  ToastMessage,
} from "@/protocol/schema";
import { ShadletConnection, type ConnectionStatus } from "@/runtime/connection";
import { applyPatches } from "@/runtime/patch";
import { TreeRenderer } from "@/runtime/tree";
import { ThemeProvider, useTheme } from "@/themes/provider";

type AppState = InitMessage["app"];
type RouteState = InitMessage["route"];

function showToast(message: ToastMessage) {
  const options = {
    description: message.description ?? undefined,
    duration: message.duration ?? undefined,
  };
  switch (message.level) {
    case "success":
      toast.success(message.message, options);
      break;
    case "error":
      toast.error(message.message, options);
      break;
    case "warning":
      toast.warning(message.message, options);
      break;
    case "info":
      toast.info(message.message, options);
      break;
    default:
      toast(message.message, options);
  }
}

function ThemeBootstrap({ theme }: { theme: AppState["theme"] }) {
  const { setTheme } = useTheme();
  const applied = React.useRef(false);
  React.useEffect(() => {
    if (applied.current) return;
    applied.current = true;
    if (!window.localStorage.getItem("shadlet-theme") && theme !== "system") {
      setTheme(theme);
    }
  }, [setTheme, theme]);
  return null;
}

function Loading() {
  return (
    <div className="flex min-h-screen items-center justify-center">
      <div className="flex items-center gap-2 text-sm text-muted-foreground">
        <Spinner />
        connecting to shadlet runtime
      </div>
    </div>
  );
}

function ErrorPanel({ error }: { error: ErrorMessage }) {
  return (
    <main className="flex min-h-screen items-center justify-center p-6">
      <div className="w-full max-w-xl rounded-xl border bg-card p-6 shadow-sm">
        <p className="font-mono text-xs uppercase tracking-wide text-destructive">
          {error.code}
        </p>
        <h1 className="mt-2 text-lg font-semibold">runtime error</h1>
        <p className="mt-2 text-sm text-muted-foreground">{error.message}</p>
        {error.details ? (
          <pre className="mt-4 max-h-72 overflow-auto rounded-md bg-muted p-3 text-xs">
            {error.details}
          </pre>
        ) : null}
        <button
          type="button"
          className="mt-4 rounded-md bg-primary px-3 py-2 text-sm text-primary-foreground"
          onClick={() => window.location.reload()}
        >
          reload
        </button>
      </div>
    </main>
  );
}

function DisconnectedBanner({
  status,
  onReconnect,
}: {
  status: ConnectionStatus;
  onReconnect: () => void;
}) {
  if (status === "connected") return null;

  return (
    <div
      role="alert"
      className="fixed inset-x-0 top-0 z-[100] flex items-center justify-between border-b border-border bg-destructive/15 px-4 py-2.5 backdrop-blur-md transition-all duration-300"
    >
      <div className="flex items-center gap-2.5">
        <span className="relative flex h-2.5 w-2.5">
          <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-destructive opacity-75" />
          <span className="relative inline-flex h-2.5 w-2.5 rounded-full bg-destructive" />
        </span>
        <div className="flex flex-col sm:flex-row sm:items-center sm:gap-2">
          <span className="text-xs font-semibold tracking-wide text-foreground">
            Server disconnected
          </span>
          <span className="text-xs text-muted-foreground">
            {status === "incompatible"
              ? "Protocol version mismatch with host."
              : "Connecting to shadlet runtime in the background..."}
          </span>
        </div>
      </div>
      <div className="flex items-center gap-2">
        <button
          type="button"
          onClick={onReconnect}
          className="inline-flex items-center gap-1.5 rounded-md border border-border bg-background/80 px-2.5 py-1 text-xs font-medium text-foreground shadow-sm transition-colors hover:bg-muted active:scale-95"
        >
          <Spinner className="h-3 w-3" />
          Reconnect
        </button>
      </div>
    </div>
  );
}

export function ShadletRoot() {
  const [status, setStatus] = React.useState<ConnectionStatus>("connecting");
  const [tree, setTree] = React.useState<ShadletNode | null>(null);
  const [app, setApp] = React.useState<AppState | null>(null);
  const [route, setRoute] = React.useState<RouteState | null>(null);
  const [error, setError] = React.useState<ErrorMessage | null>(null);
  const connectionRef = React.useRef<ShadletConnection | null>(null);

  const handleMessage = React.useCallback((message: ServerMessage) => {
    switch (message.type) {
      case "init":
        setApp(message.app);
        setRoute(message.route);
        setTree(message.tree);
        setError(null);
        document.title = message.app.title;
        if (window.shadletDesktop?.invoke) {
          window.shadletDesktop.invoke("set_window_title", { title: message.app.title }).catch(() => {});
        }
        if (message.app.icon) {
          let link =
            document.querySelector<HTMLLinkElement>("link[rel~='icon']");
          if (!link) {
            link = document.createElement("link");
            link.rel = "icon";
            document.getElementsByTagName("head")[0].appendChild(link);
          }
          link.href = message.app.icon;
        }
        break;
      case "update":
        setTree((previous) => {
          if (!previous) return previous;
          try {
            return applyPatches(previous, message.patches);
          } catch (patchError) {
            console.error("[shadlet] failed to apply patch", patchError);
            return previous;
          }
        });
        break;
      case "navigation":
        setRoute(message.route);
        setTree(message.tree);
        setError(null);
        window.history.pushState({ shadlet: true }, "", message.route.path);
        window.scrollTo(0, 0);
        break;
      case "toast":
        showToast(message);
        break;
      case "error":
        setError(message);
        break;
      case "pong":
        break;
      case "reload":
        window.location.reload();
        break;
      default:
        break;
    }
  }, []);

  React.useEffect(() => {
    const connection = new ShadletConnection(handleMessage, setStatus);
    connectionRef.current = connection;
    connection.connect();
    return () => {
      connection.destroy();
      connectionRef.current = null;
    };
  }, [handleMessage]);

  React.useEffect(() => {
    const onPopState = () => {
      connectionRef.current?.navigate(window.location.pathname || "/");
    };
    window.addEventListener("popstate", onPopState);
    return () => window.removeEventListener("popstate", onPopState);
  }, []);

  const onEvent = React.useCallback(
    (eventId: string, payload: Record<string, unknown>) => {
      connectionRef.current?.sendEvent(eventId, payload);
    },
    [],
  );

  const navigate = React.useCallback((path: string) => {
    connectionRef.current?.navigate(path);
  }, []);

  const handleManualReconnect = React.useCallback(() => {
    connectionRef.current?.connect();
  }, []);

  if (error && error.fatal) {
    return <ErrorPanel error={error} />;
  }

  return (
    <ThemeProvider defaultTheme={(app?.theme as "light" | "dark" | "system") ?? "light"}>
      <ThemeBootstrap theme={(app?.theme as "light" | "dark" | "system") ?? "light"} />
      <DisconnectedBanner
        status={status}
        onReconnect={handleManualReconnect}
      />
      {tree && route ? (
        <div className={status !== "connected" ? "pt-10 transition-all duration-200" : ""}>
          <TreeRenderer
            tree={tree}
            onEvent={onEvent}
            navigate={navigate}
            route={route.path}
          />
        </div>
      ) : (
        <Loading />
      )}
      {error && !error.fatal ? (
        <div role="alert" className="shadlet-error">
          {error.code}: {error.message}
          {error.details ? `\n\n${error.details}` : ""}
        </div>
      ) : null}
      <Toaster />
    </ThemeProvider>
  );
}
