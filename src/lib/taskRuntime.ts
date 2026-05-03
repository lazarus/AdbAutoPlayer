// Cross-component runtime state for the task UI:
//   - Per-profile task stats (elapsed, cleared/failed/issue/restart counts)
//   - Per-profile log entries
//
// Centralized so that switching layouts (full <-> mini mode) doesn't lose
// state. Components subscribe to these stores instead of holding local
// state and running their own listeners.

import { writable, get } from "svelte/store";
import { listen } from "@tauri-apps/api/event";
import { Instant } from "@js-joda/core";
import { EventNames } from "$lib/log/eventNames";
import {
  profileStates,
  appSettings,
  debugLogLevelOverwrite,
} from "$lib/stores";
import {
  formatMessage,
  logMessageToTextDisplayCardItem,
} from "$lib/log/logHelper";
import type { TextDisplayCardItem } from "$lib/log/logHelper";

export interface ProfileTaskStats {
  startTime: number | null;
  elapsedSeconds: number;
  issueCount: number;
  restartCount: number;
  clearedCount: number;
  failureCount: number;
}

const emptyStats = (): ProfileTaskStats => ({
  startTime: null,
  elapsedSeconds: 0,
  issueCount: 0,
  restartCount: 0,
  clearedCount: 0,
  failureCount: 0,
});

export const taskStats = writable<Record<number, ProfileTaskStats>>({});
export const profileLogEntries = writable<
  Record<number, TextDisplayCardItem[]>
>({});

const MAX_ENTRIES = 1000;

const logLevelOrder: Record<string, number> = {
  DEBUG: 0,
  INFO: 1,
  WARNING: 2,
  ERROR: 3,
  FATAL: 4,
};

interface TaskCompletedEvent {
  profile_index: number;
  msg: string | null;
  exit_code: number | null;
}

let initialized = false;

export async function initTaskRuntime(): Promise<void> {
  if (initialized) return;
  initialized = true;

  // Elapsed-seconds tick for any profile with an active task
  setInterval(() => {
    taskStats.update((all) => {
      let changed = false;
      const next = { ...all };
      for (const k of Object.keys(next)) {
        const idx = +k;
        const s = next[idx];
        if (s.startTime) {
          const newVal = Math.max(
            0,
            Math.floor((Date.now() - s.startTime) / 1000),
          );
          if (newVal !== s.elapsedSeconds) {
            next[idx] = { ...s, elapsedSeconds: newVal };
            changed = true;
          }
        }
      }
      return changed ? next : all;
    });
  }, 1000);

  // Detect task-start / task-end transitions to reset stats appropriately
  const prevTask: Record<number, string | null> = {};
  profileStates.subscribe((states) => {
    for (let i = 0; i < states.length; i++) {
      const cur = states[i]?.active_task ?? null;
      const prev = prevTask[i] ?? null;
      if (cur !== prev) {
        onTaskTransition(i, !!cur);
        prevTask[i] = cur;
      }
    }
  });

  await listen<any>(EventNames.LOG_MESSAGE, (event) => {
    const msg = event.payload;
    const idx = msg.profile_index;

    // --- Stats: only count while the task is actually running ---
    const states = get(profileStates);
    if (
      idx !== undefined &&
      idx !== null &&
      states[idx]?.active_task &&
      typeof msg.message === "string"
    ) {
      const text: string = msg.message;
      taskStats.update((all) => {
        const cur = all[idx] ?? emptyStats();
        const next = { ...cur };
        if (["WARNING", "ERROR", "FATAL"].includes(msg.level))
          next.issueCount++;
        if (/restart/i.test(text)) next.restartCount++;
        if (/\bcleared:?\s*\d+/i.test(text)) next.clearedCount++;
        else if (
          /\b(completed|won|success)\b/i.test(text) &&
          msg.level === "INFO"
        )
          next.clearedCount++;
        if (/\b(failed|crashed|frozen|lost)\b/i.test(text)) next.failureCount++;
        return { ...all, [idx]: next };
      });
    }

    // --- Log entries (filtered by configured level / debug override) ---
    const settings = get(appSettings);
    const configLogLevel = (settings?.logging?.level as string) ?? "INFO";
    const overrides = get(debugLogLevelOverwrite);
    const alwaysLogDebug =
      idx !== undefined && idx !== null ? (overrides[idx] ?? false) : false;

    if (
      alwaysLogDebug ||
      logLevelOrder[msg.level] >= logLevelOrder[configLogLevel]
    ) {
      const entry = logMessageToTextDisplayCardItem(msg) as any;
      entry.level = msg.level;
      insertLogEntry(idx, entry);
    }
  });

  await listen<TaskCompletedEvent>(EventNames.TASK_COMPLETED, (event) => {
    if (!event.payload) return;
    addSummaryMessage(event.payload);
  });
}

function onTaskTransition(idx: number, hasTask: boolean): void {
  taskStats.update((all) => {
    const cur = all[idx];
    if (hasTask && !cur?.startTime) {
      // Task just started — reset counts
      return { ...all, [idx]: { ...emptyStats(), startTime: Date.now() } };
    }
    if (!hasTask && cur?.startTime) {
      // Task ended — clear startTime so timer stops, keep final counts visible
      return { ...all, [idx]: { ...cur, startTime: null } };
    }
    return all;
  });
}

function insertLogEntry(
  index: number | undefined | null,
  entry: TextDisplayCardItem,
): void {
  const settings = get(appSettings);
  const insertCount =
    index === undefined || index === null
      ? (settings?.profiles?.profiles?.length ?? 1)
      : 1;
  const startIndex = index ?? 0;

  profileLogEntries.update((all) => {
    const next = { ...all };
    for (let i = 0; i < insertCount; i++) {
      const targetIndex = startIndex + i;
      const arr = next[targetIndex] ? next[targetIndex].slice() : [];
      arr.push(entry);
      if (arr.length > MAX_ENTRIES) arr.shift();
      next[targetIndex] = arr;
    }
    return next;
  });
}

function addSummaryMessage(summary: TaskCompletedEvent): void {
  if (!summary.msg) return;
  const summaryMessage = formatMessage(summary.msg);
  if (summaryMessage === "") return;

  const entry: any = {
    message: summaryMessage,
    timestamp: Instant.now(),
    html_class: "whitespace-pre-wrap text-secondary-500",
    level: "INFO",
  };
  insertLogEntry(summary.profile_index, entry);
}

export function clearLogForProfile(idx: number): void {
  profileLogEntries.update((all) => ({ ...all, [idx]: [] }));
}

export function getElapsedString(s: number): string {
  const h = Math.floor(s / 3600);
  const m = Math.floor((s % 3600) / 60);
  const ss = s % 60;
  const pad = (n: number) => String(n).padStart(2, "0");
  return h > 0 ? `${pad(h)}:${pad(m)}:${pad(ss)}` : `${pad(m)}:${pad(ss)}`;
}
