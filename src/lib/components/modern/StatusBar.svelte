<script lang="ts">
  import { t } from "$lib/i18n/i18n";
  import {
    activeProfile,
    profileStates,
    appSettings,
    appVersion,
  } from "$lib/stores";

  interface Props {
    theme: "dark" | "light";
    onToggleSidebar: () => void;
    onToggleLog: () => void;
    onDocs: () => void;
    onAppSettings: () => void;
    onGameSettings: () => void;
    onAdbSettings: () => void;
    onCustomizer: () => void;
    sidebarOpen: boolean;
    logOpen: boolean;
  }

  let {
    theme,
    onToggleSidebar,
    onToggleLog,
    onDocs,
    onAppSettings,
    onGameSettings,
    onAdbSettings,
    onCustomizer,
    sidebarOpen,
    logOpen,
  }: Props = $props();

  const profile = $derived($profileStates[$activeProfile]);
  const status = $derived(
    profile?.device_id ? (profile.active_task ? "running" : "idle") : "offline",
  );

  const dotColor = $derived(
    {
      running: "var(--ok)",
      idle: "var(--warn)",
      offline: "var(--text-4)",
    }[status],
  );

  const statusText = $derived(
    {
      running: $t("Running"),
      idle: $t("Idle"),
      offline: $t("Offline"),
    }[status],
  );
</script>

