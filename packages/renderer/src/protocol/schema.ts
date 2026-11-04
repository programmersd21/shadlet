import { z } from "zod";

export const PROTOCOL_VERSION = 2;
export const SUPPORTED_PROTOCOL_VERSIONS = [2] as const;

const jsonValueSchema: z.ZodType<unknown> = z.lazy(() =>
  z.union([
    z.string(),
    z.number(),
    z.boolean(),
    z.null(),
    z.array(jsonValueSchema),
    z.record(z.string(), jsonValueSchema),
  ]),
);

export type ShadletNode = {
  id: string;
  type: string;
  props: Record<string, unknown>;
  children: ShadletNode[];
  events: Record<string, string>;
  slots: Record<string, ShadletNode[]>;
  text: string | null;
};

export const nodeSchema: z.ZodType<ShadletNode> = z.lazy(() =>
  z
    .object({
      id: z.string().min(1),
      type: z.string().min(1),
      props: z.record(z.string(), jsonValueSchema).default({}),
      children: z.array(nodeSchema).default([]),
      events: z.record(z.string(), z.string()).default({}),
      slots: z.record(z.string(), z.array(nodeSchema)).default({}),
      text: z.string().nullable().optional(),
    })
    .strict()
    .transform((node) => ({ ...node, text: node.text ?? null }))
    .superRefine((node, context) => {
      if (node.type === "#text" && node.text === null) {
        context.addIssue({
          code: z.ZodIssueCode.custom,
          message: "text nodes require text",
        });
      }
      if (node.type !== "#text" && node.text !== null) {
        context.addIssue({
          code: z.ZodIssueCode.custom,
          message: "element nodes cannot carry text",
        });
      }
      if (
        node.type === "#text" &&
        (node.children.length > 0 ||
          Object.keys(node.props).length > 0 ||
          Object.keys(node.events).length > 0 ||
          Object.keys(node.slots).length > 0)
      ) {
        context.addIssue({
          code: z.ZodIssueCode.custom,
          message: "text nodes cannot carry props, children, events or slots",
        });
      }
    }),
);

export type RouteInfo = { path: string; title: string };
export type ExtensionInfo = {
  name: string;
  version: string;
  entry_url: string;
  stylesheet_url?: string | null;
};
export type AppInfo = {
  title: string;
  version: string;
  theme: "light" | "dark" | "system";
  platform: "web";
};

const routeInfoSchema = z
  .object({
    path: z.string(),
    title: z.string(),
  })
  .strict();

const appInfoSchema = z
  .object({
    title: z.string(),
    version: z.string(),
    theme: z.enum(["light", "dark", "system"]).default("system"),
    platform: z.literal("web").default("web"),
    icon: z.string().nullable().optional(),
  })
  .strict();

const patchSchema = z
  .object({
    op: z.enum([
      "replace",
      "set_props",
      "set_children",
      "set_slots",
      "insert",
      "remove",
    ]),
    path: z.string(),
    node: nodeSchema.nullable().optional(),
    props: z.record(z.string(), jsonValueSchema).nullable().optional(),
    events: z.record(z.string(), z.string()).nullable().optional(),
    children: z.array(nodeSchema).nullable().optional(),
    slots: z.record(z.string(), z.array(nodeSchema)).nullable().optional(),
    index: z.number().int().nonnegative().nullable().optional(),
  })
  .strict()
  .superRefine((patch, context) => {
    const required: Record<string, string[]> = {
      replace: ["node"],
      set_props: ["props", "events"],
      set_children: ["children"],
      set_slots: ["slots"],
      insert: ["node", "index"],
      remove: ["index"],
    };
    for (const field of required[patch.op] ?? []) {
      if (patch[field as keyof typeof patch] == null) {
        context.addIssue({
          code: z.ZodIssueCode.custom,
          message: `patch ${patch.op} requires ${field}`,
        });
      }
    }
  });

export type ShadletPatch = z.infer<typeof patchSchema>;

const statePatchSchema = z
  .object({
    op: z.enum(["set", "delete"]),
    key: z.string(),
    value: jsonValueSchema.optional(),
  })
  .strict();

export type StatePatch = z.infer<typeof statePatchSchema>;

const initSchema = z
  .object({
    type: z.literal("init"),
    protocol: z.number().int(),
    app: appInfoSchema,
    route: routeInfoSchema,
    routes: z.array(routeInfoSchema),
    tree: nodeSchema,
    state: z.record(z.string(), jsonValueSchema).default({}),
    features: z.array(z.string()).default([]),
    extensions: z
      .array(
        z
          .object({
            name: z.string(),
            version: z.string(),
            entry_url: z.string(),
            stylesheet_url: z.string().nullable().optional(),
          })
          .strict(),
      )
      .default([]),
    session_token: z.string().nullable().optional(),
  })
  .strict();

