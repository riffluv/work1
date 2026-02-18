import { mkdir, readFile, writeFile } from "node:fs/promises";
import path from "node:path";

export type WebhookLogEntry = {
  id: string;
  type: string;
  createdAt: string;
  livemode: boolean;
  amountTotal: number | null;
  currency: string | null;
  customerEmail: string | null;
  sessionId: string | null;
  metadata: Record<string, string> | null;
};

const dataDir = path.join(process.cwd(), "data");
const dataFile = path.join(dataDir, "webhook-events.json");

async function ensureDataFile() {
  await mkdir(dataDir, { recursive: true });

  try {
    await readFile(dataFile, "utf-8");
  } catch {
    await writeFile(dataFile, "[]\n", "utf-8");
  }
}

export async function readWebhookEvents(): Promise<WebhookLogEntry[]> {
  await ensureDataFile();
  const raw = await readFile(dataFile, "utf-8");

  try {
    const parsed = JSON.parse(raw) as WebhookLogEntry[];
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    return [];
  }
}

export async function appendWebhookEvent(entry: WebhookLogEntry): Promise<void> {
  const current = await readWebhookEvents();
  const next = [entry, ...current].slice(0, 120);
  await writeFile(dataFile, `${JSON.stringify(next, null, 2)}\n`, "utf-8");
}
