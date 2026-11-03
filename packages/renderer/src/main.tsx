import React from "react";
import ReactDOM from "react-dom/client";
import { ShadletRoot } from "@/runtime/root";
import { loadExtension } from "@/extensions";
import "@/styles/globals.css";

declare global {
  interface Window {
    React: typeof React;
    shadlet: { loadExtension: typeof loadExtension };
  }
}

window.React = React;
window.shadlet = { loadExtension };

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <ShadletRoot />
  </React.StrictMode>,
);
