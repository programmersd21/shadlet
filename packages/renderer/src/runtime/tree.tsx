import * as React from "react";
import type { ShadletNode } from "@/protocol/schema";
import { getComponentAdapter } from "@/runtime/registry";
import type { AdapterProps } from "@/shadlet/types";

type TreeContextValue = {
  onEvent: (eventId: string, payload: Record<string, unknown>) => void;
  navigate: (path: string) => void;
  route: string;
  fingerprint: (node: ShadletNode) => string;
};

const TreeContext = React.createContext<TreeContextValue | null>(null);
function hashFingerprint(value: string, seed = 0x811c9dc5): string {
  let hash = seed;
  for (let index = 0; index < value.length; index += 1) {
    hash ^= value.charCodeAt(index);
    hash = Math.imul(hash, 0x01000193);
  }
  return (hash >>> 0).toString(36);
}

function createFingerprinter(): (node: ShadletNode) => string {
  const cache = new WeakMap<ShadletNode, string>();

  const fingerprint = (node: ShadletNode): string => {
    const cached = cache.get(node);
    if (cached !== undefined) return cached;

    let digest: string;
    if (node.type === "#text") {
      digest = hashFingerprint(`text:${node.text}`);
    } else {
      const children = node.children.map(fingerprint).join(",");
      const slots = Object.entries(node.slots)
        .map(([name, values]) => `${name}:${values.map(fingerprint).join(",")}`)
        .join(",");
      digest = hashFingerprint(
        `${node.type}:${JSON.stringify(node.props)}:${JSON.stringify(
          node.events,
        )}:${children}:${slots}`,
      );
    }
    cache.set(node, digest);
    return digest;
  };

  return fingerprint;
}

const FIELD_CONTROL_TYPES = new Set([
  "Input",
  "Textarea",
  "Checkbox",
  "Switch",
  "Slider",
  "Select",
  "NativeSelect",
  "RadioGroup",
  "Combobox",
  "InputOTP",
  "DatePicker",
]);

class NodeErrorBoundary extends React.Component<
  { children: React.ReactNode; nodeType: string; resetKey: string },
  { error: Error | null; resetKey: string }
> {
  state: { error: Error | null; resetKey: string } = {
    error: null,
    resetKey: this.props.resetKey,
  };

  static getDerivedStateFromError(error: Error) {
    return { error };
  }

  static getDerivedStateFromProps(
    props: { resetKey: string },
    state: { error: Error | null; resetKey: string },
  ) {
    if (props.resetKey !== state.resetKey) {
      return { error: null, resetKey: props.resetKey };
    }
    return null;
  }

  componentDidCatch(error: Error) {
    console.error(`[shadlet] component ${this.props.nodeType} failed`, error);
  }

  render() {
    if (this.state.error) {
      return (
        <div role="alert" className="shadlet-error">
          component {this.props.nodeType} failed: {this.state.error.message}
        </div>
      );
    }
    return this.props.children;
  }
}

function renderNode(
  node: ShadletNode,
  context: TreeContextValue,
): React.ReactNode {
  if (node.type === "#text") return node.text;

  const Adapter = getComponentAdapter(node.type);
  if (!Adapter) {
    return (
      <div role="alert" className="shadlet-error">
        unknown component type: {node.type}
      </div>
    );
  }

  const fieldLabelId =
    node.type === "Field" && typeof node.props.label === "string"
      ? `${node.id}-label`
      : undefined;
  const fieldControlId = fieldLabelId ? `${node.id}-control` : undefined;
  const children = node.children.map((child) =>
    fieldLabelId && fieldControlId && FIELD_CONTROL_TYPES.has(child.type)
      ? renderNode(
          {
            ...child,
            props: {
              ...child.props,
              id: fieldControlId,
              ariaLabelledBy: fieldLabelId,
            },
          },
          context,
        )
      : renderNode(child, context),
  );
  const slots = Object.fromEntries(
    Object.entries(node.slots).map(([name, values]) => [
      name,
      values.map((child) => renderNode(child, context)),
    ]),
  );

  const dispatch = (event: string, payload: Record<string, unknown> = {}) => {
    const eventId = node.events[event];
    if (!eventId) {
      console.warn(`[shadlet] no event binding for ${node.type}.${event}`);
      return;
    }
    context.onEvent(eventId, payload);
  };

  const adapterProps: AdapterProps = {
    props: node.props,
    children,
    slots,
    events: node.events,
    dispatch,
    navigate: context.navigate,
    route: context.route,
    nodeId: node.id,
  };

  const resetKey = `${node.type}:${context.fingerprint(node)}`;

  return (
    <NodeErrorBoundary key={node.id} nodeType={node.type} resetKey={resetKey}>
      <React.Suspense
        fallback={
          <div
            aria-busy="true"
            className="shadlet-loading"
            data-shadlet-loading={node.type}
          />
        }
      >
        <Adapter {...adapterProps} />
      </React.Suspense>
    </NodeErrorBoundary>
  );
}

export function TreeRenderer({
  tree,
  onEvent,
  navigate,
  route,
}: {
  tree: ShadletNode;
  onEvent: TreeContextValue["onEvent"];
  navigate: TreeContextValue["navigate"];
  route: string;
}) {
  const context = React.useMemo(
    () => ({ onEvent, navigate, route, fingerprint: createFingerprinter() }),
    [onEvent, navigate, route],
  );
  return (
    <TreeContext.Provider value={context}>
      {renderNode(tree, context)}
    </TreeContext.Provider>
  );
}
