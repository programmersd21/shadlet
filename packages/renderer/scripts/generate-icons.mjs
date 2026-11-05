// Generate the complete Lucide icon registry from the pinned lucide-react
// package. The generated JSON is loaded lazily by the renderer; the generated
// Python tuple gives application code an exact, low-cost name registry.
import { createHash } from "node:crypto";
import { readFile, writeFile } from "node:fs/promises";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

import { format } from "prettier";
import * as React from "react";
import { renderToStaticMarkup } from "react-dom/server";
import dynamicIconImports from "lucide-react/dynamicIconImports.mjs";

const here = dirname(fileURLToPath(import.meta.url));
const rendererRoot = dirname(here);
const repoRoot = dirname(dirname(rendererRoot));
const packageJson = JSON.parse(
  await readFile(join(rendererRoot, "node_modules/lucide-react/package.json"), "utf8"),
);
const version = packageJson.version;
const names = Object.keys(dynamicIconImports).sort();
const data = [];
const dataIndex = new Map();
const index = {};

for (const name of names) {
  const module = await dynamicIconImports[name]();
  const iconNode = module.__iconNode;
  if (!Array.isArray(iconNode)) {
    throw new Error(`Lucide icon ${name} has no icon node`);
  }
  const markup = renderToStaticMarkup(
    React.createElement(
      React.Fragment,
      null,
      ...iconNode.map(([tag, attributes], childIndex) =>
        React.createElement(tag, { ...attributes, key: childIndex }),
      ),
    ),
  );
  const digest = createHash("sha256").update(markup).digest("hex");
  let position = dataIndex.get(digest);
  if (position === undefined) {
    position = data.length;
    dataIndex.set(digest, position);
    data.push(markup);
  }
  index[name] = position;
}

const payload = { lucideVersion: version, names, data, index };
await writeFile(
  join(rendererRoot, "src/shadlet/icon-data.generated.json"),
  await format(JSON.stringify(payload), { parser: "json", printWidth: 80 }),
  "utf8",
);

const pythonLines = names.map((name) => `    ${JSON.stringify(name)},`).join("\n");
const python = `"""Generated from lucide-react ${version}. Do not edit by hand.

Regenerate with: npm run generate:icons (from packages/renderer).
"""

from __future__ import annotations

LUCIDE_VERSION = ${JSON.stringify(version)}

ICON_NAMES: tuple[str, ...] = (
${pythonLines}
)

__all__ = ["ICON_NAMES", "LUCIDE_VERSION"]
`;
await writeFile(
  join(repoRoot, "packages/python/shadlet/components/icon_data.py"),
  python,
  "utf8",
);

console.log(
  `generated ${names.length} icon names (${data.length} unique shapes) from lucide-react ${version}`,
);
