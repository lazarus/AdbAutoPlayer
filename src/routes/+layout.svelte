<script lang="ts">
  import "../app.css";

  import { onMount, onDestroy } from "svelte";
  import { setupExternalLinkHandler } from "$lib/utils/external-links";
  import { applySettingsFromFile, applySettings } from "$lib/utils/settings";
  import { invoke } from "@tauri-apps/api/core";
  import { toaster } from "$lib/toast/toaster-svelte";
  import { Toast } from "@skeletonlabs/skeleton-svelte";
  import { initPostHog } from "$lib/utils/posthog";
  import { logInfo, logError } from "$lib/log/log-events";
  import { getVersion } from "@tauri-apps/api/app";
  import {
    profileStates,
    profileStateTimestamp,
    activeProfile,
    uiState,
    appSettings,
    appVersion,
    debugLogLevelOverwrite,
  } from "$lib/stores";
  import { listen } from "@tauri-apps/api/event";
  import { EventNames } from "$lib/log/eventNames";
  import type {
    ProfileStateUpdate,
    AppSettings,
    Trigger,
    MenuOption,
  } from "$pytauri/_apiTypes";
  import UpdateContainer from "$lib/components/updater/UpdateContainer.svelte";
  import StatusBar from "$lib/components/modern/StatusBar.svelte";
  import ProfileSidebar from "$lib/components/modern/ProfileSidebar.svelte";
  import LogPanel from "$lib/components/modern/LogPanel.svelte";
  import ThemeCustomizer from "$lib/components/modern/ThemeCustomizer.svelte";
  import SchemaForm from "$lib/form/SchemaForm.svelte";
  import type {
    SettingsProps,
    PydanticSettingsFormResponse,
    RustSettingsFormResponse,
  } from "$lib/menu/model";
  import {
    getAdbSettingsForm,
    getGameSettingsForm,
    getProfileState,
    cacheClear,
    debug,
    startTask,
  } from "$pytauri/apiClient";
  import { t } from "$lib/i18n/i18n";

  let { children } = $props();

  let sidebarCollapsed = $state(false);
  let settingsProps: SettingsProps = $state({
    showSettingsForm: false,
    formData: {},
    formSchema: {},
    fileName: "",
    type: undefined,
  });

  $effect(() => {
    document.documentElement.className = $uiState.theme;
    const root = document.documentElement;
    root.style.setProperty("--accent-h", $uiState.accentHue.toString());
    root.style.setProperty("--accent-c", $uiState.accentChroma.toString());
    root.style.setProperty("--accent-l", $uiState.accentLightness.toString());
  });

  async function init() {
    await applySettingsFromFile();
    await invoke("show_window");

    const version = await getVersion();
    appVersion.set(version);
    await logInfo(`App Version: ${version}`);
    initPostHog(version);
  }

  init().catch((e) => console.error("Failed to initialise app:", e));

  onMount(() => {
    return setupExternalLinkHandler();
  });

  onMount(() => {
    let unsubscribers: Array<() => void> = [];

    const setupListeners = async () => {
      const stateUnsub = await listen<ProfileStateUpdate>(
        EventNames.PROFILE_STATE_UPDATE,
        (event) => {
          if (
            $profileStateTimestamp &&
            $profileStateTimestamp >= event.payload.timestamp
          ) {
            return;
          }
          $profileStates[event.payload.index] = {
            game_menu: event.payload.state.game_menu,
            active_task: event.payload.state.active_task,
            device_id: event.payload.state.device_id,
          };
          $profileStates = [...$profileStates];
        },
      );

      unsubscribers.push(stateUnsub);
    };

    setupListeners();
    return () => unsubscribers.forEach((unsub) => unsub());
  });

  async function callDebug() {
    try {
      await debug({ profile_index: $activeProfile });
    } catch (error) {
      void logError(String(error));
    }
  }

  function handleDocs() {
    invoke("open_docs");
  }

  function toggleSidebar() {
    $uiState.sidebarOpen = !$uiState.sidebarOpen;
  }

  function toggleLog() {
    $uiState.logOpen = !$uiState.logOpen;
  }

  // --- Global Settings Logic ---
  async function openAppSettingsForm() {
    try {
      const data = (await invoke(
        "get_app_settings_form",
      )) as RustSettingsFormResponse;
      settingsProps = {
        showSettingsForm: true,
        formData: data.settings,
        formSchema: JSON.parse(data.schema),
        fileName: data.file_name,
        type: "app",
      };
    } catch (error) {
      console.error(error);
    }
  }

  const adbQuickActions = $derived.by(() => {
    const profile = $profileStates[$activeProfile];
    const options = profile?.game_menu?.menu_options ?? [];
    return options.filter((o) => o.label.includes("Display Size"));
  });

  async function handleQuickAction(option: MenuOption) {
    try {
      await startTask({
        profile_index: $activeProfile,
        label: option.label,
        args: option.args,
      });
      closeSettings();
    } catch (error) {
      void logError(String(error));
    }
  }

  async function openAdbSettingsForm() {
    try {
      const data = (await getAdbSettingsForm({
        profile_index: $activeProfile,
      })) as PydanticSettingsFormResponse;

      settingsProps = {
        showSettingsForm: true,
        formData: data[0],
        formSchema: data[1],
        fileName: data[2],
        type: "adb",
      };
    } catch (error) {
      console.error(error);
    }
  }

  async function openGameSettingsForm() {
    const profile = $activeProfile;
    const game = $profileStates[profile]?.game_menu;
    if (!game) return;

    try {
      const data = (await getGameSettingsForm({
        profile_index: profile,
      })) as PydanticSettingsFormResponse;

      settingsProps = {
        showSettingsForm: true,
        formData: data[0],
        formSchema: data[1],
        fileName: data[2],
        type: "game",
      };
    } catch (error) {
      console.error(error);
    }
  }

  function closeSettings() {
    settingsProps = {
      showSettingsForm: false,
      formData: {},
      formSchema: {},
      fileName: "",
    };
    $uiState.showSettings = false;
  }

  let settingsIsSaving = $state(false);
  let settingsSaveSuccess = $state(false);

  async function handleSettingsSave() {
    const formEl = document.getElementById(
      "schema-form",
    ) as HTMLFormElement | null;
    if (formEl && !formEl.checkValidity()) {
      formEl.reportValidity();
      return;
    }
    settingsIsSaving = true;
    try {
      await onFormSubmit();
      settingsSaveSuccess = true;
      setTimeout(() => (settingsSaveSuccess = false), 2000);
    } finally {
      settingsIsSaving = false;
    }
  }

  async function onFormSubmit() {
    const profile = $activeProfile;
    try {
      if (settingsProps.fileName === "App.toml") {
        const newSettings: AppSettings = await invoke("save_app_settings", {
          settings: settingsProps.formData,
        });
        await applySettings(newSettings);
      } else {
        await invoke("save_settings", {
          profileIndex: profile,
          fileName: settingsProps.fileName,
          jsonData: JSON.stringify(settingsProps.formData),
        });
        if (settingsProps.fileName.endsWith("ADB.toml")) {
          await cacheClear({
            profile_index: profile,
            trigger: EventNames.ADB_SETTINGS_UPDATED as Trigger,
          });
        } else {
          await cacheClear({
            profile_index: profile,
            trigger: EventNames.GAME_SETTINGS_UPDATED as Trigger,
          });
        }
      }
    } catch (e) {
      void logError(String(e));
    }
    closeSettings();
    // Signal state update (this could be improved by a better state sync system)
    window.dispatchEvent(new CustomEvent("trigger-state-update"));
  }

  async function handleAddProfile() {
    if (!$appSettings) return;

    const currentProfiles = $appSettings.profiles?.profiles ?? ["Default"];
    const newProfileName = `Profile ${currentProfiles.length + 1}`;
    const newProfiles = [...currentProfiles, newProfileName];

    try {
      const newSettings = {
        ...$appSettings,
        profiles: {
          ...$appSettings.profiles,
          profiles: newProfiles,
          active_profile: newProfiles.length - 1,
        },
      };

      const savedSettings: AppSettings = await invoke("save_app_settings", {
        settings: newSettings,
      });
      await applySettings(savedSettings);
      void logInfo(`Created new profile: ${newProfileName}`);
    } catch (error) {
      void logError(`Failed to create profile: ${error}`);
    }
  }

  $effect(() => {
    if ($uiState.showSettings && !settingsProps.showSettingsForm) {
      if ($uiState.settingsType === "app") {
        openAppSettingsForm();
      } else if ($uiState.settingsType === "adb") {
        openAdbSettingsForm();
      } else if ($uiState.settingsType === "game") {
        openGameSettingsForm();
      }
    } else if (!$uiState.showSettings && settingsProps.showSettingsForm) {
      settingsProps.showSettingsForm = false;
    }
  });
