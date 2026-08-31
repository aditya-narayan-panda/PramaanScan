import { useCallback, useEffect, useState } from "react";

/**
 * PramaanScan's backend does not (yet) expose any listing/analytics endpoints
 * (no verification-log retrieval, no dashboard stats). Rather than fabricate
 * numbers, we keep a small, honest, browser-local record of actions the
 * current user has actually taken in this session/device — real data,
 * clearly scoped as "this device" rather than presented as backend analytics.
 */

export type ActivityKind =
  | "VERIFY_FILE"
  | "VERIFY_CODE"
  | "REGISTER_COMMUNICATION"
  | "ISSUE_DOCUMENT"
  | "GENERATE_KEY"
  | "REVOKE_KEY"
  | "LOOKUP_COMMUNICATION";

export interface ActivityEntry {
  id: string;
  kind: ActivityKind;
  label: string;
  result?: string;
  timestamp: string;
}

const STORAGE_KEY = "pramaanscan.local_activity";
const MAX_ENTRIES = 60;

function read(): ActivityEntry[] {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    return raw ? (JSON.parse(raw) as ActivityEntry[]) : [];
  } catch {
    return [];
  }
}

function write(entries: ActivityEntry[]) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(entries));
  window.dispatchEvent(new Event("pramaanscan:activity-changed"));
}

export function recordActivity(kind: ActivityKind, label: string, result?: string) {
  const entries = read();
  const entry: ActivityEntry = {
    id: Math.random().toString(36).slice(2),
    kind,
    label,
    result,
    timestamp: new Date().toISOString(),
  };
  const next = [entry, ...entries].slice(0, MAX_ENTRIES);
  write(next);
}

export function useLocalActivity() {
  const [entries, setEntries] = useState<ActivityEntry[]>(() => read());

  const refresh = useCallback(() => setEntries(read()), []);

  useEffect(() => {
    window.addEventListener("pramaanscan:activity-changed", refresh);
    window.addEventListener("storage", refresh);
    return () => {
      window.removeEventListener("pramaanscan:activity-changed", refresh);
      window.removeEventListener("storage", refresh);
    };
  }, [refresh]);

  const clear = useCallback(() => {
    write([]);
  }, []);

  return { entries, clear };
}
