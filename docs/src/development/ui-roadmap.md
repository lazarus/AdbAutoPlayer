# UI Roadmap & TODOs

Items considered during the modern UI refresh that are deferred to later iterations. Capturing motivation here so future contributors don't lose context.

## Task Scheduling

**What:** Allow users to schedule tasks to run at specific times or on intervals (e.g. "run AFK Stages every 6 hours", "start Fishing at 8pm daily").

**Why deferred:**
- Requires a backend scheduler (cron-like or interval-based) that survives app restarts
- Needs UI for calendar/recurrence pickers, conflict resolution between profiles, queue visualization
- Touches the task lifecycle (start/stop/queue) in non-trivial ways

**Sketch of UI surface:**
- Per-task "Schedule" button on the task card (next to Run)
- Slide-out drawer with: one-time vs recurring, time/day/interval pickers, "skip if already running" toggle
- Top-level upcoming-runs panel showing the next N scheduled executions across all profiles
- Toast on scheduled-task start/skip

**Backend touchpoints needed:**
- Persistent schedule store (per profile)
- Scheduler tick driver in the Python core
- New events: `TASK_SCHEDULED`, `TASK_SCHEDULE_FIRED`, `TASK_SCHEDULE_SKIPPED`

## Structured Task Progress Events

**What:** Replace the current best-effort log-message parsing for stats (stages/hr, success rate) with a dedicated `TASK_PROGRESS` event emitted by the Python core.

**Why deferred:** The frontend currently infers stats by pattern-matching log message text in [Hero.svelte](../../../src/lib/components/modern/Hero.svelte) (e.g. `cleared:\s*\d+`, `failed|crashed|frozen`). This works for AFK Journey stages but is fragile and game-specific.

**Proposed event shape:**
```ts
interface TaskProgressEvent {
  profile_index: number;
  task_label: string;
  // Discrete completion event
  completion?: { type: "stage" | "battle" | "round" | "match"; index?: number };
  // Failure event
  failure?: { reason: "crash" | "freeze" | "lost" | "timeout" | "other" };
  // Optional progress hint for progress bar UIs
  progress?: { current: number; target: number; unit: string };
}
```

**Frontend plumbing:**
- Listener in `Hero.svelte` (or a dedicated `taskStats` store) consumes the event
- Replace the regex-based counters with structured counts
- Enables the deferred progress ring / stage-N → stage-M progress bar from the design handoff

## Per-Task History & Sparklines

**What:** Show a mini line/bar chart on each task card representing the last 24h of completion vs. failure counts.

**Why deferred:**
- Requires persistent stats storage (sqlite or JSON ledger), keyed by `(profile, task, day)`
- Needs the structured-progress event above to populate it cleanly
- Adds a visual element that competes with the icon/label/run-state on the card; would need design iteration

## Toast Notification Polish

**What:** Slide-in stacked toasts in the top-right with type-specific icons (info / warn / error / success), auto-dismiss with severity-tuned timeouts, and a close button. Triggers on task start/stop, game crash, connection issues.

**Why deferred:** A toast system already exists at [src/lib/toast/](../../../src/lib/toast/) but uses basic text. Visual upgrade is purely cosmetic and lower priority than data-bearing features.

## Confirmation Dialogs

Open question from the design handoff:
- Should "Stop Task" prompt for confirmation when the task has been running > 5 minutes?
- Should "Clear Log" confirm? (Currently no — logs are ephemeral.)

Defer until users report accidental stops/clears.

## Accessibility & Keyboard Nav

**Currently implemented:** Ctrl/Cmd+K focuses search, Esc clears.

**Deferred:**
- Space-to-run when a task card is focused (needs focus-visible styling and tab order audit)
- Arrow-key navigation between task cards
- Screen reader labels on icon-only buttons
- Color-blind safe alternative cues (shapes/patterns) for status indicators