<div class="status-bar">
  <button
    onclick={onToggleSidebar}
    title={$t("Toggle profiles")}
    class="icon-btn"
    class:active={sidebarOpen}
  >
    <svg
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      stroke-width="1.7"
      stroke-linecap="round"
      stroke-linejoin="round"
      width="16"
      height="16"
      ><rect x="3" y="4" width="18" height="16" rx="2" /><path
        d="M9 4v16"
      /></svg
    >
  </button>

  <div class="brand">
    <svg width="18" height="18" viewBox="0 0 24 24" aria-hidden="true">
      <defs>
        <linearGradient id="lg" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0" stop-color="var(--accent-hi)" />
          <stop offset="1" stop-color="var(--accent-lo)" />
        </linearGradient>
      </defs>
      <rect x="2" y="2" width="20" height="20" rx="6" fill="url(#lg)" />
      <path
        d="M8 16 L12 8 L16 16 M9.5 13 L14.5 13"
        stroke="white"
        stroke-width="1.8"
        stroke-linecap="round"
        stroke-linejoin="round"
        fill="none"
      />
    </svg>
    <div class="brand-name">AdbAutoPlayer</div>
    <div class="version">v{$appVersion}</div>
  </div>

  <div class="spacer"></div>

  <!-- current profile chip (compact, on right) -->
  <div class="profile-chip" title={statusText}>
    <span
      class="status-dot"
      style="background: {dotColor}; box-shadow: {status === 'running'
        ? `0 0 0 3px ${dotColor}22`
        : 'none'}; animation: {status === 'running'
        ? 'pulse 1.6s ease-in-out infinite'
        : 'none'}"
    ></span>
    <span class="device-id">{profile?.device_id || $t("no device")}</span>
    <span class="sep">·</span>
    <span class="profile-name"
      >{$appSettings?.profiles?.profiles?.[$activeProfile] ?? "Profile"}</span
    >
  </div>

  <button class="icon-btn" title={$t("Theme & accent")} onclick={onCustomizer}>
    {#if theme === "dark"}
      <svg
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        stroke-width="1.7"
        stroke-linecap="round"
        stroke-linejoin="round"
        width="14"
        height="14"
        ><circle cx="12" cy="12" r="4" /><path
          d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"
        /></svg
      >
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
        ><path d="M21 12.8A9 9 0 1 1 11.2 3a7 7 0 0 0 9.8 9.8Z" /></svg
      >
    {/if}
  </button>

  <button
    class="icon-btn"
    class:active={logOpen}
    onclick={onToggleLog}
    title={$t("Toggle log panel")}
  >
    <svg
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      stroke-width="1.7"
      stroke-linecap="round"
      stroke-linejoin="round"
      width="16"
      height="16"><path d="M4 6h12M4 12h16M4 18h10" /></svg
    >
  </button>

  <button class="icon-btn" title={$t("ADB Settings")} onclick={onAdbSettings}>
    <!-- Smartphone with screen separator + home indicator -->
    <svg
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      stroke-width="1.7"
      stroke-linecap="round"
      stroke-linejoin="round"
      width="16"
      height="16"
      ><rect x="6" y="2" width="12" height="20" rx="2.5" /><path
        d="M9 6h6"
      /><path d="M11 18h2" /></svg
    >
  </button>

  <button class="icon-btn" title={$t("Game Settings")} onclick={onGameSettings}>
    <!-- Gamepad: D-pad on left + face buttons on right -->
    <svg
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      stroke-width="1.7"
      stroke-linecap="round"
      stroke-linejoin="round"
      width="16"
      height="16"
      ><path d="M6 11h4M8 9v4" /><circle
        cx="15"
        cy="13"
        r="0.7"
        fill="currentColor"
        stroke="none"
      /><circle
        cx="18"
        cy="11"
        r="0.7"
        fill="currentColor"
        stroke="none"
      /><path
        d="M17.32 5H6.68a4 4 0 0 0-3.978 3.59c-.006.052-.01.101-.017.152C2.604 9.416 2 14.456 2 16a3 3 0 0 0 3 3c1 0 1.5-.5 2-1l1.414-1.414A2 2 0 0 1 9.828 16h4.344a2 2 0 0 1 1.414.586L17 18c.5.5 1 1 2 1a3 3 0 0 0 3-3c0-1.545-.604-6.584-.685-7.258A4 4 0 0 0 17.32 5z"
      /></svg
    >
  </button>

  <button class="icon-btn" title={$t("App Settings")} onclick={onAppSettings}>
    <svg
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      stroke-width="1.7"
      stroke-linecap="round"
      stroke-linejoin="round"
      width="16"
      height="16"
      ><circle cx="12" cy="12" r="3" /><path
        d="M19.4 15a1.7 1.7 0 0 0 .3 1.8l.1.1a2 2 0 1 1-2.8 2.8l-.1-.1a1.7 1.7 0 0 0-1.8-.3 1.7 1.7 0 0 0-1 1.5V21a2 2 0 1 1-4 0v-.1a1.7 1.7 0 0 0-1.1-1.5 1.7 1.7 0 0 0-1.8.3l-.1.1a2 2 0 1 1-2.8-2.8l.1-.1a1.7 1.7 0 0 0 .3-1.8 1.7 1.7 0 0 0-1.5-1H3a2 2 0 1 1 0-4h.1a1.7 1.7 0 0 0 1.5-1.1 1.7 1.7 0 0 0-.3-1.8l-.1-.1a2 2 0 1 1 2.8-2.8l.1.1a1.7 1.7 0 0 0 1.8.3H9a1.7 1.7 0 0 0 1-1.5V3a2 2 0 1 1 4 0v.1a1.7 1.7 0 0 0 1 1.5 1.7 1.7 0 0 0 1.8-.3l.1-.1a2 2 0 1 1 2.8 2.8l-.1.1a1.7 1.7 0 0 0-.3 1.8V9a1.7 1.7 0 0 0 1.5 1H21a2 2 0 1 1 0 4h-.1a1.7 1.7 0 0 0-1.5 1Z"
      /></svg
    >
  </button>
</div>

<style>
  .status-bar {
    height: 44px;
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 0 12px;
    border-bottom: 1px solid var(--line);
    background: var(--bg-1);
    flex: 0 0 44px;
  }

  .brand {
    display: flex;
    align-items: center;
    gap: 8px;
  }

  .brand-name {
    font-size: 13px;
    font-weight: 600;
    letter-spacing: -0.01em;
  }

  .version {
    font-size: 11px;
    color: var(--text-4);
    font-family: var(--font-mono);
  }

  .profile-chip {
    display: flex;
    align-items: center;
    gap: 6px;
    padding: 3px 10px 3px 8px;
    border-radius: 999px;
    background: var(--bg-2);
    border: 1px solid var(--line);
    font-size: 11.5px;
  }

  .status-dot {
    width: 8px;
    height: 8px;
    border-radius: 999px;
  }

  .profile-name {
    font-weight: 600;
  }

  .sep {
    color: var(--text-4);
  }

  .device-id {
    color: var(--text-2);
    font-family: var(--font-mono);
    font-size: 11px;
  }

  .spacer {
    flex: 1;
  }

  .active {
    background: var(--accent-ghost);
    color: var(--accent);
  }
</style>
