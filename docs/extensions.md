# React extensions

shadlet ships its component library, but advanced developers are not trapped
inside it. Extensions are explicit React adapters registered at runtime.

```ts
import { loadExtension } from "@/extensions";
import { MyWidgetAdapter } from "./my-widget";

loadExtension({
  name: "acme-widgets",
  version: "1.0.0",
  components: { MyWidget: MyWidgetAdapter },
  styles: ".my-widget { ... }",
});
```

The adapter receives `AdapterProps` (props, children, slots, events, dispatch,
navigate, route, nodeId) and renders genuine React. Callbacks are never
serialised; use `dispatch(eventName, payload)` to invoke the Python handler
bound to that event id.

Custom React functions cannot be serialised into Python. Use explicit component
types and props only.
