import * as React from "react";
import type { ShadletNode } from "@/protocol/schema";
import { registry } from "@/runtime/registry";
import type { AdapterProps } from "@/shadlet/types";

type TreeContextValue = {
  onEvent: (eventId: string, payload: Record<string, unknown>) => void;
  navigate: (path: string) => void;
  route: string;
};

const TreeContext = React.createContext<TreeContextValue | null>(null);

class NodeErrorBoundary extends React.Component<
  { children: React.ReactNode; nodeType: string },
  { error: Error | null }
> {
  state: { error: Error | null } = { error: null };

  static getDerivedStateFromError(error: Error) {
    return { error };
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

  const Adapter = registry[node.type];
  if (!Adapter) {
    return (
      <div role="alert" className="shadlet-error">
        unknown component type: {node.type}
      </div>
    );
  }

  const children = node.children.map((child) => renderNode(child, context));
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

  return (
    <NodeErrorBoundary key={node.id} nodeType={node.type}>
      <Adapter {...adapterProps} />
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
    () => ({ onEvent, navigate, route }),
    [onEvent, navigate, route],
  );
  return (
    <TreeContext.Provider value={context}>
      {renderNode(tree, context)}
    </TreeContext.Provider>
  );
}
