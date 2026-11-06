import { readdirSync, readFileSync } from "node:fs";
import { gzipSync } from "node:zlib";
import { join } from "node:path";
import { fileURLToPath } from "node:url";

const assetsDir = fileURLToPath(new URL("../dist/assets/", import.meta.url));
const files = readdirSync(assetsDir).filter((name) => name.endsWith(".js"));

const entryBudget = { minified: 1_100_000, gzip: 345_000 };
const totalBudget = { minified: 2_150_000, gzip: 610_000 };
const requiredLazyChunks = ["chart", "calendar", "carousel", "icon-data.generated"];

const rows = files.map((name) => {
  const contents = readFileSync(join(assetsDir, name));
  return {
    name,
    minified: contents.length,
    gzip: gzipSync(contents).length,
  };
});

rows.sort((a, b) => b.minified - a.minified);

const format = (value) => `${(value / 1000).toFixed(1)} kB`;
console.log("Renderer bundle report");
for (const row of rows) {
  console.log(`  ${row.name.padEnd(44)} ${format(row.minified).padStart(12)}  gzip ${format(row.gzip).padStart(10)}`);
}

const entry = rows.find((row) => /^index-.*\.js$/.test(row.name));
const totals = rows.reduce(
  (acc, row) => ({ minified: acc.minified + row.minified, gzip: acc.gzip + row.gzip }),
  { minified: 0, gzip: 0 },
);

const failures = [];
if (!entry) {
  failures.push("entry chunk index-*.js not found in dist/assets");
} else {
  if (entry.minified > entryBudget.minified) {
    failures.push(
      `entry chunk ${format(entry.minified)} exceeds ${format(entryBudget.minified)} minified budget`,
    );
  }
  if (entry.gzip > entryBudget.gzip) {
    failures.push(
      `entry chunk ${format(entry.gzip)} exceeds ${format(entryBudget.gzip)} gzip budget`,
    );
  }
}
if (totals.minified > totalBudget.minified) {
  failures.push(
    `total JavaScript ${format(totals.minified)} exceeds ${format(totalBudget.minified)} minified budget`,
  );
}
if (totals.gzip > totalBudget.gzip) {
  failures.push(
    `total JavaScript ${format(totals.gzip)} exceeds ${format(totalBudget.gzip)} gzip budget`,
  );
}
for (const prefix of requiredLazyChunks) {
  if (!rows.some((row) => row.name.includes(prefix))) {
    failures.push(`expected lazy chunk containing ${prefix} was not emitted`);
  }
}

if (failures.length > 0) {
  console.error("\nBundle budget check failed:");
  for (const failure of failures) console.error(`  - ${failure}`);
  process.exit(1);
}

console.log(
  `\nBundle budget OK: entry ${format(entry.minified)} / ${format(entry.gzip)} gzip, total ${format(totals.minified)} / ${format(totals.gzip)} gzip`,
);