</script>

<Toast.Group {toaster}>
  {#snippet children(toast)}
    <Toast {toast} class="data-[type=error]:preset-tonal-error">
      <Toast.Message>
        <Toast.Title>
          <span class="text-lg">{toast.title}</span>
        </Toast.Title>
        <Toast.Description>
          <p>{toast.description}</p>
        </Toast.Description>
      </Toast.Message>
      <Toast.CloseTrigger />
    </Toast>
  {/snippet}
</Toast.Group>

<div class="app-container {$uiState.theme}">
  <StatusBar
    theme={$uiState.theme}
    onToggleSidebar={toggleSidebar}
    onToggleLog={toggleLog}
    onDocs={handleDocs}
    onAppSettings={() => {
      $uiState.settingsType = "app";
      $uiState.showSettings = true;
    }}
    onGameSettings={() => {
      $uiState.settingsType = "game";
      $uiState.showSettings = true;
    }}
    onAdbSettings={() => {
      $uiState.settingsType = "adb";
      $uiState.showSettings = true;
    }}
    sidebarOpen={$uiState.sidebarOpen}
    logOpen={$uiState.logOpen}
    onCustomizer={() => ($uiState.customizerOpen = !$uiState.customizerOpen)}
  />

  {#if $uiState.customizerOpen}
    <ThemeCustomizer onClose={() => ($uiState.customizerOpen = false)} />
  {/if}

  <!-- Global Settings Overlay -->
  {#if settingsProps.showSettingsForm}
    <!-- svelte-ignore a11y_click_events_have_key_events a11y_no_static_element_interactions -->
    <div
      class="global-settings-overlay"
      onclick={closeSettings}
      role="presentation"
    >
      <!-- svelte-ignore a11y_click_events_have_key_events a11y_no_static_element_interactions -->
      <div
        class="settings-card"
        onclick={(e) => e.stopPropagation()}
        role="presentation"
      >
        <div class="settings-header">
          <div class="settings-title">
            {settingsProps.fileName === "App.toml"
              ? $t("App Settings")
              : settingsProps.type === "adb"
                ? $t("ADB Settings")
                : settingsProps.type === "game"
                  ? $t("Game Settings")
                  : $t("Settings")}
          </div>
          <div class="settings-header-actions">
            <button
              class="save-btn"
              class:success={settingsSaveSuccess}
              disabled={settingsIsSaving}
              onclick={handleSettingsSave}
            >
              {#if settingsIsSaving}
                <span class="spinner"></span>
              {:else if settingsSaveSuccess}
                <svg
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  stroke-width="2.5"
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  width="13"
                  height="13"><path d="M20 6 9 17l-5-5" /></svg
                >
                {$t("Saved")}
              {:else}
                {$t("Save")}
              {/if}
            </button>
            <button
              class="close-btn"
              onclick={closeSettings}
              aria-label="Close settings"
            >
              <svg
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                stroke-width="2"
                stroke-linecap="round"
                stroke-linejoin="round"
                width="18"
                height="18"><path d="M18 6 6 18M6 6l12 12" /></svg
              >
            </button>
          </div>
        </div>
        <div class="settings-body">
          <SchemaForm bind:settingsProps />
        </div>
        {#if settingsProps.type === "adb"}
          <div class="quick-actions">
            {#if adbQuickActions.length > 0}
              {#each adbQuickActions as action}
                <button
                  class="action-chip"
                  onclick={() => handleQuickAction(action)}
                >
                  {action.label}
                </button>
              {/each}
            {/if}
            <button
              class="action-chip"
              onclick={() => {
                callDebug();
                closeSettings();
              }}
            >
              {$t("Run Debug Routine")}
            </button>
          </div>
        {/if}
      </div>
    </div>
  {/if}

  <div
    class="main-layout"
    class:layout-bottom={$appSettings?.ui?.log_panel_position === "bottom"}
  >
    <div class="content-wrapper">
      {#if $uiState.sidebarOpen}
        <ProfileSidebar
          collapsed={sidebarCollapsed}
          onAddProfile={handleAddProfile}
        />
      {/if}

      <main class="content-area">
        <UpdateContainer />
        {@render children()}
      </main>
    </div>

    <LogPanel
      profileIndex={$activeProfile}
      onClear={() => {}}
      collapsed={!$uiState.logOpen}
      position={$appSettings?.ui?.log_panel_position}
    />
  </div>
</div>

<style>
  .app-container {
    height: 100vh;
    display: flex;
    flex-direction: column;
    overflow: hidden;
    background: var(--bg-0);
    color: var(--text-1);
    position: relative;
  }

  .main-layout {
    flex: 1;
    display: flex;
    flex-direction: row;
    overflow: hidden;
  }

  .main-layout.layout-bottom {
    flex-direction: column;
  }

  .content-wrapper {
    flex: 1;
    display: flex;
    flex-direction: row;
    overflow: hidden;
  }

  .content-area {
    flex: 1;
    display: flex;
    flex-direction: column;
    overflow-y: auto;
    position: relative;
  }

  /* Global Settings Overlay Styles */
  .global-settings-overlay {
    position: fixed;
    inset: 0;
    background: rgba(0, 0, 0, 0.5);
    backdrop-filter: blur(8px);
    z-index: 2000;
    display: grid;
    place-items: center;
    padding: 40px;
  }

  .settings-card {
    background: var(--bg-1);
    border: 1px solid var(--line);
    border-radius: var(--radius-lg);
    width: 100%;
    max-width: 800px;
    max-height: 90vh;
    display: flex;
    flex-direction: column;
    box-shadow: 0 20px 50px rgba(0, 0, 0, 0.5);
    overflow: hidden;
  }

  .settings-header {
    padding: 12px 16px 12px 20px;
    border-bottom: 1px solid var(--line);
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
    background: var(--bg-2);
  }

  .settings-title {
    font-size: 14px;
    font-weight: 700;
    color: var(--text-1);
    letter-spacing: -0.005em;
  }

  .settings-header-actions {
    display: flex;
    align-items: center;
    gap: 6px;
  }

  .save-btn {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 6px 14px;
    border-radius: 8px;
    background: var(--accent);
    color: white;
    font-weight: 700;
    font-size: 12.5px;
    transition:
      filter var(--dur-1),
      background var(--dur-1);
  }

  .save-btn:hover:not(:disabled) {
    filter: brightness(1.1);
  }

  .save-btn:disabled {
    opacity: 0.7;
    cursor: not-allowed;
  }

  .save-btn.success {
    background: var(--ok);
  }

  .quick-actions {
    padding: 12px 16px;
    background: var(--bg-2);
    border-top: 1px solid var(--line);
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
  }

  .action-chip {
    padding: 6px 12px;
    background: var(--bg-1);
    border: 1px solid var(--line);
    border-radius: 999px;
    font-size: 12px;
    font-weight: 500;
    color: var(--text-2);
    cursor: pointer;
    transition: all var(--dur-1);
  }

  .action-chip:hover {
    border-color: var(--accent);
    color: var(--accent);
    background: var(--accent-ghost);
  }

  .settings-body {
    flex: 1;
    overflow: hidden;
    display: flex;
    flex-direction: column;
    min-height: 0;
  }

  .close-btn {
    color: var(--text-3);
    transition: all var(--dur-1);
    width: 30px;
    height: 30px;
    display: grid;
    place-items: center;
    border-radius: 8px;
  }

  .close-btn:hover {
    background: var(--bg-hover);
    color: var(--text-1);
  }

  .spinner {
    width: 12px;
    height: 12px;
    border: 2px solid rgba(255, 255, 255, 0.3);
    border-top-color: white;
    border-radius: 50%;
    animation: spin 0.8s linear infinite;
  }

  @keyframes spin {
    to {
      transform: rotate(360deg);
    }
  }
</style>
