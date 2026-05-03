<script lang="ts">
  import { t } from "$lib/i18n/i18n";
  import { activeProfile, profileStates, uiState } from "$lib/stores";
  import { get } from "svelte/store";
  import { onMount } from "svelte";
  import { listen } from "@tauri-apps/api/event";
  import { EventNames } from "$lib/log/eventNames";
  import { getGameIcon } from "$lib/utils/gameIcons";
  import LogPanel from "$lib/components/modern/LogPanel.svelte";

  interface Props {
    onStop: () => void;
    onTogglePin: () => void;
    onToggleLog: () => void;
    onExitMini: () => void;
  }

  let { onStop, onTogglePin, onToggleLog, onExitMini }: Props = $props();

  const profile = $derived($profileStates[$activeProfile]);
  const gameTitle = $derived(profile?.game_menu?.game_title);
  const activeTask = $derived(profile?.active_task);
  const gameIcon = $derived(getGameIcon(gameTitle));
  const activeOption = $derived(
    profile?.game_menu?.menu_options?.find((o) => o.label === activeTask),
  );
  const taskName = $derived(
    activeOption?.custom_label ?? activeOption?.label ?? activeTask,
  );

  // Same stat tracking as Hero
  let startTime = $state<number | null>(null);
  let elapsed = $state("00:00");
  let elapsedSeconds = $state(0);
  let timer: ReturnType<typeof setInterval>;
  let issueCount = $state(0);
  let restartCount = $state(0);
  let clearedCount = $state(0);
  let failureCount = $state(0);

  $effect(() => {
    if (activeTask) {
      if (!startTime) {
        startTime = Date.now();
        issueCount = 0;
        restartCount = 0;
        clearedCount = 0;
        failureCount = 0;
      }
    } else {
      startTime = null;
      elapsed = "00:00";
      elapsedSeconds = 0;
    }
  });

  const perHour = $derived(
    elapsedSeconds > 30 && clearedCount > 0
      ? (clearedCount / elapsedSeconds) * 3600
      : 0,
  );

  const successRate = $derived(
    clearedCount + failureCount > 0
      ? Math.round((clearedCount / (clearedCount + failureCount)) * 100)
      : -1,
  );

  function updateTimer() {
    if (!startTime) return;
    const s = Math.max(0, Math.floor((Date.now() - startTime) / 1000));
    elapsedSeconds = s;
    const h = Math.floor(s / 3600);
    const m = Math.floor((s % 3600) / 60);
    const ss = s % 60;
    const pad = (n: number) => String(n).padStart(2, "0");
    elapsed = h > 0 ? `${pad(h)}:${pad(m)}:${pad(ss)}` : `${pad(m)}:${pad(ss)}`;
  }

  onMount(() => {
    timer = setInterval(updateTimer, 1000);

    let logUnsub: (() => void) | undefined;
    listen<any>(EventNames.LOG_MESSAGE, (event) => {
      const msg = event.payload;
      if (msg.profile_index !== get(activeProfile)) return;
      if (!get(profileStates)[get(activeProfile)]?.active_task) return;
      const text = typeof msg.message === "string" ? msg.message : "";
      if (["WARNING", "ERROR", "FATAL"].includes(msg.level)) issueCount++;
      if (/restart/i.test(text)) restartCount++;
      if (/\bcleared:?\s*\d+/i.test(text)) clearedCount++;
      else if (
        /\b(completed|won|success)\b/i.test(text) &&
        msg.level === "INFO"
      )
        clearedCount++;
      if (/\b(failed|crashed|frozen|lost)\b/i.test(text)) failureCount++;
    }).then((u) => {
      logUnsub = u;
    });

    return () => {
      clearInterval(timer);
      logUnsub?.();
    };
  });
</script>

