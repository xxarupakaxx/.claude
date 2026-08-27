import { copyFileSync, mkdirSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const root = dirname(fileURLToPath(import.meta.url));
const packageRoot = join(root, "..");
const outputDir = join(packageRoot, "dist", "ui");

mkdirSync(outputDir, { recursive: true });

for (const fileName of ["diagram-viewer.html", "verification-viewer.html"]) {
  copyFileSync(join(packageRoot, "ui", fileName), join(outputDir, fileName));
}
