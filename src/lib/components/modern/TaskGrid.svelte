<script lang="ts">
  import { t } from "$lib/i18n/i18n";
  import type { MenuButton } from "$lib/menu/model";
  import { uiState } from "$lib/stores";
  import { getTaskIcon } from "$lib/utils/taskIcons";

  interface Props {
    buttons: MenuButton[];
    disableActions: boolean;
    categories: string[];
  }

  let { buttons, disableActions, categories }: Props = $props();

  let query = $state("");
  let searchInput: HTMLInputElement;

  function handleGlobalKeydown(e: KeyboardEvent) {
    if ((e.ctrlKey || e.metaKey) && e.key === "k") {
      e.preventDefault();
      searchInput?.focus();
    }
  }

  const filteredButtons = $derived(
    buttons.filter((b) =>
      b.option.label.toLowerCase().includes(query.toLowerCase()),
    ),
  );

  const categorizedButtons = $derived.by(() => {
    const result: Record<string, MenuButton[]> = {};
    for (const button of filteredButtons) {
      const category = button.option.category || "";
      if (!result[category]) {
        result[category] = [];
      }
      result[category].push(button);
    }
    return result;
  });

  const activeCategories = $derived.by(() => {
    const cats = categories.filter(
      (cat) => categorizedButtons[cat]?.length > 0,
    );
    if (categorizedButtons[""]?.length > 0 && !cats.includes("")) {
      cats.push("");
    }
    return cats;
  });
</script>

<svelte:window onkeydown={handleGlobalKeydown} />

