import { rm } from "node:fs/promises";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const root = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const dist = resolve(root, "dist");

if (!dist.startsWith(root)) {
  throw new Error(`Refusing to clean unexpected path: ${dist}`);
}

await rm(dist, { recursive: true, force: true });
