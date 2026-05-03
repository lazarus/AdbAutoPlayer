<script lang="ts">
  import { t } from "$lib/i18n/i18n";
  import { uiState } from "$lib/stores";
  import { fade, fly } from "svelte/transition";

  let { onClose }: { onClose: () => void } = $props();

  // Presets are full {hue, chroma, lightness} triplets so they can express
  // muted/saturated/dark/bright variants, not just hue.
  interface Preset {
    name: string;
    h: number;
    c: number;
    l: number;
  }

  const presets: Preset[] = [
    { name: "Purple", h: 272, c: 0.18, l: 0.67 },
    { name: "Blue", h: 220, c: 0.18, l: 0.67 },
    { name: "Cyan", h: 185, c: 0.16, l: 0.72 },
    { name: "Green", h: 145, c: 0.18, l: 0.7 },
    { name: "Amber", h: 70, c: 0.18, l: 0.78 },
    { name: "Red", h: 25, c: 0.2, l: 0.65 },
    { name: "Rose", h: 350, c: 0.16, l: 0.7 },
    { name: "Mono", h: 272, c: 0, l: 0.7 },
  ];

  const DEFAULTS = { h: 272, c: 0.18, l: 0.67 };

  function applyPreset(p: Preset) {
    $uiState.accentHue = p.h;
    $uiState.accentChroma = p.c;
    $uiState.accentLightness = p.l;
  }

  function resetToDefaults() {
    $uiState.accentHue = DEFAULTS.h;
    $uiState.accentChroma = DEFAULTS.c;
    $uiState.accentLightness = DEFAULTS.l;
  }

  const matchesPreset = $derived(
    (p: Preset) =>
      Math.abs(p.h - $uiState.accentHue) < 0.5 &&
      Math.abs(p.c - $uiState.accentChroma) < 0.005 &&
      Math.abs(p.l - $uiState.accentLightness) < 0.005,
  );

  // Live oklch preview for the swatch
  const previewColor = $derived(
    `oklch(${$uiState.accentLightness} ${$uiState.accentChroma} ${$uiState.accentHue})`,
  );
</script>

<!-- Backdrop -->
<button
  class="backdrop"
  onclick={onClose}
  transition:fade={{ duration: 200 }}
  aria-label="Close customizer"
></button>