const updateSchema = z
  .object({
    type: z.literal("update"),
    seq: z.number().int(),
    request_id: z.string().nullable().optional(),
    patches: z.array(patchSchema).default([]),
    state_patches: z.array(statePatchSchema).default([]),
    url: z.string().nullable().optional(),
    url_mode: z.enum(["push", "replace"]).nullable().optional(),
  })
  .strict();

const navigationSchema = z
  .object({
    type: z.literal("navigation"),
    seq: z.number().int(),
    route: routeInfoSchema,
    tree: nodeSchema,
    state: z.record(z.string(), jsonValueSchema).default({}),
    replace: z.boolean().default(false),
  })
  .strict();

const toastSchema = z
  .object({
    type: z.literal("toast"),
    level: z
      .enum(["default", "success", "error", "warning", "info"])
      .default("default"),
    message: z.string(),
    description: z.string().nullable().optional(),
    duration: z.number().int().nullable().optional(),
  })
  .strict();

const errorSchema = z
  .object({
    type: z.literal("error"),
    code: z.string(),
    message: z.string(),
    request_id: z.string().nullable().optional(),
    details: z.string().nullable().optional(),
    fatal: z.boolean().default(false),
  })
  .strict();

const pongSchema = z
  .object({
    type: z.literal("pong"),
    seq: z.number().int(),
  })
  .strict();

export const serverMessageSchema = z.discriminatedUnion("type", [
  initSchema,
  updateSchema,
  navigationSchema,
  toastSchema,
  errorSchema,
  pongSchema,
]);

export type ServerMessage = z.infer<typeof serverMessageSchema>;
export type InitMessage = z.infer<typeof initSchema>;
export type UpdateMessage = z.infer<typeof updateSchema>;
export type NavigationMessage = z.infer<typeof navigationSchema>;
export type ToastMessage = z.infer<typeof toastSchema>;
export type ErrorMessage = z.infer<typeof errorSchema>;

export const clientMessageSchema = z
  .discriminatedUnion("type", [
    z
      .object({
        type: z.literal("hello"),
        protocol_min: z.number().int().min(1),
        protocol_max: z.number().int().min(1),
        path: z.string().min(1).max(2048).startsWith("/"),
        token: z.string().max(512).nullable().optional(),
        platform: z.literal("web"),
        icon: z.string().nullable().optional(),
      })
      .strict(),
    z
      .object({
        type: z.literal("event"),
        seq: z.number().int(),
        event_id: z.string().min(1).max(128),
        request_id: z.string().nullable().optional(),
        payload: z.record(z.string(), jsonValueSchema).default({}),
      })
      .strict(),
    z
      .object({
        type: z.literal("navigate"),
        seq: z.number().int(),
        path: z.string().min(1).max(2048),
        replace: z.boolean().default(false),
      })
      .strict(),
    z
      .object({
        type: z.literal("ping"),
        seq: z.number().int(),
      })
      .strict(),
  ])
  .superRefine((message, context) => {
    if (
      message.type === "hello" &&
      message.protocol_min > message.protocol_max
    ) {
      context.addIssue({
        code: z.ZodIssueCode.custom,
        message: "protocol_min cannot be greater than protocol_max",
      });
    }
  });

export type ClientMessage = z.infer<typeof clientMessageSchema>;

export function parseServerMessage(value: unknown): ServerMessage {
  const result = serverMessageSchema.safeParse(value);
  if (!result.success) {
    throw new Error(`invalid server message: ${result.error.message}`);
  }
  return result.data;
}

export function parseClientMessage(value: unknown): ClientMessage {
  const result = clientMessageSchema.safeParse(value);
  if (!result.success) {
    throw new Error(`invalid client message: ${result.error.message}`);
  }
  return result.data;
}

export function negotiateProtocol(
  clientMin: number,
  clientMax: number,
): number {
  const common = SUPPORTED_PROTOCOL_VERSIONS.filter(
    (version) => version >= clientMin && version <= clientMax,
  );
  if (common.length === 0) {
    throw new Error(
      `protocol incompatible: client ${clientMin}..${clientMax}, server ${Math.min(...SUPPORTED_PROTOCOL_VERSIONS)}..${Math.max(...SUPPORTED_PROTOCOL_VERSIONS)}`,
    );
  }
  return Math.max(...common);
}
