import type * as React from "react";
import type { AdapterProps } from "@/shadlet/types";
import { registerComponent } from "@/runtime/registry";

export type ShadletExtensionComponent = React.ComponentType<AdapterProps>;

export type ShadletExtension = {
  name: string;
  version: string;
  components?: Record<string, ShadletExtensionComponent>;
  styles?: string;
};

const loaded = new Set<string>();

export function loadExtension(extension: ShadletExtension): void {
  if (loaded.has(extension.name)) return;
  if (extension.components) {
    for (const [name, adapter] of Object.entries(extension.components)) {
      registerComponent(name, adapter);
    }
  }
  if (extension.styles && typeof document !== "undefined") {
    const style = document.createElement("style");
    style.dataset.shadletExtension = extension.name;
    style.textContent = extension.styles;
    document.head.appendChild(style);
  }
  loaded.add(extension.name);
}

export function isExtensionLoaded(name: string): boolean {
  return loaded.has(name);
}