<div class="mini">
  <div class="bar" data-tauri-drag-region>
    <div
      class="badge"
      class:badge-image={!!gameIcon.image}
      style={gameIcon.image
        ? ""
        : `background: linear-gradient(135deg, color-mix(in oklab, ${gameIcon.color} 80%, white), ${gameIcon.color});`}
      data-tauri-drag-region
    >
      {#if gameIcon.image}
        <img src={gameIcon.image} alt={gameTitle ?? ""} class="badge-img" />
      {:else}
        <span class="badge-initials">{gameIcon.initials}</span>
      {/if}
    </div>

    <div class="info" data-tauri-drag-region>
      {#if activeTask}
        <div class="task-name" data-tauri-drag-region>{taskName}</div>
        <div class="stats" data-tauri-drag-region>
          <span class="stat" title={$t("Elapsed")}>
            <svg
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              stroke-width="1.9"
              stroke-linecap="round"
              stroke-linejoin="round"
              width="10"
              height="10"
              ><circle cx="12" cy="12" r="9" /><path d="M12 7v5l3 2" /></svg
            >
            <span class="v">{elapsed}</span>
          </span>
          {#if perHour > 0}
            <span class="stat stat-rate">
              <svg
                viewBox="0 0 24 24"
                fill="currentColor"
                width="10"
                height="10"><path d="M13 2 4 14h7l-1 8 9-12h-7l1-8Z" /></svg
              >
              <span class="v">{perHour.toFixed(1)}/hr</span>
            </span>
          {/if}
          {#if successRate >= 0}
            <span
              class="stat"
              class:stat-ok={successRate >= 90}
              class:stat-warn={successRate >= 60 && successRate < 90}
              class:stat-err={successRate < 60}
            >
              <svg
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                stroke-width="1.9"
                stroke-linecap="round"
                stroke-linejoin="round"
                width="10"
                height="10"
                ><path d="M3 17 9 11l4 4 8-8" /><path d="M14 7h7v7" /></svg
              >
              <span class="v">{successRate}%</span>
            </span>
          {/if}
          {#if clearedCount > 0}
            <span class="stat stat-cleared">
              <svg
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                stroke-width="1.7"
                stroke-linecap="round"
                stroke-linejoin="round"
                width="10"
                height="10"
                ><path
                  d="M6 9H4.5a2.5 2.5 0 0 1 0-5H6M18 9h1.5a2.5 2.5 0 0 0 0-5H18M4 22h16M10 14.66V17c0 .55-.47.98-.97 1.21C7.85 18.75 7 20.24 7 22M14 14.66V17c0 .55.47.98.97 1.21 1.18.54 2.03 2.03 2.03 3.79M18 2H6v7a6 6 0 0 0 12 0V2z"
                /></svg
              >
              <span class="v">{clearedCount}</span>
            </span>
          {/if}
        </div>
      {:else}
        <div class="task-name muted" data-tauri-drag-region>
          {$t("No active task")}
        </div>
        <div class="stats muted" data-tauri-drag-region>
          {gameTitle ? $t(gameTitle) : $t("No game detected")}
        </div>
      {/if}
    </div>

    <div class="actions">
      {#if activeTask}
        <button class="stop-btn" onclick={onStop} title={$t("Stop Task")}>
          <svg viewBox="0 0 24 24" fill="currentColor" width="11" height="11"
            ><rect x="6" y="6" width="12" height="12" rx="2" /></svg
          >
        </button>
      {/if}
      <button
        class="icon-btn"
        class:active={$uiState.pinTop}
        onclick={onTogglePin}
        title={$uiState.pinTop ? $t("Unpin") : $t("Pin on top")}
      >
        <!-- pushpin -->
        <svg
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="1.7"
          stroke-linecap="round"
          stroke-linejoin="round"
          width="13"
          height="13"
          ><path
            d="M12 17v5M9 10.76V6h.5a2 2 0 0 0 0-4h5a2 2 0 0 0 0 4h.5v4.76a2 2 0 0 0 1.106 1.789l1.444.722A2 2 0 0 1 18.55 15H5.45a2 2 0 0 1 .894-1.729l1.448-.722A2 2 0 0 0 9 10.76z"
          /></svg
        >
      </button>
      <button
        class="icon-btn"
        class:active={$uiState.miniLogOpen}
        onclick={onToggleLog}
        title={$uiState.miniLogOpen ? $t("Hide log") : $t("Show log")}
      >
        <svg
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="1.7"
          stroke-linecap="round"
          stroke-linejoin="round"
          width="13"
          height="13"><path d="M4 6h12M4 12h16M4 18h10" /></svg
        >
      </button>
      <button
        class="icon-btn"
        onclick={onExitMini}
        title={$t("Exit mini mode")}
      >
        <!-- expand -->
        <svg
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="1.7"
          stroke-linecap="round"
          stroke-linejoin="round"
          width="13"
          height="13"><path d="M15 3h6v6M9 21H3v-6M21 3l-7 7M3 21l7-7" /></svg
        >
      </button>
    </div>
  </div>

  {#if $uiState.miniLogOpen}
    <div class="mini-log">
      <LogPanel
        profileIndex={$activeProfile}
        onClear={() => {}}
        collapsed={false}
        position="bottom"
      />
    </div>
  {/if}
</div>

<style>
  .mini {
    display: flex;
    flex-direction: column;
    height: 100vh;
    background: var(--bg-1);
    overflow: hidden;
  }

  .bar {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 8px 10px;
    flex: 0 0 auto;
    border-bottom: 1px solid transparent;
  }

  :global(.mini .mini-log) :global(.log-panel) {
    height: 100% !important;
    flex: 1 1 auto !important;
    border-top: 1px solid var(--line);
  }

  .badge {
    width: 36px;
    height: 36px;
    aspect-ratio: 1 / 1;
    border-radius: 8px;
    display: grid;
    place-items: center;
    color: white;
    font-weight: 800;
    font-size: 13px;
    flex-shrink: 0;
    overflow: hidden;
  }

  .badge.badge-image {
    background: transparent;
  }

  .badge-img {
    width: 100%;
    height: 100%;
    object-fit: cover;
    display: block;
    border-radius: inherit;
  }

  .info {
    flex: 1;
    min-width: 0;
  }

  .task-name {
    font-size: 13px;
    font-weight: 700;
    letter-spacing: -0.01em;
    color: var(--text-1);
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    line-height: 1.2;
  }

  .task-name.muted {
    color: var(--text-3);
    font-weight: 600;
  }

  .stats {
    display: flex;
    gap: 8px;
    align-items: center;
    margin-top: 2px;
    flex-wrap: wrap;
  }

  .stats.muted {
    font-size: 10.5px;
    color: var(--text-4);
    font-weight: 500;
  }

  .stat {
    display: inline-flex;
    align-items: center;
    gap: 3px;
    font-family: var(--font-mono);
    font-size: 10.5px;
    color: var(--text-3);
  }

  .stat .v {
    color: var(--text-1);
    font-weight: 600;
  }

  .stat-rate :global(svg),
  .stat-rate .v {
    color: var(--warn);
  }

  .stat-ok :global(svg),
  .stat-ok .v {
    color: var(--ok);
  }

  .stat-warn :global(svg),
  .stat-warn .v {
    color: var(--warn);
  }

  .stat-err :global(svg),
  .stat-err .v {
    color: var(--err);
  }

  .stat-cleared :global(svg),
  .stat-cleared .v {
    color: #fb923c;
  }

  .actions {
    display: flex;
    align-items: center;
    gap: 4px;
    flex-shrink: 0;
  }

  .icon-btn {
    width: 24px;
    height: 24px;
    border-radius: 6px;
    display: grid;
    place-items: center;
    color: var(--text-3);
    background: transparent;
    border: 0;
    cursor: pointer;
    transition: all var(--dur-1);
  }

  .icon-btn:hover {
    background: var(--bg-hover);
    color: var(--text-1);
  }

  .icon-btn.active {
    background: var(--accent-ghost);
    color: var(--accent);
  }

  .stop-btn {
    width: 24px;
    height: 24px;
    border-radius: 6px;
    display: grid;
    place-items: center;
    color: white;
    background: var(--err);
    border: 0;
    cursor: pointer;
    transition: filter var(--dur-1);
    margin-right: 2px;
  }

  .stop-btn:hover {
    filter: brightness(1.1);
  }

  .mini-log {
    flex: 1 1 auto;
    min-height: 0;
    display: flex;
    overflow: hidden;
  }
</style>
