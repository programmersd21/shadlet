import type * as React from "react";
import type { AdapterProps } from "@/shadlet/types";
import { registerExtensionComponents } from "@/runtime/registry";

export type ShadletExtensionComponent = React.ComponentType<AdapterProps>;
export type RemoteExtensionInfo = {
  name: string;
  version: string;
  entry_url: string;
  stylesheet_url?: string | null;
};

export type ShadletExtension = {
  name: string;
  version: string;
  components?: Record<string, ShadletExtensionComponent>;
  styles?: string;
};

const loaded = new Map<string, () => void>();
const remoteLoads = new Map<string, Promise<void>>();
const extensionNamePattern = /^[a-z][a-z0-9_-]{0,62}$/;
const versionPattern =
  /^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)(?:-[0-9A-Za-z.-]+)?$/;

export function loadExtension(extension: ShadletExtension): () => void {
  if (!extensionNamePattern.test(extension.name)) {
    throw new Error(`invalid extension name: ${extension.name}`);
  }
  if (!versionPattern.test(extension.version)) {
    throw new Error(`invalid extension version: ${extension.version}`);
  }
  if (loaded.has(extension.name)) {
    throw new Error(`extension is already loaded: ${extension.name}`);
  }
  if (!extension.components) {
    throw new Error(`extension ${extension.name} has no components`);
  }

  const unregisterComponents = registerExtensionComponents(
    extension.name,
    extension.components,
  );
  let style: HTMLStyleElement | undefined;
  try {
    if (extension.styles && typeof document !== "undefined") {
      style = document.createElement("style");
      style.dataset.shadletExtension = extension.name;
      style.textContent = extension.styles;
      document.head.appendChild(style);
    }
  } catch (error) {
    unregisterComponents();
    style?.remove();
    throw error;
  }
  const dispose = () => {
    unregisterComponents();
    style?.remove();
    loaded.delete(extension.name);
  };
  loaded.set(extension.name, dispose);
  return dispose;
}

export function isExtensionLoaded(name: string): boolean {
  return loaded.has(name);
}

export function loadRemoteExtension(info: RemoteExtensionInfo): Promise<void> {
  if (isExtensionLoaded(info.name)) return Promise.resolve();
  const pending = remoteLoads.get(info.name);
  if (pending) return pending;

  let style: HTMLLinkElement | undefined;
  const loadStyles = info.stylesheet_url
    ? new Promise<void>((resolve, reject) => {
        style = document.createElement("link");
        style.rel = "stylesheet";
        style.href = info.stylesheet_url ?? "";
        style.dataset.shadletExtension = info.name;
        style.onload = () => resolve();
        style.onerror = () =>
          reject(new Error(`failed to load extension styles: ${info.name}`));
        document.head.appendChild(style);
      })
    : Promise.resolve();
  const load = loadStyles
    .then(
      () =>
        new Promise<void>((resolve, reject) => {
          const script = document.createElement("script");
          script.src = info.entry_url;
          script.async = true;
          script.dataset.shadletExtension = info.name;
          script.onload = () => {
            script.remove();
            if (!isExtensionLoaded(info.name)) {
              style?.remove();
              reject(
                new Error(
                  `extension bundle did not register itself: ${info.name}@${info.version}`,
                ),
              );
              return;
            }
            resolve();
          };
          script.onerror = () => {
            script.remove();
            style?.remove();
            reject(
              new Error(
                `failed to load extension: ${info.name}@${info.version}`,
              ),
            );
          };
          document.head.appendChild(script);
        }),
    )
    .catch((error: unknown) => {
      style?.remove();
      throw error;
    });
  remoteLoads.set(info.name, load);
  return load;
}
