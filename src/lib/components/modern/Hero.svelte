<script lang="ts">
  import { t } from "$lib/i18n/i18n";
  import { activeProfile, profileStates, uiState } from "$lib/stores";
  import { get } from "svelte/store";
  import { onMount } from "svelte";
  import { listen } from "@tauri-apps/api/event";
  import { EventNames } from "$lib/log/eventNames";
  import { getGameIcon } from "$lib/utils/gameIcons";
  import type { MenuButton } from "$lib/menu/model";

  interface Props {
    onStop: () => void;
    activeTaskButton?: MenuButton;
  }

  let { onStop, activeTaskButton }: Props = $props();

  const profile = $derived($profileStates[$activeProfile]);
  const gameTitle = $derived(profile?.game_menu?.game_title);
  const activeTask = $derived(profile?.active_task);
  const displayTaskName = $derived(
    activeTaskButton?.option?.label ?? activeTask,
  );
  const deviceId = $derived(profile?.device_id);
  const gameIcon = $derived(getGameIcon(gameTitle));

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

      // Generic completion patterns: "cleared: N", "completed N", "battle won"
      if (/\bcleared:?\s*\d+/i.test(text)) clearedCount++;
      else if (
        /\b(completed|won|success)\b/i.test(text) &&
        msg.level === "INFO"
      )
        clearedCount++;

      // Generic failure patterns
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

