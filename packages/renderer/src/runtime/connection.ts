import {
  PROTOCOL_VERSION,
  parseServerMessage,
  type ClientMessage,
  type ServerMessage,
} from "@/protocol/schema";

export type ConnectionStatus =
  "connecting" | "connected" | "disconnected" | "incompatible";

export type DesktopRuntimeConfig = {
  apiBase: string;
  token: string;
  platform: "desktop";
};

type DesktopBridge = {
  config?: DesktopRuntimeConfig;
  invoke?: (
    method: string,
    params: Record<string, unknown>,
  ) => Promise<unknown>;
};

declare global {
  interface Window {
    shadletDesktop?: DesktopBridge;
  }
}

const DESKTOP_METHODS = new Set([
  "notify",
  "open_file",
  "save_file",
  "clipboard_read",
  "clipboard_write",
  "set_window_title",
  "set_window_size",
  "minimize",
  "maximize",
  "close_window",
  "open_external",
  "set_menu",
  "get_version",
]);

function websocketUrl(apiBase?: string): string {
  if (apiBase) {
    const url = new URL(apiBase);
    url.protocol = url.protocol === "https:" ? "wss:" : "ws:";
    url.pathname = "/ws";
    url.search = "";
    return url.toString();
  }
  const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
  return `${protocol}//${window.location.host}/ws`;
}

export function getDesktopConfig(): DesktopRuntimeConfig | null {
  const config = window.shadletDesktop?.config;
  if (!config || config.platform !== "desktop") return null;
  return config;
}

export class ShadletConnection {
  private socket: WebSocket | null = null;
  private reconnectTimer: number | null = null;
  private pingTimer: number | null = null;
  private attempts = 0;
  private disposed = false;
  private seq = 0;
  private token: string | null = null;
  private readonly desktop = getDesktopConfig();
  private readonly url: string;

  constructor(
    private readonly onMessage: (message: ServerMessage) => void,
    private readonly onStatus: (status: ConnectionStatus) => void,
  ) {
    this.url = websocketUrl(this.desktop?.apiBase);
    this.token =
      this.desktop?.token ??
      window.sessionStorage.getItem("shadlet-session-token");
  }

  connect(): void {
    if (this.disposed) return;
    this.onStatus("connecting");
    const socket = new WebSocket(this.url);
    this.socket = socket;

    socket.addEventListener("open", () => {
      this.attempts = 0;
      this.send({
        type: "hello",
        protocol_min: PROTOCOL_VERSION,
        protocol_max: PROTOCOL_VERSION,
        path: window.location.pathname || "/",
        token: this.token,
        platform: this.desktop ? "desktop" : "web",
      });
      this.startPing();
    });

    socket.addEventListener("message", (event) => {
      let message: ServerMessage;
      try {
        message = parseServerMessage(JSON.parse(String(event.data)));
      } catch (error) {
        console.error("[shadlet] rejected server message", error);
        return;
      }
      if (message.type === "init") {
        this.token = message.session_token ?? this.token;
        if (this.token && !this.desktop) {
          window.sessionStorage.setItem("shadlet-session-token", this.token);
        }
        this.onStatus("connected");
      }
      if (message.type === "desktop_request") {
        void this.handleDesktopRequest(
          message.id,
          message.method,
          message.params,
        );
        return;
      }
      this.onMessage(message);
    });

    socket.addEventListener("close", () => {
      this.stopPing();
      this.socket = null;
      if (this.disposed) return;
      this.onStatus("disconnected");
      // If we are in web browser mode, a disconnect during dev usually means the server is restarting.
      // After a short timeout, auto-refresh window once the server comes back up.
      this.scheduleReconnect();
    });

    socket.addEventListener("error", () => {
      if (socket.readyState !== WebSocket.OPEN) {
        socket.close();
      }
    });
  }

  private async handleDesktopRequest(
    id: string,
    method: string,
    params: Record<string, unknown>,
  ): Promise<void> {
    const bridge = window.shadletDesktop;
    if (!bridge?.invoke || !DESKTOP_METHODS.has(method)) {
      this.send({
        type: "desktop_result",
        id,
        ok: false,
        error: "desktop operation is not available",
      });
      return;
    }
    try {
      const result = await bridge.invoke(method, params);
      this.send({ type: "desktop_result", id, ok: true, result });
    } catch (error) {
      this.send({
        type: "desktop_result",
        id,
        ok: false,
        error: error instanceof Error ? error.message : String(error),
      });
    }
  }

  private scheduleReconnect(): void {
    if (this.reconnectTimer !== null || this.disposed) return;
    const delay = Math.min(3000, 400 * 2 ** this.attempts);
    this.attempts += 1;
    this.reconnectTimer = window.setTimeout(() => {
      this.reconnectTimer = null;
      this.connect();
    }, delay);
  }

  private startPing(): void {
    this.stopPing();
    this.pingTimer = window.setInterval(() => {
      this.send({ type: "ping", seq: this.nextSeq() });
    }, 25_000);
  }

  private stopPing(): void {
    if (this.pingTimer !== null) {
      window.clearInterval(this.pingTimer);
      this.pingTimer = null;
    }
  }

  private nextSeq(): number {
    this.seq += 1;
    return this.seq;
  }

  send(message: ClientMessage): void {
    if (!this.socket || this.socket.readyState !== WebSocket.OPEN) return;
    this.socket.send(JSON.stringify(message));
  }

  sendEvent(
    eventId: string,
    payload: Record<string, unknown>,
    requestId?: string,
  ): void {
    this.send({
      type: "event",
      seq: this.nextSeq(),
      event_id: eventId,
      payload,
      request_id: requestId,
    });
  }

  navigate(path: string): void {
    this.send({ type: "navigate", seq: this.nextSeq(), path });
  }

  destroy(): void {
    this.disposed = true;
    this.stopPing();
    if (this.reconnectTimer !== null) {
      window.clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }
    this.socket?.close();
    this.socket = null;
  }
}
