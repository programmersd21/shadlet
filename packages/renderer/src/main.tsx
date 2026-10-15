import React from "react";
import ReactDOM from "react-dom/client";
import { ShadletRoot } from "@/runtime/root";
import "@/styles/globals.css";

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <ShadletRoot />
  </React.StrictMode>,
);