{#if !activeTask}
  <!-- Calm idle hero -->
  <div class="hero-idle" class:compact={$uiState.taskViewVariant === "list"}>
    <div
      class="icon-idle"
      class:icon-idle-game={!!gameTitle}
      style={gameTitle
        ? `background: linear-gradient(135deg, color-mix(in oklab, ${gameIcon.color} 70%, white), ${gameIcon.color}); color: white;`
        : ""}
    >
      {#if gameTitle}
        <span class="idle-initials">{gameIcon.initials}</span>
      {:else}
        <svg
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="1.7"
          stroke-linecap="round"
          stroke-linejoin="round"
          width="14"
          height="14"
          ><circle cx="12" cy="12" r="9" /><path d="M12 7v5l3 2" /></svg
        >
      {/if}
    </div>
    <div class="content">
      <div class="meta">
        {gameTitle ? $t(gameTitle) : $t("No game detected")}
      </div>
      <div class="title">
        {gameTitle
          ? $t("Pick a task to begin")
          : deviceId
            ? $t("Start any supported game")
            : $t("No device connected — check ADB settings")}
      </div>
    </div>
  </div>
{:else}
  <!-- Loud running hero -->
  <div class="hero-running" class:compact={$uiState.taskViewVariant === "list"}>
    <!-- moving stripes bg -->
    <div class="stripes" aria-hidden="true"></div>

    <div class="inner">
      <div
        class="game-icon-badge"
        style="background: linear-gradient(135deg, color-mix(in oklab, {gameIcon.color} 80%, white), {gameIcon.color}); box-shadow: 0 6px 18px color-mix(in oklab, {gameIcon.color} 35%, transparent);"
      >
        {gameIcon.initials}
        <span class="ring"></span>
      </div>

      <div class="main-info">
        <div class="tag-row">
          <span class="tag">● {$t("Running")}</span>
          <span class="game-sub">{$t(gameTitle || "")}</span>
        </div>
        <div class="task-name">
          {displayTaskName}
        </div>
        <div class="stats">
          <div class="pill" title={$t("Elapsed")}>
            <svg
              class="pill-icon"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              stroke-width="1.9"
              stroke-linecap="round"
              stroke-linejoin="round"
              width="12"
              height="12"
              aria-hidden="true"
              ><circle cx="12" cy="12" r="9" /><path d="M12 7v5l3 2" /></svg
            >
            <span class="pill-value">{elapsed}</span>
          </div>
          {#if perHour > 0}
            <div class="pill pill-rate" title={$t("Per hour")}>
              <svg
                class="pill-icon"
                viewBox="0 0 24 24"
                fill="currentColor"
                width="12"
                height="12"
                aria-hidden="true"
                ><path d="M13 2 4 14h7l-1 8 9-12h-7l1-8Z" /></svg
              >
              <span class="pill-value">{perHour.toFixed(1)}</span>
              <span class="pill-unit">/hr</span>
            </div>
          {/if}
          {#if successRate >= 0}
            <div
              class="pill"
              class:pill-ok={successRate >= 90}
              class:pill-warn={successRate >= 60 && successRate < 90}
              class:pill-err={successRate < 60}
              title={$t("Success rate")}
            >
              <svg
                class="pill-icon"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                stroke-width="1.9"
                stroke-linecap="round"
                stroke-linejoin="round"
                width="12"
                height="12"
                aria-hidden="true"
                ><path d="M3 17 9 11l4 4 8-8" /><path d="M14 7h7v7" /></svg
              >
              <span class="pill-value">{successRate}%</span>
              <span class="pill-unit">{$t("win")}</span>
            </div>
          {/if}
          {#if clearedCount > 0}
            <div class="pill pill-cleared" title={$t("Total cleared")}>
              <svg
                class="pill-icon"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                stroke-width="1.8"
                stroke-linecap="round"
                stroke-linejoin="round"
                width="12"
                height="12"
                aria-hidden="true"
                ><path
                  d="M6 9H4.5a2.5 2.5 0 0 1 0-5H6M18 9h1.5a2.5 2.5 0 0 0 0-5H18M4 22h16M10 14.66V17c0 .55-.47.98-.97 1.21C7.85 18.75 7 20.24 7 22M14 14.66V17c0 .55.47.98.97 1.21 1.18.54 2.03 2.03 2.03 3.79M18 2H6v7a6 6 0 0 0 12 0V2z"
                /></svg
              >
              <span class="pill-value">{clearedCount}</span>
              <span class="pill-unit">{$t("cleared")}</span>
            </div>
          {/if}
          {#if restartCount > 0}
            <div class="pill pill-warn" title={$t("Restarts")}>
              <svg
                class="pill-icon"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                stroke-width="1.9"
                stroke-linecap="round"
                stroke-linejoin="round"
                width="12"
                height="12"
                aria-hidden="true"
                ><path d="M21 12a9 9 0 1 1-3-6.7L21 8" /><path
                  d="M21 3v5h-5"
                /></svg
              >
              <span class="pill-value">{restartCount}</span>
              <span class="pill-unit">{$t("restarts")}</span>
            </div>
          {/if}
          {#if issueCount > 0}
            <div class="pill pill-err" title={$t("Issues")}>
              <svg
                class="pill-icon"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                stroke-width="1.9"
                stroke-linecap="round"
                stroke-linejoin="round"
                width="12"
                height="12"
                aria-hidden="true"
                ><path
                  d="M10.3 3.86 1.82 18a2 2 0 0 0 1.7 3h16.96a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0zM12 9v4M12 17h.01"
                /></svg
              >
              <span class="pill-value">{issueCount}</span>
              <span class="pill-unit">{$t("issues")}</span>
            </div>
          {/if}
        </div>
      </div>

      <button class="stop-btn" onclick={onStop}>
        <svg viewBox="0 0 24 24" fill="currentColor" width="14" height="14"
          ><rect x="6" y="6" width="12" height="12" rx="2" /></svg
        >
        {$t("Stop Task")}
      </button>
    </div>
  </div>
{/if}

<style>
  .hero-idle {
    margin: 18px 20px 0;
    padding: 16px 20px;
    border-radius: var(--radius-lg);
    background: var(--bg-1);
    border: 1px solid var(--line);
    display: flex;
    align-items: center;
    gap: 14px;
  }

  .icon-idle {
    width: 44px;
    height: 44px;
    border-radius: 12px;
    background: linear-gradient(135deg, var(--bg-3), var(--bg-2));
    display: grid;
    place-items: center;
    color: var(--text-3);
    border: 1px solid var(--line);
    flex: 0 0 44px;
  }

  .icon-idle-game {
    border: none;
  }

  .idle-initials {
    font-weight: 800;
    font-size: 14px;
    letter-spacing: -0.02em;
  }

  .content {
    flex: 1;
    min-width: 0;
  }

  .meta {
    font-size: 11px;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: var(--text-3);
    font-weight: 600;
    margin-bottom: 4px;
  }

  .title {
    font-size: 17px;
    font-weight: 600;
    letter-spacing: -0.015em;
  }

  .hero-running {
    margin: 18px 20px 0;
    padding: 16px 20px;
    border-radius: var(--radius-lg);
    background:
      radial-gradient(
        120% 140% at 0% 0%,
        color-mix(in oklab, var(--accent) 22%, transparent) 0%,
        transparent 55%
      ),
      linear-gradient(180deg, var(--bg-2), var(--bg-1));
    border: 1px solid color-mix(in oklab, var(--accent) 35%, var(--line));
    box-shadow: var(--shadow);
    position: relative;
    overflow: hidden;
  }

  .stripes {
    position: absolute;
    inset: 0;
    opacity: 0.08;
    pointer-events: none;
    background-image: repeating-linear-gradient(
      135deg,
      var(--accent) 0 2px,
      transparent 2px 14px
    );
    animation: slide 14s linear infinite;
  }

  .inner {
    position: relative;
    display: flex;
    align-items: center;
    gap: 20px;
    flex-wrap: wrap;
  }

  .game-icon-badge {
    width: 52px;
    height: 52px;
    border-radius: 14px;
    display: grid;
    place-items: center;
    color: white;
    font-weight: 800;
    font-size: 17px;
    letter-spacing: -0.02em;
    position: relative;
    flex: 0 0 52px;
  }

  .ring {
    position: absolute;
    inset: -4px;
    border-radius: 18px;
    border: 2px solid color-mix(in oklab, var(--accent) 50%, transparent);
    animation: ringpulse 2s ease-out infinite;
  }

  .main-info {
    flex: 1 1 240px;
    min-width: 0;
  }

  .tag-row {
    display: flex;
    align-items: center;
    gap: 10px;
    margin-bottom: 6px;
    flex-wrap: wrap;
  }

  .tag {
    font-size: 10px;
    font-weight: 700;
    letter-spacing: 0.14em;
    text-transform: uppercase;
    color: var(--accent);
    background: var(--accent-ghost);
    padding: 3px 8px;
    border-radius: 999px;
  }

  .game-sub {
    font-size: 11px;
    color: var(--text-3);
    font-weight: 500;
  }

  .task-name {
    font-size: 19px;
    font-weight: 700;
    letter-spacing: -0.02em;
    line-height: 1.2;
    word-break: break-word;
  }

  .stats {
    display: flex;
    gap: 8px;
    margin-top: 10px;
    align-items: center;
    flex-wrap: wrap;
  }

  .pill {
    display: inline-flex;
    align-items: center;
    gap: 5px;
    padding: 5px 10px;
    border-radius: 999px;
    background: color-mix(in oklab, var(--bg-1) 70%, transparent);
    border: 1px solid var(--line);
    font-family: var(--font-mono);
    font-size: 12px;
    color: var(--text-2);
  }

  .pill-icon {
    color: var(--text-3);
    flex-shrink: 0;
  }

  .pill-value {
    font-weight: 700;
    color: var(--text-1);
  }

  .pill-unit {
    color: var(--text-3);
    font-weight: 500;
    font-size: 11px;
  }

  .pill-rate {
    border-color: color-mix(in oklab, var(--warn) 35%, var(--line));
  }
  .pill-rate .pill-icon {
    color: var(--warn);
  }
  .pill-rate .pill-value {
    color: var(--warn);
  }

  .pill-ok {
    border-color: color-mix(in oklab, var(--ok) 35%, var(--line));
  }
  .pill-ok .pill-icon,
  .pill-ok .pill-value {
    color: var(--ok);
  }

  .pill-warn {
    border-color: color-mix(in oklab, var(--warn) 35%, var(--line));
  }
  .pill-warn .pill-icon,
  .pill-warn .pill-value {
    color: var(--warn);
  }

  .pill-err {
    border-color: color-mix(in oklab, var(--err) 35%, var(--line));
  }
  .pill-err .pill-icon,
  .pill-err .pill-value {
    color: var(--err);
  }

  .pill-cleared {
    border-color: color-mix(in oklab, #fb923c 35%, var(--line));
  }
  .pill-cleared .pill-icon,
  .pill-cleared .pill-value {
    color: #fb923c;
  }

  .stop-btn {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    padding: 10px 16px;
    border-radius: 10px;
    font-weight: 600;
    font-size: 13px;
    color: white;
    background: var(--err);
    box-shadow: 0 6px 14px color-mix(in oklab, var(--err) 30%, transparent);
    transition:
      filter var(--dur-1),
      transform var(--dur-1);
    flex: 0 0 auto;
    margin-left: auto;
  }

  .stop-btn:hover {
    filter: brightness(1.08);
  }

  /* Compact Mode Styles */
  .hero-idle.compact {
    margin: 12px 20px 0;
    padding: 12px 18px;
    gap: 14px;
  }
  .hero-idle.compact .icon-idle {
    width: 32px;
    height: 32px;
    border-radius: 8px;
  }
  .hero-idle.compact .icon-idle svg {
    width: 14px;
    height: 14px;
  }
  .hero-idle.compact .title {
    font-size: 15px;
  }
  .hero-idle.compact .meta {
    font-size: 10px;
    margin-bottom: 2px;
  }
  .hero-idle.compact .status {
    font-size: 11px;
    margin-top: 2px;
  }

  .hero-running.compact {
    margin: 12px 20px 0;
    padding: 10px 14px;
  }
  .hero-running.compact .game-icon-badge {
    width: 38px;
    height: 38px;
    flex: 0 0 38px;
    border-radius: 10px;
    font-size: 13px;
  }
  .hero-running.compact .ring {
    inset: -2px;
    border-radius: 12px;
  }
  .hero-running.compact .task-name {
    font-size: 15px;
  }
  .hero-running.compact .stats {
    gap: 6px;
    margin-top: 4px;
  }
  .hero-running.compact .pill {
    padding: 3px 8px;
    font-size: 11px;
  }
  .hero-running.compact .stop-btn {
    padding: 6px 12px;
    font-size: 12px;
  }
</style>
