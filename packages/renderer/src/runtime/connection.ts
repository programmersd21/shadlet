import {
  PROTOCOL_VERSION,
  SUPPORTED_PROTOCOL_VERSIONS,
  parseServerMessage,
  type ClientMessage,
  type ServerMessage,
} from "@/protocol/schema";

export type ConnectionStatus =
  "connecting" | "connected" | "disconnected" | "incompatible";

const SESSION_TOKEN_KEY = "shadlet-session-token";
const MAX_RECONNECT_DELAY_MS = 3000;

function websocketUrl(): string {
  const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
  return `${protocol}//${window.location.host}/ws`;
}

export class ShadletConnection {
  private socket: WebSocket | null = null;
  private reconnectTimer: number | null = null;
  private pingTimer: number | null = null;
  private attempts = 0;
  private disposed = false;
  private incompatible = false;
  private fatal = false;
  private seq = 0;
  private token: string | null;
  private readonly url = websocketUrl();

  constructor(
    private readonly onMessage: (message: ServerMessage) => void,
    private readonly onStatus: (status: ConnectionStatus) => void,
  ) {
    this.token = window.sessionStorage.getItem(SESSION_TOKEN_KEY);
  }

  connect(): void {
    if (this.disposed) return;
    this.incompatible = false;
    this.fatal = false;
    if (
      this.socket &&
      (this.socket.readyState === WebSocket.OPEN ||
        this.socket.readyState === WebSocket.CONNECTING)
    ) {
      return;
    }
    this.onStatus("connecting");
    const socket = new WebSocket(this.url);
    this.socket = socket;

    socket.addEventListener("open", () => {
      if (this.socket !== socket) return;
      this.attempts = 0;
      this.send({
        type: "hello",
        protocol_min: PROTOCOL_VERSION,
        protocol_max: PROTOCOL_VERSION,
        path: `${window.location.pathname || "/"}${window.location.search}`,
        token: this.token,
        platform: "web",
      });
      this.startPing();
    });

    socket.addEventListener("message", (event) => {
      if (this.socket !== socket) return;
      let message: ServerMessage;
      try {
        message = parseServerMessage(JSON.parse(String(event.data)));
      } catch (error) {
        console.error("[shadlet] rejected server message", error);
        return;
      }
      if (message.type === "error" && message.fatal) {
        this.fatal = true;
      }
      if (message.type === "init") {
        if (
          !(SUPPORTED_PROTOCOL_VERSIONS as readonly number[]).includes(
            message.protocol,
          )
        ) {
          this.incompatible = true;
          this.onStatus("incompatible");
          socket.close(1002, "protocol mismatch");
          return;
        }
        this.token = message.session_token ?? this.token;
        if (this.token) {
          window.sessionStorage.setItem(SESSION_TOKEN_KEY, this.token);
        }
        this.onStatus("connected");
      }
      this.onMessage(message);
    });

    socket.addEventListener("close", () => {
      if (this.socket !== socket) return;
      this.stopPing();
      this.socket = null;
      if (this.disposed) return;
      this.onStatus("disconnected");
      if (this.incompatible || this.fatal) return;
      this.scheduleReconnect();
    });

    socket.addEventListener("error", () => {
      if (socket.readyState !== WebSocket.OPEN) {
        socket.close();
      }
    });
  }

  /** Drop the current connection and reconnect immediately, preserving the session. */
  reconnectNow(): void {
    if (this.disposed) return;
    this.clearReconnectTimer();
    this.attempts = 0;
    const socket = this.socket;
    this.socket = null;
    this.stopPing();
    socket?.close();
    this.connect();
  }

  private scheduleReconnect(): void {
    if (this.reconnectTimer !== null || this.disposed) return;
    const delay = Math.min(MAX_RECONNECT_DELAY_MS, 400 * 2 ** this.attempts);
    this.attempts += 1;
    this.reconnectTimer = window.setTimeout(() => {
      this.reconnectTimer = null;
      this.connect();
    }, delay);
  }

  private clearReconnectTimer(): void {
    if (this.reconnectTimer !== null) {
      window.clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }
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

  navigate(path: string, replace = false): void {
    this.send({ type: "navigate", seq: this.nextSeq(), path, replace });
  }

  destroy(): void {
    this.disposed = true;
    this.stopPing();
    this.clearReconnectTimer();
    const socket = this.socket;
    this.socket = null;
    socket?.close();
  }
}
