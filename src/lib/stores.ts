import { writable } from "svelte/store";
import type { AppSettings, ProfileState } from "$pytauri/_apiTypes";
export const appSettings = writable<null | AppSettings>(null);
export const debugLogLevelOverwrite = writable<boolean[]>([false]);
export const activeProfile = writable<number>(0);
export const profileStates = writable<ProfileState[]>([]);
export const profileStateTimestamp = writable<number | null>();
export const appVersion = writable<string>("");

const defaultUiState = {
  showSettings: false,
  settingsType: "adb" as "adb" | "game" | "app",
  sidebarOpen: true,
  logOpen: true,
  theme: "dark" as "dark" | "light",
  accentHue: 272,
  accentChroma: 0.18,
  accentLightness: 0.67,
  customizerOpen: false,
  taskViewVariant: "cards" as "cards" | "list",
};

let initialUiState = { ...defaultUiState };

if (typeof window !== "undefined") {
  try {
    const saved = localStorage.getItem("uiState");
    if (saved) {
      const parsed = JSON.parse(saved);
      initialUiState = {
        ...defaultUiState,
        ...parsed,
        showSettings: false,
        customizerOpen: false,
      };
      if (
        initialUiState.taskViewVariant !== "cards" &&
        initialUiState.taskViewVariant !== "list"
      ) {
        initialUiState.taskViewVariant = "cards";
      }
    }
  } catch (e) {
    console.error("Failed to load uiState from localStorage", e);
  }
}

export const uiState = writable(initialUiState);

if (typeof window !== "undefined") {
  uiState.subscribe((state) => {
    try {
      const stateToSave = {
        sidebarOpen: state.sidebarOpen,
        logOpen: state.logOpen,
        theme: state.theme,
        accentHue: state.accentHue,
        accentChroma: state.accentChroma,
        accentLightness: state.accentLightness,
        taskViewVariant: state.taskViewVariant,
      };
      localStorage.setItem("uiState", JSON.stringify(stateToSave));
    } catch (e) {
      console.error("Failed to save uiState to localStorage", e);
    }
  });
}