<div class="task-grid-container">
  <div class="toolbar">
    <div class="search-box">
      <svg
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        stroke-width="1.7"
        stroke-linecap="round"
        stroke-linejoin="round"
        width="14"
        height="14"
        class="search-icon"
        ><circle cx="11" cy="11" r="7" /><path d="m20 20-3.5-3.5" /></svg
      >
      <input
        bind:this={searchInput}
        bind:value={query}
        placeholder={$t("Search tasks...")}
        class="search-input"
        onkeydown={(e) => {
          if (e.key === "Escape") {
            query = "";
            (e.target as HTMLInputElement).blur();
          }
        }}
      />
      {#if query}
        <button class="search-clear" onclick={() => (query = "")} title="Clear">
          <svg
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2.5"
            stroke-linecap="round"
            width="12"
            height="12"><path d="M18 6 6 18M6 6l12 12" /></svg
          >
        </button>
      {/if}
    </div>

    <div class="variant-toggle">
      {#each [{ id: "cards", label: $t("Cards"), icon: "M3 3h7v7H3zM14 3h7v7h-7zM3 14h7v7H3zM14 14h7v7h-7z" }, { id: "list", label: $t("List"), icon: "M8 6h13M8 12h13M8 18h13M3 6h.01M3 12h.01M3 18h.01" }] as v}
        <button
          class="v-btn"
          class:active={$uiState.taskViewVariant === v.id}
          onclick={() => ($uiState.taskViewVariant = v.id as any)}
          title={v.label}
        >
          <svg
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="1.7"
            stroke-linecap="round"
            stroke-linejoin="round"
            width="14"
            height="14"
          >
            <path d={v.icon} />
          </svg>
          <span>{v.label}</span>
        </button>
      {/each}
    </div>
  </div>

  <div class="view-content">
    {#if activeCategories.length === 0 && query}
      <div class="empty-search">
        <svg
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="1.7"
          stroke-linecap="round"
          stroke-linejoin="round"
          width="28"
          height="28"
          ><circle cx="11" cy="11" r="7" /><path d="m20 20-3.5-3.5" /></svg
        >
        <p>{$t("No tasks match")} <strong>"{query}"</strong></p>
      </div>
    {:else if $uiState.taskViewVariant === "cards"}
      <div class="cards-view">
        {#each activeCategories as cat}
          <section class="section">
            <div class="section-header">
              <div class="section-title">{$t(cat || "Other")}</div>
              <div class="section-line"></div>
            </div>
            <div class="grid">
              {#each categorizedButtons[cat] as b}
                {@const isDisabled =
                  disableActions && !b.isProcessRunning && !b.alwaysEnabled}
                {@const icon = getTaskIcon(b.option.label)}
                <button
                  class="task-card"
                  class:active={b.isProcessRunning}
                  disabled={isDisabled}
                  title={isDisabled
                    ? $t("Stop the running task before starting another")
                    : b.option.tooltip
                      ? $t(b.option.tooltip)
                      : undefined}
                  onclick={b.callback}
                >
                  <div class="card-icon" style="--icon-color: {icon.color}">
                    <svg
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="currentColor"
                      stroke-width="1.8"
                      stroke-linecap="round"
                      stroke-linejoin="round"
                      width="14"
                      height="14"
                    >
                      <path d={icon.path} />
                    </svg>
                  </div>
                  <div class="card-top">
                    <div class="card-label">{$t(b.option.label)}</div>
                    {#if b.isProcessRunning}
                      <span class="running-tag">● {$t("Run")}</span>
                    {:else}
                      <div class="play-box" aria-hidden="true">
                        <svg
                          viewBox="0 0 24 24"
                          fill="none"
                          stroke="currentColor"
                          stroke-width="2"
                          stroke-linecap="round"
                          stroke-linejoin="round"
                          width="12"
                          height="12"><path d="m9 18 6-6-6-6" /></svg
                        >
                      </div>
                    {/if}
                  </div>
                  {#if b.option.tooltip}
                    <div class="card-hint">{$t(b.option.tooltip)}</div>
                  {/if}
                </button>
              {/each}
            </div>
          </section>
        {/each}
      </div>
    {:else}
      <!-- Condensed list view -->
      <div class="list-view">
        {#each activeCategories as cat}
          <div class="list-section">
            <div class="list-section-header">
              <span class="list-section-title">{$t(cat || "Other")}</span>
            </div>
            <div class="list-rows">
              {#each categorizedButtons[cat] as b}
                {@const isDisabled =
                  disableActions && !b.isProcessRunning && !b.alwaysEnabled}
                {@const icon = getTaskIcon(b.option.label)}
                <button
                  class="list-row"
                  class:active={b.isProcessRunning}
                  disabled={isDisabled}
                  title={isDisabled
                    ? $t("Stop the running task before starting another")
                    : undefined}
                  onclick={b.callback}
                >
                  <div class="list-icon" style="--icon-color: {icon.color}">
                    <svg
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="currentColor"
                      stroke-width="1.8"
                      stroke-linecap="round"
                      stroke-linejoin="round"
                      width="14"
                      height="14"
                    >
                      <path d={icon.path} />
                    </svg>
                  </div>
                  <div class="list-text">
                    <div class="list-row-top">
                      <span class="list-label">{$t(b.option.label)}</span>
                      {#if b.isProcessRunning}
                        <span class="running-tag">● {$t("Run")}</span>
                      {/if}
                    </div>
                    {#if b.option.tooltip}
                      <div class="list-hint">{$t(b.option.tooltip)}</div>
                    {/if}
                  </div>
                </button>
              {/each}
            </div>
          </div>
        {/each}
      </div>
    {/if}
  </div>
</div>

<style>
  .task-grid-container {
    display: flex;
    flex-direction: column;
    gap: 18px;
    height: 100%;
  }

  .toolbar {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 0 20px;
    margin-top: 18px;
  }

  .search-box {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 7px 10px;
    border-radius: 10px;
    flex: 1;
    background: var(--bg-1);
    border: 1px solid var(--line);
  }

  .search-icon {
    color: var(--text-3);
  }

  .search-clear {
    color: var(--text-3);
    display: grid;
    place-items: center;
    border-radius: 4px;
    padding: 2px;
    transition: color var(--dur-1);
  }

  .search-clear:hover {
    color: var(--text-1);
  }

  .search-input {
    flex: 1;
    background: transparent;
    border: 0;
    outline: 0;
    color: var(--text-1);
    font-size: 13px;
    font-family: inherit;
  }

  .variant-toggle {
    display: flex;
    padding: 2px;
    border-radius: 10px;
    background: var(--bg-1);
    border: 1px solid var(--line);
  }

  .v-btn {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 5px 10px;
    border-radius: 8px;
    font-size: 12px;
    font-weight: 500;
    background: transparent;
    color: var(--text-3);
    transition: all var(--dur-1);
  }

  .v-btn:not(.active):hover {
    background: var(--bg-2);
    color: var(--text-2);
  }

  .v-btn.active {
    background: var(--bg-3);
    color: var(--text-1);
  }

  .view-content {
    flex: 1;
    overflow-y: auto;
    padding-bottom: 20px;
  }

  .section {
    padding: 0 20px;
    margin-bottom: 24px;
  }

  .section-header {
    display: flex;
    align-items: center;
    gap: 10px;
    margin-bottom: 10px;
  }

  .section-title {
    font-size: 11px;
    font-weight: 600;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: var(--text-3);
  }

  .section-line {
    height: 1px;
    flex: 1;
    background: var(--line-soft);
  }

  .grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
    gap: 10px;
  }

  .task-card {
    position: relative;
    padding: 14px;
    border-radius: 12px;
    background: var(--bg-1);
    border: 1px solid var(--line);
    display: flex;
    flex-direction: column;
    gap: 10px;
    min-height: 80px;
    transition:
      transform var(--dur-1),
      border-color var(--dur-1),
      background var(--dur-1),
      box-shadow var(--dur-1);
    text-align: left;
  }

  .empty-search {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 12px;
    padding: 60px 20px;
    color: var(--text-4);
  }

  .empty-search p {
    font-size: 13px;
    color: var(--text-3);
  }

  .empty-search strong {
    color: var(--text-2);
  }

  .task-card:not(:disabled):hover {
    border-color: color-mix(in oklab, var(--accent) 30%, var(--line));
    transform: translateY(-2px);
    box-shadow: 0 8px 20px color-mix(in oklab, var(--accent) 10%, transparent);
  }

  .task-card:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }

  .task-card.active {
    background: color-mix(in oklab, var(--accent) 10%, var(--bg-1));
    border-color: color-mix(in oklab, var(--accent) 45%, transparent);
  }

  .card-icon {
    width: 30px;
    height: 30px;
    border-radius: 8px;
    display: grid;
    place-items: center;
    background: color-mix(in oklab, var(--icon-color) 15%, var(--bg-2));
    color: var(--icon-color);
    flex-shrink: 0;
  }

  .card-top {
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    gap: 8px;
  }

  .card-label {
    font-weight: 600;
    font-size: 13.5px;
    letter-spacing: -0.005em;
  }

  .running-tag {
    font-size: 9px;
    font-weight: 700;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: var(--accent);
    background: var(--accent-ghost);
    padding: 3px 6px;
    border-radius: 4px;
    flex: 0 0 auto;
    display: inline-flex;
    align-items: center;
    gap: 4px;
  }

  .play-box {
    width: 22px;
    height: 22px;
    border-radius: 6px;
    display: grid;
    place-items: center;
    background: var(--bg-2);
    color: var(--text-3);
  }

  .card-hint {
    font-size: 11.5px;
    color: var(--text-3);
    line-height: 1.45;
  }

  /* List View */
  .list-view {
    padding: 0 20px;
    display: flex;
    flex-direction: column;
    gap: 18px;
  }

  .list-section {
    background: var(--bg-1);
    border: 1px solid var(--line);
    border-radius: 12px;
    overflow: hidden;
  }

  .list-section-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 10px 14px 8px;
    border-bottom: 1px solid var(--line-soft);
  }

  .list-section-title {
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: var(--text-3);
  }

  .list-rows {
    display: flex;
    flex-direction: column;
  }

  .list-row {
    width: 100%;
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 10px 14px;
    background: transparent;
    border: 0;
    border-left: 2px solid transparent;
    border-bottom: 1px solid var(--line-soft);
    text-align: left;
    transition:
      background var(--dur-1),
      border-color var(--dur-1);
  }

  .list-row:last-child {
    border-bottom: none;
  }

  .list-row:not(:disabled):hover {
    background: var(--bg-hover);
  }

  .list-row:disabled {
    opacity: 0.45;
    cursor: not-allowed;
  }

  .list-row.active {
    background: color-mix(in oklab, var(--accent) 8%, var(--bg-1));
    border-left-color: var(--accent);
  }

  .list-icon {
    width: 30px;
    height: 30px;
    border-radius: 8px;
    display: grid;
    place-items: center;
    background: color-mix(in oklab, var(--icon-color) 18%, var(--bg-2));
    color: var(--icon-color);
    flex: 0 0 30px;
  }

  .list-text {
    flex: 1;
    min-width: 0;
  }

  .list-row-top {
    display: flex;
    align-items: center;
    gap: 8px;
  }

  .list-label {
    font-weight: 600;
    font-size: 13.5px;
    color: var(--text-1);
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .list-hint {
    font-size: 11.5px;
    color: var(--text-3);
    margin-top: 2px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }
</style>