<div class="customizer-panel" transition:fly={{ x: 300, duration: 300 }}>
  <div class="panel-header">
    <h3>{$t("Customize Theme")}</h3>
    <button class="close-btn" onclick={onClose} aria-label="Close customizer">
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

  <div class="panel-body">
    <!-- Appearance -->
    <section class="section">
      <div class="section-label">{$t("Appearance")}</div>
      <div class="mode-toggle">
        <button
          class="mode-btn"
          class:active={$uiState.theme === "dark"}
          onclick={() => ($uiState.theme = "dark")}
        >
          <svg
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
            width="14"
            height="14"
            ><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z" /></svg
          >
          {$t("Dark")}
        </button>
        <button
          class="mode-btn"
          class:active={$uiState.theme === "light"}
          onclick={() => ($uiState.theme = "light")}
        >
          <svg
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
            width="14"
            height="14"
            ><circle cx="12" cy="12" r="5" /><path
              d="M12 1v2M12 21v2M4.22 4.22l1.42 1.42M18.36 18.36l1.42 1.42M1 12h2M21 12h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42"
            /></svg
          >
          {$t("Light")}
        </button>
      </div>
    </section>

    <!-- Accent Color -->
    <section class="section">
      <div class="section-head">
        <div class="section-label">{$t("Accent Color")}</div>
        <button class="reset-btn" onclick={resetToDefaults}>
          {$t("Reset")}
        </button>
      </div>

      <div class="swatch-row">
        <div class="swatch" style="background: {previewColor}"></div>
        <div class="swatch-meta">
          <div class="swatch-label">{$t("Preview")}</div>
          <code class="swatch-code">{previewColor}</code>
        </div>
      </div>

      <div class="slider-group">
        <div class="slider-row">
          <label class="slider-label" for="hue-slider">
            {$t("Hue")}
            <span class="slider-val">{Math.round($uiState.accentHue)}°</span>
          </label>
          <input
            id="hue-slider"
            type="range"
            min="0"
            max="360"
            step="1"
            bind:value={$uiState.accentHue}
            class="slider hue-slider"
          />
        </div>

        <div class="slider-row">
          <label class="slider-label" for="sat-slider">
            {$t("Saturation")}
            <span class="slider-val"
              >{Math.round(($uiState.accentChroma / 0.3) * 100)}%</span
            >
          </label>
          <input
            id="sat-slider"
            type="range"
            min="0"
            max="0.3"
            step="0.005"
            bind:value={$uiState.accentChroma}
            class="slider"
            style="background: linear-gradient(to right, oklch({$uiState.accentLightness} 0 {$uiState.accentHue}), oklch({$uiState.accentLightness} 0.3 {$uiState.accentHue}))"
          />
        </div>

        <div class="slider-row">
          <label class="slider-label" for="light-slider">
            {$t("Lightness")}
            <span class="slider-val"
              >{Math.round($uiState.accentLightness * 100)}%</span
            >
          </label>
          <input
            id="light-slider"
            type="range"
            min="0.2"
            max="0.95"
            step="0.005"
            bind:value={$uiState.accentLightness}
            class="slider"
            style="background: linear-gradient(to right, oklch(0.2 {$uiState.accentChroma} {$uiState.accentHue}), oklch(0.95 {$uiState.accentChroma} {$uiState.accentHue}))"
          />
        </div>
      </div>

      <div class="presets-grid">
        {#each presets as p}
          <button
            class="preset-btn"
            style="--p-color: oklch({p.l} {p.c} {p.h})"
            class:active={matchesPreset(p)}
            onclick={() => applyPreset(p)}
            title={p.name}
            aria-label={p.name}
          ></button>
        {/each}
      </div>
    </section>

    <div class="info-card">
      <svg
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        stroke-width="2"
        width="16"
        height="16"
        ><circle cx="12" cy="12" r="10" /><path d="M12 16v-4M12 8h.01" /></svg
      >
      <p>{$t("Theme and accent preferences are saved automatically.")}</p>
    </div>
  </div>
</div>

<style>
  .backdrop {
    position: fixed;
    inset: 0;
    background: rgba(0, 0, 0, 0.4);
    backdrop-filter: blur(4px);
    z-index: 1000;
  }

  .customizer-panel {
    position: fixed;
    top: 44px;
    right: 0;
    bottom: 0;
    width: 340px;
    background: var(--bg-1);
    border-left: 1px solid var(--line);
    box-shadow: -8px 0 32px rgba(0, 0, 0, 0.2);
    z-index: 1001;
    display: flex;
    flex-direction: column;
  }

  .panel-header {
    padding: 18px 20px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    border-bottom: 1px solid var(--line-soft);
  }

  .panel-header h3 {
    margin: 0;
    font-size: 15px;
    font-weight: 700;
  }

  .close-btn {
    color: var(--text-3);
    transition: color var(--dur-1);
  }

  .close-btn:hover {
    color: var(--text-1);
  }

  .panel-body {
    flex: 1;
    overflow-y: auto;
    padding: 20px;
    display: flex;
    flex-direction: column;
    gap: 28px;
  }

  .section-label {
    font-size: 11px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    color: var(--text-3);
    margin-bottom: 12px;
  }

  .section-head {
    display: flex;
    align-items: baseline;
    justify-content: space-between;
    margin-bottom: 12px;
  }

  .section-head .section-label {
    margin-bottom: 0;
  }

  .reset-btn {
    font-size: 11px;
    color: var(--text-3);
    padding: 2px 8px;
    border-radius: 4px;
    transition: all var(--dur-1);
  }

  .reset-btn:hover {
    color: var(--text-1);
    background: var(--bg-hover);
  }

  .mode-toggle {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 8px;
    background: var(--bg-2);
    padding: 4px;
    border-radius: 10px;
    border: 1px solid var(--line);
  }

  .mode-btn {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 8px;
    padding: 8px;
    border-radius: 7px;
    font-size: 12px;
    font-weight: 600;
    color: var(--text-3);
    transition: all var(--dur-1);
  }

  .mode-btn:not(.active):hover {
    background: var(--bg-hover);
    color: var(--text-2);
  }

  .mode-btn.active {
    background: var(--bg-1);
    color: var(--text-1);
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  }

  .swatch-row {
    display: flex;
    align-items: center;
    gap: 12px;
    margin-bottom: 16px;
    padding: 10px;
    background: var(--bg-2);
    border: 1px solid var(--line);
    border-radius: 10px;
  }

  .swatch {
    width: 44px;
    height: 44px;
    border-radius: 10px;
    flex: 0 0 44px;
    box-shadow: 0 4px 12px color-mix(in oklab, var(--accent) 25%, transparent);
  }

  .swatch-meta {
    flex: 1;
    min-width: 0;
  }

  .swatch-label {
    font-size: 10px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: var(--text-4);
    margin-bottom: 2px;
  }

  .swatch-code {
    font-family: var(--font-mono);
    font-size: 10.5px;
    color: var(--text-2);
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    display: block;
  }

  .slider-group {
    display: flex;
    flex-direction: column;
    gap: 14px;
    margin-bottom: 18px;
  }

  .slider-label {
    display: flex;
    justify-content: space-between;
    align-items: baseline;
    font-size: 11px;
    font-weight: 600;
    color: var(--text-2);
    margin-bottom: 6px;
  }

  .slider-val {
    font-family: var(--font-mono);
    font-size: 11px;
    color: var(--text-3);
    font-weight: 500;
  }

  .slider {
    width: 100%;
    appearance: none;
    height: 8px;
    border-radius: 4px;
    background: var(--bg-3);
    border: 1px solid var(--line);
    outline: none;
  }

  .hue-slider {
    background: linear-gradient(
      to right,
      oklch(0.7 0.18 0),
      oklch(0.7 0.18 60),
      oklch(0.7 0.18 120),
      oklch(0.7 0.18 180),
      oklch(0.7 0.18 240),
      oklch(0.7 0.18 300),
      oklch(0.7 0.18 360)
    );
    border: none;
  }

  .slider::-webkit-slider-thumb {
    appearance: none;
    width: 18px;
    height: 18px;
    border-radius: 50%;
    background: white;
    border: 3px solid var(--accent);
    cursor: pointer;
    box-shadow: 0 2px 6px rgba(0, 0, 0, 0.3);
  }

  .presets-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(36px, 1fr));
    gap: 10px;
  }

  .preset-btn {
    aspect-ratio: 1;
    border-radius: 8px;
    background: var(--p-color);
    border: 2px solid transparent;
    transition: transform var(--dur-1);
  }

  .preset-btn:hover {
    transform: scale(1.1);
  }

  .preset-btn.active {
    border-color: var(--text-1);
    transform: scale(1.15);
  }

  .info-card {
    margin-top: auto;
    padding: 12px;
    background: var(--bg-2);
    border-radius: 10px;
    border: 1px solid var(--line-soft);
    display: flex;
    gap: 10px;
    color: var(--text-3);
    font-size: 11.5px;
    line-height: 1.4;
  }

  .info-card svg {
    flex-shrink: 0;
  }
</style>
